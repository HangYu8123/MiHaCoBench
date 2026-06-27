import sys
sys.setrecursionlimit(100000)


class _Parser:
    def __init__(self, pattern):
        self.s = pattern
        self.i = 0
        self.n = len(pattern)

    def _peek(self):
        if self.i < self.n:
            return self.s[self.i]
        return None

    def _next(self):
        c = self.s[self.i]
        self.i += 1
        return c

    def _eof(self):
        return self.i >= self.n

    def parse(self):
        node = self._parse_alt()
        if not self._eof():
            raise ValueError("unexpected character %r at position %d"
                             % (self._peek(), self.i))
        return node

    def _parse_alt(self):
        branches = [self._parse_seq()]
        while self._peek() == '|':
            self._next()
            branches.append(self._parse_seq())
        if len(branches) == 1:
            return branches[0]
        return ('alt', branches)

    def _parse_seq(self):
        nodes = []
        while True:
            c = self._peek()
            if c is None or c == '|' or c == ')':
                break
            nodes.append(self._parse_quant())
        if len(nodes) == 1:
            return nodes[0]
        return ('seq', nodes)

    def _parse_quant(self):
        atom = self._parse_atom()
        c = self._peek()
        if c == '*':
            self._next()
            return ('star', atom)
        if c == '+':
            self._next()
            return ('plus', atom)
        if c == '?':
            self._next()
            return ('opt', atom)
        return atom

    def _parse_atom(self):
        c = self._peek()
        if c is None:
            raise ValueError("unexpected end of pattern")
        if c in ('*', '+', '?'):
            raise ValueError("quantifier %r with nothing to apply to" % c)
        if c == '(':
            self._next()
            inner = self._parse_alt()
            if self._peek() != ')':
                raise ValueError("unbalanced parenthesis")
            self._next()
            return inner
        if c == ')':
            raise ValueError("unexpected ')'")
        if c == '[':
            return self._parse_class()
        if c == '.':
            self._next()
            return ('any',)
        if c == '\\':
            self._next()
            if self._eof():
                raise ValueError("trailing backslash")
            lit = self._next()
            return ('char', lit)
        self._next()
        return ('char', c)

    def _parse_class(self):
        self._next()
        neg = False
        if self._peek() == '^':
            self._next()
            neg = True

        ranges = []
        items = []
        first = True
        while True:
            c = self._peek()
            if c is None:
                raise ValueError("unterminated character class")
            if c == ']' and not first:
                self._next()
                break
            first = False

            if c == '\\':
                self._next()
                if self._eof():
                    raise ValueError("trailing backslash in class")
                lit = self._next()
                items.append(('lit', ord(lit)))
                continue

            if c == '-' and items and items[-1][0] == 'lit' \
                    and self._is_range_continuation():
                self._next()
                nc = self._peek()
                if nc == '\\':
                    self._next()
                    if self._eof():
                        raise ValueError("trailing backslash in class")
                    hi = ord(self._next())
                else:
                    hi = ord(self._next())
                lo = items[-1][1]
                items[-1] = ('range', lo, hi)
                continue

            self._next()
            items.append(('lit', ord(c)))

        for it in items:
            if it[0] == 'lit':
                ranges.append((it[1], it[1]))
            else:
                lo, hi = it[1], it[2]
                if lo > hi:
                    raise ValueError("bad character range")
                ranges.append((lo, hi))

        if not ranges:
            raise ValueError("empty character class")

        return ('class', neg, ranges)

    def _is_range_continuation(self):
        if self.i + 1 >= self.n:
            return False
        nxt = self.s[self.i + 1]
        if nxt == ']':
            return False
        return True


class _NFA:
    def __init__(self):
        self.eps = []
        self.consume = []

    def new_state(self):
        self.eps.append([])
        self.consume.append([])
        return len(self.eps) - 1


def _char_matcher(c):
    return lambda ch: ch == c


def _any_matcher():
    return lambda ch: True


def _class_matcher(neg, ranges):
    def m(ch):
        o = ord(ch)
        inside = False
        for lo, hi in ranges:
            if lo <= o <= hi:
                inside = True
                break
        return inside != neg
    return m


def _compile(node, nfa):
    tag = node[0]

    if tag == 'char':
        s = nfa.new_state()
        e = nfa.new_state()
        nfa.consume[s].append((_char_matcher(node[1]), e))
        return s, e

    if tag == 'any':
        s = nfa.new_state()
        e = nfa.new_state()
        nfa.consume[s].append((_any_matcher(), e))
        return s, e

    if tag == 'class':
        s = nfa.new_state()
        e = nfa.new_state()
        nfa.consume[s].append((_class_matcher(node[1], node[2]), e))
        return s, e

    if tag == 'seq':
        nodes = node[1]
        if not nodes:
            s = nfa.new_state()
            return s, s
        start, cur_out = _compile(nodes[0], nfa)
        for nd in nodes[1:]:
            s2, e2 = _compile(nd, nfa)
            nfa.eps[cur_out].append(s2)
            cur_out = e2
        return start, cur_out

    if tag == 'alt':
        s = nfa.new_state()
        e = nfa.new_state()
        for branch in node[1]:
            bs, be = _compile(branch, nfa)
            nfa.eps[s].append(bs)
            nfa.eps[be].append(e)
        return s, e

    if tag == 'star':
        s = nfa.new_state()
        e = nfa.new_state()
        inner_s, inner_e = _compile(node[1], nfa)
        nfa.eps[s].append(inner_s)
        nfa.eps[s].append(e)
        nfa.eps[inner_e].append(inner_s)
        nfa.eps[inner_e].append(e)
        return s, e

    if tag == 'plus':
        s = nfa.new_state()
        e = nfa.new_state()
        inner_s, inner_e = _compile(node[1], nfa)
        nfa.eps[s].append(inner_s)
        nfa.eps[inner_e].append(inner_s)
        nfa.eps[inner_e].append(e)
        return s, e

    if tag == 'opt':
        s = nfa.new_state()
        e = nfa.new_state()
        inner_s, inner_e = _compile(node[1], nfa)
        nfa.eps[s].append(inner_s)
        nfa.eps[s].append(e)
        nfa.eps[inner_e].append(e)
        return s, e

    raise ValueError("unknown node tag %r" % (tag,))


def _epsilon_closure(nfa, states):
    stack = list(states)
    seen = set(states)
    while stack:
        st = stack.pop()
        for t in nfa.eps[st]:
            if t not in seen:
                seen.add(t)
                stack.append(t)
    return seen


def fullmatch(pattern, text):
    ast = _Parser(pattern).parse()

    nfa = _NFA()
    start, accept = _compile(ast, nfa)

    current = _epsilon_closure(nfa, {start})
    for ch in text:
        nxt = set()
        for st in current:
            for matcher, target in nfa.consume[st]:
                if matcher(ch):
                    nxt.add(target)
        if not nxt:
            return False
        current = _epsilon_closure(nfa, nxt)

    return accept in current
