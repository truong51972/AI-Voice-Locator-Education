from pathlib import Path

import numpy as np
import soundfile as sf

from voice_locator.audio import prepare_gradio_audio
from voice_locator.ui import MAX_REFERENCE_SPEAKERS, _readiness, _switch_target_mode


def _audio():
    return (16_000, np.zeros(16_000, dtype=np.float32))


def test_reference_limit_is_hard_capped_at_three():
    assert MAX_REFERENCE_SPEAKERS == 3


def test_readiness_accepts_up_to_three_fixed_references():
    refs = ["A", _audio(), "B", _audio(), "", None]
    status, button = _readiness(*refs, None, "sample.mp4")
    assert "Target: ready" in status
    assert "References: 2/3" in status
    assert button["interactive"] is True
    assert button["value"] == "Analyze 2 speakers"


def test_target_mode_switch_clears_hidden_alternative():
    video_update, audio_update = _switch_target_mode("audio")
    assert video_update["visible"] is False
    assert video_update["value"] is None
    assert audio_update["visible"] is True


def test_prepare_gradio_audio_accepts_filepath(tmp_path: Path):
    path = tmp_path / "ref.wav"
    sf.write(path, np.zeros(16_000, dtype=np.float32), 16_000)
    samples = prepare_gradio_audio(str(path))
    assert samples.dtype == np.float32
    assert samples.shape == (16_000,)


def _config():
    from voice_locator.ui import build_app

    return build_app().get_config_file()


def test_native_layout_has_no_custom_ui_hooks():
    config = _config()
    for component in config["components"]:
        props = component.get("props", {})
        assert not props.get("elem_classes")
        assert not props.get("elem_id")

    for dependency in config["dependencies"]:
        assert not dependency.get("js")


def test_reference_inputs_live_in_native_accordion_and_are_filepath_backed():
    config = _config()

    accordions = [
        component for component in config["components"]
        if component.get("type") == "accordion"
    ]
    labels = [component.get("props", {}).get("label", "") for component in accordions]
    assert any(label.startswith("2. Reference speakers") for label in labels)

    audios = [
        component for component in config["components"]
        if component.get("type") == "audio"
        and component.get("props", {}).get("label") == "Reference audio"
    ]
    assert len(audios) == 3
    for audio in audios:
        props = audio["props"]
        assert props.get("visible", True) is True
        assert props.get("sources") == ["upload", "microphone"]
        assert props.get("type") == "filepath"
        assert props.get("format") == "wav"
        assert props.get("editable") is False
        assert props.get("waveform_options", {}).get("show_recording_waveform") is False


def test_reference_audio_has_no_frontend_event_listener():
    config = _config()
    ref_audio_ids = {
        component["id"]
        for component in config["components"]
        if component.get("type") == "audio"
        and component.get("props", {}).get("label") == "Reference audio"
    }
    assert len(ref_audio_ids) == 3

    triggers = []
    for dependency in config["dependencies"]:
        for target in dependency.get("targets", []):
            if isinstance(target, (list, tuple)) and target and target[0] in ref_audio_ids:
                triggers.append(target[1])
    assert triggers == []


def test_primary_timeline_is_always_mounted_with_initial_plot_value():
    config = _config()
    timeline_plots = [
        component
        for component in config["components"]
        if component.get("type") == "plot"
        and component.get("props", {}).get("label") == "Speaker timeline"
    ]
    assert len(timeline_plots) == 1
    assert timeline_plots[0]["props"].get("visible", True) is True
    assert timeline_plots[0]["props"].get("value") is not None


def test_analyze_updates_timeline_but_does_not_mount_or_hide_it():
    config = _config()
    timeline_id = next(
        component["id"]
        for component in config["components"]
        if component.get("type") == "plot"
        and component.get("props", {}).get("label") == "Speaker timeline"
    )
    analyze_dependencies = [
        dep for dep in config["dependencies"]
        if any(event == "click" for _, event in dep.get("targets", []))
    ]
    assert len(analyze_dependencies) == 1
    assert timeline_id in analyze_dependencies[0]["outputs"]


def test_app_launch_uses_gradio_defaults_without_custom_css_or_theme():
    source = (Path(__file__).parents[1] / "app.py").read_text(encoding="utf-8")
    assert "css=" not in source
    assert "theme=" not in source
    assert "app.launch(inbrowser=True)" in source
