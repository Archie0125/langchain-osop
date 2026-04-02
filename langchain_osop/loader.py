"""Load OSOP workflows as LangChain Documents."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

try:
    from langchain_core.documents import Document
except ImportError:
    raise ImportError("langchain-core is required: pip install langchain-core")


# Valid OSOP node types
NODE_TYPES = {"human", "agent", "api", "cli", "db", "git", "docker", "cicd", "mcp", "system", "infra", "data"}
EDGE_MODES = {"sequential", "conditional", "parallel", "loop", "event", "fallback", "error", "timeout", "spawn", "switch"}


class OsopWorkflowLoader:
    """Load .osop.yaml files as LangChain Documents.

    Each workflow becomes a Document with:
    - page_content: human-readable workflow description
    - metadata: structured workflow data (nodes, edges, stats)

    Example:
        loader = OsopWorkflowLoader("path/to/workflow.osop.yaml")
        docs = loader.load()
        print(docs[0].page_content)
    """

    def __init__(
        self,
        file_path: str | Path | None = None,
        content: str | None = None,
        include_yaml: bool = True,
    ):
        self.file_path = Path(file_path) if file_path else None
        self.content = content
        self.include_yaml = include_yaml

    def _parse(self) -> tuple[str, dict[str, Any]]:
        """Parse OSOP YAML and return (raw, parsed)."""
        if self.content:
            raw = self.content
        elif self.file_path:
            raw = self.file_path.read_text(encoding="utf-8")
        else:
            raise ValueError("Either file_path or content must be provided")
        parsed = yaml.safe_load(raw)
        if not isinstance(parsed, dict):
            raise ValueError("OSOP content must be a YAML mapping")
        return raw, parsed

    def load(self) -> list[Document]:
        """Load the OSOP workflow as a list of Documents."""
        raw, data = self._parse()
        nodes = data.get("nodes", [])
        edges = data.get("edges", [])

        # Build readable description
        lines = [
            f"# {data.get('name', data.get('id', 'Untitled Workflow'))}",
            "",
            data.get("description", ""),
            "",
            f"**Nodes ({len(nodes)}):**",
        ]
        for n in nodes:
            if isinstance(n, dict):
                ntype = n.get("type", "system")
                nname = n.get("name", n.get("id", "?"))
                purpose = n.get("purpose", n.get("description", ""))
                lines.append(f"- [{ntype}] {nname}: {purpose}")

        lines.extend(["", f"**Edges ({len(edges)}):**"])
        for e in edges:
            if isinstance(e, dict):
                mode = e.get("mode", "sequential")
                label = e.get("label", "")
                lines.append(f"- {e.get('from', '?')} → {e.get('to', '?')} ({mode}){f' — {label}' if label else ''}")

        page_content = "\n".join(lines)
        if self.include_yaml:
            page_content += f"\n\n---\n\n```yaml\n{raw}\n```"

        # Compute metadata
        node_types = sorted(set(n.get("type", "system") for n in nodes if isinstance(n, dict)))
        edge_modes = sorted(set(e.get("mode", "sequential") for e in edges if isinstance(e, dict)))

        metadata: dict[str, Any] = {
            "source": str(self.file_path) if self.file_path else "inline",
            "format": "osop",
            "osop_version": data.get("osop_version", "1.0"),
            "workflow_id": data.get("id", ""),
            "workflow_name": data.get("name", ""),
            "node_count": len(nodes),
            "edge_count": len(edges),
            "node_types": node_types,
            "edge_modes": edge_modes,
            "tags": data.get("tags", []),
        }

        return [Document(page_content=page_content, metadata=metadata)]

    @classmethod
    def from_directory(cls, directory: str | Path, glob: str = "**/*.osop.yaml") -> list[Document]:
        """Load all .osop.yaml files from a directory."""
        docs = []
        for path in sorted(Path(directory).glob(glob)):
            loader = cls(file_path=path)
            docs.extend(loader.load())
        return docs
