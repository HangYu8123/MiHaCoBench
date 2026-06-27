import re


class Database:
    def __init__(self):
        self.tables = {}

    def _tokenize(self, sql):
        tokens = []
        i = 0
        n = len(sql)
        while i < n:
            c = sql[i]
            if c.isspace():
                i += 1
                continue
            if c == "'":
                j = i + 1
                buf = []
                closed = False
                while j < n:
                    if sql[j] == "'":
                        if j + 1 < n and sql[j + 1] == "'":
                            buf.append("'")
                            j += 2
                            continue
                        else:
                            closed = True
                            j += 1
                            break
                    else:
                        buf.append(sql[j])
                        j += 1
                if not closed:
                    raise ValueError("unterminated string literal")
                tokens.append(("str", "".join(buf)))
                i = j
                continue
            if c in "<>":
                if i + 1 < n and sql[i + 1] == "=":
                    tokens.append(("op", c + "="))
                    i += 2
                    continue
                if c == "<" and i + 1 < n and sql[i + 1] == ">":
                    tokens.append(("op", "<>"))
                    i += 2
                    continue
                tokens.append(("op", c))
                i += 1
                continue
            if c == "=":
                tokens.append(("op", "="))
                i += 1
                continue
            if c in "(),*":
                tokens.append(("punct", c))
                i += 1
                continue
            if c == "-" or c.isdigit():
                m = re.match(r"-?\d+", sql[i:])
                if m and (c.isdigit() or (c == "-" and m.group(0) != "-")):
                    text = m.group(0)
                    end = i + len(text)
                    if end < n and (sql[end].isalnum() or sql[end] == "_"):
                        raise ValueError("malformed numeric literal")
                    tokens.append(("num", int(text)))
                    i = end
                    continue
                raise ValueError("unexpected character '-'")
            if c.isalpha() or c == "_":
                m = re.match(r"[A-Za-z_][A-Za-z0-9_]*", sql[i:])
                text = m.group(0)
                tokens.append(("word", text))
                i += len(text)
                continue
            raise ValueError("unexpected character %r" % c)
        return tokens

    class _Stream:
        def __init__(self, tokens):
            self.tokens = tokens
            self.pos = 0

        def peek(self):
            if self.pos < len(self.tokens):
                return self.tokens[self.pos]
            return (None, None)

        def next(self):
            tok = self.peek()
            self.pos += 1
            return tok

        def at_end(self):
            return self.pos >= len(self.tokens)

        def expect_punct(self, p):
            t = self.next()
            if t[0] != "punct" or t[1] != p:
                raise ValueError("expected %r" % p)

        def expect_word_ci(self, w):
            t = self.next()
            if t[0] != "word" or t[1].upper() != w.upper():
                raise ValueError("expected keyword %s" % w)

        def is_word_ci(self, w):
            t = self.peek()
            return t[0] == "word" and t[1].upper() == w.upper()

        def is_punct(self, p):
            t = self.peek()
            return t[0] == "punct" and t[1] == p

        def take_word(self):
            t = self.next()
            if t[0] != "word":
                raise ValueError("expected identifier")
            return t[1]

    def execute(self, sql):
        tokens = self._tokenize(sql)
        if not tokens:
            raise ValueError("empty statement")
        first = tokens[0]
        if first[0] != "word":
            raise ValueError("statement must begin with a keyword")
        kw = first[1].upper()
        if kw == "CREATE":
            return self._exec_create(tokens)
        elif kw == "INSERT":
            return self._exec_insert(tokens)
        elif kw == "SELECT":
            return self._exec_select(tokens)
        else:
            raise ValueError("unsupported statement")

    def _exec_create(self, tokens):
        s = self._Stream(tokens)
        s.expect_word_ci("CREATE")
        s.expect_word_ci("TABLE")
        table = s.take_word()
        s.expect_punct("(")
        columns = []
        types = {}
        while True:
            col = s.take_word()
            tt = s.next()
            if tt[0] != "word":
                raise ValueError("expected column type")
            ttype = tt[1].upper()
            if ttype not in ("INT", "TEXT"):
                raise ValueError("unknown type %s" % tt[1])
            if col in types:
                raise ValueError("duplicate column name %s" % col)
            columns.append(col)
            types[col] = ttype
            if s.is_punct(","):
                s.next()
                continue
            break
        s.expect_punct(")")
        if not s.at_end():
            raise ValueError("trailing tokens after CREATE TABLE")
        if not columns:
            raise ValueError("table requires at least one column")
        if table in self.tables:
            raise ValueError("table %s already exists" % table)
        self.tables[table] = {"columns": columns, "types": types, "rows": []}
        return None

    def _parse_literal(self, s):
        t = s.peek()
        if t[0] == "num":
            s.next()
            return ("int", t[1])
        if t[0] == "str":
            s.next()
            return ("str", t[1])
        if t[0] == "word" and t[1].upper() == "NULL":
            s.next()
            return ("null", None)
        raise ValueError("expected a literal value")

    def _exec_insert(self, tokens):
        s = self._Stream(tokens)
        s.expect_word_ci("INSERT")
        s.expect_word_ci("INTO")
        table = s.take_word()
        if table not in self.tables:
            raise ValueError("unknown table %s" % table)
        tbl = self.tables[table]

        named_cols = None
        if s.is_punct("("):
            s.next()
            named_cols = []
            while True:
                col = s.take_word()
                named_cols.append(col)
                if s.is_punct(","):
                    s.next()
                    continue
                break
            s.expect_punct(")")

        s.expect_word_ci("VALUES")
        s.expect_punct("(")
        values = []
        while True:
            values.append(self._parse_literal(s))
            if s.is_punct(","):
                s.next()
                continue
            break
        s.expect_punct(")")
        if not s.at_end():
            raise ValueError("trailing tokens after INSERT")

        if named_cols is None:
            if len(values) != len(tbl["columns"]):
                raise ValueError("value count mismatch")
            target_cols = list(tbl["columns"])
        else:
            if len(named_cols) != len(set(named_cols)):
                raise ValueError("duplicate column in INSERT list")
            for col in named_cols:
                if col not in tbl["types"]:
                    raise ValueError("unknown column %s" % col)
            if len(values) != len(named_cols):
                raise ValueError("value count mismatch")
            target_cols = named_cols

        row = {col: None for col in tbl["columns"]}
        for col, (vtype, vval) in zip(target_cols, values):
            coltype = tbl["types"][col]
            if vtype == "null":
                row[col] = None
            elif vtype == "int":
                if coltype != "INT":
                    raise ValueError("type mismatch on column %s" % col)
                row[col] = vval
            elif vtype == "str":
                if coltype != "TEXT":
                    raise ValueError("type mismatch on column %s" % col)
                row[col] = vval
            else:
                raise ValueError("bad literal")
        tbl["rows"].append(row)
        return None

    _AGG_FUNCS = ("COUNT", "SUM", "AVG", "MIN", "MAX")

    def _exec_select(self, tokens):
        s = self._Stream(tokens)
        s.expect_word_ci("SELECT")

        distinct = False
        if s.is_word_ci("DISTINCT"):
            s.next()
            distinct = True

        select_list, is_star = self._parse_select_list(s)

        s.expect_word_ci("FROM")
        table = s.take_word()
        if table not in self.tables:
            raise ValueError("unknown table %s" % table)
        tbl = self.tables[table]
        types = tbl["types"]
        columns = tbl["columns"]

        where_ast = None
        if s.is_word_ci("WHERE"):
            s.next()
            where_ast = self._parse_or(s)

        group_cols = None
        if s.is_word_ci("GROUP"):
            s.next()
            s.expect_word_ci("BY")
            group_cols = []
            while True:
                col = s.take_word()
                if col not in types:
                    raise ValueError("unknown column in GROUP BY: %s" % col)
                group_cols.append(col)
                if s.is_punct(","):
                    s.next()
                    continue
                break

        order_keys = None
        if s.is_word_ci("ORDER"):
            s.next()
            s.expect_word_ci("BY")
            order_keys = []
            while True:
                col = s.take_word()
                if col not in types:
                    raise ValueError("unknown column in ORDER BY: %s" % col)
                direction = "ASC"
                if s.is_word_ci("ASC"):
                    s.next()
                    direction = "ASC"
                elif s.is_word_ci("DESC"):
                    s.next()
                    direction = "DESC"
                order_keys.append((col, direction))
                if s.is_punct(","):
                    s.next()
                    continue
                break

        limit = None
        offset = None
        while s.is_word_ci("LIMIT") or s.is_word_ci("OFFSET"):
            if s.is_word_ci("LIMIT"):
                if limit is not None:
                    raise ValueError("duplicate LIMIT")
                s.next()
                t = s.next()
                if t[0] != "num":
                    raise ValueError("LIMIT expects an integer")
                if t[1] < 0:
                    raise ValueError("LIMIT must be non-negative")
                limit = t[1]
            else:
                if offset is not None:
                    raise ValueError("duplicate OFFSET")
                s.next()
                t = s.next()
                if t[0] != "num":
                    raise ValueError("OFFSET expects an integer")
                if t[1] < 0:
                    raise ValueError("OFFSET must be non-negative")
                offset = t[1]

        if not s.at_end():
            raise ValueError("trailing tokens after SELECT")

        has_aggregate = any(e["kind"] == "agg" for e in select_list) if not is_star else False

        if not is_star:
            for e in select_list:
                if e["kind"] == "col":
                    if e["col"] not in types:
                        raise ValueError("unknown column %s" % e["col"])
                elif e["kind"] == "agg":
                    if e["func"] != "COUNT" or e["arg"] != "*":
                        if e["arg"] != "*" and e["arg"] not in types:
                            raise ValueError("unknown column %s" % e["arg"])

        if is_star and group_cols is not None:
            raise ValueError("'*' cannot combine with GROUP BY")

        if where_ast is not None:
            self._validate_where(where_ast, types)

        grouping = group_cols is not None
        if grouping:
            gset = set(group_cols)
            for e in select_list:
                if e["kind"] == "col":
                    if e["col"] not in gset:
                        raise ValueError("non-aggregated column %s not in GROUP BY" % e["col"])
            if order_keys is not None:
                for col, _ in order_keys:
                    if col not in gset:
                        raise ValueError("ORDER BY column %s must be a grouping column" % col)

        rows = tbl["rows"]
        if where_ast is not None:
            filtered = [r for r in rows if self._eval_where(where_ast, r, types) is True]
        else:
            filtered = list(rows)

        if grouping:
            result_rows, sort_source = self._do_grouped(filtered, select_list, group_cols)
        elif has_aggregate:
            out = self._project_aggregate_group(filtered, select_list)
            result_rows = [out]
            sort_source = [None]
        else:
            result_rows = []
            sort_source = []
            if is_star:
                for r in filtered:
                    result_rows.append({c: r[c] for c in columns})
                    sort_source.append(r)
            else:
                for r in filtered:
                    out = {}
                    for e in select_list:
                        out[e["key"]] = r[e["col"]]
                    result_rows.append(out)
                    sort_source.append(r)

        if distinct:
            seen = set()
            dr = []
            ds = []
            for out, src in zip(result_rows, sort_source):
                key = self._row_dedupe_key(out)
                if key not in seen:
                    seen.add(key)
                    dr.append(out)
                    ds.append(src)
            result_rows = dr
            sort_source = ds

        if order_keys is not None:
            indexed = list(zip(result_rows, sort_source, range(len(result_rows))))
            for col, direction in reversed(order_keys):
                desc = direction == "DESC"

                def sort_key(item, _col=col, _desc=desc):
                    src = item[1]
                    val = src[_col] if src is not None else None
                    is_null = val is None
                    if _desc:
                        return (1 if is_null else 0, _NegKey(val) if not is_null else None)
                    else:
                        return (0 if is_null else 1, val if not is_null else None)

                indexed.sort(key=sort_key)
            result_rows = [item[0] for item in indexed]

        if offset is not None:
            result_rows = result_rows[offset:]
        if limit is not None:
            result_rows = result_rows[:limit]

        return result_rows

    def _row_dedupe_key(self, row):
        items = []
        for k in row:
            v = row[k]
            if v is None:
                items.append((k, 0, None))
            elif isinstance(v, bool):
                items.append((k, 1, ("bool", v)))
            elif isinstance(v, int):
                items.append((k, 1, ("int", v)))
            elif isinstance(v, float):
                items.append((k, 1, ("float", v)))
            else:
                items.append((k, 1, ("str", v)))
        return tuple(items)

    def _parse_select_list(self, s):
        if s.is_punct("*"):
            s.next()
            return ([], True)
        entries = []
        while True:
            entry = self._parse_select_entry(s)
            entries.append(entry)
            if s.is_punct(","):
                s.next()
                continue
            break
        return (entries, False)

    def _parse_select_entry(self, s):
        t = s.peek()
        if t[0] == "word" and t[1].upper() in self._AGG_FUNCS:
            save = s.pos
            func = t[1].upper()
            s.next()
            if s.is_punct("("):
                s.next()
                if func == "COUNT" and s.is_punct("*"):
                    s.next()
                    s.expect_punct(")")
                    arg = "*"
                else:
                    if s.is_punct("*"):
                        raise ValueError("'*' only allowed in COUNT")
                    arg = s.take_word()
                    s.expect_punct(")")
                key = "%s(%s)" % (func, arg)
                entry = {"kind": "agg", "func": func, "arg": arg, "key": key, "src": key}
                if s.is_word_ci("AS"):
                    s.next()
                    alias = s.take_word()
                    entry["key"] = alias
                return entry
            else:
                s.pos = save
                col = s.take_word()
                entry = {"kind": "col", "col": col, "key": col, "src": col}
                if s.is_word_ci("AS"):
                    s.next()
                    alias = s.take_word()
                    entry["key"] = alias
                return entry
        col = s.take_word()
        entry = {"kind": "col", "col": col, "key": col, "src": col}
        if s.is_word_ci("AS"):
            s.next()
            alias = s.take_word()
            entry["key"] = alias
        return entry

    def _parse_or(self, s):
        left = self._parse_and(s)
        while s.is_word_ci("OR"):
            s.next()
            right = self._parse_and(s)
            left = ("or", left, right)
        return left

    def _parse_and(self, s):
        left = self._parse_not(s)
        while s.is_word_ci("AND"):
            s.next()
            right = self._parse_not(s)
            left = ("and", left, right)
        return left

    def _parse_not(self, s):
        if s.is_word_ci("NOT"):
            s.next()
            operand = self._parse_not(s)
            return ("not", operand)
        return self._parse_primary(s)

    def _parse_primary(self, s):
        if s.is_punct("("):
            s.next()
            inner = self._parse_or(s)
            s.expect_punct(")")
            return inner
        return self._parse_predicate(s)

    def _parse_predicate(self, s):
        left = self._parse_operand(s)
        if s.is_word_ci("IS"):
            s.next()
            negate = False
            if s.is_word_ci("NOT"):
                s.next()
                negate = True
            s.expect_word_ci("NULL")
            if left[0] != "col":
                raise ValueError("IS NULL requires a column operand")
            return ("isnull", left[1], negate)
        t = s.peek()
        if t[0] != "op":
            raise ValueError("expected comparison operator")
        op = t[1]
        s.next()
        right = self._parse_operand(s)
        if left[0] == "col" and right[0] == "col":
            raise ValueError("comparison between two columns not supported")
        if left[0] == "lit" and right[0] == "lit":
            raise ValueError("comparison between two literals not supported")
        return ("cmp", op, left, right)

    def _parse_operand(self, s):
        t = s.peek()
        if t[0] == "num":
            s.next()
            return ("lit", "int", t[1])
        if t[0] == "str":
            s.next()
            return ("lit", "str", t[1])
        if t[0] == "word":
            if t[1].upper() == "NULL":
                s.next()
                return ("lit", "null", None)
            s.next()
            return ("col", t[1])
        raise ValueError("expected operand")

    def _validate_where(self, ast, types):
        kind = ast[0]
        if kind in ("and", "or"):
            self._validate_where(ast[1], types)
            self._validate_where(ast[2], types)
        elif kind == "not":
            self._validate_where(ast[1], types)
        elif kind == "isnull":
            col = ast[1]
            if col not in types:
                raise ValueError("unknown column %s" % col)
        elif kind == "cmp":
            _, op, left, right = ast
            col_operand = None
            lit_operand = None
            if left[0] == "col":
                col_operand = left[1]
            elif left[0] == "lit":
                lit_operand = left
            if right[0] == "col":
                col_operand = right[1]
            elif right[0] == "lit":
                lit_operand = right
            if col_operand is None:
                raise ValueError("comparison requires a column")
            if col_operand not in types:
                raise ValueError("unknown column %s" % col_operand)
            coltype = types[col_operand]
            if lit_operand is not None and lit_operand[1] != "null":
                littype = lit_operand[1]
                if coltype == "INT" and littype != "int":
                    raise ValueError("type mismatch in comparison")
                if coltype == "TEXT" and littype != "str":
                    raise ValueError("type mismatch in comparison")
        else:
            raise ValueError("bad WHERE ast")

    def _eval_where(self, ast, row, types):
        kind = ast[0]
        if kind == "and":
            a = self._eval_where(ast[1], row, types)
            b = self._eval_where(ast[2], row, types)
            return self._kleene_and(a, b)
        if kind == "or":
            a = self._eval_where(ast[1], row, types)
            b = self._eval_where(ast[2], row, types)
            return self._kleene_or(a, b)
        if kind == "not":
            a = self._eval_where(ast[1], row, types)
            return self._kleene_not(a)
        if kind == "isnull":
            col = ast[1]
            negate = ast[2]
            isnull = row[col] is None
            if negate:
                return not isnull
            return isnull
        if kind == "cmp":
            _, op, left, right = ast
            lval = self._operand_value(left, row)
            rval = self._operand_value(right, row)
            if lval is None or rval is None:
                return None
            return self._compare(op, lval, rval)
        raise ValueError("bad WHERE ast")

    def _operand_value(self, operand, row):
        if operand[0] == "col":
            return row[operand[1]]
        if operand[1] == "null":
            return None
        return operand[2]

    def _compare(self, op, a, b):
        if op == "=":
            return a == b
        if op == "<>":
            return a != b
        if op == "<":
            return a < b
        if op == "<=":
            return a <= b
        if op == ">":
            return a > b
        if op == ">=":
            return a >= b
        raise ValueError("bad operator %s" % op)

    @staticmethod
    def _kleene_and(a, b):
        if a is False or b is False:
            return False
        if a is True and b is True:
            return True
        return None

    @staticmethod
    def _kleene_or(a, b):
        if a is True or b is True:
            return True
        if a is False and b is False:
            return False
        return None

    @staticmethod
    def _kleene_not(a):
        if a is None:
            return None
        return not a

    def _do_grouped(self, rows, select_list, group_cols):
        order = []
        groups = {}
        for r in rows:
            key = tuple(_GroupVal(r[c]) for c in group_cols)
            if key not in groups:
                groups[key] = []
                order.append(key)
            groups[key].append(r)
        result_rows = []
        sort_source = []
        for key in order:
            grp = groups[key]
            out = self._project_aggregate_group(grp, select_list, group_cols=group_cols, group_rep=grp[0])
            result_rows.append(out)
            sort_source.append(grp[0])
        return result_rows, sort_source

    def _project_aggregate_group(self, group_rows, select_list, group_cols=None, group_rep=None):
        out = {}
        for e in select_list:
            if e["kind"] == "col":
                if group_rep is not None:
                    out[e["key"]] = group_rep[e["col"]]
                else:
                    out[e["key"]] = None
            else:
                out[e["key"]] = self._compute_aggregate(e["func"], e["arg"], group_rows)
        return out

    def _compute_aggregate(self, func, arg, group_rows):
        if func == "COUNT":
            if arg == "*":
                return len(group_rows)
            return sum(1 for r in group_rows if r[arg] is not None)
        vals = [r[arg] for r in group_rows if r[arg] is not None]
        if func == "SUM":
            if not vals:
                return None
            total = 0
            for v in vals:
                total += v
            return total
        if func == "AVG":
            if not vals:
                return None
            return sum(vals) / len(vals)
        if func == "MIN":
            if not vals:
                return None
            return min(vals)
        if func == "MAX":
            if not vals:
                return None
            return max(vals)
        raise ValueError("bad aggregate %s" % func)


class _NegKey:
    __slots__ = ("v",)

    def __init__(self, v):
        self.v = v

    def __lt__(self, other):
        return other.v < self.v

    def __eq__(self, other):
        return isinstance(other, _NegKey) and self.v == other.v


class _GroupVal:
    __slots__ = ("v",)

    def __init__(self, v):
        self.v = v

    def __hash__(self):
        if self.v is None:
            return hash((0,))
        if isinstance(self.v, bool):
            return hash((1, "bool", self.v))
        if isinstance(self.v, int):
            return hash((1, "int", self.v))
        return hash((1, "str", self.v))

    def __eq__(self, other):
        if not isinstance(other, _GroupVal):
            return NotImplemented
        a, b = self.v, other.v
        if a is None or b is None:
            return a is None and b is None
        if isinstance(a, bool) != isinstance(b, bool):
            return False
        if isinstance(a, int) and isinstance(b, int):
            return a == b
        if isinstance(a, str) and isinstance(b, str):
            return a == b
        return type(a) == type(b) and a == b
