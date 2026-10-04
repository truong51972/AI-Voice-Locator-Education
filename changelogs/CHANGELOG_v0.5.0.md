# CHANGELOG v0.5.0 — Native PySide6 desktop UI

## Changed

- Replaced the Gradio/browser presentation layer with a native **PySide6 / Qt 6** desktop application.
- Added native media playback with `QMediaPlayer`, `QVideoWidget`, and `QAudioOutput`.
- Added reference-speaker microphone recording with `QAudioInput`, `QMediaCaptureSession`, and `QMediaRecorder`.
- Moved analysis execution to a `QThread` worker so speaker embedding/localization does not block the UI thread.
- Replaced browser-rendered result surfaces with native Qt widgets:
  - speaker timeline;
  - similarity diagnostics;
  - detected-segment table;
  - click-to-seek media review.
- Preserved the existing **Fast / CAM++** and **Accurate / ERes2NetV2** inference profiles.
- Added `voice_locator.service.analyze_bundle()` as a small presentation-neutral adapter over the existing analysis core.

## Packaging

- Added `PySide6>=6.8,<7`.
- Removed Gradio, `gradio-client`, `groovy`, and `safehttpx` runtime dependencies.
- Removed the obsolete custom Gradio PyInstaller hook.
- Updated PyInstaller packaging for Qt Multimedia and retained bundled FFmpeg + sherpa ONNX Runtime handling.
- Packaged smoke tests now construct the Qt UI with the offscreen platform plugin and initialize every configured speaker model.
- Updated `one-click.bat` and release naming to v0.5.0.

## Compatibility

- Speaker embedding, similarity, localization, media extraction, inference-profile registry, and core pipeline behavior remain unchanged.
- Existing pipeline compatibility APIs remain available; the desktop UI is a presentation-layer migration rather than a model rewrite.

## Validation note

The updated tests cover Qt window composition, inference-profile selection, filepath audio compatibility, and native segment seek behavior. A real Windows `one-click.bat` / packaged `.exe` smoke test should still be run before final release to validate host-specific Qt Multimedia plugins and device backends.
