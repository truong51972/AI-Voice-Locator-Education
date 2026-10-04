# v0.4.5 — Reference Audio Native Player Fix

## Why

The reference panel could upload an audio file but fail to show a usable waveform/player on some Windows/Gradio setups. The previous implementation still relied on Gradio's interactive waveform frontend inside a narrow scrollable sidebar.

## Changes

- Reference audio keeps the fixed three-slot design.
- Reference `gr.Audio` now defaults to **Upload** before Microphone.
- Reference inputs use `type="filepath"` with `format="wav"` so user files are normalized to a browser-safe WAV representation before analysis.
- The Gradio waveform/editor is disabled for references with `WaveformOptions(show_recording_waveform=False)`; playback uses the browser-native audio player instead.
- Reference audio editing is disabled because the application only needs a clean sample for matching.
- Removed CSS that targeted Gradio's private `.audio-container` frontend class.
- Target media, timeline, multi-reference matching, and seek behavior are unchanged.

## Rationale

Reference samples need reliable upload/record/playback, not waveform editing. Using the browser-native player reduces dependence on Gradio's waveform renderer and internal DOM layout, both of which have had rendering regressions across releases.
