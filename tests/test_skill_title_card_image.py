"""Tests for the bundled title-card-image skill."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

from agentos.skills.loader import SkillLoader

ROOT = Path(__file__).resolve().parents[1]
BUNDLED = ROOT / "src" / "agentos" / "skills" / "bundled"
SCRIPTS = BUNDLED / "title-card-image" / "scripts"


def _render_module():
    sys.path.insert(0, str(SCRIPTS))
    try:
        import render  # type: ignore[import-not-found]
    finally:
        sys.path.pop(0)
    return render


def test_skill_loads() -> None:
    loader = SkillLoader(bundled_dir=BUNDLED)
    spec = loader.get_by_name("title-card-image")
    assert spec is not None
    assert spec.name == "title-card-image"


def test_wrap_text_handles_zero_or_negative_max_chars() -> None:
    render = _render_module()
    # Must not raise ValueError: range() arg 3 must not be zero
    lines = render._wrap_text("短剧标题", 0)
    assert lines == ["短", "剧", "标", "题"]

    ascii_lines = render._wrap_text("hello world", 0)
    assert ascii_lines == ["hello", "world"]


def test_main_rejects_non_positive_max_chars(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    render = _render_module()
    out = tmp_path / "out.png"

    rc = render.main(["--text", "短剧标题", "--output", str(out), "--max-chars-per-line", "0"])
    assert rc == 1
    err = capsys.readouterr().err
    assert "Error: --max-chars-per-line must be greater than 0." in err
    assert not out.exists()


def test_main_rejects_invalid_dimensions(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    render = _render_module()
    out = tmp_path / "out.png"

    rc = render.main(["--text", "Title", "--output", str(out), "--width", "0"])
    assert rc == 1
    err = capsys.readouterr().err
    assert "Error: --width and --height must be greater than 0." in err
    assert not out.exists()


def test_main_renders_valid_card(tmp_path: Path) -> None:
    render = _render_module()
    out = tmp_path / "out.png"

    rc = render.main([
        "--text", "Episode 1: The Beginning",
        "--subtitle", "Season 1",
        "--output", str(out),
        "--width", "400",
        "--height", "600",
    ])
    assert rc == 0
    assert out.exists()
    assert out.stat().st_size > 0
