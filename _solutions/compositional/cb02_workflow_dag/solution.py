"""Gold reference for compositional/cb02_workflow_dag.

Composes pyyaml + networkx + jinja2 to parse a YAML workflow,
build a DAG, compute topological layers, and render an HTML report.
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

    Parameters
    ----------
    yaml_text:
        YAML string with a top-level ``tasks`` key (list of ``{name, deps}``).

    Returns
    -------
    dict with keys:
        layers : list[list[str]]  — topological layers, each inner list sorted.
        order  : list[str]        — a valid topological order.
        html   : str              — HTML fragment rendered with Jinja2.

    Raises
    ------
    ValueError
        If the workflow contains a cycle.
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

    # Detect cycles
    if not nx.is_directed_acyclic_graph(g):
        raise ValueError(
            "Workflow contains a cycle: "
            + str(list(nx.find_cycle(g)))
        )

    # Compute topological layers via the "peel sources" algorithm
    layers: list[list[str]] = []
    remaining = g.copy()
    while remaining.number_of_nodes() > 0:
        sources = sorted(
            [n for n, deg in remaining.in_degree() if deg == 0]
        )
        if not sources:
            # Should not happen after cycle check, but guard defensively
            raise ValueError("Unexpected: no source node found after cycle check.")
        layers.append(sources)
        remaining.remove_nodes_from(sources)

    # Valid topological order — flatten layers (already valid since each layer's
    # nodes have all deps satisfied by previous layers)
    order: list[str] = [node for layer in layers for node in layer]

    # Render HTML with Jinja2
    tmpl = Template(_HTML_TEMPLATE)
    html = tmpl.render(layers=layers)

    return {"layers": layers, "order": order, "html": html}
