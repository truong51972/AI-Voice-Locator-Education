# v0.4.6 — Reference Panel Layout Stabilization

## Why

Reference `gr.Audio` controls could render blank immediately on initial page load, before any audio was uploaded. That rules out file decoding and waveform playback as the primary trigger and points to the constrained Gradio layout around the controls.

## Changes

- Keep the existing three fixed reference `gr.Audio` controls for one final stability pass.
- Remove the nested `vl-reference-scroll` Gradio Column entirely.
- Make the reference sidebar itself the single vertical scroll owner.
- Remove forced `height`, `min-height`, nested flex sizing, and `overflow:hidden` from the reference sidebar.
- Remove the `min-width: 0` override from reference audio controls.
- Increase spacing slightly between reference cards so the controls are not tightly packed.
- Keep reference audio free of frontend event listeners.
- Keep `type="filepath"`, WAV normalization, and native-player configuration unchanged.
- Add regression tests that reject the previous nested flex/scroll structure.

## Fallback

If reference audio still renders blank on the target Windows build, stop working around `gr.Audio` and replace the three reference inputs with upload-only `gr.File(file_types=["audio"], type="filepath")`. The analysis pipeline already accepts file paths, so this fallback does not require a model or localization rewrite.
