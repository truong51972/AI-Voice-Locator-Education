from __future__ import annotations

import importlib.util
import os
import platform
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "models" / "3dspeaker_speech_campplus_sv_en_voxceleb_16k.onnx"
APP_NAME = "voice-locator"
HOOKS_DIR = ROOT / "scripts" / "pyinstaller_hooks"


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


def _required_resource(package: str, filename: str) -> Path:
    path = _package_dir(package) / filename
    if not path.is_file():
        raise SystemExit(
            f"Không tìm thấy runtime resource `{package}/{filename}` trong virtual environment. "
            "Chạy `uv sync --dev` rồi thử lại."
        )
    return path


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
    pretty = "\n  - ".join(str(p) for p in candidates)
    raise SystemExit(
        "Không tìm thấy onnxruntime.dll của sherpa-onnx-core trong môi trường Windows.\n"
        "Hãy chạy `uv sync --dev --refresh` trước khi build. Đã kiểm tra:\n  - " + pretty
    )


def _is_wsl() -> bool:
    release = platform.release().lower()
    return os.name != "nt" and ("microsoft" in release or "wsl" in release)


def main() -> None:
    if not MODEL.is_file():
        raise SystemExit("Thiếu model. Chạy `poe models` trước khi build.")
    if not HOOKS_DIR.is_dir():
        raise SystemExit(f"Thiếu custom PyInstaller hooks: {HOOKS_DIR}")

    gradio_client_types = _required_resource("gradio_client", "types.json")
    safehttpx_version = _required_resource("safehttpx", "version.txt")
    groovy_version = _required_resource("groovy", "version.txt")

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
        "--additional-hooks-dir",
        str(HOOKS_DIR),
        "--add-data",
        f"{ROOT / 'models'}{sep}models",
        "--collect-all",
        "gradio",
        "--collect-all",
        "gradio_client",
        "--collect-all",
        "safehttpx",
        "--collect-all",
        "groovy",
        "--add-data",
        f"{gradio_client_types}{sep}gradio_client",
        "--add-data",
        f"{safehttpx_version}{sep}safehttpx",
        "--add-data",
        f"{groovy_version}{sep}groovy",
        "--collect-all",
        "sherpa_onnx",
        "--collect-all",
        "imageio_ffmpeg",
    ]

    bundled_ort_source: Path | None = None
    if os.name == "nt":
        # sherpa-onnx-core currently ships onnxruntime.dll as native package data
        # (and on some wheel layouts in .venv/Scripts). Add the exact DLL to a
        # deterministic private path. runtime.py preloads this absolute copy before
        # importing sherpa_onnx, preventing stale System32 ORT DLLs from winning.
        bundled_ort_source = _find_windows_onnxruntime_dll()
        cmd += [
            "--add-binary",
            f"{bundled_ort_source}{sep}sherpa_onnx/lib",
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
        "gradio_client/types.json": internal_dir / "gradio_client" / "types.json",
        "safehttpx/version.txt": internal_dir / "safehttpx" / "version.txt",
        "groovy/version.txt": internal_dir / "groovy" / "version.txt",
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

    # Real startup smoke test: it constructs the full UI AND creates a Sherpa
    # SpeakerEmbeddingExtractor from the bundled model. This catches both Gradio
    # resources and ONNX Runtime API/DLL mismatches before dist is accepted.
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
