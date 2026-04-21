from pathlib import Path

import pytest

from usf.obsidian import load_vault, resolve_wikilinks


@pytest.fixture
def vault(tmp_path: Path):
    (tmp_path / "short.md").write_text(
        "---\nsummary: SHORT-SUMMARY\n---\n\n# Body\nhello world\n", encoding="utf-8"
    )
    big = "x" * 10000
    (tmp_path / "big.md").write_text(f"# Body\n{big}\n", encoding="utf-8")
    (tmp_path / "a.md").write_text("# Body\nlinks to [[b]]\n", encoding="utf-8")
    (tmp_path / "b.md").write_text("# Body\nlinks to [[a]]\n", encoding="utf-8")
    return load_vault(tmp_path)


def test_resolve_unknown_leaves_literal(vault):
    out, stats = resolve_wikilinks(vault, "see [[missing]]")
    assert "[[missing]]" in out
    assert stats.skipped >= 1


def test_resolve_truncate_mode(vault):
    out, stats = resolve_wikilinks(vault, "ref: [[big]]", mode="truncate", per_link_token_limit=100)
    assert "[truncated]" in out
    assert stats.truncated == 1


def test_resolve_summary_mode(vault):
    out, stats = resolve_wikilinks(vault, "ref: [[short]]", mode="summary")
    assert "SHORT-SUMMARY" in out


def test_resolve_full_mode(vault):
    out, _ = resolve_wikilinks(vault, "ref: [[big]]", mode="full", per_link_token_limit=100)
    assert "[truncated]" not in out


def test_cycle_detected(vault):
    out, _ = resolve_wikilinks(vault, "ref: [[a]]")
    # Cycle should terminate; both links appear but don't infinite-loop
    assert "links to" in out


def test_invalid_mode_raises(vault):
    with pytest.raises(ValueError):
        resolve_wikilinks(vault, "[[short]]", mode="bogus")
