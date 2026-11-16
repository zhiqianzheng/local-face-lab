# Standalone Linux distribution

The portable build contains Python, native inference dependencies, model files and license notices. Users do not run these build steps.

Build on Ubuntu 22.04 x86_64 with Python 3.12 to keep the glibc baseline at 2.35. PyInstaller does not cross-compile; do not label this Linux build as Windows/ARM compatible.

```bash
uv venv --python 3.12 .freeze-venv
uv pip install --python .freeze-venv/bin/python . pyinstaller
# The web UI does not need OpenCV's desktop GUI. Avoid Qt dependencies in the bundle.
uv pip uninstall --python .freeze-venv/bin/python opencv-contrib-python
uv pip install --python .freeze-venv/bin/python opencv-python-headless
.freeze-venv/bin/python -m face_lab --model-dir models --download-only
.freeze-venv/bin/python scripts/build_portable.py
```

The deliberate OpenCV headless substitution replaces the `cv2` module; do not install both OpenCV distributions into this environment afterward. This is a packaging environment separate from normal development.

Tests performed for the initial portable release:

- Run the frozen executable with an isolated HOME, no external Python paths and no network, hiding the entire developer home directory using bubblewrap.
- `--self-test` exercises native MediaPipe loading/detection and all required model inference graphs on synthetic inputs, without a camera or network.
- Run the frozen server in isolation and exercise face predictions, AU output, all modes, WebM recording and CSV/JSON downloads with a simulated camera.
- Inspect release contents and verify each bundled model against the pinned manifest.

Linux portable archives preserve executable permissions. Keep `_internal/` next to `LocalFaceLab`. A normal operating system, camera driver and modern browser remain prerequisites; the application does not bundle an entire OS/browser.
