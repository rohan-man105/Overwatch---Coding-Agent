import weaviate
from sentence_transformers import SentenceTransformer


_client = None
_model = None

def get_client():
    global _client
    if _client is None or not _client.is_connected():
        _client = weaviate.connect_to_local(
            host="localhost",
            port=8080,
            grpc_port=50051
        )
    return _client


def close_client():
    global _client
    if _client is not None:
        _client.close()
        _client = None


def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def format_doc(doc: dict) -> str:
    name = doc.get("name") or "Unknown"
    kind = doc.get("kind") or "symbol"
    file_path = doc.get("file_path") or "Unknown file"
    source_code = doc.get("source_code") or ""
    docstring = doc.get("docstring") or "No docstring"
    start_line = doc.get("start_line")
    end_line = doc.get("end_line")
    line_info = f"{start_line}-{end_line}" if start_line and end_line else "Unknown"

    return f"""
{kind.title()}: {name}
File: {file_path}
Lines: {line_info}
Docstring: {docstring}

Source Code:
```python
{source_code}
```
""".strip()


def format_docs(docs: list[dict]) -> str:
    if not docs:
        return "No relevant code context found."

    return "\n\n---\n\n".join(format_doc(doc) for doc in docs)


url = r"C:\New folder (2)\multi-agent-procurement-system"