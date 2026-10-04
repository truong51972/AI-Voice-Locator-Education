# v0.4.1 — Single-player Split Workspace

## UX

- Removed the duplicate result video/audio player.
- Target Media is now the single playback and seek surface.
- Moved the speaker timeline directly below Target Media.
- Reworked desktop analysis into a 70/30 split: target/timeline left, references right.
- Reference sidebar scrolls independently and keeps Add Reference visible.
- Compact reference cards retain speaker name, remove action, and playable reference audio.
- Detected Segments now uses a 220px capped table with internal scrolling.
- Reduced hero, controls, and timeline vertical footprint to minimize main-page scrolling.

## Behavior

- Segment-row selection updates `playback_position` on the original target Audio/Video component.
- No `result_audio` or `result_video` component is created.
- Model, inference, multi-reference matching, thresholds, and result schema are unchanged.
