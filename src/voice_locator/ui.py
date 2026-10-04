from __future__ import annotations

from html import escape

import gradio as gr

from .config import DEFAULT_THRESHOLD
from .pipeline import analyze_workspace
from .profiles import DEFAULT_PROFILE_KEY, INFERENCE_PROFILES, get_inference_profile
from .visualization import build_timeline_placeholder_figure


SCENARIOS = [
    "Thảo luận / làm việc nhóm",
    "Tranh biện / thuyết trình",
    "Luyện nói / đọc thành tiếng",
    "Xem lại bản ghi hoạt động lớp học",
]

PROFILE_CHOICES = [
    (profile.label, profile.key)
    for profile in INFERENCE_PROFILES.values()
]

MAX_REFERENCE_SPEAKERS = 3

SEGMENT_HEADERS = [
    "Người nói",
    "Đoạn",
    "Bắt đầu",
    "Kết thúc",
    "Thời lượng",
    "Similarity TB",
    "Cao nhất",
]


def _parse_timecode(value: object) -> float:
    text = str(value or "").strip()
    if not text:
        raise ValueError("Timestamp trống.")
    if text.endswith("s"):
        return float(text[:-1])
    if ":" in text:
        minutes, seconds = text.split(":", 1)
        return int(minutes) * 60.0 + float(seconds)
    return float(text)


def _select_segment(evt: gr.SelectData):
    """Seek the single target media player using Gradio native playback_position."""
    if not getattr(evt, "selected", True):
        no_seek = gr.update()
        return no_seek, no_seek, ""

    row = getattr(evt, "row_value", None)
    if not row or len(row) < 4:
        no_seek = gr.update()
        return no_seek, no_seek, "Không đọc được đoạn đã chọn."

    try:
        start = _parse_timecode(row[2])
    except (TypeError, ValueError):
        no_seek = gr.update()
        return no_seek, no_seek, "Timestamp của đoạn không hợp lệ."

    speaker = str(row[0])
    segment_no = str(row[1])
    start_label = str(row[2])
    end_label = str(row[3])
    seek_update = gr.update(playback_position=start)
    status = f"▶ **{speaker} · đoạn {segment_no}** — {start_label} → {end_label}"
    return seek_update, seek_update.copy(), status


def _switch_target_mode(mode: str):
    if mode == "audio":
        return gr.update(value=None, visible=False), gr.update(visible=True)
    return gr.update(visible=True), gr.update(value=None, visible=False)


def _apply_profile_defaults(profile_key: str):
    profile = get_inference_profile(profile_key)
    return gr.update(value=profile.default_threshold)


def _readiness(*values):
    """Compatibility helper kept for tests and callers; UI validation happens on Analyze."""
    reference_values = values[: MAX_REFERENCE_SPEAKERS * 2]
    target_audio, target_video = values[MAX_REFERENCE_SPEAKERS * 2 :]

    ready_refs = 0
    partial_refs = 0
    for idx in range(MAX_REFERENCE_SPEAKERS):
        name = (reference_values[idx * 2] or "").strip()
        audio = reference_values[idx * 2 + 1]
        if name and audio is not None:
            ready_refs += 1
        elif name or audio is not None:
            partial_refs += 1

    has_target = target_audio is not None or target_video is not None
    both_targets = target_audio is not None and target_video is not None

    parts = [f"Target: {'ready' if has_target and not both_targets else 'cần chọn'}", f"References: {ready_refs}/{MAX_REFERENCE_SPEAKERS}"]
    if partial_refs:
        parts.append(f"{partial_refs} reference chưa hoàn chỉnh")
    if both_targets:
        parts.append("chỉ dùng một audio/video target")

    button_label = f"Analyze {ready_refs} speaker{'s' if ready_refs != 1 else ''}" if ready_refs else "Analyze voices"
    return " · ".join(parts), gr.update(interactive=True, value=button_label)


def _placeholder_summary(note: str = "Kết quả theo từng reference sẽ xuất hiện ở đây.") -> str:
    return (
        "<div>"
        "<strong>—</strong> references · <strong>—</strong> detected · "
        "<strong>—</strong> matches · <strong>—</strong> target"
        f"<br><small>{escape(note)}</small>"
        "</div>"
    )


