import os


# Directories to always skip
SKIP_DIRS = {
    '__pycache__', '.git', '.venv', 'venv', 'env',
    'node_modules', '.idea', '.vscode', '.mypy_cache',
    '.pytest_cache', 'dist', 'build', '.egg-info'
}


def walk_python_files(root_path: str) -> list[str]:
    
    py_files = []

    for dirpath, dirnames, filenames in os.walk(root_path):
        # Remove dirs we want to skip (modifying in-place so os.walk doesn't enter them)
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith('.')]

        for filename in filenames:
            if filename.endswith('.py'):
                full_path = os.path.join(dirpath, filename)
                py_files.append(full_path)

    return py_files


def load_file(file_path: str) -> str | None:
   
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except (UnicodeDecodeError, PermissionError, FileNotFoundError) as e:
        print(f"Skipping {file_path}: {e}")
        return None


def load_codebase(root_path: str) -> list[dict]:
    root_path = os.path.abspath(root_path)

    if not os.path.isdir(root_path):
        raise ValueError(f"Path does not exist or is not a directory: {root_path}")

    py_files = walk_python_files(root_path)
    loaded = []

    for file_path in py_files:
        source = load_file(file_path)
        if source is not None and source.strip():  # skip empty files
            loaded.append({
                "file_path": file_path,
                "relative_path": os.path.relpath(file_path, root_path),
                "source_code": source,
            })

    print(f"Loaded {len(loaded)} Python files from: {root_path}")
    return loaded



