"""
lexer.py — Tokenizer for the spreadsheet formula language.

Tokens produced:
  ('NUMBER', float)
  ('STRING', str)          # double-quoted string literal, quotes stripped
  ('RANGE', str)           # e.g. 'A1:B3'
  ('CELL', str)            # e.g. 'A1'
  ('FUNC', str)            # IF, SUM, AVG, MIN, MAX
  ('OP', str)              # + - * / ^ ( ) , < <= > >= = <>
"""

import re

# Ordered list of (token_type, compiled_regex) pairs.
# Longer / more-specific patterns come first so they match preferentially.
_TOKEN_PATTERNS = [
    ('SKIP',   re.compile(r'\s+')),
    ('NUMBER', re.compile(r'\d+(?:\.\d*)?(?:[eE][+-]?\d+)?')),
    ('STRING', re.compile(r'"[^"]*"')),
    # RANGE must come before CELL so A1:B3 is one token
    ('RANGE',  re.compile(r'[A-Z]+[0-9]+:[A-Z]+[0-9]+')),
    ('CELL',   re.compile(r'[A-Z]+[0-9]+')),
    ('FUNC',   re.compile(r'(?:IF|SUM|AVG|MIN|MAX)(?=\()')),
    ('OP',     re.compile(r'<>|<=|>=|[+\-*/^(),<>=]')),
]


def tokenize(formula: str) -> list:
    """
    Tokenize *formula* (the part after the leading '=').

    Returns a list of (type, value) tuples.
    Raises ValueError on unrecognised input.
    """
    tokens = []
    pos = 0
    length = len(formula)
    while pos < length:
        matched = False
        for tok_type, pattern in _TOKEN_PATTERNS:
            m = pattern.match(formula, pos)
            if m:
                text = m.group(0)
                if tok_type == 'SKIP':
                    pass  # whitespace — discard
                elif tok_type == 'NUMBER':
                    tokens.append(('NUMBER', float(text)))
                elif tok_type == 'STRING':
                    tokens.append(('STRING', text[1:-1]))  # strip quotes
                elif tok_type == 'RANGE':
                    tokens.append(('RANGE', text))
                elif tok_type == 'CELL':
                    tokens.append(('CELL', text))
                elif tok_type == 'FUNC':
                    tokens.append(('FUNC', text))
                elif tok_type == 'OP':
                    tokens.append(('OP', text))
                pos = m.end()
                matched = True
                break
        if not matched:
            raise ValueError(f"Unexpected character at position {pos}: {formula[pos]!r}")
    return tokens
