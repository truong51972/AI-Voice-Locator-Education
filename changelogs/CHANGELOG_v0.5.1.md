# v0.5.1 — Video-editor workspace

## UX

- Replace the vertically scrolling analysis page with a fixed video-editor style workspace.
- Keep Preview on the left and a compact inspector on the right.
- Inspector tabs separate Speakers, Analysis settings/diagnostics, and detailed Segments.
- Move the primary result surface to a persistent bottom speaker timeline.
- Render detected speaker regions as timeline clips with a synchronized playhead.
- Click/scrub the timeline to seek the native media player.
- Overlay the currently matched speaker(s) and peak similarity directly on the video preview.
- Keep the detailed segment table as a secondary inspector instead of the primary result surface.

## Packaging / src layout

- Move the application entrypoint from repository-root `app.py` to `src/voice_locator/app.py`.
- Add `src/voice_locator/__main__.py` so `python -m voice_locator` works.
- Declare the project as an installable package with Hatchling and force `uv` package installation.
- Add the `voice-locator = "voice_locator.app:main"` console script.
- Make `poe start` and `poe desktop` run the installed console entrypoint instead of `python app.py`.
- Remove pytest's `pythonpath = ["src"]` escape hatch so tests exercise the installed package contract.
- Point PyInstaller at the packaged application entrypoint under `src/voice_locator`.
- Add `assets/voice-locator.png` for the Qt window/application icon.
- Add `assets/voice-locator.ico` for the Windows executable icon.
- Bundle icon assets through PyInstaller and fail the build if they are missing.
- Bump release version to `0.5.1` and update the one-click Windows ZIP name.

## Scope

The speaker embedding models, Fast/Accurate profiles, media extraction, matching, thresholding, and localization core are unchanged.
