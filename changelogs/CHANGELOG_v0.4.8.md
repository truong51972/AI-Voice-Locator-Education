# v0.4.8 — Native Gradio UI

- Removed the custom right-side reference panel.
- Removed all custom UI CSS and JavaScript hooks.
- Moved references into the main vertical Gradio flow.
- Added a native `gr.Accordion` for the three fixed reference speakers.
- Kept reference `gr.Audio` inputs plain and filepath-backed without custom sizing/scroll containers.
- Kept target switching, analysis, timeline rendering, segment seek, and research details behavior.
- App now launches with Gradio defaults (`app.launch(inbrowser=True)`) rather than passing a custom theme/CSS.
