from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path


def _load_downloader():
    script = Path(__file__).resolve().parents[1] / "scripts" / "download_models.py"
    spec = importlib.util.spec_from_file_location("download_models_test", script)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_validate_model_checks_exact_size_and_sha256(tmp_path, monkeypatch):
    module = _load_downloader()
    payload = b"voice-locator-model-test" * 100
    model = tmp_path / "model.onnx"
    model.write_bytes(payload)

    monkeypatch.setattr(module, "EXPECTED_SIZE", len(payload))
    monkeypatch.setattr(module, "EXPECTED_SHA256", hashlib.sha256(payload).hexdigest())

    assert module.validate_model(model, verbose=False)

    model.write_bytes(payload[:-1])
    assert not module.validate_model(model, verbose=False)


def test_download_once_streams_local_source(tmp_path, monkeypatch):
    module = _load_downloader()
    payload = (b"0123456789abcdef" * 4096) + b"done"
    source = tmp_path / "source.onnx"
    part = tmp_path / "download.onnx.part"
    source.write_bytes(payload)

    monkeypatch.setattr(module, "EXPECTED_SIZE", len(payload))
    monkeypatch.setattr(module, "CHUNK_SIZE", 4096)

    module._download_once(source.as_uri(), part)

    assert part.read_bytes() == payload


def test_main_repairs_corrupt_final_model(tmp_path, monkeypatch):
    module = _load_downloader()
    payload = b"correct-model" * 64
    model_dir = tmp_path / "models"
    model_dir.mkdir()
    destination = model_dir / module.FILENAME
    destination.write_bytes(b"corrupt-but-present")

    monkeypatch.setattr(module, "MODEL_DIR", model_dir)
    monkeypatch.setattr(module, "EXPECTED_SIZE", len(payload))
    monkeypatch.setattr(module, "EXPECTED_SHA256", hashlib.sha256(payload).hexdigest())

    def fake_download(path):
        assert path == destination
        path.write_bytes(payload)

    monkeypatch.setattr(module, "_download_model", fake_download)
    module.main()

    assert destination.read_bytes() == payload
    assert module.validate_model(destination, verbose=False)


def test_main_preserves_interrupted_legacy_download_for_resume(tmp_path, monkeypatch):
    module = _load_downloader()
    full_payload = b"0123456789" * 100
    partial_payload = full_payload[:400]
    model_dir = tmp_path / "models"
    model_dir.mkdir()
    destination = model_dir / module.FILENAME
    destination.write_bytes(partial_payload)

    monkeypatch.setattr(module, "MODEL_DIR", model_dir)
    monkeypatch.setattr(module, "EXPECTED_SIZE", len(full_payload))
    monkeypatch.setattr(module, "EXPECTED_SHA256", hashlib.sha256(full_payload).hexdigest())

    observed = {}

    def fake_download(path):
        part = path.with_suffix(path.suffix + ".part")
        observed["part"] = part.read_bytes()
        path.write_bytes(full_payload)
        part.unlink(missing_ok=True)

    monkeypatch.setattr(module, "_download_model", fake_download)
    module.main()

    assert observed["part"] == partial_payload
    assert destination.read_bytes() == full_payload
