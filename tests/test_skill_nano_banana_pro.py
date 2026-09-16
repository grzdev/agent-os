from __future__ import annotations

import importlib.util
from pathlib import Path
from unittest.mock import patch

SCRIPT_PATH = (
    Path(__file__).resolve().parent.parent
    / "src"
    / "agentos"
    / "skills"
    / "bundled"
    / "nano-banana-pro"
    / "scripts"
    / "generate_image.py"
)


def _import_generate_image():
    spec = importlib.util.spec_from_file_location("nano_banana_pro_generate_image", SCRIPT_PATH)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_placeholder_flag_parsing(tmp_path: Path):
    mod = _import_generate_image()
    out_file = tmp_path / "test.png"

    # 1. Bare flag should parse as const="yes"
    with (
        patch.object(mod, "resolve_api_key", return_value="fake-key"),
        patch.object(mod, "_try_one_attempt", side_effect=RuntimeError("fail")),
        patch.object(mod, "_write_placeholder_png") as mock_ph,
    ):
        code = mod.main(["--prompt", "test", "--filename", str(out_file), "--placeholder-on-fail"])
        assert code == 0
        assert mock_ph.called

    # 2. Omitted flag should default to "no" and fail
    with (
        patch.object(mod, "resolve_api_key", return_value="fake-key"),
        patch.object(mod, "_try_one_attempt", side_effect=RuntimeError("fail")),
        patch.object(mod, "_write_placeholder_png") as mock_ph,
    ):
        code = mod.main(["--prompt", "test", "--filename", str(out_file)])
        assert code == 1
        assert not mock_ph.called

    # 3. Explicit --placeholder-on-fail yes
    with (
        patch.object(mod, "resolve_api_key", return_value="fake-key"),
        patch.object(mod, "_try_one_attempt", side_effect=RuntimeError("fail")),
        patch.object(mod, "_write_placeholder_png") as mock_ph,
    ):
        code = mod.main(
            ["--prompt", "test", "--filename", str(out_file), "--placeholder-on-fail", "yes"]
        )
        assert code == 0
        assert mock_ph.called

    # 4. Explicit --placeholder-on-fail no
    with (
        patch.object(mod, "resolve_api_key", return_value="fake-key"),
        patch.object(mod, "_try_one_attempt", side_effect=RuntimeError("fail")),
        patch.object(mod, "_write_placeholder_png") as mock_ph,
    ):
        code = mod.main(
            ["--prompt", "test", "--filename", str(out_file), "--placeholder-on-fail", "no"]
        )
        assert code == 1
        assert not mock_ph.called
