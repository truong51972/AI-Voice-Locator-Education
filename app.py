from __future__ import annotations

import os
import sys

# The application is designed for local/offline educational use. Disable
# framework telemetry before Gradio is imported. This also avoids a non-daemon
# analytics thread delaying interpreter shutdown on restricted Windows networks.
os.environ.setdefault("GRADIO_ANALYTICS_ENABLED", "False")
os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")


def main() -> None:
    # Configure Windows native DLL resolution before anything can import sherpa's
    # extension module. This also makes the packaged app resilient to stale
    # onnxruntime.dll files installed globally in Windows/System32.
    from voice_locator.runtime import configure_windows_native_runtime, selected_onnxruntime_path

    configure_windows_native_runtime(strict=(sys.platform == "win32"))

    # Keep imports inside main so the packaged executable can provide a controlled
    # smoke-test path. The smoke test constructs the UI and the speaker extractor,
    # so both package-data and native ONNX Runtime problems fail the build early.
    from voice_locator.ui import build_app

    app = build_app()

    if "--smoke-test" in sys.argv:
        import gradio  # noqa: F401
        import gradio_client  # noqa: F401
        import imageio_ffmpeg  # noqa: F401
        import groovy  # noqa: F401
        import safehttpx  # noqa: F401

        from voice_locator.config import SPEAKER_MODEL
        from voice_locator.embedding import SpeakerEmbedder
        from voice_locator.media import ffmpeg_executable

        embedder = SpeakerEmbedder(SPEAKER_MODEL, num_threads=1)
        ort_path = selected_onnxruntime_path()
        if ort_path:
            print(f"[smoke] Bundled ONNX Runtime: {ort_path}")
        ffmpeg_path = ffmpeg_executable()
        print(f"[smoke] Speaker extractor initialized: dim={embedder.dim}")
        print(f"[smoke] Bundled FFmpeg: {ffmpeg_path}")
        print("[smoke] UI + Gradio + FFmpeg + speaker runtime/model: OK")
        return

    # Intentionally use Gradio's native theme/layout with no custom CSS or JS.
    app.launch(inbrowser=True)


if __name__ == "__main__":
    main()