def _run_workspace(*values):
    reference_values = values[: MAX_REFERENCE_SPEAKERS * 2]
    target_audio, target_video, profile_key, threshold, scenario = values[MAX_REFERENCE_SPEAKERS * 2 :]
    references = [
        (reference_values[i], reference_values[i + 1])
        for i in range(0, len(reference_values), 2)
    ]

    try:
        lanes, details, note, summary, rows = analyze_workspace(
            references,
            target_audio,
            target_video,
            threshold,
            scenario=scenario,
            profile_key=profile_key,
        )
        return (
            lanes,
            details,
            note,
            summary,
            rows,
            gr.update(visible=True),
            "",
        )
    except ValueError as exc:
        message = f"### Dữ liệu chưa hợp lệ\n{escape(str(exc))}"
    except Exception as exc:
        message = (
            "### Không thể chạy mô hình\n"
            f"{escape(str(exc))}\n\n"
            "Nếu vừa cập nhật source, hãy chạy lại `uv sync --dev --refresh`, `uv run poe models` và `uv run poe build`."
        )

    return (
        build_timeline_placeholder_figure(),
        None,
        message,
        _placeholder_summary("Kiểm tra lại target, inference profile và các reference speaker."),
        [],
        gr.update(visible=True),
        "",
    )


def _reference_input(index: int):
    """Build one plain Gradio reference input with no custom layout/CSS hooks."""
    with gr.Group():
        gr.Markdown(f"#### Speaker {index}")
        name = gr.Textbox(
            label="Tên speaker",
            placeholder=f"Ví dụ: Học sinh {index}",
        )
        audio = gr.Audio(
            sources=["upload", "microphone"],
            type="filepath",
            format="wav",
            editable=False,
            waveform_options=gr.WaveformOptions(show_recording_waveform=False),
            label="Reference audio",
        )
    return name, audio


