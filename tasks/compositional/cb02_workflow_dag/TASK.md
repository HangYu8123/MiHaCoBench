# Compositional 02 — `cb02_workflow_dag`: YAML workflow DAG analyser

**Created:** 2026-06-15 · **Category:** compositional · **Weight:** 4

Implement a function that parses a YAML workflow definition, builds a
directed acyclic graph, computes execution layers, and renders an HTML
report.  Write your solution as **`solution.py`**.

You **must** use `yaml` (PyYAML), `networkx`, and `jinja2` — each library
must appear in your source code.

## Public contract (must match exactly)

```python
def build_report(yaml_text: str) -> dict:
    ...
```

### Input

`yaml_text` is a YAML string describing a workflow.  Its top-level key is
`tasks`, a list of task objects.  Each task object has:

| Field  | Type           | Description                                     |
|--------|----------------|-------------------------------------------------|
| `name` | `str`          | Unique task name                                |
| `deps` | `list[str]`    | Names of tasks this task depends on (may be absent / empty) |

Example:

```yaml
tasks:
  - name: A
  - name: B
    deps: [A]
  - name: C
    deps: [A]
  - name: D
    deps: [B, C]
```

### Output

The function returns a **`dict`** with exactly these three keys:

| Key      | Type                  | Description                                                                 |
|----------|-----------------------|-----------------------------------------------------------------------------|
| `layers` | `list[list[str]]`     | Topological layers: layer 0 contains tasks with no unresolved deps; layer 1 contains tasks whose deps are all in layer 0; and so on.  Each inner list is **sorted alphabetically**.  An empty workflow returns `[]`. |
| `order`  | `list[str]`           | A valid topological order of all tasks (every dependency appears before the task that depends on it).  An empty workflow returns `[]`. |
| `html`   | `str`                 | An HTML string rendered with Jinja2 that contains the substring `'Layer'` and mentions every task name at least once. |

### Cycle detection

If the workflow contains a cycle, `build_report` **must raise `ValueError`**.

### Empty workflow

An input with no tasks (e.g. `tasks: []` or `tasks:` absent) must return
`{"layers": [], "order": [], "html": <some non-empty string>}`.

## Notes

* The `layers` computation is the standard "peel the sources" algorithm:
  remove all nodes with in-degree 0, collect them (sorted) as a layer,
  repeat on the remaining graph.
* `order` must be a valid topological sort — you may derive it by
  flattening `layers` or by using `networkx.topological_sort`.
* The `html` value need not be a full HTML document; a fragment is fine,
  as long as it contains the word `Layer` and all task names.
* Fixed seeds are not required (no randomness in this task).
