# v0.4.0 — Media-first Workspace

## UX / information architecture

- Replaced the old step/form-oriented analysis tab with a media-first workspace.
- Target video/audio is now the dominant top-level surface.
- Added a Video/Audio mode switch so only one target component is shown at a time.
- Reference speakers now behave as a collection: one visible slot initially, Add/Remove controls, up to six visible speakers, and compacting on removal.
- Reference audio players remain visible so samples can be reviewed before analysis.
- Added readiness chips and disabled Analyze until one valid target and at least one complete reference are present.
- Moved context and threshold into secondary Analysis Settings.

## Results

- Added a dedicated Results Workspace with a result media player next to per-speaker summary.
- Segment selection now seeks the result player, keeping media and evidence spatially close.
- Split visualization into a primary speaker-lane timeline and a collapsed waveform/similarity research panel.
- Replaced the large four-KPI dashboard with compact run summary chips plus the per-speaker table.

## Compatibility

- CAM++ inference and multi-reference scoring are unchanged.
- Existing `analyze()` / `analyze_many()` APIs remain available.
- `analyze_workspace()` is the new UI-oriented output contract.
- Gradio native `playback_position` seek remains in use.
- Reliable model download and Windows one-click build remain unchanged.

## Verification

- Added UI regression tests for Add/Remove speaker behavior, readiness state, target-mode switching, and results-player seek wiring.
