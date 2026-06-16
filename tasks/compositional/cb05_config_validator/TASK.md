# Compositional 05 — `config_validator`: YAML Config Validator with Canonical Hashing

**Created:** 2026-06-16 · **Category:** compositional · **Weight:** 4

Implement a small configuration validator that parses a YAML document, validates
it against a typed schema, and returns the validated configuration together with
a canonical SHA-256 fingerprint. The implementation composes four libraries:

* `yaml` (PyYAML, `yaml.safe_load`) — parse the YAML text,
* `re` — apply regex `pattern` constraints to string fields,
* `json` — canonical serialization of the validated config,
* `hashlib` — SHA-256 of the canonical bytes.

Implement your solution in a single file `solution.py`.

## Public contract

### `validate_config(yaml_text: str, schema: dict) -> dict`

Parse `yaml_text` with `yaml.safe_load`, validate the resulting mapping against
`schema`, and return a new dict containing the validated key/value pairs plus an
added `"_hash"` key.

#### Schema shape

`schema` maps each **key name** to a **rule dict**. A rule may contain:

| Rule field | Meaning |
|------------|---------|
| `"type"` | **Required.** One of `"int"`, `"float"`, `"str"`, `"bool"`, `"list"`. |
| `"required"` | Optional `bool`, default `False`. |
| `"default"` | Optional. Value to fill in when the key is **absent** and **not required**. |
| `"pattern"` | Optional regex string. Only meaningful for `type == "str"`. Applied with `re.search`. |
| `"min"` / `"max"` | Optional numeric bounds (inclusive) for `type` `"int"` or `"float"`. |

#### Algorithm

1. `yaml.safe_load(yaml_text)` to obtain a parsed object.
2. Iterate the schema keys in **sorted order** (`sorted(schema)`).
3. Build a `validated` dict from the parsed mapping and the rules.
4. Compute
   `_hash = hashlib.sha256(json.dumps(validated, sort_keys=True, separators=(",", ":")).encode()).hexdigest()`
   over the validated dict **before** the `"_hash"` key is added.
5. Return `validated` with the extra key `"_hash"` set to that hex digest.

A key that is **absent** and has a `"default"` (and is not required) is filled
with the default value **without** type-checking the default.

#### Type matching

A present value matches its rule `type` iff its Python type is:

| `type` | accepted Python type |
|--------|----------------------|
| `"int"` | `int` **but not** `bool` |
| `"float"` | `float` **or** `int` (but not `bool`) |
| `"str"` | `str` |
| `"bool"` | `bool` |
| `"list"` | `list` |

Note: a `bool` value supplied where `type` is `"int"` is a **type error**
(`bool` is not accepted as `int`).

#### Exception contract (assert types only — never messages)

| Condition | Exception |
|-----------|-----------|
| `yaml.safe_load` raises, **or** the parsed result is not a mapping (`dict`) | `ValueError` |
| A key is `required` and absent (and has no usable default) | `KeyError` |
| A present value's Python type does not match the rule `type` | `TypeError` |
| A `str` value fails its `pattern` (`re.search` returns `None`) | `ValueError` |
| A numeric value falls outside `[min, max]` | `ValueError` |

**Precedence, evaluated per key in this exact order:**

```
required-presence (KeyError)  >  type (TypeError)  >  constraint (ValueError)
```

So a **missing required key** raises `KeyError` — the presence check happens
**before** any type or constraint check, and it never substitutes a default for a
required key.

## Notes

* The same `yaml_text` + `schema` must always yield the same `"_hash"`.
* Changing any validated value changes the `"_hash"`.
* `yaml.safe_load` must appear in your source (only `safe_load`, never `yaml.load`).
* No I/O, no randomness, no global state.
