import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import numpy as np
import soundfile as sf
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMainWindow, QScrollArea

from voice_locator.audio import prepare_gradio_audio
from voice_locator.localization import MatchSegment
from voice_locator.pipeline import AnalysisBundle, SpeakerResult
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


def test_workspace_uses_editor_splitters_without_page_scroll():
    app = create_application([])
    window = build_app()
    try:
        assert isinstance(window, QMainWindow)
        assert window.root_splitter.orientation() == Qt.Orientation.Vertical
        assert window.workspace_splitter.orientation() == Qt.Orientation.Horizontal
        assert window.analysis_page.findChildren(QScrollArea) == []
        assert len(window.reference_inputs) == 3
        assert window.segment_table.columnCount() == 4
        assert window.profile.currentData() == DEFAULT_PROFILE_KEY
        assert not window.windowIcon().isNull()
    finally:
        window.close()
        app.processEvents()


def test_preview_overlay_tracks_active_speaker_segment():
    app = create_application([])
    window = build_app()
    try:
        segment = MatchSegment(start=1.0, end=3.0, avg_score=0.72, max_score=0.84)
        result = SpeakerResult(
            key="spk_01",
            name="Học sinh A",
            scores=[],
            segments=[segment],
            matched_duration=2.0,
            coverage=20.0,
            max_score=0.84,
        )
        bundle = AnalysisBundle(
            target=np.zeros(16_000, dtype=np.float32),
            media_kind="video",
            duration=10.0,
            results=[result],
            scores_by_name={"Học sinh A": []},
            segments_by_name={"Học sinh A": [segment]},
        )
        window.video_widget.overlay.set_bundle(bundle)
        window.video_widget.overlay.set_position(2.0)
        active = window.video_widget.overlay._active_results()
        assert len(active) == 1
        assert active[0][0].name == "Học sinh A"
        window.video_widget.overlay.set_position(5.0)
        assert window.video_widget.overlay._active_results() == []
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


def test_src_layout_exposes_installed_desktop_entrypoint():
    root = Path(__file__).parents[1]
    source = (root / "src" / "voice_locator" / "app.py").read_text(encoding="utf-8")
    module_entry = (root / "src" / "voice_locator" / "__main__.py").read_text(encoding="utf-8")
    project = (root / "pyproject.toml").read_text(encoding="utf-8")

    assert not (root / "app.py").exists()
    assert "app.launch" not in source
    assert "create_application" in source
    assert "qt_app.exec()" in source
    assert "from .app import main" in module_entry
    assert '[build-system]' in project
    assert 'build-backend = "hatchling.build"' in project
    assert '[project.scripts]' in project
    assert 'voice-locator = "voice_locator.app:main"' in project
    assert 'start = "voice-locator"' in project
    assert 'desktop = "voice-locator"' in project
    assert 'pythonpath = ["src"]' not in project
    assert "PySide6" in project
    assert '"gradio==' not in project
