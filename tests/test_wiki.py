from __future__ import annotations

from pathlib import Path

from tp3_sds.wiki import (
    lint_wiki,
    load_page,
    refresh_index,
    scaffold_source,
    search_wiki,
    write_page,
)


def test_scaffold_source_creates_deterministic_page_and_log(tmp_path: Path) -> None:
    root = tmp_path
    (root / "docs" / "raw" / "bibliografia").mkdir(parents=True)
    (root / "docs" / "wiki").mkdir(parents=True)
    raw_path = root / "docs" / "raw" / "bibliografia" / "Hard Spheres Notes.pdf"
    raw_path.write_bytes(b"%PDF-1.4")

    page_path = scaffold_source(root, raw_path)

    assert page_path.name == "source_hard_spheres_notes.md"
    page = load_page(page_path)
    assert page.metadata["type"] == "source"
    assert page.metadata["source_path"] == "docs/raw/bibliografia/Hard Spheres Notes.pdf"
    assert "CITATION NEEDED" in page.body

    log = load_page(root / "docs" / "wiki" / "log.md")
    assert "Hard Spheres Notes [scaffolded]" in log.body


def test_refresh_index_groups_and_sorts_pages(tmp_path: Path) -> None:
    wiki_root = tmp_path / "docs" / "wiki"
    wiki_root.mkdir(parents=True)

    write_page(
        wiki_root / "zeta.md",
        {
            "type": "concept",
            "title": "Zeta Concept",
            "summary": "Zeta summary.",
            "last_updated": "2026-04-13",
        },
        "# Zeta\n",
    )
    write_page(
        wiki_root / "alpha.md",
        {
            "type": "concept",
            "title": "Alpha Concept",
            "summary": "Alpha summary.",
            "last_updated": "2026-04-13",
        },
        "# Alpha\n",
    )
    write_page(
        wiki_root / "system.md",
        {
            "type": "system",
            "title": "System 1",
            "summary": "Main system page.",
            "last_updated": "2026-04-13",
        },
        "# System 1\n",
    )

    index_path = refresh_index(tmp_path)
    index_body = load_page(index_path).body

    assert "## Systems" in index_body
    assert "## Concepts" in index_body
    assert index_body.index("System 1") < index_body.index("Alpha Concept")
    assert index_body.index("Alpha Concept") < index_body.index("Zeta Concept")


def test_lint_detects_broken_links_orphans_missing_index_and_stale_sources(tmp_path: Path) -> None:
    wiki_root = tmp_path / "docs" / "wiki"
    raw_root = tmp_path / "docs" / "raw"
    wiki_root.mkdir(parents=True)
    raw_root.mkdir(parents=True)

    write_page(
        wiki_root / "index.md",
        {
            "type": "administration",
            "title": "Wiki Index",
            "summary": "Index.",
            "last_updated": "2026-04-13",
        },
        "# Wiki Index\n\n## Concepts\n- [Existing](existing.md) - Listed page.\n",
    )
    write_page(
        wiki_root / "existing.md",
        {
            "type": "concept",
            "title": "Existing",
            "summary": "Has broken references.",
            "source_path": "docs/raw/missing.pdf",
            "last_updated": "2026-04-13",
        },
        "# Existing\n\n[Broken](missing.md)\n\nTODO[cite]: add support.\n",
    )
    write_page(
        wiki_root / "orphan.md",
        {
            "type": "analysis",
            "title": "Orphan",
            "summary": "Not linked anywhere.",
            "last_updated": "2026-04-13",
        },
        "# Orphan\n",
    )

    issues = lint_wiki(tmp_path)
    codes = {issue.code for issue in issues}

    assert "broken_link" in codes
    assert "orphan_page" in codes
    assert "missing_index_entry" in codes
    assert "stale_source_reference" in codes
    assert "uncited_claim_marker" in codes


def test_search_uses_index_then_rg_fallback(tmp_path: Path) -> None:
    wiki_root = tmp_path / "docs" / "wiki"
    wiki_root.mkdir(parents=True)

    write_page(
        wiki_root / "system.md",
        {
            "type": "system",
            "title": "System 1",
            "summary": "Hard-sphere scanning rate.",
            "last_updated": "2026-04-13",
        },
        "# System 1\n\nThis body mentions hidden phrase omega-signal.\n",
    )
    refresh_index(tmp_path)

    index_results = search_wiki(tmp_path, "Hard-sphere")
    assert index_results
    assert index_results[0].source == "index"

    fallback_results = search_wiki(tmp_path, "omega-signal")
    assert fallback_results
    assert fallback_results[0].source.startswith("rg:")
