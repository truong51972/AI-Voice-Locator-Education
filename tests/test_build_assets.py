from scripts import build


def test_windows_build_uses_valid_png_icon_source() -> None:
    assert build.APP_ICON.name == "voice-locator.png"
    assert build.APP_ICON.read_bytes().startswith(build.PNG_SIGNATURE)
    build._verify_assets()
