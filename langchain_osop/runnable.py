"""OSOP workflow as a LangChain Runnable."""

from __future__ import annotations

from typing import Any

import yaml

try:
    from langchain_core.runnables import RunnableConfig, RunnableLambda
except ImportError:
    raise ImportError("langchain-core is required: pip install langchain-core")

from .loader import OsopWorkflowLoader


class OsopWorkflowRunnable:
    """Wrap an OSOP workflow as a LangChain Runnable.

    This creates a runnable that, when invoked, returns the workflow
    structure as a dict — useful for chains that need workflow context.

    For actual workflow execution, use the OSOP MCP server or CLI.

    Example:
        runnable = OsopWorkflowRunnable.from_file("workflow.osop.yaml")
        result = runnable.invoke({"query": "analyze this workflow"})
        # result contains parsed workflow data
    """

    def __init__(self, content: str):
        self._raw = content
        self._parsed = yaml.safe_load(content)
        if not isinstance(self._parsed, dict):
            raise ValueError("OSOP content must be a YAML mapping")

    @classmethod
    def from_file(cls, path: str) -> "OsopWorkflowRunnable":
        from pathlib import Path
        return cls(Path(path).read_text(encoding="utf-8"))

    def as_runnable(self) -> RunnableLambda:
        """Return a LangChain Runnable that outputs the workflow data."""
        parsed = self._parsed

        def _invoke(input_: Any, config: RunnableConfig | None = None) -> dict[str, Any]:
            nodes = parsed.get("nodes", [])
            edges = parsed.get("edges", [])
            return {
                "workflow": {
                    "id": parsed.get("id", ""),
                    "name": parsed.get("name", ""),
                    "description": parsed.get("description", ""),
                    "node_count": len(nodes),
                    "edge_count": len(edges),
                    "nodes": nodes,
                    "edges": edges,
                },
                "input": input_,
            }

        return RunnableLambda(_invoke)

    def get_node_descriptions(self) -> list[dict[str, str]]:
        """Get a list of node summaries for use in prompts."""
        nodes = self._parsed.get("nodes", [])
        return [
            {
                "id": n.get("id", ""),
                "type": n.get("type", "system"),
                "name": n.get("name", n.get("id", "")),
                "purpose": n.get("purpose", n.get("description", "")),
            }
            for n in nodes
            if isinstance(n, dict)
        ]

    def to_mermaid(self) -> str:
        """Generate a Mermaid diagram string."""
        nodes = self._parsed.get("nodes", [])
        edges = self._parsed.get("edges", [])
        lines = ["graph TD"]
        for n in nodes:
            if isinstance(n, dict):
                nid = n.get("id", "")
                name = n.get("name", nid)
                lines.append(f'    {nid}["{name}"]')
        for e in edges:
            if isinstance(e, dict):
                f = e.get("from", "")
                t = e.get("to", "")
                label = e.get("label", e.get("mode", ""))
                if label:
                    lines.append(f'    {f} -->|"{label}"| {t}')
                else:
                    lines.append(f"    {f} --> {t}")
        return "\n".join(lines)
