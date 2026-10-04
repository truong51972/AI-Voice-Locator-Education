# Implementation Plan — AI Voice Locator v0.3.0

## Scope khóa cho v0.3.0

- **1–6 reference speakers** trong một lượt phân tích; mỗi reference có tên hiển thị và audio riêng.
- **Một target media**: audio hoặc video.
- Video được giải mã cục bộ bằng FFmpeg; AI chỉ sử dụng audio track.
- CPU-only speaker embedding bằng CAM++ ONNX + sherpa-onnx.
- Target được chia sliding window 2.5 giây, hop 0.5 giây và **encode đúng một lần**.
- N reference embeddings được so sánh với cùng target-window embedding matrix.
- Independent matching: không ép mỗi window chỉ thuộc một speaker và không tuyên bố full diarization.
- Multi-speaker timeline + KPI theo speaker + bảng timestamp.
- Không database; không speech-to-text; không cloud inference bắt buộc.

## Phase 1 — Multi-reference model

**Implemented**

- Tối đa 6 reference cards trong UI.
- Mỗi reference yêu cầu `name + audio`.
- Validate duplicate names, missing name/audio và reference quá ngắn.
- Pipeline bên trong dùng mapping speaker key → samples nên không phụ thuộc giới hạn UI 6 speaker.

## Phase 2 — Shared target embedding pass

**Implemented**

1. Compute mỗi reference embedding một lần.
2. Chia target thành windows.
3. Compute target-window embeddings một lần.
4. Tạo cosine similarity matrix `[num_speakers, num_windows]`.
5. Smoothing, threshold và merge segment độc lập theo speaker.

Điểm này tránh chạy lại CAM++ trên toàn target cho từng reference.

## Phase 3 — Video input

**Implemented**

- Upload MP4, MOV, MKV, WEBM, AVI, M4V.
- `imageio-ffmpeg` cung cấp binary FFmpeg theo platform.
- Decode trực tiếp audio stream → mono float32 16 kHz trong memory.
- Không cần cài FFmpeg system-wide.
- Video không có audio stream trả lỗi rõ ràng.

## Phase 4 — Result UX

**Implemented**

Timeline ba tầng:

1. waveform của audio track;
2. lane riêng cho từng reference speaker;
3. similarity curves của tất cả speaker + threshold.

KPI gồm:

- số reference speaker;
- số speaker có phát hiện;
- tổng số match segments;
- target duration;
- per-speaker: segment count, matched duration, coverage, peak similarity.

## Phase 5 — Compatibility

**Implemented**

- Giữ `pipeline.analyze(...)` và `localization.score_windows(...)` dưới dạng compatibility wrapper cho code/tests v0.2.x.
- Single-reference + audio target vẫn hoạt động trên cùng core mới.

## Phase 6 — Packaging

**Implemented trong source; cần build thật trên Windows để xác nhận artifact `.exe`.**

`poe build` collect thêm `imageio_ffmpeg`. Packaged smoke test kiểm tra:

- Gradio runtime;
- sherpa-onnx + CAM++ model;
- bundled ONNX Runtime;
- bundled FFmpeg executable.

Windows flow:

1. `uv sync --dev --refresh`
2. `uv run poe models`
3. `uv run poe test`
4. `uv run poe build`
5. chạy `dist/voice-locator/voice-locator.exe`

## Deferred / v0.3.x+

- Dynamic add/remove speaker card không giới hạn 6 ở UI.
- Click segment để seek trực tiếp video player tới timestamp tương ứng.
- Per-speaker calibrated threshold.
- Best-speaker / ambiguity-margin assignment mode.
- Full diarization hoặc unknown-speaker discovery (nếu scope nghiên cứu thực sự cần).

## Guardrails

- Chỉ phân tích reference speaker được người dùng chủ động cung cấp.
- Không dùng similarity như xác nhận danh tính tuyệt đối.
- Không dùng speaking duration để tự động chấm điểm/kỷ luật.
- Consent và data minimization vẫn là yêu cầu khi dùng trong bối cảnh học đường.

