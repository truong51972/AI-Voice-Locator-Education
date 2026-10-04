from types import SimpleNamespace

import pytest

from voice_locator.ui import _parse_timecode, _select_segment


def test_parse_timecode_seconds_and_minutes():
    assert _parse_timecode("8.5s") == pytest.approx(8.5)
    assert _parse_timecode("01:12.5") == pytest.approx(72.5)


def test_select_segment_returns_seek_start_and_status():
    evt = SimpleNamespace(
        selected=True,
        row_value=["Học sinh A", 2, "01:12.5", "01:18.0", "5.5s", 0.72, 0.84],
    )
    audio_update, video_update, status = _select_segment(evt)
    assert audio_update["playback_position"] == pytest.approx(72.5)
    assert video_update["playback_position"] == pytest.approx(72.5)
    assert audio_update["__type__"] == "update"
    assert video_update["__type__"] == "update"
    assert "Học sinh A" in status
    assert "01:12.5" in status
    assert "01:18.0" in status


def test_select_segment_ignores_deselect():
    evt = SimpleNamespace(selected=False, row_value=["A", 1, "2.0s", "4.0s"])
    audio_update, video_update, status = _select_segment(evt)
    assert audio_update == {"__type__": "update"}
    assert video_update == {"__type__": "update"}
    assert status == ""


def test_build_app_wires_native_seek_to_single_target_player_without_javascript():
    from voice_locator.ui import build_app

    app = build_app()
    config = app.get_config_file()
    assert config.get("analytics_enabled") is False

    media_ids = {
        component["props"].get("label"): component["id"]
        for component in config["components"]
        if component.get("type") in {"audio", "video"}
        and component.get("props", {}).get("label") in {"Audio cần phân tích", "Video cần phân tích"}
    }
    assert set(media_ids) == {"Audio cần phân tích", "Video cần phân tích"}

    select_dependencies = [
        dependency
        for dependency in config.get("dependencies", [])
        if any(event == "select" for _, event in dependency.get("targets", []))
    ]
    assert len(select_dependencies) == 1
    dependency = select_dependencies[0]
    assert media_ids["Audio cần phân tích"] in dependency["outputs"]
    assert media_ids["Video cần phân tích"] in dependency["outputs"]
    assert not dependency.get("js")
