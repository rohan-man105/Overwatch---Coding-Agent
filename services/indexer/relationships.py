import ast

from services.indexer.models import Relationship
from services.indexer.parser import make_symbol_id


def extract_relationships(file_path: str, source_code: str):
    try:
        tree = ast.parse(source_code, filename=file_path)
    except SyntaxError:
        return []

    relationships = []

    class Visitor(ast.NodeVisitor):
        def __init__(self):
            self.scope = []
            self.current_id = None
            self.current_name = None

        def visit_ClassDef(self, node):
            name = ".".join(self.scope + [node.name])
            class_id = make_symbol_id(file_path, name, "class")
            previous = self.current_id, self.current_name

            if self.current_id:
                relationships.append(Relationship(
                    source_id=self.current_id,
                    source_name=self.current_name,
                    target_name=name,
                    target_id=class_id,
                    resolved=True,
                    relationship_type="contains",
                    file_path=file_path,
                    line_number=node.lineno,
                ))

            self.current_id, self.current_name = class_id, name
            for base in node.bases:
                relationships.append(Relationship(
                    source_id=class_id,
                    source_name=name,
                    target_name=ast.unparse(base),
                    relationship_type="inherits",
                    file_path=file_path,
                    line_number=node.lineno,
                ))

            self.scope.append(node.name)
            self.generic_visit(node)
            self.scope.pop()
            self.current_id, self.current_name = previous

        def visit_FunctionDef(self, node):
            self.visit_function(node, "function")

        def visit_AsyncFunctionDef(self, node):
            self.visit_function(node, "async_function")

        def visit_function(self, node, kind):
            name = ".".join(self.scope + [node.name])
            function_id = make_symbol_id(file_path, name, kind)
            previous = self.current_id, self.current_name

            if self.current_id:
                relationships.append(Relationship(
                    source_id=self.current_id,
                    source_name=self.current_name,
                    target_name=name,
                    target_id=function_id,
                    resolved=True,
                    relationship_type="contains",
                    file_path=file_path,
                    line_number=node.lineno,
                ))

            self.current_id, self.current_name = function_id, name
            self.scope.append(node.name)
            self.generic_visit(node)
            self.scope.pop()
            self.current_id, self.current_name = previous

        def visit_Import(self, node):
            if self.current_id:
                for alias in node.names:
                    relationships.append(Relationship(
                        source_id=self.current_id,
                        source_name=self.current_name,
                        target_name=alias.name,
                        relationship_type="imports",
                        file_path=file_path,
                        line_number=node.lineno,
                    ))
            self.generic_visit(node)

        def visit_ImportFrom(self, node):
            if self.current_id:
                module = node.module or ""
                for alias in node.names:
                    relationships.append(Relationship(
                        source_id=self.current_id,
                        source_name=self.current_name,
                        target_name=f"{module}.{alias.name}",
                        relationship_type="imports",
                        file_path=file_path,
                        line_number=node.lineno,
                    ))
            self.generic_visit(node)

        def visit_Call(self, node):
            if self.current_id:
                if isinstance(node.func, ast.Name):
                    target = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    target = ast.unparse(node.func)
                else:
                    target = None

                if target:
                    relationships.append(Relationship(
                        source_id=self.current_id,
                        source_name=self.current_name,
                        target_name=target,
                        relationship_type="calls",
                        file_path=file_path,
                        line_number=node.lineno,
                    ))
            self.generic_visit(node)

    Visitor().visit(tree)
    return relationships


def resolve_relationships(relationships, symbols):
    by_name = {}
    for symbol in symbols:
        by_name.setdefault(symbol.name, symbol.symbol_id)
        by_name.setdefault(symbol.qualified_name, symbol.symbol_id)

    for relationship in relationships:
        target_id = by_name.get(relationship.target_name)
        if target_id:
            relationship.target_id = target_id
            relationship.resolved = True

    return relationships
