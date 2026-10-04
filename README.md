# AI Voice Locator — định vị và đối sánh giọng nói trong giáo dục

AI Voice Locator là MVP nghiên cứu khoa học hướng tới học sinh cấp 2. Ứng dụng dùng **speaker embedding + cosine similarity** để đối sánh các mẫu giọng tham chiếu đã biết với audio/video hoạt động học tập và xác định các khoảng thời gian có khả năng chứa từng người nói.

Ứng dụng chạy **local/offline**, không cần speech-to-text, database hay cloud inference bắt buộc.

## Chức năng chính

- Native desktop UI bằng **PySide6 / Qt 6**; không cần chạy web server hay mở browser.
- Chọn **audio hoặc video target** và phát lại trực tiếp bằng Qt Multimedia.
- Tối đa **3 reference speakers** trong UI; mỗi speaker có tên và audio riêng.
- Reference audio có thể upload hoặc ghi trực tiếp bằng microphone.
- Hai inference profile:
  - **Nhanh · CAM++** — nhẹ hơn, phù hợp vòng thử nghiệm và CPU.
  - **Chính xác · ERes2NetV2** — model embedding lớn hơn, ưu tiên chất lượng hơn tốc độ.
- Video được tách audio cục bộ bằng FFmpeg đi kèm ứng dụng.
- Target được chia sliding windows và encode một lần; các reference cùng dùng lại target-window embeddings.
- Independent matching theo từng reference speaker; không ép một timestamp chỉ thuộc một speaker.
- Native speaker timeline và similarity diagnostics bằng Qt painting.
- Bảng detected segments; click một segment để seek player tới timestamp bắt đầu.
- Chạy inference trên worker thread để desktop UI không bị freeze.

> Đây là **known-speaker localization**, không phải full speaker diarization hoặc hệ thống xác nhận danh tính tuyệt đối.

## Cài đặt

Yêu cầu:

- CPython 3.11 hoặc 3.12
- Windows x86-64, Linux x86-64, macOS Intel hoặc Apple Silicon
- `uv`

```bash
uv sync --dev
uv run poe models
```

`poe models` tải và kiểm tra tất cả speaker embedding model được khai báo trong `src/voice_locator/profiles.py`.

## Chạy desktop app

```bash
uv run poe start
```

hoặc:

```bash
uv run poe desktop
```

Ứng dụng mở trực tiếp một cửa sổ Qt native.

## Workflow

1. Chọn **Video** hoặc **Audio** target.
2. Chọn file target.
3. Thêm tên và mẫu giọng cho 1–3 reference speakers; có thể upload hoặc ghi microphone.
4. Chọn profile **Nhanh** hoặc **Chính xác**.
5. Điều chỉnh similarity threshold nếu cần calibration.
6. Chạy **Analyze voices**.
7. Xem speaker timeline và detected segments.
8. Click một segment để seek player về đúng timestamp.

## Inference profiles

Profile được định nghĩa trong `src/voice_locator/profiles.py` và gồm model file, checksum, download URL, threshold mặc định và số CPU threads.

| Profile | Model | Mục tiêu |
|---|---|---|
| `fast` | CAM++ | latency thấp hơn, thử nghiệm nhanh |
| `accurate` | ERes2NetV2 | speaker embedding lớn hơn, ưu tiên accuracy |

Threshold hiện là baseline và vẫn cần calibration bằng dữ liệu lớp học/tiếng Việt thực tế. Không nên hiểu similarity score như xác suất danh tính.

## Pipeline

```text
Reference speaker audio
        │
        └── speaker embedding model ──> reference embeddings

Audio target hoặc Video ──> FFmpeg ──> mono 16 kHz
        │
        └── sliding windows
                │
                └── speaker embedding model ──> target-window embeddings
                                │
                                └── cosine similarity matrix
                                        │
                                smoothing + threshold
                                        │
                                   merge regions
                                        │
                         timeline + segments + seek
```

Core matching vẫn nằm ngoài presentation layer. PySide6 gọi pipeline thông qua `voice_locator.service.analyze_bundle()`, vì vậy UI có thể thay đổi mà không cần rewrite embedding/localization logic.

## One-click Windows build

Trên Windows x64, double-click:

```text
one-click.bat
```

Script sẽ:

1. kiểm tra Windows x64;
2. dùng `uv` hiện có hoặc cài project-local `uv`;
3. đảm bảo Python 3.12;
4. sync dependencies;
5. tải/verify tất cả speaker embedding models;
6. chạy compile check + unit tests;
7. build standalone app bằng PyInstaller;
8. chạy packaged smoke test với Qt offscreen, FFmpeg, ONNX Runtime và tất cả model profiles;
9. tạo release ZIP.

Artifact:

```text
dist/voice-locator/voice-locator.exe
release/AI-Voice-Locator-v0.5.0-Windows.zip
```

Windows `.exe` phải được build trực tiếp trong CMD/PowerShell Windows; PyInstaller không cross-compile Windows executable từ WSL/Linux.

## Poe tasks

```bash
uv run poe models   # tải/verify speaker embedding models
uv run poe desktop  # mở PySide6 desktop app
uv run poe start    # alias desktop app
uv run poe test     # unit tests
uv run poe check    # compile check
uv run poe build    # PyInstaller + packaged smoke test
uv run poe docs     # render Quarto docs
```

## Project structure

```text
app.py
src/voice_locator/
├── audio.py
├── embedding.py
├── localization.py
├── media.py
├── pipeline.py
├── profiles.py
├── runtime.py
├── service.py       # desktop-facing application service
├── similarity.py
├── ui.py            # PySide6 presentation layer
└── visualization.py # legacy/research Plotly helpers
```

## Nghiên cứu và đánh giá

Một hướng nghiên cứu phù hợp:

> Ngưỡng tương đồng, model embedding, độ dài mẫu giọng và nhiễu môi trường ảnh hưởng như thế nào đến khả năng định vị người nói trong bản ghi hoạt động học tập?

Có thể đánh giá theo:

- Precision / Recall / F1
- inference profile: CAM++ vs ERes2NetV2
- reference duration: 2 s / 3 s / 5 s
- threshold
- môi trường yên tĩnh / nhiễu lớp học
- CPU processing time

## An toàn và quyền riêng tư

- Chỉ thu và phân tích audio/video khi có consent phù hợp.
- Ưu tiên tên hiển thị hoặc mã thay vì thông tin định danh không cần thiết.
- Không dùng similarity như xác nhận danh tính tuyệt đối.
- Không dùng speaking duration để tự động chấm điểm hoặc kỷ luật.
- Nên xóa dữ liệu thử nghiệm khi không còn mục đích sử dụng.
- Một timestamp có thể match nhiều reference vì MVP dùng independent matching.

## v0.5.0 — Native PySide6 desktop UI

v0.5.0 thay presentation layer Gradio bằng PySide6/Qt 6. Model, localization methodology, profile Fast/Accurate, FFmpeg media extraction và Windows ONNX Runtime protection được giữ nguyên. Desktop app dùng Qt Multimedia cho playback/recording, Qt widgets cho form/table, native painting cho timeline/diagnostics và `QThread` cho inference.
