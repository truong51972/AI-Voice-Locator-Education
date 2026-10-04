# v0.3.0 — Multi-speaker + Video

Base: `AI-Voice-Locator-Education-MVP-v0.2.5-ux-refresh`

## Added

- 1–6 named reference speakers per analysis run.
- Audio or video target input.
- Local video audio extraction with bundled `imageio-ffmpeg`.
- Shared target-window embedding pass for all reference speakers.
- Cosine similarity matrix `[speaker × window]`.
- Three-layer Plotly result: waveform, speaker lanes, similarity curves.
- Per-speaker KPI table and timestamp result table.
- Multi-speaker and media unit tests.
- FFmpeg verification in packaged smoke test.

## Preserved

- CAM++ ONNX + sherpa-onnx CPU inference.
- 2.5 s window / 0.5 s hop defaults.
- RMS speech gate, smoothing, threshold and segment merge behavior.
- v0.2.x single-reference `analyze()` and `score_windows()` compatibility wrappers.
- v0.2.5 Gradio theme-aware UX styling.
- Existing Windows ONNX Runtime conflict protections.

## Semantics

Matching is independent per known reference speaker. A timestamp may match more than one reference if multiple similarities exceed the threshold. This version does not claim full speaker diarization or unknown-speaker discovery.

## Deferred

- Unlimited/dynamic reference-card creation in the UI.
- Click a detected segment to seek the video player.
- Per-speaker threshold calibration.
- Exclusive best-speaker / ambiguity-margin assignment.
