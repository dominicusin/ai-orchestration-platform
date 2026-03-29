"""AST utilities"""

import ast


def parse_code(code: str) -> ast.Module:
    """Parse Python code to AST"""
    return ast.parse(code)


def get_functions(tree: ast.Module) -> list[ast.FunctionDef]:
    """Get all functions from AST"""
    return [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]


def get_classes(tree: ast.Module) -> list[ast.ClassDef]:
    """Get all classes from AST"""
    return [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]


def get_imports(tree: ast.Module) -> list[str]:
    """Get all imports from AST"""
    return [node.names[0].name for node in ast.walk(tree) if isinstance(node, ast.Import)]


def get_import_froms(tree: ast.Module) -> list[tuple]:
    """Get from...import statements"""
    result = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                result.append((node.module, alias.name))
    return result


def ast_to_code(tree: ast.Module) -> str:
    """Convert AST back to code"""
    return ast.unparse(tree)
