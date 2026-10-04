from __future__ import annotations

import sys
import tempfile
import uuid
from pathlib import Path

from PySide6.QtCore import Qt, QThread, QUrl, Signal, Slot
from PySide6.QtGui import QPainter, QPen
from PySide6.QtMultimedia import (
    QAudioInput,
    QAudioOutput,
    QMediaCaptureSession,
    QMediaFormat,
    QMediaPlayer,
    QMediaRecorder,
)
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSlider,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from .config import DEFAULT_THRESHOLD
from .pipeline import AnalysisBundle
from .profiles import DEFAULT_PROFILE_KEY, INFERENCE_PROFILES, get_inference_profile
from .service import analyze_bundle


SCENARIOS = [
    "Thảo luận / làm việc nhóm",
    "Tranh biện / thuyết trình",
    "Luyện nói / đọc thành tiếng",
    "Xem lại bản ghi hoạt động lớp học",
]

PROFILE_CHOICES = [(profile.label, profile.key) for profile in INFERENCE_PROFILES.values()]
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


def _fmt_time(seconds: float) -> str:
    seconds = max(0.0, float(seconds))
    minutes = int(seconds // 60)
    remain = seconds - minutes * 60
    if minutes:
        return f"{minutes:02d}:{remain:04.1f}"
    return f"{remain:.1f}s"


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


class AnalysisWorker(QThread):
    completed = Signal(object)
    failed = Signal(str)

    def __init__(
        self,
        references,
        target_audio,
        target_video,
        threshold: float,
        scenario: str,
        profile_key: str,
    ):
        super().__init__()
        self._references = references
        self._target_audio = target_audio
        self._target_video = target_video
        self._threshold = threshold
        self._scenario = scenario
        self._profile_key = profile_key

    def run(self) -> None:
        try:
            bundle, resolved_threshold = analyze_bundle(
                self._references,
                self._target_audio,
                self._target_video,
                self._threshold,
                profile_key=self._profile_key,
            )
        except Exception as exc:
            self.failed.emit(str(exc))
            return
        self.completed.emit(
            (bundle, resolved_threshold, self._scenario, self._profile_key)
        )


class SpeakerTimelineWidget(QWidget):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._bundle: AnalysisBundle | None = None
        self.setMinimumHeight(180)

    def set_bundle(self, bundle: AnalysisBundle | None) -> None:
        self._bundle = bundle
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802 - Qt API
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(110, 18, -18, -24)
        painter.setPen(self.palette().text().color())

        if self._bundle is None or not self._bundle.results:
            painter.drawText(
                self.rect(),
                Qt.AlignmentFlag.AlignCenter,
                "Speaker timeline sẽ xuất hiện sau khi phân tích",
            )
            return

        duration = max(self._bundle.duration, 0.001)
        lane_height = max(24, rect.height() // max(1, len(self._bundle.results)))
        base_pen = QPen(self.palette().mid().color())
        segment_pen = QPen(self.palette().highlight().color())
        segment_pen.setWidth(8)

        for index, result in enumerate(self._bundle.results):
            y = rect.top() + lane_height * index + lane_height // 2
            painter.setPen(self.palette().text().color())
            painter.drawText(8, y + 5, result.name)
            painter.setPen(base_pen)
            painter.drawLine(rect.left(), y, rect.right(), y)
            painter.setPen(segment_pen)
            for segment in result.segments:
                x1 = rect.left() + int(rect.width() * segment.start / duration)
                x2 = rect.left() + int(rect.width() * segment.end / duration)
                painter.drawLine(x1, y, max(x1 + 2, x2), y)

        painter.setPen(self.palette().text().color())
        painter.drawText(rect.left(), self.height() - 6, "0s")
        painter.drawText(rect.right() - 70, self.height() - 6, _fmt_time(duration))


class SimilarityPlotWidget(QWidget):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._bundle: AnalysisBundle | None = None
        self._threshold = DEFAULT_THRESHOLD
        self.setMinimumHeight(220)

    def set_bundle(self, bundle: AnalysisBundle | None, threshold: float) -> None:
        self._bundle = bundle
        self._threshold = threshold
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802 - Qt API
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(52, 18, -18, -30)

        if self._bundle is None or not self._bundle.results:
            painter.drawText(
                self.rect(), Qt.AlignmentFlag.AlignCenter, "Similarity diagnostics"
            )
            return

        duration = max(self._bundle.duration, 0.001)
        painter.setPen(QPen(self.palette().mid().color()))
        painter.drawRect(rect)

        threshold_y = rect.bottom() - int(rect.height() * self._threshold)
        threshold_pen = QPen(self.palette().link().color())
        threshold_pen.setStyle(Qt.PenStyle.DashLine)
        painter.setPen(threshold_pen)
        painter.drawLine(rect.left(), threshold_y, rect.right(), threshold_y)

        colors = [
            self.palette().highlight().color(),
            self.palette().link().color(),
            self.palette().text().color(),
        ]
        for index, result in enumerate(self._bundle.results):
            if not result.scores:
                continue
            pen = QPen(colors[index % len(colors)])
            pen.setWidth(2)
            painter.setPen(pen)
            previous = None
            for score in result.scores:
                center = (score.start + score.end) / 2.0
                x = rect.left() + int(rect.width() * center / duration)
                normalized = max(0.0, min(1.0, float(score.score)))
                y = rect.bottom() - int(rect.height() * normalized)
                if previous is not None:
                    painter.drawLine(previous[0], previous[1], x, y)
                previous = (x, y)

        painter.setPen(self.palette().text().color())
        painter.drawText(8, rect.top() + 5, "1.0")
        painter.drawText(8, rect.bottom(), "0.0")
        painter.drawText(rect.left(), self.height() - 8, "Similarity theo thời gian")


class ReferenceInput(QGroupBox):
    def __init__(self, index: int, parent: QWidget | None = None):
        super().__init__(f"Speaker {index}", parent)
        self.audio_path: str | None = None
        self._record_path: str | None = None
        self._audio_input: QAudioInput | None = None
        self._recorder: QMediaRecorder | None = None
        self._capture_session: QMediaCaptureSession | None = None

        layout = QGridLayout(self)
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText(f"Ví dụ: Học sinh {index}")
        self.path_label = QLabel("Chưa chọn audio")
        self.path_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        choose_button = QPushButton("Chọn audio")
        self.record_button = QPushButton("Ghi âm")
        clear_button = QPushButton("Xóa")

        choose_button.clicked.connect(self._choose_audio)
        self.record_button.clicked.connect(self._toggle_recording)
        clear_button.clicked.connect(self.clear)

        layout.addWidget(QLabel("Tên"), 0, 0)
        layout.addWidget(self.name_edit, 0, 1, 1, 3)
        layout.addWidget(self.path_label, 1, 0, 1, 4)
        layout.addWidget(choose_button, 2, 1)
        layout.addWidget(self.record_button, 2, 2)
        layout.addWidget(clear_button, 2, 3)

    def value(self) -> tuple[str, str | None]:
        return self.name_edit.text().strip(), self.audio_path

    @Slot()
    def clear(self) -> None:
        if (
            self._recorder
            and self._recorder.recorderState()
            == QMediaRecorder.RecorderState.RecordingState
        ):
            self._recorder.stop()
        self.audio_path = None
        self.path_label.setText("Chưa chọn audio")
        self.record_button.setText("Ghi âm")

    @Slot()
    def _choose_audio(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Chọn reference audio",
            "",
            "Audio (*.wav *.flac *.ogg *.mp3 *.m4a);;Tất cả file (*)",
        )
        if path:
            self.audio_path = path
            self.path_label.setText(Path(path).name)

    @Slot()
    def _toggle_recording(self) -> None:
        if (
            self._recorder
            and self._recorder.recorderState()
            == QMediaRecorder.RecorderState.RecordingState
        ):
            self._recorder.stop()
            self.record_button.setText("Ghi âm")
            if self._record_path:
                self.audio_path = self._record_path
                self.path_label.setText(Path(self._record_path).name)
            return

        record_path = str(
            Path(tempfile.gettempdir())
            / f"voice-locator-ref-{uuid.uuid4().hex}.wav"
        )
        audio_input = QAudioInput(self)
        recorder = QMediaRecorder(self)
        capture_session = QMediaCaptureSession(self)
        capture_session.setAudioInput(audio_input)
        capture_session.setRecorder(recorder)

        media_format = QMediaFormat()
        media_format.setFileFormat(QMediaFormat.FileFormat.Wave)
        recorder.setMediaFormat(media_format)
        recorder.setOutputLocation(QUrl.fromLocalFile(record_path))
        recorder.errorOccurred.connect(
            lambda _error, message: self._recording_error(message)
        )

        self._audio_input = audio_input
        self._recorder = recorder
        self._capture_session = capture_session
        self._record_path = record_path
        recorder.record()
        self.record_button.setText("Dừng ghi")
        self.path_label.setText("Đang ghi âm…")

    def _recording_error(self, message: str) -> None:
        self.record_button.setText("Ghi âm")
        QMessageBox.warning(
            self,
            "Không thể ghi âm",
            message or "Qt Multimedia không thể mở microphone.",
        )


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Voice Locator · Giáo dục")
        self.resize(1180, 820)
        self._target_path: str | None = None
        self._worker: AnalysisWorker | None = None
        self._bundle: AnalysisBundle | None = None

        self._player = QMediaPlayer(self)
        self._audio_output = QAudioOutput(self)
        self._player.setAudioOutput(self._audio_output)

        tabs = QTabWidget()
        tabs.addTab(self._build_analysis_tab(), "🎯 Phân tích")
        tabs.addTab(self._build_education_tab(), "🏫 Ứng dụng trong giáo dục")
        tabs.addTab(self._build_privacy_tab(), "🛡️ Hướng dẫn & quyền riêng tư")
        self.setCentralWidget(tabs)

    def _build_analysis_tab(self) -> QWidget:
        page = QWidget()
        page_layout = QVBoxLayout(page)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        root = QVBoxLayout(content)
        scroll.setWidget(content)
        page_layout.addWidget(scroll)

        root.addWidget(
            QLabel(
                "<h1>AI Voice Locator</h1>"
                "<b>Known-speaker localization cho audio/video giáo dục.</b>"
            )
        )

        media_group = QGroupBox("1. Target media")
        media_layout = QVBoxLayout(media_group)
        controls = QHBoxLayout()
        self.target_mode = QComboBox()
        self.target_mode.addItem("🎬 Video", "video")
        self.target_mode.addItem("🎵 Audio", "audio")
        choose_target = QPushButton("Chọn target")
        choose_target.clicked.connect(self._choose_target)
        self.target_label = QLabel("Chưa chọn target")
        controls.addWidget(self.target_mode)
        controls.addWidget(choose_target)
        controls.addWidget(self.target_label, 1)
        media_layout.addLayout(controls)

        self.video_widget = QVideoWidget()
        self.video_widget.setMinimumHeight(300)
        self._player.setVideoOutput(self.video_widget)
        media_layout.addWidget(self.video_widget)

        player_controls = QHBoxLayout()
        play_button = QPushButton("Play / Pause")
        play_button.clicked.connect(self._toggle_playback)
        self.position_slider = QSlider(Qt.Orientation.Horizontal)
        self.position_slider.setRange(0, 0)
        self.position_slider.sliderMoved.connect(self._player.setPosition)
        self._player.positionChanged.connect(self.position_slider.setValue)
        self._player.durationChanged.connect(
            lambda duration: self.position_slider.setRange(0, max(0, duration))
        )
        player_controls.addWidget(play_button)
        player_controls.addWidget(self.position_slider, 1)
        media_layout.addLayout(player_controls)
        root.addWidget(media_group)

        refs_group = QGroupBox(
            f"2. Reference speakers · tối đa {MAX_REFERENCE_SPEAKERS}"
        )
        refs_layout = QVBoxLayout(refs_group)
        refs_layout.addWidget(
            QLabel(
                "Khuyến nghị mỗi mẫu dài 3–5 giây, rõ tiếng. "
                "Có thể upload hoặc ghi trực tiếp bằng microphone."
            )
        )
        self.reference_inputs = [
            ReferenceInput(index) for index in range(1, MAX_REFERENCE_SPEAKERS + 1)
        ]
        for reference in self.reference_inputs:
            refs_layout.addWidget(reference)
        root.addWidget(refs_group)

        settings_group = QGroupBox("3. Analysis settings")
        form = QFormLayout(settings_group)
        self.scenario = QComboBox()
        self.scenario.addItems(SCENARIOS)
        self.profile = QComboBox()
        for label, key in PROFILE_CHOICES:
            self.profile.addItem(label, key)
        self.profile.setCurrentIndex(max(0, self.profile.findData(DEFAULT_PROFILE_KEY)))
        self.profile.currentIndexChanged.connect(self._apply_profile_default)
        self.profile_help = QLabel(get_inference_profile(DEFAULT_PROFILE_KEY).description)
        self.profile_help.setWordWrap(True)
        self.threshold = QDoubleSpinBox()
        self.threshold.setRange(0.20, 0.90)
        self.threshold.setDecimals(2)
        self.threshold.setSingleStep(0.01)
        self.threshold.setValue(DEFAULT_THRESHOLD)
        form.addRow("Bối cảnh giáo dục", self.scenario)
        form.addRow("Độ chính xác", self.profile)
        form.addRow("", self.profile_help)
        form.addRow("Similarity threshold", self.threshold)
        root.addWidget(settings_group)

        self.analyze_button = QPushButton("Analyze voices")
        self.analyze_button.clicked.connect(self._start_analysis)
        root.addWidget(self.analyze_button)

        self.summary_label = QLabel("Kết quả sẽ xuất hiện ở đây.")
        self.summary_label.setWordWrap(True)
        root.addWidget(self.summary_label)

        self.timeline = SpeakerTimelineWidget()
        root.addWidget(self.timeline)

        self.segment_table = QTableWidget(0, len(SEGMENT_HEADERS))
        self.segment_table.setHorizontalHeaderLabels(SEGMENT_HEADERS)
        self.segment_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.segment_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.segment_table.cellClicked.connect(self._seek_segment)
        root.addWidget(self.segment_table)

        detail_group = QGroupBox("Research details · similarity")
        detail_layout = QVBoxLayout(detail_group)
        self.similarity_plot = SimilarityPlotWidget()
        detail_layout.addWidget(self.similarity_plot)
        detail_layout.addWidget(
            QLabel(
                "Similarity là tín hiệu đối sánh, không phải xác nhận danh tính tuyệt đối."
            )
        )
        root.addWidget(detail_group)
        return page

    def _build_education_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        browser = QTextBrowser()
        browser.setHtml(
            """
            <h2>Các tình huống sử dụng</h2>
            <p><b>Thảo luận nhóm:</b> đăng ký vài thành viên bằng mẫu giọng, rồi tìm vị trí từng người trong audio/video.</p>
            <p><b>Tranh biện / thuyết trình:</b> tìm nhanh phần phát biểu của nhiều học sinh trong cùng một bản ghi.</p>
            <p><b>Luyện nói / đọc thành tiếng:</b> đối sánh các mẫu giọng đã biết với recording chung để hỗ trợ xem lại.</p>
            <p><b>Video hoạt động lớp học:</b> audio track được tách cục bộ và trả timeline theo timestamp.</p>
            <p><b>Giới hạn:</b> đây là known-speaker localization, không phải full speaker diarization hay hệ thống xác nhận danh tính.</p>
            """
        )
        layout.addWidget(browser)
        return page

    def _build_privacy_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        browser = QTextBrowser()
        browser.setHtml(
            """
            <h2>Hướng dẫn & quyền riêng tư</h2>
            <ol>
              <li>Chọn video/audio target.</li>
              <li>Đặt tên và upload/ghi 3–5 giây giọng rõ cho từng reference speaker.</li>
              <li>Chọn profile Nhanh hoặc Chính xác.</li>
              <li>Chạy Analyze voices.</li>
              <li>Click một segment để seek player tới timestamp tương ứng.</li>
            </ol>
            <p>Chỉ thu âm/video khi người tham gia và giáo viên/phụ huynh đã đồng ý theo quy định áp dụng.</p>
            <p>Matching là tín hiệu hỗ trợ tìm đoạn cần xem lại, không phải xác nhận danh tính tuyệt đối.</p>
            <p>Audio/video được xử lý cục bộ; ứng dụng không cần gửi media lên dịch vụ speech-to-text hoặc cloud AI.</p>
            """
        )
        layout.addWidget(browser)
        return page

    @Slot()
    def _apply_profile_default(self) -> None:
        profile = get_inference_profile(str(self.profile.currentData()))
        self.threshold.setValue(profile.default_threshold)
        self.profile_help.setText(profile.description)

    @Slot()
    def _choose_target(self) -> None:
        is_video = self.target_mode.currentData() == "video"
        file_filter = (
            "Video (*.mp4 *.mov *.mkv *.avi *.webm);;Tất cả file (*)"
            if is_video
            else "Audio (*.wav *.flac *.ogg *.mp3 *.m4a);;Tất cả file (*)"
        )
        path, _ = QFileDialog.getOpenFileName(
            self, "Chọn target media", "", file_filter
        )
        if not path:
            return
        self._target_path = path
        self.target_label.setText(Path(path).name)
        self._player.setSource(QUrl.fromLocalFile(path))

    @Slot()
    def _toggle_playback(self) -> None:
        if self._player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self._player.pause()
        else:
            self._player.play()

    @Slot()
    def _start_analysis(self) -> None:
        if self._worker and self._worker.isRunning():
            return

        references = [reference.value() for reference in self.reference_inputs]
        is_video = self.target_mode.currentData() == "video"
        target_audio = None if is_video else self._target_path
        target_video = self._target_path if is_video else None
        threshold = self.threshold.value()
        profile_key = str(self.profile.currentData())

        self.analyze_button.setEnabled(False)
        self.analyze_button.setText("Đang phân tích…")
        self.summary_label.setText(
            "Đang chạy speaker embedding và đối sánh các target windows…"
        )
        self._worker = AnalysisWorker(
            references,
            target_audio,
            target_video,
            threshold,
            self.scenario.currentText(),
            profile_key,
        )
        self._worker.completed.connect(self._analysis_complete)
        self._worker.failed.connect(self._analysis_failed)
        self._worker.finished.connect(self._analysis_finished)
        self._worker.start()

    @Slot(object)
    def _analysis_complete(self, payload: object) -> None:
        bundle, resolved_threshold, scenario, profile_key = payload
        self._bundle = bundle
        detected = sum(1 for result in bundle.results if result.segments)
        total_segments = sum(len(result.segments) for result in bundle.results)
        profile = get_inference_profile(profile_key)
        self.summary_label.setText(
            f"{len(bundle.results)} references · {detected} detected · "
            f"{total_segments} matches · {_fmt_time(bundle.duration)} {bundle.media_kind} · "
            f"{profile.label} · threshold {resolved_threshold:.2f} · {scenario}"
        )
        self.timeline.set_bundle(bundle)
        self.similarity_plot.set_bundle(bundle, resolved_threshold)
        self._populate_segments(bundle)

    @Slot(str)
    def _analysis_failed(self, message: str) -> None:
        self.summary_label.setText(
            "Không thể chạy mô hình. Kiểm tra lại target và reference audio."
        )
        QMessageBox.warning(self, "Không thể phân tích", message)

    @Slot()
    def _analysis_finished(self) -> None:
        self.analyze_button.setEnabled(True)
        self.analyze_button.setText("Analyze voices")

    def _populate_segments(self, bundle: AnalysisBundle) -> None:
        rows = []
        for result in bundle.results:
            for index, segment in enumerate(result.segments, start=1):
                rows.append(
                    [
                        result.name,
                        str(index),
                        _fmt_time(segment.start),
                        _fmt_time(segment.end),
                        _fmt_time(segment.end - segment.start),
                        f"{segment.avg_score:.3f}",
                        f"{segment.max_score:.3f}",
                    ]
                )

        self.segment_table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            for column_index, value in enumerate(row):
                self.segment_table.setItem(
                    row_index, column_index, QTableWidgetItem(value)
                )

    @Slot(int, int)
    def _seek_segment(self, row: int, _column: int) -> None:
        item = self.segment_table.item(row, 2)
        if item is None:
            return
        try:
            seconds = _parse_timecode(item.text())
        except ValueError:
            return
        self._player.setPosition(int(seconds * 1000))
        self._player.pause()


def create_application(argv: list[str] | None = None) -> QApplication:
    existing = QApplication.instance()
    if existing is not None:
        return existing
    return QApplication(argv if argv is not None else sys.argv)


def build_app() -> MainWindow:
    return MainWindow()
