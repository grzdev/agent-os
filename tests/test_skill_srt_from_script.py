"""Tests for the bundled srt-from-script skill."""

from __future__ import annotations

import io
import sys
from pathlib import Path

import pytest

from agentos.skills.loader import SkillLoader

ROOT = Path(__file__).resolve().parents[1]
BUNDLED = ROOT / "src" / "agentos" / "skills" / "bundled"
SCRIPTS = BUNDLED / "srt-from-script" / "scripts"


def _srt_module():
    sys.path.insert(0, str(SCRIPTS))
    try:
        import build_srt  # type: ignore[import-not-found]
    finally:
        sys.path.pop(0)
    return build_srt


SAMPLE_SCRIPT = """=== SHOT_1 ===
DURATION_S: 3
VOICEOVER: First scene begins.

=== SHOT_2 ===
DURATION_S: 4
VOICEOVER: Second scene continues.
"""


def test_skill_loads() -> None:
    loader = SkillLoader(bundled_dir=BUNDLED)
    spec = loader.get_by_name("srt-from-script")
    assert spec is not None
    assert spec.name == "srt-from-script"


def test_build_srt_from_file(tmp_path: Path) -> None:
    build_srt = _srt_module()
    script_file = tmp_path / "script.txt"
    script_file.write_text(SAMPLE_SCRIPT, encoding="utf-8")
    out_file = tmp_path / "out.srt"

    rc = build_srt.main(["--script", str(script_file), "--output", str(out_file)])
    assert rc == 0
    assert out_file.exists()
    content = out_file.read_text(encoding="utf-8")
    assert "First scene begins." in content
    assert "Second scene continues." in content
    assert "00:00:00,000 --> 00:00:02,800" in content


def test_build_srt_from_stdin_buffer(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    build_srt = _srt_module()
    out_file = tmp_path / "out.srt"

    buf = io.BytesIO(SAMPLE_SCRIPT.encode("utf-8"))
    wrapper = io.TextIOWrapper(buf, encoding="utf-8")
    monkeypatch.setattr(sys, "stdin", wrapper)

    rc = build_srt.main(["--output", str(out_file)])
    assert rc == 0
    assert out_file.exists()
    content = out_file.read_text(encoding="utf-8")
    assert "First scene begins." in content


def test_build_srt_from_stdin_text_fallback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    build_srt = _srt_module()
    out_file = tmp_path / "out.srt"

    string_io = io.StringIO(SAMPLE_SCRIPT)
    monkeypatch.setattr(sys, "stdin", string_io)

    rc = build_srt.main(["--output", str(out_file)])
    assert rc == 0
    assert out_file.exists()
    content = out_file.read_text(encoding="utf-8")
    assert "First scene begins." in content


def test_build_srt_unreadable_script(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    build_srt = _srt_module()
    missing_file = tmp_path / "nonexistent.txt"
    out_file = tmp_path / "out.srt"

    rc = build_srt.main(["--script", str(missing_file), "--output", str(out_file)])
    assert rc == 1
    err = capsys.readouterr().err
    assert "Error: cannot read --script" in err


def test_build_srt_empty_script(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    build_srt = _srt_module()
    monkeypatch.setattr(sys, "stdin", io.StringIO(""))

    rc = build_srt.main(["--output", "out.srt"])
    assert rc == 1
    err = capsys.readouterr().err
    assert "Error: empty script input." in err


def test_build_srt_no_shots(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    build_srt = _srt_module()
    monkeypatch.setattr(sys, "stdin", io.StringIO("Just random text with no shot blocks"))

    rc = build_srt.main(["--output", "out.srt"])
    assert rc == 1
    err = capsys.readouterr().err
    assert "Error: no SHOT_N blocks found in script." in err


def test_build_srt_write_error(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    build_srt = _srt_module()
    script_file = tmp_path / "script.txt"
    script_file.write_text(SAMPLE_SCRIPT, encoding="utf-8")

    blocker = tmp_path / "blocker"
    blocker.write_text("file", encoding="utf-8")
    out_file = blocker / "out.srt"

    rc = build_srt.main(["--script", str(script_file), "--output", str(out_file)])
    assert rc == 1
    err = capsys.readouterr().err
    assert "Error: cannot write --output" in err
