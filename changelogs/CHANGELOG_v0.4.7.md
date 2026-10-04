# v0.4.7 — Compact Vertical Reference Panel

## Why

The v0.4.6 reference controls render again, but the reference sidebar can expose a horizontal scrollbar and the reference cards/audio controls occupy more space than necessary.

## Changes

- Keep the stable v0.4.6 structure: three direct `gr.Audio` children under a single sidebar scroll owner.
- Make the reference sidebar vertical-only with `overflow-y: auto` and `overflow-x: hidden`.
- Reduce sidebar padding and reference card spacing.
- Reduce reference header/card typography slightly.
- Set reference `gr.Audio(container=False)` to remove extra Gradio container chrome.
- Do **not** force a fixed audio height and do not style Gradio's private audio DOM, avoiding the blank-render regression.
- Keep upload + microphone, filepath input, WAV normalization, and native-browser playback behavior unchanged.
