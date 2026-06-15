"""Grader for easy/e05_tiny_template.  Tests the public contract only (see TASK.md).

Validity invariant: PASSES on the gold reference, FAILS >=1 test on the broken
reference (which skips HTML escaping).
"""
import pytest

from _lib import grading_utils as gu

CATEGORY, TASK_ID = "easy", "e05_tiny_template"
SOL = gu.require_solution_dir(CATEGORY, TASK_ID)
render = gu.load_callable(SOL, "solution.py", "render")


# --------------------------------------------------------------------------- #
# 1. Simple variable substitution
# --------------------------------------------------------------------------- #

def test_simple_variable():
    result = render("Hello, {{ name }}!", {"name": "World"})
    assert result == "Hello, World!"


def test_simple_variable_no_whitespace():
    """Tags with no inner whitespace still work."""
    result = render("{{greeting}}", {"greeting": "hi"})
    assert result == "hi"


# --------------------------------------------------------------------------- #
# 2. Dotted lookup
# --------------------------------------------------------------------------- #

def test_dotted_variable():
    ctx = {"user": {"first": "Alice", "last": "Smith"}}
    result = render("{{ user.first }} {{ user.last }}", ctx)
    assert result == "Alice Smith"


def test_dotted_deep():
    ctx = {"a": {"b": {"c": "deep"}}}
    result = render("{{ a.b.c }}", ctx)
    assert result == "deep"


# --------------------------------------------------------------------------- #
# 3. HTML escaping — DEFAULT ON
# --------------------------------------------------------------------------- #

def test_html_escape_ampersand():
    result = render("{{ val }}", {"val": "A & B"})
    assert result == "A &amp; B"


def test_html_escape_angle_brackets():
    result = render("{{ code }}", {"code": "<script>"})
    assert result == "&lt;script&gt;"


def test_html_escape_quote():
    result = render('{{ attr }}', {"attr": 'say "hi"'})
    assert result == 'say &quot;hi&quot;'


def test_html_escape_all_four():
    result = render("{{ v }}", {"v": '& < > "'})
    assert result == "&amp; &lt; &gt; &quot;"


# --------------------------------------------------------------------------- #
# 4. |safe filter disables escaping
# --------------------------------------------------------------------------- #

def test_safe_filter_no_escape():
    result = render("{{ html|safe }}", {"html": "<b>bold</b>"})
    assert result == "<b>bold</b>"


def test_safe_filter_with_spaces():
    result = render("{{ html | safe }}", {"html": "<em>x</em>"})
    assert result == "<em>x</em>"


# --------------------------------------------------------------------------- #
# 5. Missing variable → empty string
# --------------------------------------------------------------------------- #

def test_missing_var_empty():
    result = render("Hello, {{ missing }}!", {})
    assert result == "Hello, !"


def test_missing_dotted_var_empty():
    result = render("{{ a.b }}", {"a": {"c": "nope"}})
    assert result == ""


# --------------------------------------------------------------------------- #
# 6. Conditionals — {% if %} / {% if not %}
# --------------------------------------------------------------------------- #

def test_if_true():
    result = render("{% if show %}visible{% endif %}", {"show": True})
    assert result == "visible"


def test_if_false():
    result = render("{% if show %}visible{% endif %}", {"show": False})
    assert result == ""


def test_if_missing_key_false():
    result = render("{% if ghost %}here{% endif %}", {})
    assert result == ""


def test_if_not_true():
    result = render("{% if not flag %}shown{% endif %}", {"flag": False})
    assert result == "shown"


def test_if_not_false():
    result = render("{% if not flag %}shown{% endif %}", {"flag": True})
    assert result == ""


# --------------------------------------------------------------------------- #
# 7. For loops
# --------------------------------------------------------------------------- #

def test_for_basic_list():
    result = render("{% for x in items %}{{ x }},{% endfor %}", {"items": [1, 2, 3]})
    assert result == "1,2,3,"


def test_for_empty_list():
    result = render("{% for x in items %}{{ x }}{% endfor %}", {"items": []})
    assert result == ""


def test_for_missing_key():
    result = render("{% for x in items %}{{ x }}{% endfor %}", {})
    assert result == ""


def test_for_none_iterable():
    result = render("{% for x in items %}{{ x }}{% endfor %}", {"items": None})
    assert result == ""


def test_for_dotted_access():
    ctx = {"rows": [{"name": "Alice"}, {"name": "Bob"}]}
    result = render("{% for row in rows %}{{ row.name }} {% endfor %}", ctx)
    assert result == "Alice Bob "


def test_for_html_escape_in_body():
    ctx = {"vals": ["<b>", "<i>"]}
    result = render("{% for v in vals %}{{ v }}{% endfor %}", ctx)
    assert result == "&lt;b&gt;&lt;i&gt;"


def test_for_safe_in_body():
    ctx = {"vals": ["<b>bold</b>"]}
    result = render("{% for v in vals %}{{ v|safe }}{% endfor %}", ctx)
    assert result == "<b>bold</b>"


# --------------------------------------------------------------------------- #
# 8. if inside for
# --------------------------------------------------------------------------- #

def test_if_inside_for():
    ctx = {"items": [{"name": "Alice", "active": True}, {"name": "Bob", "active": False}]}
    tmpl = "{% for item in items %}{% if active %}{{ item.name }}{% endif %}{% endfor %}"
    # 'active' is looked up in child_ctx which inherits the dict element as 'item',
    # but 'active' itself must be in the context. Adjust: use a flat list with booleans.
    # Actually per TASK.md: {% if name %} does plain key lookup in context.
    # In a for loop the child_ctx is the parent ctx + loop var. So 'active' should be
    # a key in the parent ctx OR we use the loop var's dotted lookup in the var tag.
    # Let's test with a simpler if: check context-level key.
    ctx2 = {"items": ["Alice", "Bob", "Charlie"], "show": True}
    tmpl2 = "{% for x in items %}{% if show %}{{ x }} {% endif %}{% endfor %}"
    result = render(tmpl2, ctx2)
    assert result == "Alice Bob Charlie "


def test_if_not_inside_for():
    ctx = {"items": ["a", "b"], "hide": False}
    tmpl = "{% for x in items %}{% if not hide %}{{ x }}{% endif %}{% endfor %}"
    result = render(tmpl, ctx)
    assert result == "ab"


# --------------------------------------------------------------------------- #
# 9. Literal text outside tags preserved
# --------------------------------------------------------------------------- #

def test_literal_text_preserved():
    result = render("no tags here", {})
    assert result == "no tags here"


def test_mixed_literal_and_var():
    result = render("<p>Hello {{ name }}</p>", {"name": "World"})
    assert result == "<p>Hello World</p>"


# --------------------------------------------------------------------------- #
# Advisory code quality
# --------------------------------------------------------------------------- #

@pytest.mark.code_quality
def test_code_quality_report():
    rep = gu.code_quality_report(SOL)
    print("code_quality:", rep)  # advisory only — never asserted
