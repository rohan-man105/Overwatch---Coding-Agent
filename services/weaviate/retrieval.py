from services.weaviate.utils import format_doc, format_docs, get_client, get_model
from weaviate.classes.query import Filter
import os
from agents import function_tool
from services.weaviate import utils 


def get_codebase_collection():
    client = get_client()
    return client.collections.use("CodeBase")


# Semantic Search for Knowing about a function or class 
@function_tool()
def grasp_func(user_query:str , limit:int=3):

    model = get_model()
    query_vector = model.encode(user_query).tolist()
    collection = get_codebase_collection()

    results = collection.query.hybrid(
        query=user_query,
        vector=query_vector,
        alpha=0.7,
        limit=limit,
        #return_metadata
    )

    return format_docs([obj.properties for obj in results.objects])


# For finding a particular function
@function_tool()
def search_func(func_name:str,limit: int=2):

    collection = get_codebase_collection()

    results = collection.query.fetch_objects(
        filters= Filter.by_property("name").equal(func_name),
        limit=limit
    )

    if results.objects:
        return format_doc(results.objects[0].properties)
    return f"No symbol found with name: {func_name}"


# To understand a whole file
@function_tool()
def grasp_file(file_path:str,limit:int=50):

    collection = get_codebase_collection()

    results = collection.query.fetch_objects(
        filters=Filter.by_property("file_path").equal(file_path),
        limit=limit
    )

    return format_docs([obj.properties for obj in results.objects])





# Understanding project structure
@function_tool()
def get_project_structure( depth: int = 3):
    
    SKIP_DIRS = {'__pycache__', '.git', '.venv', 'venv', 'node_modules', '.idea'}
    tree = []
    root_path = os.path.abspath(utils.url) 
    
    for dirpath, dirnames, filenames in os.walk(root_path):

        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith('.')]
        
        level = dirpath.replace(root_path, "").count(os.sep)
        if level >= depth:
            dirnames.clear()
            continue
        
        rel_dir = os.path.relpath(dirpath, root_path)
        
        for filename in filenames:
            if filename.endswith('.py'):
                file_rel = os.path.join(rel_dir, filename) if rel_dir != "." else filename
                tree.append(file_rel)
    
    return tree


# Understanding whole codebase
@function_tool()
def grasp_codebase(limit:int=200):
    
    collection = get_codebase_collection()

    results = collection.query.fetch_objects(
        limit=limit
    )

    symbols = []

    for obj in results.objects:
        symbols.append({
            "name" : obj.properties.get("name"),
            "kind" : obj.properties.get("kind"),
            "file_path" : obj.properties.get("file_path"),
            "source_code" : obj.properties.get("source_code"),
            "docstring" : obj.properties.get("docstring"),
            "start_line" : obj.properties.get("start_line"),
            "end_line" : obj.properties.get("end_line"),
        })

    return format_docs(symbols)
