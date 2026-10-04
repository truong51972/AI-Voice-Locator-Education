# AI Voice Locator — Ứng dụng AI trong định vị và đối sánh giọng nói trong giáo dục

Đây là MVP nghiên cứu khoa học hướng tới học sinh cấp 2. Ứng dụng dùng **speaker embedding + cosine similarity** để đối sánh **một hoặc nhiều mẫu giọng tham chiếu có tên** với audio/video hoạt động học tập và xác định các khoảng thời gian có khả năng chứa từng người nói.

## Hệ thống có thể phục vụ những gì?

MVP tập trung vào các tình huống giáo dục mà core speaker matching hiện tại thực sự hỗ trợ:

- **Thảo luận / làm việc nhóm:** tìm nhanh các khoảng một thành viên đã phát biểu để hỗ trợ xem lại buổi thảo luận.
- **Tranh biện / thuyết trình:** định vị phần phát biểu của một học sinh trong bản ghi dài.
- **Luyện nói / đọc thành tiếng:** tìm các đoạn luyện tập của cùng người nói dựa trên mẫu giọng đã cung cấp.
- **Xem lại bản ghi lớp học:** tìm phần xuất hiện của một người tham chiếu, ví dụ giáo viên hoặc người trình bày.

MVP **không phải** hệ thống nhận diện toàn trường, không thực hiện full speaker diarization và không tự động chấm điểm học sinh.

## Chức năng chính

- Ghi âm trực tiếp hoặc upload **1–6 mẫu giọng tham chiếu**, mỗi mẫu có tên hiển thị.
- Upload **audio hoặc video** hoạt động học tập cần phân tích.
- Video được tách audio cục bộ bằng FFmpeg đi kèm ứng dụng.
- Chia target thành sliding windows và tạo CAM++ embedding **một lần**, không lặp lại toàn target cho từng speaker.
- Tính cosine similarity matrix giữa N reference embeddings và target-window embeddings.
- Highlight mỗi speaker trên lane riêng của timeline.
- **Click một segment trong bảng kết quả để seek video/audio tới đúng timestamp bắt đầu.**
- Hiển thị KPI theo speaker: số vùng khớp, tổng thời lượng khớp, tỷ lệ xuất hiện và peak similarity.
- Cho phép chỉnh threshold trong mục **Thiết lập nâng cao** để phục vụ thí nghiệm.
- Chạy CPU-first, không cần database trong MVP.

## UI dành cho bối cảnh giáo dục

Giao diện được tổ chức thành ba tab:

1. **Phân tích giọng nói** — workflow chính cho học sinh/giáo viên.
2. **Ứng dụng trong giáo dục** — giải thích bốn kịch bản sử dụng thực tế.
3. **Hướng dẫn & quyền riêng tư** — giải thích cách đọc kết quả, consent và giới hạn của hệ thống.

Các tham số kỹ thuật như threshold được đưa vào accordion nâng cao để giao diện chính dễ sử dụng hơn với học sinh cấp 2.

## Cài đặt

Project ưu tiên chạy đa môi trường desktop:

- Linux/WSL x86-64
- Windows x86-64
- macOS Intel x86-64
- macOS Apple Silicon arm64
- CPython 3.11 hoặc 3.12

File `.python-version` đặt **3.12** làm mặc định cho `uv`.

```bash
uv sync --dev
uv run poe models
```

Nếu muốn ép Python 3.11:

```bash
uv sync --python 3.11 --dev
```

## Chạy ứng dụng

```bash
uv run poe gradio
```

hoặc:

```bash
uv run poe start
```

Ứng dụng sẽ mở Gradio trên trình duyệt local.

## One-click Windows build

Trên Windows x64, có thể chạy toàn bộ quy trình bằng cách **double-click `one-click.bat`**.

Script tự động thực hiện:

1. kiểm tra Windows x64;
2. dùng `uv` hiện có hoặc tự cài một bản project-local nếu máy chưa có `uv`;
3. cài/đảm bảo Python 3.12 qua `uv`;
4. chạy `uv sync --python 3.12 --dev --refresh`;
5. tải/kiểm tra model CAM++;
6. chạy compile check và unit tests;
7. build app standalone bằng PyInstaller và chạy packaged smoke test;
8. tạo file bàn giao `release/AI-Voice-Locator-v0.4.8-Windows.zip`.

Output chính sau khi thành công:

```text
dist/voice-locator/voice-locator.exe
release/AI-Voice-Locator-v0.4.8-Windows.zip
```

Có thể chạy không dừng ở màn hình cuối bằng:

```bat
one-click.bat --no-pause
```

> `one-click.bat` phải chạy bằng Windows CMD/PowerShell, không chạy trong WSL, vì Windows `.exe` cần được PyInstaller build trực tiếp trên Windows.

