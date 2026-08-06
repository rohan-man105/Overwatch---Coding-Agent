from typing import List

import strawberry

from services.graphql.types import Health
from services.weaviate.retrieval import (
    get_project_structure,
    grasp_codebase,
    grasp_file,
    grasp_func,
    search_func,
)
from services.weaviate.utils import get_client


@strawberry.type
class Query:
    @strawberry.field
    def health(self) -> Health:
        try:
            client = get_client()
            if client.is_connected():
                return Health(status="ok", detail="Connected to Weaviate")
            return Health(status="error", detail="Weaviate client is not connected")
        except Exception as exc:
            return Health(status="error", detail=str(exc))

    @strawberry.field
    def search_code(self, query: str, limit: int = 3) -> str:
        return grasp_func(query, limit)

    @strawberry.field
    def symbol(self, name: str, limit: int = 2) -> str:
        return search_func(name, limit)

    @strawberry.field
    def file_symbols(self, path: str, limit: int = 50) -> str:
        return grasp_file(path, limit)

    @strawberry.field
    def project_structure(self, root_path: str, depth: int = 3) -> List[str]:
        return get_project_structure(root_path, depth)

    @strawberry.field
    def codebase_symbols(self, limit: int = 200) -> str:
        return grasp_codebase(limit)


schema = strawberry.Schema(query=Query)
