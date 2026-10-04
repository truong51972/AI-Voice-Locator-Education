# v0.3.3 - One-click Windows build

## Added

- Root-level `one-click.bat` for a complete Windows x64 setup/build workflow.
- Automatic project-local `uv` installation when `uv` is not already available.
- Automatic Python 3.12 installation through `uv`.
- Dependency synchronization with `uv sync --dev --refresh`.
- CAM++ model download/verification.
- Compile check and unit-test gate before packaging.
- PyInstaller standalone Windows build using the existing packaged smoke test.
- Automatic release archive at `release/AI-Voice-Locator-v0.3.3-Windows.zip`.
- `--no-pause` argument for scripted/CI invocation.

## Notes

The script must run from native Windows CMD/PowerShell, not WSL, because PyInstaller does not cross-compile a Windows `.exe` from Linux/WSL.
