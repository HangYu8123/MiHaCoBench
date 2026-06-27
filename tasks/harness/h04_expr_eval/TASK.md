# Harness 04 — `expr_eval`: Arithmetic Expression Evaluator with Precise Precedence

**Created:** 2026-06-18 · **Category:** harness · **Weight:** 4

Evaluate an arithmetic expression over the real numbers. The difficulty is
entirely in the **precedence and associativity lattice** — in particular how
unary minus and the right-associative power operator `**` interact. Getting any
one of those rules wrong silently changes the value of common expressions.

Implement your solution in a single file `solution.py`. It uses only the Python
standard library (no third-party packages).

## Public contract

### `evaluate(expr: str) -> float`

Evaluate the arithmetic expression `expr` and return a **`float`**.

**Grammar tokens.** Non-negative integer and decimal literals (`12`, `3.5`,
`.5`, `2.`), the binary operators `+` `-` `*` `/` `**`, unary `+` and unary `-`,
and parentheses `(` `)`. **All whitespace is insignificant.**

**Operator precedence, lowest (binds loosest) to highest (binds tightest):**

1. binary `+` `-`  — **left-associative**
2. binary `*` `/`  — **left-associative**; `/` is **true division** (always a `float`, never floor division)
3. **unary** `+` `-`
4. `**`  — **right-associative**, and it **binds tighter than unary minus**

The result is **always** a Python `float`.

**Consequences of this lattice** (each holds exactly):

```python
evaluate("-2 ** 2")   == -4.0     # unary minus is looser than **, so this is -(2 ** 2)
evaluate("2 ** 3 ** 2") == 512.0  # ** is right-associative: 2 ** (3 ** 2) = 2 ** 9
evaluate("2 ** -2")   == 0.25     # a unary minus IS allowed as the exponent's operand
evaluate("-2 ** -2")  == -0.25    # = -(2 ** (-2))
evaluate("--3")       == 3.0      # double unary minus
evaluate("-(3 + 4)")  == -7.0     # unary minus over a parenthesised group
evaluate("(1 + 2) * 3") == 9.0    # parentheses override precedence
evaluate("8 / 2 / 2") == 2.0      # left-associative: (8 / 2) / 2
evaluate("1 + 2 * 3") == 7.0      # * binds tighter than +
evaluate("2 ** 3 * 2") == 16.0    # ** binds tighter than *: (2 ** 3) * 2
evaluate("10 / 4")    == 2.5      # true division
evaluate(".5 + 2.")   == 2.5      # leading-dot and trailing-dot literals
```

### Exception contract

| Condition | Raise |
|-----------|-------|
| division by zero, or `0` raised to a **negative** power (e.g. `0 ** -1`) | `ZeroDivisionError` |
| a malformed expression: empty/blank input, unbalanced parentheses, a missing or trailing operand, two adjacent binary operators, or an unknown character | `ValueError` |

Examples of malformed input that raise `ValueError`: `""`, `"("`, `"1 + 2)"`,
`"1 +"`, `"* 3"`, `"** 3"`, `"2 **"`, `"1 2"`, `"1 +* 2"`, `"3 $ 4"`, `"()"`,
`"."`, `"1..2"`.

Assert exception **types**; messages are unspecified.

## Notes

* `evaluate` must be **pure** (no global state) and **deterministic**: the value
  is fully determined by `expr`; no seeds are needed.
* The grader checks **behaviour** against the contract above. You may implement
  the evaluator however you like, but it must define its own `evaluate`
  callable in `solution.py` that satisfies every rule and worked example.
* Floating-point results are compared with a tolerance, so ordinary `float`
  arithmetic is fine.
