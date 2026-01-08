import re

CLASS_ATTR_RE = re.compile(r'\sclass(Name)?=["\'][^"\']*["\']')


def remove_class_attribute_from_node(html: str) -> str:
    """Remove class / className attributes"""
    return CLASS_ATTR_RE.sub("", html)


def clean_code_snippet(code: str) -> str:
    """
    Prepare a code snippet for browser-based accessibility analysis.
    """
    if not code or not code.strip():
        raise ValueError("Empty code snippet provided")

    return remove_class_attribute_from_node(code.strip())


def extract_applicability_signals(ax_nodes):
    roles = set()
    categories = set()

    for node in ax_nodes.values():
        role = node.get("role")
        if role:
            roles.add(role)

        if role in ["textbox", "checkbox", "radio"]:
            categories.add("forms")

        if node.get("focusable"):
            categories.add("keyboard")

        if node.get("labels"):
            categories.add("labels")

    return {
        "roles": list(roles),
        "categories": list(categories),
    }
