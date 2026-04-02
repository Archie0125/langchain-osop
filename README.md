# langchain-osop

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![PyPI](https://img.shields.io/pypi/v/langchain-osop)](https://pypi.org/project/langchain-osop/)

LangChain integration for [OSOP](https://osop.ai) (Open Standard Operating Procedures) workflows. Load, validate, visualize, and use `.osop.yaml` workflow files in LangChain chains and agents.

## Installation

```bash
pip install langchain-osop
```

## Features

### 1. Load workflows as Documents

```python
from langchain_osop import OsopWorkflowLoader

# Load a single workflow
loader = OsopWorkflowLoader("path/to/workflow.osop.yaml")
docs = loader.load()
print(docs[0].page_content)     # Human-readable description
print(docs[0].metadata)         # Structured metadata (node_count, edge_count, etc.)

# Load all workflows from a directory
docs = OsopWorkflowLoader.from_directory("path/to/workflows/")
```

### 2. Use as a Runnable

```python
from langchain_osop import OsopWorkflowRunnable

runnable = OsopWorkflowRunnable.from_file("workflow.osop.yaml")

# Get structured data
chain = runnable.as_runnable()
result = chain.invoke("analyze this workflow")

# Generate Mermaid diagram
mermaid = runnable.to_mermaid()
print(mermaid)

# Get node summaries for prompts
nodes = runnable.get_node_descriptions()
```

### 3. Agent Tools

```python
from langchain_osop import create_osop_tools
from langchain.agents import create_react_agent

tools = create_osop_tools()
# Provides: osop_validate, osop_describe, osop_to_mermaid
agent = create_react_agent(llm, tools)
```

## Tools

| Tool | Description |
|------|-------------|
| `osop_validate` | Validate OSOP YAML — checks required fields, node types, edge modes, dangling references |
| `osop_describe` | Generate human-readable workflow description |
| `osop_to_mermaid` | Convert workflow to Mermaid diagram |

## What is OSOP?

OSOP is the OpenAPI of workflows — a YAML standard for defining AI agent workflows with 12 node types and 10 edge modes. See [osop.ai](https://osop.ai) for the full spec.

## Links

- [OSOP Spec](https://github.com/Archie0125/osop-spec)
- [OSOP MCP Server](https://github.com/Archie0125/osop-mcp) — 12 MCP tools
- [OSOP Interop](https://github.com/Archie0125/osop-interop) — Format converters (CrewAI, n8n, Airflow, etc.)
- [Visual Editor](https://osop-editor.vercel.app)

## License

Apache License 2.0