## Poe tasks

```bash
uv run poe models  # tải CAM++ ONNX
uv run poe gradio # start Gradio
uv run poe start   # alias start Gradio
uv run poe test    # unit tests
uv run poe check   # compile check
uv run poe build   # build Windows app bằng PyInstaller
uv run poe docs    # render QMD bằng Quarto
```

## Pipeline

```text
Reference A/B/C... (~3–5s mỗi người)
    │
    └── CAM++ ──> N reference embeddings

Audio target hoặc Video → FFmpeg → audio 16 kHz mono
    │
    └── sliding windows (2.5s, hop 0.5s)
            │
            └── CAM++ ──> target-window embeddings (một lần)
                         │
                         └── cosine matrix [speaker × window]
                                      │
                           smoothing + threshold / speaker
                                      │
                                  merge regions
                                      │
                    multi-speaker timeline + KPI + timestamps
                                      │
                         click segment → seek media
```

Cấu hình mặc định trong `src/voice_locator/config.py`:

- Window: 2.5 s
- Hop: 0.5 s
- Threshold mặc định: 0.60
- Smoothing kernel: 3
- Minimum match duration: 1.0 s

Threshold **không phải giá trị đúng tuyệt đối cho mọi dữ liệu**. Đây là biến nghiên cứu cần khảo sát.

## Hướng nghiên cứu phù hợp cấp 2

Câu hỏi nghiên cứu đề xuất:

> **Ngưỡng tương đồng, độ dài mẫu giọng và nhiễu môi trường ảnh hưởng như thế nào đến khả năng định vị và đối sánh giọng nói trong bản ghi hoạt động học tập?**

Có thể thử:

- Threshold: 0.45 / 0.55 / 0.65 / 0.75
- Reference duration: 2 s / 3 s / 5 s
- Môi trường: yên tĩnh / nhiễu lớp học nhẹ / nhiễu cao hơn
- Tình huống: đọc thành tiếng / thuyết trình / thảo luận nhóm

Đánh giá bằng **Precision, Recall, F1-score** và thời gian xử lý CPU.

## An toàn và quyền riêng tư

- Chỉ thu và phân tích audio khi có sự đồng ý phù hợp.
- Ưu tiên mã hiển thị như `Học sinh A` thay vì dữ liệu định danh không cần thiết.
- Không dùng kết quả để tự động chấm điểm, kỷ luật hoặc xác nhận danh tính tuyệt đối.
- Nên xóa dữ liệu thử nghiệm khi không còn mục đích sử dụng.
- Xem similarity như một tín hiệu kỹ thuật cần được người dùng kiểm tra lại.

## Model

MVP sử dụng `3dspeaker_speech_campplus_sv_en_voxceleb_16k.onnx` qua sherpa-onnx. File model không commit vào source zip; chạy `poe models` để tải.

## Tài liệu

- `docs/AI_Voice_Locator_Giao_Duc.qmd`: báo cáo/đề cương Quarto có thể tiếp tục chỉnh sửa.
- `docs/AI_Voice_Locator_Giao_Duc_Ban_Giao.docx`: bản Word bàn giao.
- `docs/implementation_plan.md`: implementation plan và phạm vi MVP.

## Build `.exe`

Trên Windows:

```powershell
uv sync --dev
uv run poe models
uv run poe test
uv run poe build
```

MVP dùng PyInstaller `--onedir`. Kết quả nằm trong `dist/voice-locator/`.

## Windows executable packaging

Để tạo `voice-locator.exe`, **phải build từ PowerShell/CMD trên Windows**. PyInstaller không cross-compile Windows `.exe` từ WSL/Linux.

```powershell
cd D:\Downloads\AI-Voice-Locator-Education-MVP\voice_locator_work
uv sync --dev
uv run poe models
uv run poe build
```

Artifact mong đợi:

```text
dist\voice-locator\voice-locator.exe
```

Build script đã được cấu hình để đóng gói đầy đủ `gradio`, `gradio_client` (bao gồm `gradio_client/types.json`) và `sherpa_onnx`. Sau build, script tự kiểm tra `voice-locator.exe` và `gradio_client/types.json`; nếu thiếu, build sẽ được xem là thất bại thay vì tạo một bundle lỗi runtime.

Nếu chạy build trong WSL, script sẽ cảnh báo rằng output chỉ là Linux executable và không phải `.exe`.


## Windows packaging notes (v0.2.3)

`poe build` now explicitly bundles runtime data files used by `gradio_client` and `safehttpx`, then runs a packaged-executable smoke test. A build is considered successful only when the generated executable can import the Gradio UI stack and `sherpa_onnx` without missing-resource/native-library errors.

