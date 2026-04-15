import ast
import os
from pathlib import Path
from dataclasses import dataclass, field


@dataclass
class FileNode:
    path: str
    module: str
    classes: list[str] = field(default_factory=list)
    functions: list[str] = field(default_factory=list)
    imports: list[str] = field(default_factory=list)
    loc: int = 0


def path_to_module(path: Path, root: Path) -> str:
    rel = path.relative_to(root)
    return str(rel).replace(os.sep, ".").removesuffix(".py")


def parse_file(path: Path, root: Path) -> FileNode | None:
    try:
        source = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return None

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return None

    module = path_to_module(path, root)
    node = FileNode(
        path=str(path.relative_to(root)),
        module=module,
        loc=len(source.splitlines()),
    )

    for item in ast.walk(tree):
        if isinstance(item, ast.ClassDef):
            node.classes.append(item.name)
        elif isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
            node.functions.append(item.name)
        elif isinstance(item, ast.Import):
            for alias in item.names:
                node.imports.append(alias.name)
        elif isinstance(item, ast.ImportFrom):
            if item.module:
                node.imports.append(item.module)

    return node


def build_graph(root_path: str) -> dict:
    root = Path(root_path).resolve()
    py_files = list(root.rglob("*.py"))

    # Skip common noise
    skip = {"__pycache__", ".venv", "venv", "env", ".git", "node_modules", "migrations"}
    py_files = [
        f for f in py_files
        if not any(part in skip for part in f.parts)
    ]

    nodes = []
    module_map = {}

    for f in py_files:
        parsed = parse_file(f, root)
        if parsed:
            nodes.append(parsed)
            module_map[parsed.module] = parsed

    # Build edges: file A imports file B (internal only)
    edges = []
    all_modules = set(module_map.keys())

    for node in nodes:
        for imp in node.imports:
            # Match against internal modules
            for mod in all_modules:
                if mod == imp or mod.endswith("." + imp) or imp.startswith(mod):
                    if mod != node.module:
                        edges.append({
                            "source": node.module,
                            "target": mod,
                        })
                        break

    # Deduplicate edges
    seen = set()
    unique_edges = []
    for e in edges:
        key = (e["source"], e["target"])
        if key not in seen:
            seen.add(key)
            unique_edges.append(e)

    graph_nodes = [
        {
            "id": n.module,
            "path": n.path,
            "loc": n.loc,
            "classes": n.classes,
            "functions": n.functions[:10],  # cap for display
            "num_imports": len(n.imports),
        }
        for n in nodes
    ]

    return {
        "nodes": graph_nodes,
        "edges": unique_edges,
        "root": str(root),
        "total_files": len(nodes),
        "total_loc": sum(n.loc for n in nodes),
    }
