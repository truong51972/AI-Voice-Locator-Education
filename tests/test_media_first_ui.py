import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import numpy as np
import soundfile as sf
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtWidgets import QMainWindow

from voice_locator.audio import prepare_gradio_audio
from voice_locator.profiles import DEFAULT_PROFILE_KEY, INFERENCE_PROFILES
from voice_locator.ui import MAX_REFERENCE_SPEAKERS, build_app, create_application


def test_reference_limit_is_hard_capped_at_three():
    assert MAX_REFERENCE_SPEAKERS == 3


def test_prepare_audio_filepath_contract_is_preserved(tmp_path: Path):
    path = tmp_path / "ref.wav"
    sf.write(path, np.zeros(16_000, dtype=np.float32), 16_000)
    samples = prepare_gradio_audio(str(path))
    assert samples.dtype == np.float32
    assert samples.shape == (16_000,)


def test_desktop_window_uses_native_qt_media_and_three_references():
    app = create_application([])
    window = build_app()
    try:
        assert isinstance(window, QMainWindow)
        assert isinstance(window.video_widget, QVideoWidget)
        assert len(window.reference_inputs) == 3
        assert window.profile.currentData() == DEFAULT_PROFILE_KEY
        assert window.segment_table.columnCount() == 7
    finally:
        window.close()
        app.processEvents()


def test_profile_selector_applies_profile_default_threshold():
    app = create_application([])
    window = build_app()
    try:
        profile = INFERENCE_PROFILES["accurate"]
        index = window.profile.findData(profile.key)
        assert index >= 0
        window.profile.setCurrentIndex(index)
        assert window.threshold.value() == profile.default_threshold
        assert profile.description in window.profile_help.text()
    finally:
        window.close()
        app.processEvents()


def test_entrypoint_is_desktop_qt_not_gradio():
    source = (Path(__file__).parents[1] / "app.py").read_text(encoding="utf-8")
    project = (Path(__file__).parents[1] / "pyproject.toml").read_text(encoding="utf-8")
    assert "app.launch" not in source
    assert "create_application" in source
    assert "qt_app.exec()" in source
    assert "PySide6" in project
    assert '"gradio==' not in project
