"""PyInstaller hook for the Gradio runtime stack used by Voice Locator.

Gradio's dependency tree contains a few packages that read non-Python files
(e.g. version.txt/types.json) directly during import. Static analysis sees the
Python imports but may omit those resources, which makes a successfully built
executable crash at startup. Keep the runtime packaging policy centralized here.
"""

from PyInstaller.utils.hooks import collect_all, copy_metadata

RUNTIME_PACKAGES = (
    "gradio",
    "gradio_client",
    "safehttpx",
    "groovy",
)

# Package data, native binaries and dynamically imported submodules.
datas = []
binaries = []
hiddenimports = []
for package in RUNTIME_PACKAGES:
    package_datas, package_binaries, package_hiddenimports = collect_all(package)
    datas += package_datas
    binaries += package_binaries
    hiddenimports += package_hiddenimports

# Some libraries inspect installed-distribution metadata through importlib.metadata.
# copy_metadata is cheap compared with the Gradio bundle and makes that behavior
# deterministic inside the frozen executable.
for distribution in ("gradio", "gradio-client", "safehttpx", "groovy"):
    try:
        datas += copy_metadata(distribution, recursive=False)
    except Exception:
        # Package payload collection above is the critical path. Keep metadata
        # best-effort to remain compatible with PyInstaller metadata APIs.
        pass
