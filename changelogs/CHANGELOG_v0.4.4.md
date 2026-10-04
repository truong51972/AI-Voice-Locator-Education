# v0.4.4 — Timeline Render Stability

- Keep the primary speaker timeline mounted at all times.
- Initialize the timeline with a stable placeholder Plotly figure.
- Analyze updates only the plot value; it no longer toggles timeline-container visibility.
- Preserve the single target media player and fixed three-reference workflow.
- Add regression coverage for lane traces, placeholder sizing, and Gradio visibility wiring.
