"""cb02_workflow_dag — YAML workflow DAG analyser."""

import yaml
import networkx as nx
from jinja2 import Template

_HTML_TEMPLATE = Template(
    "<h1>Workflow Layers</h1>\n"
    "{% for i, layer in layers %}"
    "<p>Layer {{ i }}: {{ layer | join(', ') }}</p>\n"
    "{% endfor %}"
)


def build_report(yaml_text: str) -> dict:
    """Parse a YAML workflow, build a DAG, and return layers, order, and HTML.

    Parameters
    ----------
    yaml_text : str
        YAML string with a top-level ``tasks`` key.

    Returns
    -------
    dict
        ``{"layers": list[list[str]], "order": list[str], "html": str}``

    Raises
    ------
    ValueError
        If the workflow contains a cycle.
    """
    # 1. Parse YAML
    data = yaml.safe_load(yaml_text) or {}
    tasks = data.get("tasks") or []

    # 2. Build directed graph
    G = nx.DiGraph()
    for task in tasks:
        name = task["name"]
        G.add_node(name)

    for task in tasks:
        name = task["name"]
        for dep in task.get("deps", []) or []:
            G.add_edge(dep, name)

    # 3. Cycle detection
    if not nx.is_directed_acyclic_graph(G):
        raise ValueError("Cycle detected")

    # 4. Compute topological layers using "peel sources" via topological_generations.
    #    On an empty graph this yields nothing, so layers = [] naturally.
    layers = [sorted(gen) for gen in nx.topological_generations(G)]

    # 5. Topological order — flatten layers (each dep is in a strictly earlier layer)
    order = [node for layer in layers for node in layer]

    # 6. Render HTML with Jinja2.
    #    The static <h1> header always contains 'Layer', even for empty workflows.
    html = _HTML_TEMPLATE.render(layers=list(enumerate(layers, 1)))

    # 7. Return result dict
    return {"layers": layers, "order": order, "html": html}
