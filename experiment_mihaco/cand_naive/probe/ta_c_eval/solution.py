def evaluate(expr: str) -> int:
    def tokenize(s: str):
        tokens = []
        i = 0
        n = len(s)
        while i < n:
            c = s[i]
            if c.isspace():
                i += 1
                continue
            if c.isdigit():
                j = i
                while j < n and s[j].isdigit():
                    j += 1
                tokens.append(("NUM", int(s[i:j])))
                i = j
                continue
            if c in "+-*/%()":
                tokens.append((c, c))
                i += 1
                continue
            raise ValueError(f"unknown character: {c!r}")
        return tokens

    def trunc_div(a: int, b: int) -> int:
        if b == 0:
            raise ZeroDivisionError("division by zero")
        q = abs(a) // abs(b)
        if (a < 0) != (b < 0):
            q = -q
        return q

    def trunc_mod(a: int, b: int) -> int:
        if b == 0:
            raise ZeroDivisionError("modulo by zero")
        return a - trunc_div(a, b) * b

    tokens = tokenize(expr)
    pos = 0

    def peek():
        return tokens[pos][0] if pos < len(tokens) else None

    def advance():
        nonlocal pos
        tok = tokens[pos]
        pos += 1
        return tok

    def parse_expr() -> int:
        value = parse_term()
        while peek() in ("+", "-"):
            op = advance()[0]
            rhs = parse_term()
            if op == "+":
                value = value + rhs
            else:
                value = value - rhs
        return value

    def parse_term() -> int:
        value = parse_factor()
        while peek() in ("*", "/", "%"):
            op = advance()[0]
            rhs = parse_factor()
            if op == "*":
                value = value * rhs
            elif op == "/":
                value = trunc_div(value, rhs)
            else:
                value = trunc_mod(value, rhs)
        return value

    def parse_factor() -> int:
        tok = peek()
        if tok == "+":
            advance()
            return parse_factor()
        if tok == "-":
            advance()
            return -parse_factor()
        return parse_atom()

    def parse_atom() -> int:
        tok = peek()
        if tok is None:
            raise ValueError("unexpected end of expression")
        if tok == "NUM":
            return advance()[1]
        if tok == "(":
            advance()
            value = parse_expr()
            if peek() != ")":
                raise ValueError("unbalanced parentheses: expected ')'")
            advance()
            return value
        raise ValueError(f"unexpected token: {tok!r}")

    if not tokens:
        raise ValueError("empty expression")

    result = parse_expr()
    if pos != len(tokens):
        raise ValueError("trailing tokens after valid expression")
    return result
