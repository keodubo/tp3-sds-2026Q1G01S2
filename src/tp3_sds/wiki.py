from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from datetime import date
from os import path as os_path
from pathlib import Path
from urllib.parse import unquote

from tp3_sds.frontmatter import dump_frontmatter, parse_frontmatter
from tp3_sds.paths import raw_dir, wiki_dir

SECTION_TITLES = {
    "system": "Systems",
    "concept": "Concepts",
    "observable": "Observables",
    "source": "Sources",
    "analysis": "Analyses",
    "decision": "Decisions",
    "administration": "Administration",
}
SECTION_ORDER = [
    "system",
    "concept",
    "observable",
    "source",
    "analysis",
    "decision",
    "administration",
]
MARKDOWN_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
CITATION_MARKERS = ("CITATION NEEDED", "TODO[cite]")
INDEX_FILE = "index.md"
LOG_FILE = "log.md"


@dataclass(frozen=True)
class WikiPage:
    path: Path
    metadata: dict[str, object]
    body: str


@dataclass(frozen=True)
class SearchResult:
    path: Path
    title: str
    summary: str
    source: str
    snippet: str


@dataclass(frozen=True)
class LintIssue:
    code: str
    path: Path
    message: str
    level: str = "error"


def load_page(path: Path) -> WikiPage:
    document = parse_frontmatter(path.read_text(encoding="utf-8"))
    return WikiPage(path=path, metadata=document.metadata, body=document.body)


def write_page(path: Path, metadata: dict[str, object], body: str) -> None:
    path.write_text(dump_frontmatter(metadata, body), encoding="utf-8")


def ensure_log_file(root: Path) -> Path:
    log_path = wiki_dir(root) / LOG_FILE
    if not log_path.exists():
        write_page(
            log_path,
            {
                "type": "administration",
                "title": "Wiki Log",
                "summary": "Chronological record of wiki operations.",
                "tags": ["administration", "log"],
                "last_updated": today(),
            },
            "# Wiki Log\n\nChronological record of knowledge ingestion and synthesis operations.\n",
        )
    return log_path


def append_log_entry(root: Path, header: str, bullet_points: list[str]) -> None:
    log_path = ensure_log_file(root)
    page = load_page(log_path)
    if header in page.body:
        return
    lines = [page.body.rstrip(), "", header]
    lines.extend(f"- {item}" for item in bullet_points)
    lines.append("")
    metadata = dict(page.metadata)
    metadata["last_updated"] = today()
    write_page(log_path, metadata, "\n".join(lines))


def scaffold_source(root: Path, raw_path: Path) -> Path:
    resolved_root = root.resolve()
    raw_abs = raw_path.resolve() if raw_path.is_absolute() else (resolved_root / raw_path).resolve()
    raw_base = raw_dir(resolved_root).resolve()
    try:
        relative_raw = raw_abs.relative_to(raw_base)
    except ValueError as exc:
        raise ValueError(f"{raw_abs} is outside {raw_base}") from exc
    if not raw_abs.exists():
        raise FileNotFoundError(raw_abs)

    page_name = f"source_{slugify(raw_abs.stem)}.md"
    page_path = wiki_dir(resolved_root) / page_name
    title = humanize_title(raw_abs.stem)
    metadata = {
        "type": "source",
        "title": f"Source: {title}",
        "summary": "Pending manual ingest.",
        "tags": ["source"],
        "source_path": (Path("docs/raw") / relative_raw).as_posix(),
        "last_updated": today(),
    }

    if page_path.exists():
        existing = load_page(page_path)
        current_metadata = dict(existing.metadata)
        current_metadata.update(metadata)
        write_page(page_path, current_metadata, existing.body)
    else:
        raw_link = Path(os_path.relpath(raw_abs, page_path.parent))
        body = "\n".join(
            [
                f"# Source: {title}",
                "",
                f"**File**: [{raw_abs.name}]({raw_link.as_posix()})",
                f"**Date Ingested**: {today()}",
                "**Status**: Scaffolded for manual ingest.",
                "",
                "## Summary",
                "CITATION NEEDED: Replace this placeholder with a synthesized summary after reading the source.",
                "",
                "## Key Points",
                "- TODO[cite]: Add the most relevant claims, methods, and constraints.",
                "",
                "## Related Pages",
                "- Link this source to the affected system, concept, and analysis pages.",
            ]
        )
        write_page(page_path, metadata, body)

    append_log_entry(
        resolved_root,
        f"## [{today()}] ingest | {title} [scaffolded]",
        [
            f"Created or refreshed source stub: `{page_name}`.",
            f"Queued manual ingest for `{Path('docs/raw') / relative_raw}`.",
        ],
    )
    return page_path