Build from **Windows PowerShell/CMD**, not WSL, when you need `voice-locator.exe`.


### Packaging v0.2.3

Windows packaging now uses a custom PyInstaller hook for the Gradio runtime stack (`gradio`, `gradio_client`, `safehttpx`, `groovy`). The build validates `types.json` and both `version.txt` resources and then runs the packaged executable with `--smoke-test`; a failing smoke test means the `dist/` directory must not be handed off.

## Windows packaging notes (v0.2.4)

Bản v0.2.4 xử lý hai nhóm lỗi từng xuất hiện khi đóng gói bằng PyInstaller:

1. **Gradio package data** (`gradio_client/types.json`, `safehttpx/version.txt`, `groovy/version.txt`) được collect và smoke-test sau build.
2. **ONNX Runtime DLL conflict trên Windows**: một số máy có `onnxruntime.dll` cũ trong `C:\Windows\System32`, khiến sherpa-onnx nạp nhầm ORT 1.17.1. App hiện preload `onnxruntime.dll` đi kèm `sherpa-onnx-core` trước khi import sherpa và smoke-test tạo thật `SpeakerEmbeddingExtractor`.

Khi chuyển từ bản cũ, nên refresh môi trường để chắc chắn lấy đúng native runtime:

```powershell
uv sync --dev --refresh
uv run poe models
uv run poe build
```

Build chỉ được coi là đạt khi cuối log có:

```text
[smoke] Speaker extractor initialized: dim=...
[smoke] UI + Gradio resources + speaker runtime/model: OK
[ok] Packaged executable smoke test passed.
```


## UI/UX refresh (v0.2.5)

Bản v0.2.5 giữ nguyên toàn bộ runtime/build fixes của v0.2.4 nhưng trả các form controls và surfaces về màu/theme native của Gradio thay vì ép light/white. Layout desktop được mở rộng tối đa 1520px, giảm padding hai bên, hero/step spacing gọn hơn và chỉ dùng màu như semantic accent thay vì tô toàn bộ card. Giao diện vì vậy hoạt động tự nhiên ở cả light/dark mode của Gradio.


## Multi-speaker + video update (v0.3.0)

Bản v0.3.0 mở rộng v0.2.5 UX refresh với multi-reference known-speaker localization và video input. UI hỗ trợ tối đa 6 reference speakers trong một lượt; core pipeline không hard-code giới hạn này. Matching vẫn độc lập theo reference, vì vậy một timestamp có thể match nhiều speaker nếu nhiều score cùng vượt threshold. Đây là chủ đích để tránh biến MVP thành full diarization hoặc ép kết luận danh tính khi score gần nhau.

`imageio-ffmpeg` được collect vào PyInstaller bundle và packaged smoke test kiểm tra FFmpeg cùng Gradio/CAM++/ONNX Runtime.

### Documentation note for v0.3.0

`docs/AI_Voice_Locator_Giao_Duc.qmd` and `docs/implementation_plan.md` have been updated for the multi-speaker/video scope. The existing handover `.docx` is retained from the previous delivery for reference; regenerate the formal handover document from the updated source before a final v0.3.0 submission if needed.

## Seekable segment review (v0.3.2)

Bản v0.3.2 giữ workflow xem lại trực tiếp sau phân tích và chuyển phần seek sang Gradio 6 native:

1. Chạy phân tích như v0.3.0.
2. Các detected segments xuất hiện trong bảng ngay dưới timeline.
3. Click/tap bất kỳ ô nào của một hàng segment.
4. Video target (hoặc audio target) tự seek tới timestamp bắt đầu của segment và dừng tại đó để người dùng kiểm tra lại.

Implementation dùng `gradio==6.28.0`. Event chọn hàng được xử lý bằng `Dataframe.select` và cập nhật `playback_position` native của `gr.Audio` / `gr.Video`; không còn phụ thuộc DOM selector hay custom JavaScript để seek. Pipeline AI và kết quả localization không thay đổi.

### Nếu bước tải CAM++ có vẻ đứng


### Windows test/build shutdown reliability (v0.3.5)

Gradio analytics is disabled explicitly for this local/offline application and for the one-click build pipeline. This avoids a non-daemon telemetry thread keeping `pytest` alive after it has already reached `100%` on some Windows networks. If upgrading from v0.3.4 and the console is stuck immediately after the pytest progress bar reaches `100%`, press `Ctrl+C` once and rerun with v0.3.5.

Từ v0.3.4, downloader hiển thị `%`, MiB và tốc độ tải. Nếu không nhận được dữ liệu trong 30 giây, nó tự retry rồi chuyển từ GitHub sang Hugging Face. Model hoàn chỉnh phải có đúng `29,596,978` bytes và SHA-256 `357a834f702b80161e5b981182c038e18553c1f2ca752ed6cec2052365d4129b`.

