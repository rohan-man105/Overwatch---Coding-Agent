from typing import Optional

import strawberry


@strawberry.type
class CodeSymbol:
    name: str
    kind: str
    file_path: str
    source_code: Optional[str] = None
    docstring: Optional[str] = None
    start_line: Optional[int] = None
    end_line: Optional[int] = None


@strawberry.type
class Health:
    status: str
    detail: str
