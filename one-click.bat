@echo off
setlocal EnableExtensions
cd /d "%~dp0"

title AI Voice Locator - One Click Setup and Build

set "APP_VERSION=0.5.1"
set "PYTHON_VERSION=3.12"
set "PROJECT_ROOT=%CD%"
set "LOCAL_UV_DIR=%PROJECT_ROOT%\.tools\uv"
set "RELEASE_DIR=%PROJECT_ROOT%\release"
set "RELEASE_ZIP=%RELEASE_DIR%\AI-Voice-Locator-v%APP_VERSION%-Windows.zip"
set "UV_EXE="

set "HF_HUB_DISABLE_TELEMETRY=1"

call :banner
call :check_windows || goto :failed
call :setup_uv || goto :failed
call :setup_python || goto :failed
call :prepare_environment || goto :failed
call :download_models || goto :failed
call :verify_source || goto :failed
call :build_app || goto :failed
call :package_release || goto :failed

echo.
echo ================================================================
echo   BUILD COMPLETED SUCCESSFULLY
echo ================================================================
echo.
echo App folder:
echo   %PROJECT_ROOT%\dist\voice-locator
echo.
echo Windows executable:
echo   %PROJECT_ROOT%\dist\voice-locator\voice-locator.exe
echo.
echo Release ZIP:
echo   %RELEASE_ZIP%
echo.
echo You can copy the whole dist\voice-locator folder or the release ZIP
echo to another Windows x64 machine. No separate Python installation is needed.
echo.
if /I "%~1"=="--no-pause" goto :eof
pause
goto :eof

:banner
echo ================================================================
echo   AI Voice Locator v%APP_VERSION%
echo   PySide6 desktop - one-click setup + model download + test + build
echo ================================================================
echo.
exit /b 0

:check_windows
echo [1/7] Checking Windows environment...
if not "%OS%"=="Windows_NT" (
  echo [ERROR] This script must be run from Windows CMD/PowerShell.
  echo         Do not run it inside WSL.
  exit /b 1
)
if /I "%PROCESSOR_ARCHITECTURE%"=="AMD64" goto :windows_ok
if /I "%PROCESSOR_ARCHITEW6432%"=="AMD64" goto :windows_ok

echo [ERROR] This build is currently prepared for Windows x64 ^(AMD64^).
exit /b 1

:windows_ok
echo [OK] Windows x64 detected.
exit /b 0

:setup_uv
echo.
echo [2/7] Checking uv...
where uv >nul 2>&1
if errorlevel 1 goto :install_uv
for /f "delims=" %%I in ('where uv') do if not defined UV_EXE set "UV_EXE=%%I"
echo [OK] Using existing uv: %UV_EXE%
"%UV_EXE%" --version
if errorlevel 1 exit /b 1
exit /b 0

:install_uv
echo [INFO] uv was not found. Installing a project-local copy...
where powershell >nul 2>&1
if errorlevel 1 (
  echo [ERROR] PowerShell is required to install uv automatically.
  exit /b 1
)

if not exist "%LOCAL_UV_DIR%" mkdir "%LOCAL_UV_DIR%"
set "UV_INSTALL_DIR=%LOCAL_UV_DIR%"
set "UV_NO_MODIFY_PATH=1"
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; irm https://astral.sh/uv/install.ps1 ^| iex"
if errorlevel 1 (
  echo [ERROR] uv installation failed.
  exit /b 1
)
set "UV_INSTALL_DIR="
set "UV_NO_MODIFY_PATH="

if not exist "%LOCAL_UV_DIR%\uv.exe" (
  echo [ERROR] uv installer finished but uv.exe was not found at:
  echo         %LOCAL_UV_DIR%\uv.exe
  exit /b 1
)
set "UV_EXE=%LOCAL_UV_DIR%\uv.exe"
echo [OK] Installed uv: %UV_EXE%
"%UV_EXE%" --version
if errorlevel 1 exit /b 1
exit /b 0

:setup_python
echo.
echo [3/7] Ensuring Python %PYTHON_VERSION% is available through uv...
"%UV_EXE%" python install %PYTHON_VERSION%
if errorlevel 1 (
  echo [ERROR] Python %PYTHON_VERSION% setup failed.
  exit /b 1
)
echo [OK] Python %PYTHON_VERSION% is ready.
exit /b 0

:prepare_environment
echo.
echo [4/7] Synchronizing project dependencies...
if exist ".venv" if not exist ".venv\Scripts\python.exe" (
  echo [INFO] Existing .venv is not a Windows virtual environment. Recreating it...
  rmdir /s /q ".venv"
)
"%UV_EXE%" sync --python %PYTHON_VERSION% --dev --refresh
if errorlevel 1 (
  echo [ERROR] Dependency synchronization failed.
  exit /b 1
)
echo [OK] Dependencies are synchronized.
exit /b 0

:download_models
echo.
echo [5/7] Downloading/verifying configured speaker embedding models...
"%UV_EXE%" run poe models
if errorlevel 1 (
  echo [ERROR] Model download/verification failed.
  echo         If GitHub/Hugging Face is blocked on this network,
  echo         download the required ONNX models manually into the models folder
  echo         and run one-click.bat again.
  exit /b 1
)
echo [OK] Models are ready.
exit /b 0

:verify_source
echo.
echo [6/7] Running source checks and unit tests...
"%UV_EXE%" run poe check
if errorlevel 1 (
  echo [ERROR] Compile check failed. Build stopped.
  exit /b 1
)
"%UV_EXE%" run poe test
if errorlevel 1 (
  echo [ERROR] Unit tests failed. Build stopped.
  exit /b 1
)
echo [OK] Source checks and tests passed.
exit /b 0

:build_app
echo.
echo [7/7] Building standalone Windows desktop application...
"%UV_EXE%" run poe build
if errorlevel 1 (
  echo [ERROR] PyInstaller build or packaged smoke test failed.
  exit /b 1
)
if not exist "%PROJECT_ROOT%\dist\voice-locator\voice-locator.exe" (
  echo [ERROR] Build command completed but voice-locator.exe is missing.
  exit /b 1
)
echo [OK] Standalone Windows app built successfully.
exit /b 0

:package_release
echo.
echo [release] Creating distributable ZIP...
if not exist "%RELEASE_DIR%" mkdir "%RELEASE_DIR%"
set "VOICE_LOCATOR_RELEASE_SOURCE=%PROJECT_ROOT%\dist\voice-locator"
set "VOICE_LOCATOR_RELEASE_ZIP=%RELEASE_ZIP%"
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; if (Test-Path $env:VOICE_LOCATOR_RELEASE_ZIP) { Remove-Item -Force $env:VOICE_LOCATOR_RELEASE_ZIP }; Compress-Archive -Path $env:VOICE_LOCATOR_RELEASE_SOURCE -DestinationPath $env:VOICE_LOCATOR_RELEASE_ZIP -CompressionLevel Optimal"
set "VOICE_LOCATOR_RELEASE_SOURCE="
set "VOICE_LOCATOR_RELEASE_ZIP="
if errorlevel 1 (
  echo [ERROR] Release ZIP creation failed.
  exit /b 1
)
if not exist "%RELEASE_ZIP%" (
  echo [ERROR] Release ZIP was not created.
  exit /b 1
)
echo [OK] Release ZIP created.
exit /b 0

:failed
echo.
echo ================================================================
echo   BUILD FAILED
echo ================================================================
echo Review the error above, then run one-click.bat again.
echo.
if /I "%~1"=="--no-pause" exit /b 1
pause
exit /b 1