def build_app() -> gr.Blocks:
    with gr.Blocks(title="AI Voice Locator · Giáo dục", analytics_enabled=False) as demo:
        gr.Markdown(
            """
            # AI Voice Locator
            **Known-speaker localization cho audio/video giáo dục.** Ứng dụng chạy local và không cần speech-to-text.
            """
        )

        with gr.Tabs():
            with gr.Tab("🎯 Phân tích"):
                gr.Markdown("## 1. Target media")
                target_mode = gr.Radio(
                    choices=[("🎬 Video", "video"), ("🎵 Audio", "audio")],
                    value="video",
                    type="value",
                    label="Loại target",
                )

                target_video = gr.Video(
                    sources=["upload"],
                    height=400,
                    label="Video cần phân tích",
                )
                target_audio = gr.Audio(
                    sources=["upload"],
                    type="numpy",
                    label="Audio cần phân tích",
                    visible=False,
                )

                reference_components = []
                with gr.Accordion(f"2. Reference speakers · tối đa {MAX_REFERENCE_SPEAKERS}", open=True):
                    gr.Markdown(
                        "Thêm tên và mẫu giọng cho tối đa 3 người. Khuyến nghị mỗi mẫu dài **3–5 giây**, rõ tiếng."
                    )
                    for idx in range(1, MAX_REFERENCE_SPEAKERS + 1):
                        name, audio = _reference_input(idx)
                        reference_components.extend([name, audio])

                with gr.Accordion("3. Analysis settings", open=False):
                    scenario = gr.Dropdown(
                        choices=SCENARIOS,
                        value=SCENARIOS[0],
                        label="Bối cảnh giáo dục",
                    )
                    profile = gr.Radio(
                        choices=PROFILE_CHOICES,
                        value=DEFAULT_PROFILE_KEY,
                        type="value",
                        label="Độ chính xác",
                        info="Nhanh dùng CAM++; Chính xác dùng ERes2NetV2 lớn hơn và sẽ chậm hơn trên CPU.",
                    )
                    threshold = gr.Slider(
                        minimum=0.20,
                        maximum=0.90,
                        value=DEFAULT_THRESHOLD,
                        step=0.01,
                        label="Similarity threshold",
                        info="Threshold được giữ riêng theo profile; các giá trị tối ưu cần calibration trên dữ liệu thực tế.",
                    )

                gr.Markdown("Cần **1 target** và ít nhất **1 reference speaker** có cả tên + audio.")
                analyze_btn = gr.Button("Analyze voices", variant="primary")

                gr.Markdown("## Kết quả")
                summary = gr.HTML(_placeholder_summary())
                result_note = gr.Markdown()
                lane_plot = gr.Plot(
                    value=build_timeline_placeholder_figure(),
                    label="Speaker timeline",
                    show_label=True,
                )

                with gr.Group(visible=False) as results_shell:
                    with gr.Accordion("Detected segments", open=True):
                        segment_table = gr.Dataframe(
                            value=[],
                            headers=SEGMENT_HEADERS,
                            column_count=len(SEGMENT_HEADERS),
                            row_count=0,
                            datatype=["str", "number", "str", "str", "str", "number", "number"],
                            type="array",
                            interactive=False,
                            wrap=False,
                            max_height=260,
                            label="Segments",
                        )
                        selected_segment = gr.Markdown()

                    with gr.Accordion("Research details · waveform & similarity", open=False):
                        detail_plot = gr.Plot(label="Similarity diagnostics")
                        gr.Markdown(
                            "Đồ thị này phục vụ calibration/research. Similarity là tín hiệu đối sánh, không phải xác nhận danh tính tuyệt đối."
                        )

                target_mode.change(
                    _switch_target_mode,
                    inputs=[target_mode],
                    outputs=[target_video, target_audio],
                    queue=False,
                )

                profile.change(
                    _apply_profile_defaults,
                    inputs=[profile],
                    outputs=[threshold],
                    queue=False,
                )

                analyze_btn.click(
                    _run_workspace,
                    inputs=[*reference_components, target_audio, target_video, profile, threshold, scenario],
                    outputs=[
                        lane_plot,
                        detail_plot,
                        result_note,
                        summary,
                        segment_table,
                        results_shell,
                        selected_segment,
                    ],
                )

                segment_table.select(
                    _select_segment,
                    inputs=None,
                    outputs=[target_audio, target_video, selected_segment],
                    show_progress="hidden",
                    queue=False,
                )

            with gr.Tab("🏫 Ứng dụng trong giáo dục"):
                gr.Markdown(
                    """
                    ## Các tình huống sử dụng

                    **Thảo luận nhóm**  
                    Đăng ký vài thành viên bằng mẫu giọng, rồi tìm vị trí từng người trong audio/video của buổi thảo luận.

                    **Tranh biện / thuyết trình**  
                    Tìm nhanh phần phát biểu của nhiều học sinh hoặc người trình bày trong cùng một video.

                    **Luyện nói / đọc thành tiếng**  
                    Đối sánh nhiều mẫu giọng đã biết với một recording chung để hỗ trợ xem lại.

                    **Video hoạt động lớp học**  
                    Upload video trực tiếp; hệ thống tách audio cục bộ và trả timeline theo timestamp của video.

                    > **Giới hạn chức năng:** đây là *known-speaker localization* dựa trên các mẫu giọng người dùng chủ động cung cấp. Hệ thống không tự phát hiện danh tính người lạ, không phải full speaker diarization và không nên dùng làm căn cứ chấm điểm hay kỷ luật tự động.
                    """
                )

            with gr.Tab("🛡️ Hướng dẫn & quyền riêng tư"):
                gr.Markdown(
                    """
                    ### Quy trình sử dụng khuyến nghị
                    1. Chọn video/audio target.
                    2. Mở **Reference speakers**, đặt tên và record/upload 3–5 giây giọng rõ cho từng người.
                    3. Có thể đóng Accordion reference sau khi chuẩn bị xong để tiết kiệm không gian.
                    4. Chọn **Độ chính xác**: Nhanh cho vòng thử nghiệm, Chính xác khi cần model embedding lớn hơn.
                    5. Chạy **Analyze voices**.
                    6. Xem speaker timeline và click một segment để seek player tới timestamp tương ứng.
                    7. Chỉ mở **Research details** khi cần xem waveform/similarity để calibration.

                    ### Quyền riêng tư & cách diễn giải
                    - Chỉ thu âm/video khi người tham gia và giáo viên/phụ huynh đã đồng ý theo quy định áp dụng.
                    - Dùng tên hiển thị/mã thay vì thông tin định danh không cần thiết.
                    - Matching là tín hiệu hỗ trợ tìm đoạn cần xem lại, không phải xác nhận danh tính tuyệt đối.
                    - Thời lượng nói không đồng nghĩa với chất lượng đóng góp.
                    - Một timestamp có thể match nhiều reference vì MVP dùng independent matching.

                    > Audio track của video được giải mã cục bộ. Ứng dụng không cần gửi video lên dịch vụ speech-to-text hoặc cloud AI.
                    """
                )

    return demo
