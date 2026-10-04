# v0.3.2 — Gradio 6 Native Seek

## Changed

- Upgraded Gradio from `5.49.1` to `6.28.0`.
- Upgraded `gradio-client` from `1.13.3` to `2.7.1`.
- Replaced the DOM/JavaScript media seek hook with native `playback_position` updates on `gr.Audio` and `gr.Video`.
- Migrated `gr.Dataframe` row/column configuration to the Gradio 6 API.
- Moved theme/CSS application to `Blocks.launch()`, matching the Gradio 6 runtime contract.

## Preserved

- Multi-reference CAM++ pipeline and shared target-window embedding pass.
- Audio/video input workflow.
- Segment table interaction and selected-segment status.
- Existing CPU-first/offline processing and PyInstaller packaging strategy.
