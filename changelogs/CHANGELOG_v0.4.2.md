# v0.4.2 — Reference Audio Stability

- Fixed blank reference audio UI after **Add reference speaker → Upload**.
- Inactive reference cards remain mounted with `visible="hidden"` for frontend stability.
- Removed `Audio.change` listeners from reference samples; readiness now responds to upload, recording-stop, and clear events.
- Removed helper subtitles from Target Media and Reference Speakers plus other redundant workspace microcopy.
- Reduced the reference sidebar height while keeping independent scrolling.
- 27 regression tests pass.
