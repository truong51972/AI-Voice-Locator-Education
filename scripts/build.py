from __future__ import annotations

import importlib.util
import os
import platform
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP_NAME = "voice-locator"
ASSETS_DIR = ROOT / "assets"
APP_ICON = ASSETS_DIR / "voice-locator.ico"


def _package_dir(package: str) -> Path:
    spec = importlib.util.find_spec(package)
    if spec is None:
        raise SystemExit(
            f"Không tìm thấy package `{package}` trong môi trường hiện tại. "
            "Chạy `uv sync --dev` trước khi build."
        )
    if spec.submodule_search_locations:
        try:
            return Path(next(iter(spec.submodule_search_locations))).resolve()
        except StopIteration:
            pass
    if spec.origin is None:
        raise SystemExit(f"Không xác định được thư mục của package `{package}`.")
    return Path(spec.origin).resolve().parent


def _find_windows_onnxruntime_dll() -> Path:
    """Find the ONNX Runtime that belongs to the installed sherpa release."""
    sherpa_dir = _package_dir("sherpa_onnx")
    candidates = [
        sherpa_dir / "lib" / "onnxruntime.dll",
        sherpa_dir / "onnxruntime.dll",
        Path(sys.prefix) / "Scripts" / "onnxruntime.dll",
        Path(sys.executable).resolve().parent / "onnxruntime.dll",
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    pretty = "\n  - ".join(str(path) for path in candidates)
    raise SystemExit(
        "Không tìm thấy onnxruntime.dll của sherpa-onnx-core trong môi trường Windows.\n"
        "Hãy chạy `uv sync --dev --refresh` trước khi build. Đã kiểm tra:\n  - " + pretty
    )


def _is_wsl() -> bool:
    release = platform.release().lower()
    return os.name != "nt" and ("microsoft" in release or "wsl" in release)


def _verify_models() -> None:
    sys.path.insert(0, str(ROOT / "src"))
    from voice_locator.profiles import INFERENCE_PROFILES

    missing = [profile.model_path for profile in INFERENCE_PROFILES.values() if not profile.model_path.is_file()]
    if missing:
        pretty = "\n  - ".join(str(path) for path in missing)
        raise SystemExit("Thiếu model. Chạy `poe models` trước khi build.\n  - " + pretty)


def _verify_assets() -> None:
    required = [
        ASSETS_DIR / "voice-locator.png",
        APP_ICON,
    ]
    missing = [path for path in required if not path.is_file()]
    if missing:
        pretty = "\n  - ".join(str(path) for path in missing)
        raise SystemExit("Thiếu application icon assets:\n  - " + pretty)


def main() -> None:
    _verify_models()
    _verify_assets()

    sep = ";" if os.name == "nt" else ":"
    cmd = [
        "pyinstaller",
        "--noconfirm",
        "--clean",
        "--onedir",
        "--name",
        APP_NAME,
        "--paths",
        str(ROOT / "src"),
        "--add-data",
        f"{ROOT / 'models'}{sep}models",
        "--add-data",
        f"{ASSETS_DIR}{sep}assets",
        "--collect-all",
        "sherpa_onnx",
        "--collect-all",
        "imageio_ffmpeg",
        "--hidden-import",
        "PySide6.QtMultimedia",
        "--hidden-import",
        "PySide6.QtMultimediaWidgets",
    ]

    bundled_ort_source: Path | None = None
    if os.name == "nt":
        bundled_ort_source = _find_windows_onnxruntime_dll()
        cmd += [
            "--add-binary",
            f"{bundled_ort_source}{sep}sherpa_onnx/lib",
            "--icon",
            str(APP_ICON),
        ]

    cmd.append(str(ROOT / "app.py"))

    system = platform.system()
    print(f"[build] Host platform: {system} ({platform.release()})")
    if bundled_ort_source is not None:
        print(f"[build] sherpa ONNX Runtime source: {bundled_ort_source}")
    if _is_wsl():
        print(
            "[build][warning] Bạn đang build trong WSL/Linux. "
            "PyInstaller sẽ tạo Linux executable, KHÔNG tạo file .exe.\n"
            "[build][warning] Muốn tạo Windows .exe, hãy chạy `uv run poe build` "
            "từ PowerShell/CMD bằng Python/uv của Windows."
        )

    print("[build]", " ".join(cmd))
    subprocess.run(cmd, cwd=ROOT, check=True)

    dist_dir = ROOT / "dist" / APP_NAME
    internal_dir = dist_dir / "_internal"
    executable = dist_dir / (f"{APP_NAME}.exe" if os.name == "nt" else APP_NAME)

    required_outputs = {
        "executable": executable,
        "assets/voice-locator.png": internal_dir / "assets" / "voice-locator.png",
        "assets/voice-locator.ico": internal_dir / "assets" / "voice-locator.ico",
    }
    if os.name == "nt":
        required_outputs["sherpa_onnx/lib/onnxruntime.dll"] = (
            internal_dir / "sherpa_onnx" / "lib" / "onnxruntime.dll"
        )

    missing = [f"{label}: {path}" for label, path in required_outputs.items() if not path.is_file()]
    if missing:
        raise SystemExit(
            "Build kết thúc nhưng thiếu artifact/runtime resource bắt buộc:\n  - "
            + "\n  - ".join(missing)
            + "\nKhông nên bàn giao thư mục dist này."
        )

    for label, path in required_outputs.items():
        print(f"[ok] {label}: {path}")

    print("[build] Running packaged executable smoke test...")
    try:
        smoke = subprocess.run(
            [str(executable), "--smoke-test"],
            cwd=dist_dir,
            check=False,
            capture_output=True,
            text=True,
            timeout=120,
        )
    except subprocess.TimeoutExpired as exc:
        raise SystemExit(
            "Packaged executable smoke test bị timeout. "
            "Bundle có thể vẫn còn dependency/runtime issue."
        ) from exc

    if smoke.stdout:
        print(smoke.stdout.rstrip())
    if smoke.returncode != 0:
        if smoke.stderr:
            print(smoke.stderr.rstrip())
        raise SystemExit(
            f"Packaged executable smoke test FAILED (exit={smoke.returncode}). "
            "Không nên bàn giao thư mục dist này."
        )

    print("[ok] Packaged executable smoke test passed.")
    if os.name == "nt":
        print(f"[ok] Windows build hoàn tất: {executable}")
    else:
        print(f"[ok] Build hoàn tất cho {system}: {executable}")


if __name__ == "__main__":
    main()
