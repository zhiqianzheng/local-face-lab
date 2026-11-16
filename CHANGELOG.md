# Changelog

## 0.1.1

- Add a Linux x86_64 portable distribution with embedded Python, native dependencies and verified models; no installation or first-run downloads required.
- Add offline runtime/model `--self-test` and frozen-resource path support.
- Preserve recordings in the user data directory, independently of the extracted application folder.
- Clearly distinguish standalone user downloads from developer source/wheel packages.

## 0.1.0

First packaged release of Local Face Lab.

- Local webcam preview and side-by-side MobileFaceNet / EmotiEffLib classification.
- LibreFace AU intensity/presence and 30-second trend visualization.
- Silent WebM recording, CSV and JSON timeline export.
- Installable Python wheel, Linux installation/start scripts and local Waitress server.
- Upstream model downloader with SHA-256/SHA-512 integrity verification.
- Portable model/data paths, license notices, functional and browser verification tools.

Validated on Ubuntu 22.04 x86_64 with Python 3.12 and Chromium. No RK3568 port, psychological inference, or validated micro-expression recognition is included.
