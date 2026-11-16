# Third-party components and model provenance

Original application code is licensed under the terms in LICENSE. That license does not override upstream restrictions.

| Component | Included or downloaded | Terms / source |
| --- | --- | --- |
| OpenCV Zoo `facial_fer_model.py` | Included, with original copyright | Apache-2.0; `face_lab/resources/licenses/OpenCV-Zoo-Apache-2.0.txt` |
| LibreFace face-alignment helper | Adapted code included in `face_lab/libreface_alignment.py` | USC Research License; `face_lab/resources/licenses/LibreFace-USC-Research.txt` |
| YuNet | Model downloaded from OpenCV Zoo | MIT; `face_lab/resources/licenses/YuNet-MIT.txt` |
| Progressive Teacher / MobileFaceNet FER | Model downloaded from OpenCV Zoo | Directory's Apache-2.0 license; upstream documentation retained under `models/README-upstream.md` |
| EmotiEffLib EfficientNet-B0 | Model downloaded from the official repository | Upstream Apache-2.0 license retained; applicable dataset terms remain separate |
| LibreFace AU Encoder / Intensity / Presence | Extracted from official NuGet package 2.0.0 | USC Research License; educational, research and non-profit purposes; commercial permission required |
| MediaPipe Face Landmarker | Task model downloaded from Google's model hosting | MediaPipe source is Apache-2.0; consult Google's applicable model terms/model card separately; a source-code license alone does not establish all model rights |

This release is intended for personal learning and non-commercial research. It does not include pretrained model binaries, training datasets, camera recordings, or downloaded sample photographs. Model download URLs and integrity hashes are in `face_lab/resources/model-manifest.json`.

## LibreFace version clarification

The official NuGet package version is **2.0.0**. Its metadata describes the **WACV 2024** implementation and references OpenSense commit `33dcaf80d0c07ca2751f489b40d4399b78972e75`. This project does **not** claim the package contains the latest FG 2026 LibreFace 2.0 paper checkpoints.

## Modifications to upstream code

- OpenCV Zoo helper: retained behavior, adjusted license-file reference for the package layout.
- LibreFace alignment: isolated the image-alignment function; updated deprecated Pillow resampling API; retained the 256-pixel resized output before a 224-pixel center crop instead of overwriting it with the 512-pixel intermediate. The route follows the official OpenSense 256→224 pipeline. These preprocessing differences are documented rather than treated as new model training.

## References

- https://github.com/opencv/opencv_zoo
- https://github.com/sb-ai-lab/EmotiEffLib
- https://github.com/ihp-lab/LibreFace
- https://github.com/ihp-lab/OpenSense/tree/master/Utilities/LibreFace
- https://www.nuget.org/packages/LibreFace/2.0.0
- https://ai.google.dev/edge/mediapipe/solutions/vision/face_landmarker
