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
    # smoke-test path. The smoke test constructs the UI and every configured
    # speaker extractor, so package-data/native/model problems fail the build early.
    from voice_locator.ui import build_app

    app = build_app()

    if "--smoke-test" in sys.argv:
        import gradio  # noqa: F401
        import gradio_client  # noqa: F401
        import imageio_ffmpeg  # noqa: F401
        import groovy  # noqa: F401
        import safehttpx  # noqa: F401

        from voice_locator.embedding import SpeakerEmbedder
        from voice_locator.media import ffmpeg_executable
        from voice_locator.profiles import INFERENCE_PROFILES

        ort_path = selected_onnxruntime_path()
        if ort_path:
            print(f"[smoke] Bundled ONNX Runtime: {ort_path}")

        for profile in INFERENCE_PROFILES.values():
            embedder = SpeakerEmbedder(profile.model_path, num_threads=1)
            print(f"[smoke] {profile.label}: extractor initialized, dim={embedder.dim}")

        ffmpeg_path = ffmpeg_executable()
        print(f"[smoke] Bundled FFmpeg: {ffmpeg_path}")
        print("[smoke] UI + Gradio + FFmpeg + all speaker profiles: OK")
        return

    # Intentionally use Gradio's native theme/layout with no custom CSS or JS.
    app.launch(inbrowser=True)


if __name__ == "__main__":
    main()
