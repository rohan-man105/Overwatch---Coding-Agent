from dataclasses import dataclass
from typing import Optional


@dataclass
class Symbol:
    symbol_id: str
    name: str
    qualified_name: str
    kind: str
    file_path: str
    start_line: int
    end_line: int
    source_code: str
    docstring: str
    content_hash: str


@dataclass
class Relationship:
    source_id: str
    source_name: str
    target_name: str
    relationship_type: str
    file_path: str
    line_number: int
    target_id: Optional[str] = None
    resolved: bool = False