def refresh_index(root: Path) -> Path:
    pages = [
        load_page(path)
        for path in sorted(wiki_dir(root).glob("*.md"))
        if path.name != INDEX_FILE
    ]
    grouped: dict[str, list[WikiPage]] = {section: [] for section in SECTION_ORDER}
    for page in pages:
        page_type = str(page.metadata.get("type", "analysis"))
        grouped.setdefault(page_type, []).append(page)

    body_lines = [
        "# Wiki Index",
        "",
        "This index is a catalog of all knowledge synthesized from source documents.",
        "",
    ]
    for section in SECTION_ORDER:
        items = sorted(grouped.get(section, []), key=lambda item: str(item.metadata.get("title", item.path.stem)).lower())
        if not items:
            continue
        body_lines.append(f"## {SECTION_TITLES.get(section, humanize_title(section))}")
        for item in items:
            title = str(item.metadata.get("title", humanize_title(item.path.stem)))
            summary = str(item.metadata.get("summary", "No summary yet."))
            body_lines.append(f"- [{title}]({item.path.name}) - {summary}")
        body_lines.append("")

    index_path = wiki_dir(root) / INDEX_FILE
    write_page(
        index_path,
        {
            "type": "administration",
            "title": "Wiki Index",
            "summary": "Catalog of wiki pages grouped by type.",
            "tags": ["administration", "index"],
            "last_updated": today(),
        },
        "\n".join(body_lines).strip() + "\n",
    )
    return index_path


def search_wiki(root: Path, query: str) -> list[SearchResult]:
    tokens = [token.lower() for token in query.split() if token.strip()]
    index_path = wiki_dir(root) / INDEX_FILE
    if index_path.exists():
        index_page = load_page(index_path)
        matches: list[SearchResult] = []
        for line in index_page.body.splitlines():
            if not line.startswith("- ["):
                continue
            lowered = line.lower()
            if not tokens or all(token in lowered for token in tokens):
                title, link_target = _extract_markdown_link(line)
                summary = line.split(" - ", maxsplit=1)[1] if " - " in line else ""
                matches.append(
                    SearchResult(
                        path=wiki_dir(root) / link_target,
                        title=title,
                        summary=summary,
                        source="index",
                        snippet=line.strip(),
                    )
                )
        if matches:
            return matches

    return _search_with_rg(root, query)


