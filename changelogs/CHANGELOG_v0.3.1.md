# v0.3.1 — Seekable Segments

Base: `v0.3.0-multi-speaker-video`

## Added

- Read-only detected-segment table below the multi-speaker timeline.
- Click/tap any segment row to seek the uploaded video to that segment start time.
- The same interaction also seeks an audio target when audio is used instead of video.
- Selected-segment status showing speaker, segment number, start and end timestamps.
- Smooth scroll to the target media player after seeking.

## Compatibility

- Keeps `gradio==5.49.1`; no major Gradio upgrade is required.
- Uses the existing native `<video>` / `<audio>` element and a small frontend event hook.
- AI inference, multi-speaker matching, thresholding and packaging semantics are unchanged from v0.3.0.
