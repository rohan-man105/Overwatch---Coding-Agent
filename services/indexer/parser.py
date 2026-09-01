import ast
import hashlib
import uuid

from services.indexer.models import Symbol


CAS_NAMESPACE = uuid.UUID("f4c4f72e-5f2e-4ba3-8f8e-3bcf9eb7a001")


def make_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def make_symbol_id(file_path: str, qualified_name: str, kind: str) -> str:
    value = f"{file_path}:{qualified_name}:{kind}"
    return str(uuid.uuid5(CAS_NAMESPACE, value))


def parse_python_file(file_path: str, source_code: str) -> dict:
    try:
        tree = ast.parse(source_code, filename=file_path)
    except SyntaxError as error:
        return {
            "status": "syntax_error",
            "file_path": file_path,
            "error": str(error),
            "symbols": [],
        }

    symbols = []

    class SymbolVisitor(ast.NodeVisitor):
        def __init__(self):
            self.scope = []

        def visit_ClassDef(self, node):
            self.add_symbol(node, "class")
            self.scope.append(node.name)
            self.generic_visit(node)
            self.scope.pop()

        def visit_FunctionDef(self, node):
            self.add_symbol(node, "function")
            self.scope.append(node.name)
            self.generic_visit(node)
            self.scope.pop()

        def visit_AsyncFunctionDef(self, node):
            self.add_symbol(node, "async_function")
            self.scope.append(node.name)
            self.generic_visit(node)
            self.scope.pop()

        def add_symbol(self, node, kind):
            qualified_name = ".".join(self.scope + [node.name])
            code = ast.get_source_segment(source_code, node) or ""
            symbols.append(
                Symbol(
                    symbol_id=make_symbol_id(file_path, qualified_name, kind),
                    name=node.name,
                    qualified_name=qualified_name,
                    kind=kind,
                    file_path=file_path,
                    start_line=node.lineno,
                    end_line=node.end_lineno or node.lineno,
                    source_code=code,
                    docstring=ast.get_docstring(node) or "",
                    content_hash=make_hash(code),
                )
            )

    SymbolVisitor().visit(tree)
    return {
        "status": "ok",
        "file_path": file_path,
        "error": None,
        "symbols": symbols,
    }