def lint_wiki(root: Path) -> list[LintIssue]:
    wiki_root = wiki_dir(root)
    pages = {
        path.name: load_page(path)
        for path in sorted(wiki_root.glob("*.md"))
    }
    issues: list[LintIssue] = []
    index_links = _load_index_targets(pages.get(INDEX_FILE))
    inbound_links = {name: 0 for name in pages}

    for name, page in pages.items():
        for marker in CITATION_MARKERS:
            if marker in page.body:
                issues.append(
                    LintIssue(
                        code="uncited_claim_marker",
                        path=page.path,
                        message=f"Found citation placeholder marker: {marker}.",
                        level="warning",
                    )
                )

        source_path = page.metadata.get("source_path")
        if isinstance(source_path, str):
            referenced = (root / source_path).resolve()
            if not referenced.exists():
                issues.append(
                    LintIssue(
                        code="stale_source_reference",
                        path=page.path,
                        message=f"Metadata source_path points to missing file: {source_path}.",
                    )
                )

        for _, target in iter_links(page.body):
            if target.startswith("http://") or target.startswith("https://") or target.startswith("#"):
                continue
            resolved = (page.path.parent / unquote(target)).resolve()
            if target.endswith(".md"):
                if not resolved.exists():
                    issues.append(
                        LintIssue(
                            code="broken_link",
                            path=page.path,
                            message=f"Broken wiki link: {target}.",
                        )
                    )
                    continue
                target_name = resolved.name
                if target_name in inbound_links and name != INDEX_FILE:
                    inbound_links[target_name] += 1
            elif "/raw/" in target or target.startswith("../raw/"):
                if not resolved.exists():
                    issues.append(
                        LintIssue(
                            code="stale_source_reference",
                            path=page.path,
                            message=f"Broken raw-source link: {target}.",
                        )
                    )

    for name, page in pages.items():
        if name in {INDEX_FILE}:
            continue
        if name not in index_links:
            issues.append(
                LintIssue(
                    code="missing_index_entry",
                    path=page.path,
                    message="Page is not listed in docs/wiki/index.md.",
                    level="warning",
                )
            )
        if str(page.metadata.get("type")) != "administration" and inbound_links.get(name, 0) == 0:
            issues.append(
                LintIssue(
                    code="orphan_page",
                    path=page.path,
                    message="Page has no inbound links from other non-index wiki pages.",
                    level="warning",
                )
            )

    return issues


def iter_links(body: str) -> list[tuple[str, str]]:
    return MARKDOWN_LINK_RE.findall(body)


def slugify(text: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "_", text.strip().lower())
    return cleaned.strip("_")


def humanize_title(text: str) -> str:
    return re.sub(r"[_-]+", " ", text).strip()


def today() -> str:
    return date.today().isoformat()


def _extract_markdown_link(line: str) -> tuple[str, str]:
    match = MARKDOWN_LINK_RE.search(line)
    if not match:
        raise ValueError(f"Line does not contain a markdown link: {line}")
    return match.group(1), match.group(2)


def _load_index_targets(index_page: WikiPage | None) -> set[str]:
    if index_page is None:
        return set()
    targets = set()
    for _, target in iter_links(index_page.body):
        if target.endswith(".md"):
            targets.add(Path(target).name)
    return targets


def _search_with_rg(root: Path, query: str) -> list[SearchResult]:
    wiki_root = wiki_dir(root)
    try:
        completed = subprocess.run(
            ["rg", "-n", "--no-heading", "--glob", "*.md", query, str(wiki_root)],
            check=False,
            capture_output=True,
            text=True,
        )
    except (FileNotFoundError, PermissionError, OSError):
        return _search_without_rg(wiki_root, query)

    if completed.returncode not in {0, 1}:
        return _search_without_rg(wiki_root, query)

    results: list[SearchResult] = []
    for line in completed.stdout.splitlines():
        try:
            raw_path, line_number, snippet = line.split(":", maxsplit=2)
        except ValueError:
            continue
        path = Path(raw_path)
        if path.name == INDEX_FILE:
            continue
        page = load_page(path)
        results.append(
            SearchResult(
                path=path,
                title=str(page.metadata.get("title", humanize_title(path.stem))),
                summary=str(page.metadata.get("summary", "")),
                source=f"rg:{line_number}",
                snippet=snippet.strip(),
            )
        )
    return results


def _search_without_rg(wiki_root: Path, query: str) -> list[SearchResult]:
    needle = query.lower()
    results: list[SearchResult] = []
    for path in sorted(wiki_root.glob("*.md")):
        if path.name == INDEX_FILE:
            continue
        page = load_page(path)
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if needle not in line.lower():
                continue
            results.append(
                SearchResult(
                    path=path,
                    title=str(page.metadata.get("title", humanize_title(path.stem))),
                    summary=str(page.metadata.get("summary", "")),
                    source=f"rg:{line_number}",
                    snippet=line.strip(),
                )
            )
    return results
