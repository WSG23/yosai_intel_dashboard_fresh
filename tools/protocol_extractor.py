from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Dict, List, Optional

from tools.robust_file_reader import safe_read_text


class StubModuleVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        # variable name -> module name
        self.alias_to_module: Dict[str, str] = {}
        # spec variable -> module name
        self.spec_to_name: Dict[str, str] = {}
        # module alias -> {attr: assigned_name}
        self.alias_attrs: Dict[str, Dict[str, str]] = {}
        # class name -> list of method signatures
        self.class_methods: Dict[str, List[str]] = {}

    # --------------------------------------------------------------
    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        methods: List[str] = []
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                params = [arg.arg for arg in item.args.args]
                if item.args.vararg:
                    params.append(f"*{item.args.vararg.arg}")
                if item.args.kwarg:
                    params.append(f"**{item.args.kwarg.arg}")
                methods.append(f"{item.name}({', '.join(params)})")
        self.class_methods[node.name] = methods
        self.generic_visit(node)

    # --------------------------------------------------------------
    def visit_Assign(self, node: ast.Assign) -> None:
        if len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name):
                alias = target.id
                mod_name = self._extract_module_type_name(node.value)
                if mod_name:
                    self.alias_to_module[alias] = mod_name
                elif isinstance(node.value, ast.Call):
                    mod_name = self._extract_module_from_spec(node.value)
                    if mod_name:
                        self.alias_to_module[alias] = mod_name

        # handle attribute assignments like alias.attr = Something
        for tgt in node.targets:
            if isinstance(tgt, ast.Attribute) and isinstance(tgt.value, ast.Name):
                alias = tgt.value.id
                attr = tgt.attr
                val_name = self._get_name(node.value)
                if val_name is not None:
                    self.alias_attrs.setdefault(alias, {})[attr] = val_name

        # handle sys.modules["foo"] = alias
        if len(node.targets) == 1:
            tgt = node.targets[0]
            if isinstance(tgt, ast.Subscript):
                mod_name = self._extract_sys_modules_key(tgt)
                if mod_name:
                    alias_name = self._get_name(node.value)
                    if alias_name:
                        self.alias_to_module[alias_name] = mod_name

        self.generic_visit(node)

    # --------------------------------------------------------------
    def visit_Call(self, node: ast.Call) -> None:
        # handle sys.modules.setdefault("foo", alias)
        if (
            isinstance(node.func, ast.Attribute)
            and node.func.attr == "setdefault"
            and isinstance(node.func.value, ast.Attribute)
            and isinstance(node.func.value.value, ast.Name)
            and node.func.value.value.id == "sys"
            and node.func.value.attr == "modules"
        ):
            if node.args and isinstance(node.args[0], ast.Constant):
                mod_name = node.args[0].value
                if len(node.args) > 1:
                    alias_name = self._get_name(node.args[1])
                    if alias_name:
                        self.alias_to_module[alias_name] = mod_name
        self.generic_visit(node)

    # --------------------------------------------------------------
    def _get_name(self, node: ast.AST) -> Optional[str]:
        if isinstance(node, ast.Name):
            return node.id
        return None

    # --------------------------------------------------------------
    def _extract_module_type_name(self, node: ast.AST) -> Optional[str]:
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "ModuleType"
            and node.args
            and isinstance(node.args[0], ast.Constant)
        ):
            return str(node.args[0].value)
        return None

    # --------------------------------------------------------------
    def _extract_module_from_spec(self, node: ast.Call) -> Optional[str]:
        if (
            isinstance(node.func, ast.Attribute)
            and node.func.attr == "module_from_spec"
            and node.args
            and isinstance(node.args[0], ast.Name)
        ):
            spec_var = node.args[0].id
            return self.spec_to_name.get(spec_var)
        return None

    # --------------------------------------------------------------
    def _extract_sys_modules_key(self, sub: ast.Subscript) -> Optional[str]:
        if (
            isinstance(sub.value, ast.Attribute)
            and isinstance(sub.value.value, ast.Name)
            and sub.value.value.id == "sys"
            and sub.value.attr == "modules"
        ):
            key = sub.slice
            if isinstance(key, ast.Constant) and isinstance(key.value, str):
                return key.value
            if (
                isinstance(key, ast.Attribute)
                and key.attr == "name"
                and isinstance(key.value, ast.Name)
            ):
                return self.spec_to_name.get(key.value.id)
        return None

    # --------------------------------------------------------------
    def visit_Expr(self, node: ast.Expr) -> None:
        # capture calls like spec = importlib.util.spec_from_file_location(...)
        if isinstance(node.value, ast.Call):
            self.visit_Call(node.value)
        self.generic_visit(node)

    # --------------------------------------------------------------
    def visit_AugAssign(self, node: ast.AugAssign) -> None:
        self.generic_visit(node)

    # --------------------------------------------------------------
    def visit(self, node: ast.AST) -> None:
        if isinstance(node, ast.Assign):
            # special case to capture spec assignments early
            val = node.value
            if (
                isinstance(val, ast.Call)
                and isinstance(val.func, ast.Attribute)
                and val.func.attr == "spec_from_file_location"
                and val.args
                and isinstance(val.args[0], ast.Constant)
                and isinstance(node.targets[0], ast.Name)
            ):
                spec_var = node.targets[0].id
                self.spec_to_name[spec_var] = str(val.args[0].value)
        super().visit(node)


# ---------------------------------------------------------------------------


def scan_tests(root: Path) -> Dict[str, Dict[str, Dict[str, object]]]:
    visitor = StubModuleVisitor()
    for path in root.rglob("*.py"):
        try:
            tree = ast.parse(safe_read_text(path))
        except Exception:
            continue
        visitor.visit(tree)

    report: Dict[str, Dict[str, Dict[str, object]]] = {}
    for alias, module_name in visitor.alias_to_module.items():
        attrs = visitor.alias_attrs.get(alias, {})
        if not attrs:
            continue
        module_info: Dict[str, Dict[str, object]] = {}
        for attr, value in attrs.items():
            if value in visitor.class_methods:
                module_info[attr] = {
                    "class": value,
                    "methods": visitor.class_methods[value],
                }
        if module_info:
            report[module_name] = module_info
    return report


# ---------------------------------------------------------------------------


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Extract protocol info from tests")
    parser.add_argument("path", nargs="?", default="tests", help="tests directory")
    args = parser.parse_args()
    report = scan_tests(Path(args.path))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":  # pragma: no cover - manual tool
    main()
