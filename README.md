# AI Voice Locator — định vị và đối sánh giọng nói trong giáo dục

AI Voice Locator là MVP nghiên cứu khoa học hướng tới học sinh cấp 2. Ứng dụng dùng **speaker embedding + cosine similarity** để đối sánh các mẫu giọng tham chiếu đã biết với audio/video hoạt động học tập và xác định các khoảng thời gian có khả năng chứa từng người nói.

Ứng dụng chạy **local/offline**, không cần speech-to-text, database hay cloud inference bắt buộc.

## Chức năng chính

- Native desktop UI bằng **PySide6 / Qt 6**; không cần chạy web server hay mở browser.
- Workspace kiểu **video editor**: Preview bên trái, Speakers/Analysis/Segments inspector bên phải, speaker timeline cố định ở đáy.
- Main workspace không dùng page scroll; các vùng được chia bằng `QSplitter` và có thể resize.
- Chọn **audio hoặc video target** và phát lại trực tiếp bằng Qt Multimedia.
- Tối đa **3 reference speakers** trong UI; mỗi speaker có tên và audio riêng.
- Reference audio có thể upload hoặc ghi trực tiếp bằng microphone.
- Hai inference profile:
  - **Nhanh · CAM++** — nhẹ hơn, phù hợp vòng thử nghiệm và CPU.
  - **Chính xác · ERes2NetV2** — model embedding lớn hơn, ưu tiên chất lượng hơn tốc độ.
- Video được tách audio cục bộ bằng FFmpeg đi kèm ứng dụng.
- Target được chia sliding windows và encode một lần; các reference cùng dùng lại target-window embeddings.
- Independent matching theo từng reference speaker; không ép một timestamp chỉ thuộc một speaker.
- Kết quả được render thành **speaker clips trên timeline** với playhead đồng bộ player.
- Khi playhead đi qua một detected segment, speaker + peak similarity được **overlay trực tiếp trên video preview**.
- Click timeline hoặc một row trong Segments inspector để seek player tới timestamp tương ứng.
- Similarity diagnostics nằm trong Analysis inspector thay vì kéo dài page.
- Chạy inference trên worker thread để desktop UI không bị freeze.
- Có app icon riêng cho cửa sổ Qt và Windows `.exe`.

> Đây là **known-speaker localization**, không phải full speaker diarization hoặc hệ thống xác nhận danh tính tuyệt đối.

## Cài đặt

Yêu cầu:

- CPython 3.11 hoặc 3.12
- Windows x86-64, Linux x86-64, macOS Intel hoặc Apple Silicon
- `uv`

Project dùng **standard `src/` layout** và được khai báo là installable package trong `pyproject.toml`. `uv sync` sẽ cài project vào environment thay vì phụ thuộc vào việc chạy một script ở repository root.

```bash
uv sync --dev
uv run poe models
```

`poe models` tải và kiểm tra tất cả speaker embedding model được khai báo trong `src/voice_locator/profiles.py`.

## Chạy desktop app

Cách khuyến nghị:

```bash
uv run poe start
```

hoặc:

```bash
uv run poe desktop
```

Hai Poe task đều gọi console entrypoint được cài từ:

```toml
[project.scripts]
voice-locator = "voice_locator.app:main"
```

Có thể chạy trực tiếp package theo hai cách tương đương:

```bash
uv run voice-locator
uv run python -m voice_locator
```

Không còn `app.py` ở repository root.

## Editor workflow

```text
┌───────────────────────────────┬──────────────────┐
│                               │ Speakers         │
│           Preview             │ Analysis         │
│     + speaker overlay         │ Segments         │
│                               │                  │
├───────────────────────────────┴──────────────────┤
│ speaker A  █████      ███                        │
│ speaker B       ████          █████              │
│ speaker C             ███                         │
│                 timeline + playhead               │
└───────────────────────────────────────────────────┘
```

1. Chọn **Video** hoặc **Audio** target và open file.
2. Ở inspector **Speakers**, thêm tên và mẫu giọng cho 1–3 reference speakers.
3. Ở **Analysis**, chọn profile và threshold nếu cần calibration.
4. Bấm **Analyze** ở toolbar.
5. Các detected regions xuất hiện như clip trên speaker tracks ở timeline.
6. Scrub/click timeline để review; playhead luôn đồng bộ với player.
7. Khi timestamp hiện tại nằm trong một match, speaker badge xuất hiện ngay trên preview.
8. Nếu cần danh sách chi tiết, mở **Segments** inspector và click row để seek.

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
                  editor timeline + preview overlay + seek
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
4. sync dependencies và install `voice_locator` package từ `src/`;
5. tải/verify tất cả speaker embedding models;
6. chạy compile check + unit tests;
7. build standalone app bằng PyInstaller với application icon;
8. chạy packaged smoke test với Qt offscreen, FFmpeg, ONNX Runtime và tất cả model profiles;
9. tạo release ZIP.

Artifact:

```text
dist/voice-locator/voice-locator.exe
release/AI-Voice-Locator-v0.5.1-Windows.zip
```

Windows `.exe` phải được build trực tiếp trong CMD/PowerShell Windows; PyInstaller không cross-compile Windows executable từ WSL/Linux.

## Poe tasks

```bash
uv run poe models   # tải/verify speaker embedding models
uv run poe desktop  # chạy installed voice-locator entrypoint
uv run poe start    # alias desktop app
uv run poe test     # unit tests
uv run poe check    # compile check
uv run poe build    # PyInstaller + packaged smoke test
uv run poe docs     # render Quarto docs
```

## Project structure

```text
pyproject.toml
assets/
├── voice-locator.png
└── voice-locator.ico
src/
└── voice_locator/
    ├── __init__.py
    ├── __main__.py       # python -m voice_locator
    ├── app.py            # canonical application entrypoint
    ├── audio.py
    ├── embedding.py
    ├── localization.py
    ├── media.py
    ├── pipeline.py
    ├── profiles.py
    ├── runtime.py
    ├── service.py        # desktop-facing application service
    ├── similarity.py
    ├── ui.py             # PySide6 editor workspace
    └── visualization.py  # legacy/research Plotly helpers
```

`app.py` nằm trong package, không nằm ở repository root. Các domain module hiện vẫn giữ flat bên trong `voice_locator`; có thể tiếp tục tách thành `ui/`, `inference/`, `media/`, `runtime/` packages khi cần mà không ảnh hưởng entrypoint/package installation.

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

v0.5.0 thay presentation layer Gradio bằng PySide6/Qt 6. Model, localization methodology, profile Fast/Accurate, FFmpeg media extraction và Windows ONNX Runtime protection được giữ nguyên.

## v0.5.1 — Video-editor workspace

v0.5.1 chuyển main analysis experience sang editor workspace không-scroll: preview + overlay ở trái, compact inspector ở phải và speaker timeline cố định ở đáy. Timeline có playhead đồng bộ, detected regions được hiển thị như clips, app có branding icon cho cửa sổ lẫn Windows executable, đồng thời chuẩn hóa application entrypoint thành installable `src/voice_locator` package.
