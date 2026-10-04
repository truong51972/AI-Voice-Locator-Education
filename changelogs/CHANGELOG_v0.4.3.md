# v0.4.3 — Fixed 3 Reference Slots

- Hard limit: maximum 3 reference speakers.
- Removed dynamic Add/Remove reference lifecycle.
- All 3 reference cards are always mounted and visible.
- Reference audio uses filepath-backed Gradio values.
- Reference audio components have no frontend state listeners; validation runs on Analyze.
- Pipeline audio preparation accepts both Gradio numpy tuples and file paths.
- Reduced reference sidebar height for the fixed 3-slot layout.
