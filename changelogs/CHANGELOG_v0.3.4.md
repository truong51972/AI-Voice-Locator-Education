# v0.3.4 - Reliable model download

Fixes the apparent hang during `[5/7] Downloading/verifying CAM++ speaker model` in `one-click.bat`.

- Replaces silent `urllib.request.urlretrieve()` with a streamed downloader that prints live percentage, MiB downloaded, and transfer speed.
- Adds a 30-second socket timeout, automatic retries, and source fallback.
- Uses the official sherpa-onnx GitHub release as the primary source and the `csukuangfj/speaker-embedding-models` Hugging Face mirror as fallback.
- Downloads to `.onnx.part` and only atomically promotes it to the final filename after integrity verification.
- Supports resuming a partial `.part` download when the server accepts HTTP Range requests.
- Validates exact size (`29,596,978` bytes) and SHA-256 (`357a834f702b80161e5b981182c038e18553c1f2ca752ed6cec2052365d4129b`).
- Removes/re-downloads stale or corrupted final model files instead of accepting any file larger than 1 MB.
- Preserves an interrupted v0.3.3 final `.onnx` as `.onnx.part` so v0.3.4 can attempt an HTTP Range resume.
- Gives a clear manual-install path when both network sources fail.
