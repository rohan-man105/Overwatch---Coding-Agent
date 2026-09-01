"""Parse the repository, create embeddings, and store the index in Weaviate."""

import hashlib
import uuid

import weaviate.classes.config as wc

from data.ingest import load_codebase
from services.indexer.parser import parse_python_file
from services.indexer.relationships import (
    extract_relationships,
    resolve_relationships,
)
from services.weaviate.utils import close_client, get_client, get_model, url


RELATIONSHIP_NAMESPACE = uuid.UUID("f4c4f72e-5f2e-4ba3-8f8e-3bcf9eb7a002")


def get_or_create_collection():
    client = get_client()
    if not client.collections.exists("CodeBase"):
        client.collections.create(
            name="CodeBase",
            vector_config=wc.Configure.Vectors.self_provided()
        )
    return client.collections.use("CodeBase")


def get_or_create_relationship_collection():
    client = get_client()
    if not client.collections.exists("CodeRelationship"):
        client.collections.create(
            name="CodeRelationship",
            vector_config=wc.Configure.Vectors.self_provided(),
        )
    return client.collections.use("CodeRelationship")


def repository_id(root_path: str) -> str:
    normalized = str(root_path).replace("\\", "/").lower()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def collect_records(files):
    symbols = []
    relationships = []
    errors = []

    for file in files:
        path = file["relative_path"]
        source = file["source_code"]
        parsed = parse_python_file(path, source)

        if parsed["status"] != "ok":
            errors.append(parsed)
            continue

        symbols.extend(parsed["symbols"])
        relationships.extend(extract_relationships(path, source))

    return symbols, resolve_relationships(relationships, symbols), errors


def relationship_uuid(relationship) -> str:
    value = (
        f"{relationship.source_id}:{relationship.target_name}:"
        f"{relationship.relationship_type}:{relationship.file_path}:"
        f"{relationship.line_number}"
    )
    return str(uuid.uuid5(RELATIONSHIP_NAMESPACE, value))


def delete_stale_objects(collection, repo_id: str, current_ids: set[str]):
    """Remove old records for this repository that are no longer present."""
    try:
        old_objects = collection.query.fetch_objects(limit=10000).objects
    except Exception as error:
        print(f"Could not inspect old Weaviate records: {error}")
        return

    for obj in old_objects:
        if (obj.properties or {}).get("repository_id") != repo_id:
            continue
        if str(obj.uuid) not in current_ids:
            collection.data.delete_by_id(obj.uuid)


def upsert_object(collection, object_id: str, properties: dict, vector):
    """Replace an existing object, or insert it when it is new."""
    object_uuid = uuid.UUID(object_id)

    try:
        collection.data.replace(
            uuid=object_uuid,
            properties=properties,
            vector=vector,
        )
    except Exception:
        collection.data.insert(
            uuid=object_uuid,
            properties=properties,
            vector=vector,
        )


def embed(root_path: str | None = None):
    """Index a repository. A syntax error only skips that individual file."""
    root_path = root_path or url
    repo_id = repository_id(root_path)

    try:
        files = load_codebase(root_path)
        symbols, relationships, errors = collect_records(files)
        collection = get_or_create_collection()
        relationship_collection = get_or_create_relationship_collection()
        model = get_model()

        symbol_ids = set()
        for symbol in symbols:
            symbol_ids.add(symbol.symbol_id)
            text = (
                f"{symbol.kind}\n{symbol.qualified_name}\n"
                f"{symbol.docstring}\n{symbol.source_code}"
            )
            upsert_object(
                collection=collection,
                object_id=symbol.symbol_id,
                properties={
                    "repository_id": repo_id,
                    "symbol_id": symbol.symbol_id,
                    "name": symbol.name,
                    "qualified_name": symbol.qualified_name,
                    "kind": symbol.kind,
                    "file_path": symbol.file_path,
                    "source_code": symbol.source_code,
                    "docstring": symbol.docstring,
                    "start_line": symbol.start_line,
                    "end_line": symbol.end_line,
                    "content_hash": symbol.content_hash,
                },
                vector=model.encode(text).tolist(),
            )

        relationship_ids = set()
        for relationship in relationships:
            relation_id = relationship_uuid(relationship)
            relationship_ids.add(relation_id)
            upsert_object(
                collection=relationship_collection,
                object_id=relation_id,
                properties={
                    "repository_id": repo_id,
                    "source_id": relationship.source_id,
                    "source_name": relationship.source_name,
                    "target_id": relationship.target_id or "",
                    "target_name": relationship.target_name,
                    "relationship_type": relationship.relationship_type,
                    "file_path": relationship.file_path,
                    "line_number": relationship.line_number,
                    "resolved": relationship.resolved,
                },
                # Relationships are queried by filters, not semantic similarity.
                vector=[0.0],
            )

        delete_stale_objects(collection, repo_id, symbol_ids)
        delete_stale_objects(relationship_collection, repo_id, relationship_ids)

        print(f"\nIndexed {len(files)} files, {len(symbols)} symbols, "
              f"and {len(relationships)} relationships.\n")
        for error in errors:
            print(f"Skipped {error['file_path']}: {error['error']}")
    finally:
        close_client()
        










