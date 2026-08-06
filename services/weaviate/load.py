import ast
import weaviate.classes.config as wc
from services.weaviate.utils import close_client, get_client, get_model, url
from data.ingest import load_codebase


def get_or_create_collection():
    client = get_client()
    if not client.collections.exists("CodeBase"):
        client.collections.create(
            name="CodeBase",
            vector_config=wc.Configure.Vectors.self_provided()
        )
    return client.collections.use("CodeBase")


def embed(root_path: str = url):
    try:
        files = load_codebase(root_path)
        collection = get_or_create_collection()
        model = get_model()

        for file in files:
            path = file["relative_path"]
            source = file["source_code"]


            tree = ast.parse(source,filename=path)

            for node in ast.iter_child_nodes(tree):
                
                # Is it a function 
                if isinstance(node,ast.FunctionDef):
                    name = node.name
                    kind = "function"
                    start = node.lineno
                    end = node.end_lineno
                    docs = ast.get_docstring(node) or ""
                    code = ast.get_source_segment(source,node)


                # Is it a class
                elif isinstance(node,ast.ClassDef):
                    name = node.name
                    kind = "class"
                    start = node.lineno
                    end = node.end_lineno
                    docs = ast.get_docstring(node) or ""
                    code = ast.get_source_segment(source,node)
                
                # Skip everything other than class and functions
                else:
                    continue    


                text = f"{kind}\n{name}\n{docs}\n{code}"
                vector = model.encode(text).tolist()


                # Storing in Weaviate
                collection.data.insert(
                    properties={
                        "name": name,           
                        "kind": kind,          
                        "file_path": path,     
                        "source_code": code,    
                        "docstring": docs,      
                        "start_line": start,    
                        "end_line": end,        
                    },
                    vector=vector
                )

        print("\nCode Base Loaded\n")
    finally:
        close_client()
        