## v0.3.1 — Seekable detected segments

- Giữ nguyên pipeline multi-speaker/video của v0.3.0.
- Render detected segments thành bảng read-only ngay dưới timeline.
- `Dataframe.select` lấy row được chọn và suy ra timestamp `start`.
- Một frontend hook nhỏ seek `<video>` hoặc `<audio>` target bằng `HTMLMediaElement.currentTime`.
- Không nâng Gradio major version và không thêm custom component, để giữ packaging PyInstaller ổn định.
- Nếu target là audio, cùng interaction vẫn seek audio player.


## v0.3.2 — Gradio 6 native seek

- Upgrade `gradio` to `6.28.0` and `gradio-client` to `2.7.1`.
- Replace DOM/JavaScript `HTMLMediaElement.currentTime` hook with native `playback_position`.
- Keep `Dataframe.select` as the segment interaction surface.
- Migrate Dataframe row/column configuration to the Gradio 6 API.
- Apply theme/CSS at launch time for the Gradio 6 runtime contract.
- Preserve the existing multi-speaker inference pipeline and result schema.

## v0.3.3 — One-click Windows setup/build

Add a root-level `one-click.bat` that turns a clean source checkout/archive into a distributable Windows build with one double-click. The script verifies native Windows x64, installs a project-local `uv` when necessary, ensures Python 3.12, recreates non-Windows `.venv` folders, synchronizes dependencies, downloads CAM++, runs compile/tests, executes the existing PyInstaller build + packaged smoke test, and creates `release/AI-Voice-Locator-v0.3.3-Windows.zip`.

The one-click path intentionally reuses the existing Poe tasks instead of duplicating build logic in batch, so `scripts/build.py` remains the source of truth for packaging and smoke validation.

## v0.3.4 — Reliable CAM++ model bootstrap

Harden the one-click model bootstrap so the setup does not appear frozen on slow or blocked networks. The model downloader now streams with visible progress, applies a 30-second no-data timeout, retries, falls back from the sherpa-onnx GitHub release to a Hugging Face mirror, resumes `.part` files when HTTP Range is supported, and validates both the exact 29,596,978-byte file size and SHA-256 before atomically promoting the model into `models/`.

## v0.4.0 — Media-first workspace

The analysis UI is now organized by task priority rather than implementation inputs:

1. target media occupies the primary workspace;
2. reference speakers are managed as an add/remove collection;
3. analysis settings are secondary;
4. readiness precedes execution;
5. results keep the media player next to summary/timeline/seekable segments;
6. speaker lanes are primary, while waveform/similarity are diagnostic details.

This is a UI/state-management change only. The model, media decoding, embedding reuse, independent reference matching, threshold logic, and localization methodology remain unchanged.


## v0.4.1 — Single-player split workspace

- Remove the duplicated Results Workspace media player.
- Seek detected segments directly on the original Target Media player.
- Use a desktop split layout: target + inline timeline on the left, scrollable references on the right.
- Keep Add Reference sticky and compact each reference card.
- Cap the Detected Segments table height so evidence scrolls locally instead of stretching the page.
- Keep research diagnostics collapsed by default.
- Reduce primary speaker-lane plot height to preserve a near-single-viewport desktop workflow.


## v0.4.2 — Reference audio stability

- Keep inactive reference cards mounted using Gradio's `visible="hidden"` state.
- Replace reference `Audio.change` readiness hooks with `upload`, `stop_recording`, and `clear`.
- Remove non-essential helper copy from the primary workspace.
- Reduce desktop reference-sidebar height while preserving local scrolling.


## v0.4.3 — Fixed three-reference mode

Temporarily cap the MVP at three known reference speakers to remove dynamic Gradio Audio lifecycle risk. Render all three slots from initial page load, remove Add/Remove state transitions, use filepath-backed reference audio, and avoid frontend event callbacks on those audio components. Empty slots remain valid and are skipped by the existing reference validation pipeline.
