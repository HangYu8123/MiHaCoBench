"""BROKEN reference for compositional/cb02_workflow_dag.

Localized defect: cycle detection is SKIPPED. Cyclic workflows do NOT raise
ValueError; instead the "peel sources" loop exits early (leaving unprocessed
nodes), so the result is silently wrong. Acyclic inputs still produce correct
layers, order, and html.
"""
from __future__ import annotations

import yaml
import networkx as nx
from jinja2 import Template


_HTML_TEMPLATE = """\
<!DOCTYPE html>
<html>
<body>
<h1>Workflow Report</h1>
{% if layers %}
{% for layer in layers %}
<h2>Layer {{ loop.index0 }}</h2>
<ul>
{% for task in layer %}
<li>{{ task }}</li>
{% endfor %}
</ul>
{% endfor %}
{% else %}
<p>No tasks defined.</p>
{% endif %}
</body>
</html>
"""


def build_report(yaml_text: str) -> dict:
    """Parse a YAML workflow, build a DAG, compute layers, render HTML.

    NOTE (broken): cycle detection is intentionally removed.
    Cyclic workflows will NOT raise ValueError.
    """
    data = yaml.safe_load(yaml_text) or {}
    task_list = data.get("tasks") or []

    # Build directed graph
    g = nx.DiGraph()
    for task in task_list:
        name = task["name"]
        g.add_node(name)
        for dep in task.get("deps") or []:
            g.add_edge(dep, name)

    # DEFECT: cycle detection removed — cyclic input silently proceeds

    # Compute topological layers via the "peel sources" algorithm
    # (will terminate early for cyclic graphs, leaving some nodes unprocessed)
    layers: list[list[str]] = []
    remaining = g.copy()
    while remaining.number_of_nodes() > 0:
        sources = sorted(
            [n for n, deg in remaining.in_degree() if deg == 0]
        )
        if not sources:
            # No source found (cycle present) — just break silently instead of raising
            break
        layers.append(sources)
        remaining.remove_nodes_from(sources)

    order: list[str] = [node for layer in layers for node in layer]

    tmpl = Template(_HTML_TEMPLATE)
    html = tmpl.render(layers=layers)

    return {"layers": layers, "order": order, "html": html}
