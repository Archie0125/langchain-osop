"""OSOP tools for LangChain agents."""

from __future__ import annotations

from typing import Any

import yaml

try:
    from langchain_core.tools import tool
except ImportError:
    raise ImportError("langchain-core is required: pip install langchain-core")


@tool
def osop_validate(content: str) -> str:
    """Validate an OSOP workflow YAML string. Returns validation results with any errors found."""
    try:
        data = yaml.safe_load(content)
    except yaml.YAMLError as e:
        return f"YAML parse error: {e}"

    if not isinstance(data, dict):
        return "Error: OSOP content must be a YAML mapping"

    errors = []
    warnings = []

    # Required fields
    if "osop_version" not in data:
        errors.append("Missing required field: osop_version")
    if "id" not in data:
        errors.append("Missing required field: id")
    if "nodes" not in data:
        errors.append("Missing required field: nodes")
    if "edges" not in data:
        errors.append("Missing required field: edges")

    valid_types = {"human", "agent", "api", "cli", "db", "git", "docker", "cicd", "mcp", "system", "infra", "data"}
    valid_modes = {"sequential", "conditional", "parallel", "loop", "event", "fallback", "error", "timeout", "spawn", "switch"}

    # Validate nodes
    nodes = data.get("nodes", [])
    node_ids = set()
    for i, n in enumerate(nodes):
        if not isinstance(n, dict):
            errors.append(f"Node {i}: must be a mapping")
            continue
        nid = n.get("id")
        if not nid:
            errors.append(f"Node {i}: missing 'id'")
        elif nid in node_ids:
            errors.append(f"Node '{nid}': duplicate id")
        else:
            node_ids.add(nid)
        ntype = n.get("type")
        if ntype and ntype not in valid_types:
            warnings.append(f"Node '{nid}': unknown type '{ntype}' (valid: {', '.join(sorted(valid_types))})")

    # Validate edges
    edges = data.get("edges", [])
    for i, e in enumerate(edges):
        if not isinstance(e, dict):
            errors.append(f"Edge {i}: must be a mapping")
            continue
        f = e.get("from")
        t = e.get("to")
        if not f:
            errors.append(f"Edge {i}: missing 'from'")
        elif f not in node_ids:
            errors.append(f"Edge {i}: 'from' references unknown node '{f}'")
        if not t:
            errors.append(f"Edge {i}: missing 'to'")
        elif t not in node_ids:
            errors.append(f"Edge {i}: 'to' references unknown node '{t}'")
        mode = e.get("mode")
        if mode and mode not in valid_modes:
            warnings.append(f"Edge {i}: unknown mode '{mode}'")

    if not errors and not warnings:
        return f"Valid OSOP workflow: {len(nodes)} nodes, {len(edges)} edges."
    parts = []
    if errors:
        parts.append(f"Errors ({len(errors)}):\n" + "\n".join(f"  - {e}" for e in errors))
    if warnings:
        parts.append(f"Warnings ({len(warnings)}):\n" + "\n".join(f"  - {w}" for w in warnings))
    return "\n".join(parts)


@tool
def osop_describe(content: str) -> str:
    """Describe an OSOP workflow in natural language. Takes YAML content and returns a human-readable summary."""
    try:
        data = yaml.safe_load(content)
    except yaml.YAMLError as e:
        return f"YAML parse error: {e}"

    if not isinstance(data, dict):
        return "Error: not a valid OSOP workflow"

    name = data.get("name", data.get("id", "Untitled"))
    desc = data.get("description", "")
    nodes = data.get("nodes", [])
    edges = data.get("edges", [])

    lines = [f"**{name}**"]
    if desc:
        lines.append(desc)
    lines.append(f"\n{len(nodes)} nodes, {len(edges)} edges\n")

    for n in nodes:
        if isinstance(n, dict):
            ntype = n.get("type", "system")
            nname = n.get("name", n.get("id", "?"))
            purpose = n.get("purpose", n.get("description", ""))
            lines.append(f"• [{ntype}] {nname}{f': {purpose}' if purpose else ''}")

    lines.append("\nFlow:")
    for e in edges:
        if isinstance(e, dict):
            mode = e.get("mode", "→")
            lines.append(f"  {e.get('from', '?')} {mode} {e.get('to', '?')}")

    return "\n".join(lines)


@tool
def osop_to_mermaid(content: str) -> str:
    """Convert an OSOP workflow YAML to a Mermaid diagram string."""
    try:
        data = yaml.safe_load(content)
    except yaml.YAMLError as e:
        return f"YAML parse error: {e}"

    nodes = data.get("nodes", [])
    edges = data.get("edges", [])
    lines = ["graph TD"]

    type_styles = {
        "human": ":::blue", "agent": ":::purple", "api": ":::green",
        "cli": ":::yellow", "cicd": ":::orange", "git": ":::red",
    }

    for n in nodes:
        if isinstance(n, dict):
            nid = n.get("id", "")
            name = n.get("name", nid)
            lines.append(f'    {nid}["{name}"]')

    for e in edges:
        if isinstance(e, dict):
            f = e.get("from", "")
            t = e.get("to", "")
            label = e.get("label", "")
            mode = e.get("mode", "sequential")
            edge_label = label or (mode if mode != "sequential" else "")
            if edge_label:
                lines.append(f'    {f} -->|"{edge_label}"| {t}')
            else:
                lines.append(f"    {f} --> {t}")

    return "\n".join(lines)


def create_osop_tools() -> list:
    """Create all OSOP tools for use with a LangChain agent.

    Example:
        from langchain_osop import create_osop_tools
        tools = create_osop_tools()
        agent = create_react_agent(llm, tools)
    """
    return [osop_validate, osop_describe, osop_to_mermaid]
