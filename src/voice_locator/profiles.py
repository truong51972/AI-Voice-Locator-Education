from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .config import MODEL_DIR


@dataclass(frozen=True)
class InferenceProfile:
    """User-facing inference preset backed by one speaker-embedding model."""

    key: str
    label: str
    description: str
    model_filename: str
    default_threshold: float
    num_threads: int = 2

    @property
    def model_path(self) -> Path:
        return MODEL_DIR / self.model_filename


DEFAULT_PROFILE_KEY = "fast"

INFERENCE_PROFILES: dict[str, InferenceProfile] = {
    "fast": InferenceProfile(
        key="fast",
        label="Nhanh · CAM++",
        description="Model mặc định, nhẹ hơn và phù hợp phân tích nhanh trên CPU.",
        model_filename="3dspeaker_speech_campplus_sv_en_voxceleb_16k.onnx",
        default_threshold=0.60,
        num_threads=2,
    ),
    "accurate": InferenceProfile(
        key="accurate",
        label="Chính xác · ERes2NetV2",
        description="Model lớn hơn, ưu tiên chất lượng speaker embedding hơn tốc độ xử lý.",
        model_filename="3dspeaker_speech_eres2netv2_sv_zh-cn_16k-common.onnx",
        # Keep the existing threshold as a conservative baseline until the
        # Vietnamese/classroom benchmark calibrates a profile-specific optimum.
        default_threshold=0.60,
        num_threads=2,
    ),
}


def get_inference_profile(profile_key: str | None = None) -> InferenceProfile:
    key = (profile_key or DEFAULT_PROFILE_KEY).strip().lower()
    try:
        return INFERENCE_PROFILES[key]
    except KeyError as exc:
        choices = ", ".join(INFERENCE_PROFILES)
        raise ValueError(f"Inference profile không hợp lệ: {profile_key!r}. Chọn một trong: {choices}.") from exc
