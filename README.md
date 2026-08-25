# CAS Agent

CAS Agent is a local, code-aware assistant for understanding and debugging Python projects. You point it at a project folder, it indexes the code into Weaviate, and then you chat with a small team of agents that can explain architecture, find symbols, trace code, and reason through bugs.

It is built to feel less like a one-shot chatbot and more like a practical coding companion: first it maps the codebase, then it routes your request to the specialist best suited for the job.

## What It Does

- Indexes Python files from a project directory.
- Extracts top-level functions and classes with Python's `ast` module.
- Creates semantic embeddings with `sentence-transformers`.
- Stores searchable code chunks in a local Weaviate vector database.
- Runs a streamed CLI chat loop powered by the OpenAI Agents SDK.
- Uses an NVIDIA-hosted OpenAI-compatible model endpoint.
- Routes work between focused agents:
  - **Orchestrator** decides where each request should go.
  - **Atlas** explains code, architecture, files, symbols, and dependencies.
  - **Patcher** analyzes bugs, tracebacks, failing behavior, and patch ideas.

## Project Structure

```text
cas-private/
+-- main.py                         # CLI entry point
+-- env.py                          # Model/client configuration
+-- docker-compose.yml              # Local Weaviate service
+-- requirements.txt                # Python dependencies
+-- data/
|   +-- ingest.py                   # Walks and loads Python files
+-- services/
    +-- agentservices/
    |   +-- orchestrator.py         # Main CAS routing agent
    |   +-- atlas.py                # Code understanding specialist
    |   +-- patcher.py              # Debugging and patch specialist
    |   +-- prompt.py               # Agent instructions
    |   +-- run.py                  # Streaming agent runner
    +-- graphql/
    |   +-- schema.py               # Experimental GraphQL query surface
    |   +-- types.py                # GraphQL response types
    +-- weaviate/
        +-- load.py                 # Embeds code symbols into Weaviate
        +-- retrieval.py            # Search/retrieval tools exposed to agents
        +-- utils.py                # Weaviate and embedding model helpers
```

## How It Works

1. You start Weaviate locally with Docker.
2. You run `main.py`.
3. CAS asks for the path of the project you want to analyze.
4. The loader walks that project and reads Python files.
5. Top-level functions and classes are parsed, embedded, and stored in Weaviate.
6. You chat with CAS in the terminal.
7. CAS chooses whether Atlas or Patcher should handle the request, then streams the answer back.

## Requirements

- Python 3.10 or newer
- Docker and Docker Compose
- An NVIDIA API key for the OpenAI-compatible endpoint

Python packages are listed in `requirements.txt`:

```text
openai
openai-agents
python-dotenv
sentence-transformers
strawberry-graphql
weaviate-client
```

## Setup

Clone or open the project, then move into the CAS Agent directory:

```bash
cd casagent/cas-private
```

Create and activate a virtual environment:

```bash
python -m venv .venv
.venv\Scripts\activate
```

On macOS or Linux, activation looks like this:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file:

```env
NVIDIA_API_KEY=your_nvidia_api_key_here
```

## Running CAS Agent

Start Weaviate:

```bash
docker compose up -d
```

Run the CLI:

```bash
python main.py
```

When prompted, enter the absolute or relative path to the Python project you want CAS to analyze:

```text
Enter the project path to analyze: C:\path\to\your\project
```

After indexing finishes, ask questions naturally:

```text
YOU: give me a high-level overview of this project
YOU: explain how authentication works
YOU: find the function that creates new orders
YOU: this traceback is failing, can you help debug it?
```

To end the session:

```text
exit
```

or:

```text
quit
```

## Agent Roles

### Orchestrator

The Orchestrator is the front door. It reads your request, decides whether the task is about exploration, explanation, debugging, modification, or verification, and hands the work to the right specialist.

It is also the only agent that should speak directly to the user.

### Atlas

Atlas is for understanding. It retrieves relevant code context from Weaviate and explains what it finds.

Use Atlas-style prompts when you want to know:

- where something lives
- what a function or class does
- how files relate to each other
- what the overall architecture looks like
- which symbols are relevant to a feature

### Patcher

Patcher is for debugging and change planning. It looks at failures, traces related code, and proposes focused fixes.

Use Patcher-style prompts when you have:

- a traceback
- incorrect behavior
- failing tests
- a suspected bug
- a refactor or patch idea

## Retrieval Tools

CAS exposes several code retrieval tools to the agents:

- `get_project_structure` lists Python files in the target project.
- `grasp_func` performs semantic search for relevant functions or classes.
- `search_func` finds an exact function or class name.
- `grasp_file` retrieves symbols from a specific file.
- `grasp_codebase` returns a broad view of indexed symbols.

These tools are what keep the agents grounded in the actual project instead of guessing from memory.

## Configuration

Model configuration lives in `env.py`.

By default, CAS uses:

```text
nvidia/llama-3.3-nemotron-super-49b-v1.5
```

through:

```text
https://integrate.api.nvidia.com/v1
```

If you want to use a different OpenAI-compatible provider, update the `AsyncOpenAI` client and model name in `env.py`.

Weaviate connection settings live in `services/weaviate/utils.py`. The current defaults expect Weaviate to be available at:

```text
localhost:8080
localhost:50051
```

## GraphQL Surface

The `services/graphql` folder contains an experimental Strawberry GraphQL schema for querying the indexed codebase. It includes fields for:

- health checks
- semantic code search
- exact symbol lookup
- file-level symbol retrieval
- project structure
- broad codebase symbol retrieval

This layer is present in the codebase, but the main application entry point today is still the CLI in `main.py`.

## Current Limitations

CAS Agent is useful, but it is still early-stage software. A few things to know:

- It currently indexes Python files only.
- It stores top-level functions and classes, not every nested block.
- Weaviate data is persistent through the Docker volume, so repeated indexing can add duplicate entries unless the collection is cleared.
- The CLI loads the project at startup before the chat begins, so larger projects may take a while.
- The patching agent proposes fixes, but this codebase does not yet apply edits automatically.
- The GraphQL schema may need wiring into an ASGI server before it can be used as an API.

## Troubleshooting

If CAS cannot connect to Weaviate, make sure Docker is running and start the service again:

```bash
docker compose up -d
```

If model calls fail, check that `.env` exists and contains a valid key:

```env
NVIDIA_API_KEY=your_nvidia_api_key_here
```

If imports fail, confirm your virtual environment is active and dependencies are installed:

```bash
pip install -r requirements.txt
```

If indexing fails on a project path, make sure the path exists and points to a directory that contains Python files.

## Development Notes

The most important flow is:

```text
main.py
  -> services.weaviate.load.embed()
  -> data.ingest.load_codebase()
  -> services.weaviate.retrieval tools
  -> services.agentservices.run.run_agents()
  -> Orchestrator / Atlas / Patcher
```

When changing the agent behavior, start with `services/agentservices/prompt.py`.

When changing how code is indexed, start with `services/weaviate/load.py` and `data/ingest.py`.

When changing retrieval behavior, start with `services/weaviate/retrieval.py`.

## Roadmap Ideas

- Add automatic duplicate cleanup or collection reset before re-indexing.
- Store nested functions, methods, imports, and module-level metadata.
- Add direct patch application with user confirmation.
- Add tests for ingestion, retrieval, and routing.
- Expose the GraphQL schema through a runnable web server.
- Add a small web UI for browsing indexed symbols and chatting with CAS.
- Support JavaScript, TypeScript, Go, and other languages.

## License

No license file is currently included. Add one before publishing or distributing this project.
