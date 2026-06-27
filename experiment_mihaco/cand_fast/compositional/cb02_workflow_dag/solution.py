"""cb02_workflow_dag — YAML workflow DAG analyser."""

import yaml
import networkx
from jinja2 import Environment, BaseLoader


TEMPLATE_STR = """\
<div class="workflow-report">
{% if layers %}
{% for layer in layers %}
<div class="layer">
<h2>Layer {{ loop.index }}: {{ layer | join(', ') }}</h2>
</div>
{% endfor %}
{% else %}
<div class="layer"><h2>Layer list empty — no tasks defined</h2></div>
{% endif %}
</div>
"""


def build_report(yaml_text: str) -> dict:
    """Parse a YAML workflow definition, build a DAG, compute layers, and render HTML.

    Args:
        yaml_text: YAML string with a top-level 'tasks' key.

    Returns:
        dict with keys 'layers', 'order', and 'html'.

    Raises:
        ValueError: if the workflow contains a cycle.
    """
    # Step 1: Parse YAML; handle absent/null tasks key
    data = yaml.safe_load(yaml_text) or {}
    tasks = data.get("tasks") or []

    # Build set of declared task names for ghost-node guard
    declared_names = {t["name"] for t in tasks}

    # Step 2: Build directed graph — add all declared nodes first
    G = networkx.DiGraph()
    G.add_nodes_from(declared_names)

    for task in tasks:
        name = task["name"]
        deps = task.get("deps") or []
        for dep in deps:
            # Only add edges for declared dep names (guard against ghost nodes)
            if dep in declared_names:
                G.add_edge(dep, name)
            # If dep not declared, it's an invalid reference — raise ValueError
            else:
                raise ValueError(
                    f"Task '{name}' depends on undeclared task '{dep}'"
                )

    # Step 3: Cycle detection
    if not networkx.is_directed_acyclic_graph(G):
        raise ValueError("Workflow contains a cycle")

    # Step 4: Compute layers via peel-sources algorithm on a mutable copy
    H = G.copy()
    layers = []
    while H.number_of_nodes() > 0:
        sources = sorted(n for n, d in H.in_degree() if d == 0)
        layers.append(sources)
        H.remove_nodes_from(sources)

    # Step 5: Compute topological order by flattening layers
    order = [t for layer in layers for t in layer]

    # Step 6: Render HTML with Jinja2
    env = Environment(loader=BaseLoader())
    tmpl = env.from_string(TEMPLATE_STR)
    html = tmpl.render(layers=layers)

    # Step 7: Return result dict
    return {"layers": layers, "order": order, "html": html}
