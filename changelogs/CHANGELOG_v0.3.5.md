# AI Voice Locator v0.3.5

## Windows build/test shutdown fix

- Disable Gradio analytics explicitly in `gr.Blocks`.
- Set `GRADIO_ANALYTICS_ENABLED=False` before importing Gradio in the app entrypoint.
- Set Gradio/Hugging Face telemetry-off environment variables in `one-click.bat`.
- Prevent the Gradio telemetry worker from keeping `pytest` alive after the progress bar reaches 100% on restricted Windows networks.
- Add a regression assertion that the generated Gradio config has analytics disabled.
- Retain all v0.3.4 reliable model-download behavior.