Nếu đang nâng từ v0.3.3 và đã dừng giữa lúc tải, cứ chạy lại `one-click.bat` của v0.3.4. Downloader sẽ nhận diện file `.onnx` chưa hoàn chỉnh, bảo toàn nó dưới dạng `.onnx.part`, rồi thử resume khi server hỗ trợ HTTP Range.


## Media-first workspace redesign (v0.4.0)

v0.4.0 reorganizes the analysis experience around the actual review workflow instead of a fixed multi-step form:

- **Target media first:** one large media workspace, with a Video/Audio switch instead of two equal target cards.
- **Reference speaker manager:** starts with one visible speaker, supports Add/Remove up to six slots, keeps every reference audio player visible, and compacts speaker values when a card is removed.
- **Readiness-aware analysis:** the action bar shows target/reference readiness and only enables Analyze when the current inputs are valid.
- **Results workspace:** duplicates the selected target next to the result summary so seekable segment review happens close to the media player.
- **Primary speaker lanes:** the default chart answers “who appears where?”; waveform and cosine similarity move to a collapsed research-details panel.
- **Native seek preserved:** clicking a detected segment seeks the single Target Media audio/video player using Gradio 6 `playback_position`.

The AI pipeline, CAM++ model, target-window embedding reuse, independent multi-reference matching, video extraction, reliable model downloader, and one-click Windows build remain unchanged.


## Single-player split workspace refinement (v0.4.1)

v0.4.1 tightens the media-first layout to reduce page scrolling and remove duplicate playback surfaces:

- one Target Media player is the only audio/video player used for upload, review, and segment seek;
- the speaker timeline is rendered immediately below that player after analysis;
- Reference Speakers move to a compact right sidebar with its own vertical scroll and sticky Add control;
- speaker cards are smaller while keeping the reference audio player visible;
- Detected Segments use a capped-height table with internal scrolling;
- waveform/similarity diagnostics remain collapsed under Research details;
- desktop layout is optimized to keep the main analysis workspace close to one viewport.


## Fixed three-reference mode (v0.4.3)

v0.4.3 temporarily simplifies reference handling for maximum Gradio stability:

- hard limit of **3 reference speakers**;
- all three reference cards are always mounted and visible;
- dynamic Add/Remove speaker controls are removed;
- empty reference slots are ignored during analysis;
- reference `gr.Audio` values use `type="filepath"` instead of numpy payloads;
- reference audio components have **no frontend event listeners**; validation happens when Analyze runs;
- `prepare_gradio_audio()` accepts both file paths and legacy Gradio numpy tuples;
- the right reference panel is shorter for the fixed three-slot layout.


## Timeline render stability (v0.4.4)

v0.4.4 keeps the primary speaker timeline mounted from initial page load with a stable placeholder figure. Analyze now replaces only the Plot value instead of simultaneously updating the chart and revealing a hidden parent container. This avoids zero-size/blank Plotly renders observed on some Gradio/Windows sessions.


### Reference audio stability (v0.4.5)
Reference samples use WAV normalization and the browser-native audio player rather than Gradio waveform editing. The UI remains hard-capped at three reference speakers.


### Reference layout stability (v0.4.6)

v0.4.6 keeps the three fixed `gr.Audio` reference inputs, but removes the nested scroll/flex layout that could make the inputs render blank before any file was uploaded. The reference sidebar is now the only scroll owner; speaker cards are direct children, and reference audio no longer receives a forced `min-width: 0`. If `gr.Audio` still fails on a target Windows/Gradio setup, the planned fallback is upload-only `gr.File` references with the same filepath-based analysis pipeline.


### Reference panel compact scroll (v0.4.7)

v0.4.7 keeps the stabilized direct-child reference layout from v0.4.6, but makes the right panel more compact and explicitly vertical-only. The sidebar now owns `overflow-y: auto` while horizontal overflow is clipped, card spacing/padding is reduced, and reference `gr.Audio` uses `container=False` to remove unnecessary Gradio chrome without forcing a fragile fixed height on the audio component.


### Native Gradio layout (v0.4.8)

v0.4.8 removes the custom two-column/reference-sidebar layout and all custom UI CSS/JavaScript. The Analyze workspace now follows a plain vertical Gradio flow: target media, a native `gr.Accordion` containing the three fixed reference inputs, analysis settings, Analyze, timeline, and result accordions. This avoids custom scroll/flex sizing around `gr.Audio` and keeps the reference controls on Gradio's default layout path.
# AI-Voice-Locator-Education
