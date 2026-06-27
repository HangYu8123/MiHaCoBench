"""
cb02_workflow_dag — YAML workflow DAG analyser
"""

import yaml
import networkx as nx
from jinja2 import Template


_HTML_TEMPLATE = """
<html>
<body>
<h1>Workflow DAG Report</h1>
{% if layers %}
{% for layer in layers %}
<h2>Layer {{ loop.index0 }}</h2>
<ul>
{% for task in layer %}
<li>{{ task }}</li>
{% endfor %}
</ul>
{% endfor %}
<h2>Topological Order</h2>
<ol>
{% for task in order %}
<li>{{ task }}</li>
{% endfor %}
</ol>
{% else %}
<p>Layer: (empty workflow — no tasks defined)</p>
{% endif %}
</body>
</html>
"""


def build_report(yaml_text: str) -> dict:
    """
    Parse a YAML workflow definition, build a DAG, compute execution layers,
    and render an HTML report.

    Parameters
    ----------
    yaml_text : str
        YAML string with a top-level 'tasks' key.

    Returns
    -------
    dict with keys:
        'layers' : list[list[str]]  — topological layers, each sorted alphabetically
        'order'  : list[str]        — valid topological order
        'html'   : str              — HTML fragment mentioning 'Layer' and all task names
    """
    data = yaml.safe_load(yaml_text) or {}
    tasks = data.get("tasks") or []

    if not tasks:
        tmpl = Template(_HTML_TEMPLATE)
        html = tmpl.render(layers=[], order=[])
        return {"layers": [], "order": [], "html": html}

    # Build directed graph
    G = nx.DiGraph()

    for task in tasks:
        name = task["name"]
        G.add_node(name)

    for task in tasks:
        name = task["name"]
        deps = task.get("deps") or []
        for dep in deps:
            # Edge from dep -> name (dep must come before name)
            G.add_edge(dep, name)

    # Cycle detection
    if not nx.is_directed_acyclic_graph(G):
        raise ValueError("Workflow contains a cycle")

    # Compute topological layers ("peel the sources" algorithm)
    layers = []
    remaining = G.copy()
    while remaining.number_of_nodes() > 0:
        # Find all nodes with in-degree 0
        sources = sorted([n for n, d in remaining.in_degree() if d == 0])
        layers.append(sources)
        remaining.remove_nodes_from(sources)

    # Compute topological order by flattening layers
    order = [task for layer in layers for task in layer]

    # Render HTML with Jinja2
    tmpl = Template(_HTML_TEMPLATE)
    html = tmpl.render(layers=layers, order=order)

    return {"layers": layers, "order": order, "html": html}
