import ast
from typing import Iterable, Tuple

# Simple extractor that yields all string literals in Dash layout files


def extract(
    fileobj, keywords, comment_tags, options
) -> Iterable[Tuple[int, str, str, list]]:
    source = fileobj.read()
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            text = node.value.strip()
            if text:
                yield node.lineno, "dash", text, []
