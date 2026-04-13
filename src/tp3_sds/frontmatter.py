from __future__ import annotations

import json
from dataclasses import dataclass


@dataclass(frozen=True)
class MarkdownDocument:
    metadata: dict[str, object]
    body: str


def parse_frontmatter(text: str) -> MarkdownDocument:
    if not text.startswith("---\n"):
        return MarkdownDocument(metadata={}, body=text)

    closing = text.find("\n---\n", 4)
    if closing == -1:
        return MarkdownDocument(metadata={}, body=text)

    raw_meta = text[4:closing]
    body = text[closing + 5 :]
    metadata: dict[str, object] = {}
    for line in raw_meta.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        key, sep, raw_value = stripped.partition(":")
        if not sep:
            continue
        metadata[key.strip()] = _parse_value(raw_value.strip())
    return MarkdownDocument(metadata=metadata, body=body)


def dump_frontmatter(metadata: dict[str, object], body: str) -> str:
    lines = ["---"]
    for key, value in metadata.items():
        lines.append(f"{key}: {_dump_value(value)}")
    lines.append("---")
    lines.append(body.rstrip())
    lines.append("")
    return "\n".join(lines)


def _parse_value(raw_value: str) -> object:
    if raw_value == "":
        return ""
    try:
        return json.loads(raw_value)
    except json.JSONDecodeError:
        return raw_value


def _dump_value(value: object) -> str:
    if isinstance(value, str):
        return json.dumps(value)
    return json.dumps(value)
