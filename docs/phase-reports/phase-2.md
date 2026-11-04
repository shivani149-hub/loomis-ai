# Phase 2 Report: Face Detection and Landmark Extraction

## 1. Phase Objective

The objective of **Phase 2: Face Detection and Landmark Extraction** is to integrate Google's official **MediaPipe Face Landmarker Tasks API** into the Loomis AI backend to detect human faces from preprocessed portraits, extract dense 478 3D facial landmarks, convert normalized coordinates into pixel space, and serve the structured result through a dedicated RESTful API endpoint.

In accordance with strict Phase 2 scope boundaries:
- Loomis construction spheres, centerlines, temporal discs, thirds lines, and drawing stages are **NOT** implemented in this phase.
- Head pose estimation as a separate feature, eye/nose/mouth drawing generation, hair segmentation, and frontend UIs are deferred to later phases.
- All existing Phase 1 image validation and preprocessing capabilities are preserved and reused.
- No personal or real human portrait photographs are committed to Git; all tests utilize programmatically generated synthetic images.

---

## 2. Features Implemented

1. **MediaPipe Face Landmarker Tasks API Integration (`backend/services/face_detector.py`)**:
   - Integrated `mediapipe.tasks.python.vision.FaceLandmarker` using `RunningMode.IMAGE` for still portraits.
   - Configured official `face_landmarker.task` model bundle.
   - Built a thread-safe singleton service (`FaceDetectorService`) with double-checked locking (`threading.Lock()`), ensuring the model is loaded once into memory on application startup or first request and reused across concurrent requests without redundant disk I/O or model re-initialization.

2. **Single-Face Policy Validation**:
   - Configured detection for up to 3 faces to assess multi-person presence.
   - **Zero-Face Rejection**: If no face is detected in the image, raises `NoFaceDetectedError` mapped to `HTTP 400 Bad Request` with an actionable message prompting the user for a clear portrait.
   - **Multi-Face Rejection**: If multiple faces are detected, raises `MultipleFacesDetectedError` mapped to `HTTP 400 Bad Request` under the default single-portrait policy.
   - **Configurable Primary Face Selection**: Provides a programmatic option (`require_single_face=False`) that isolates the primary subject based on maximum bounding box area.

3. **Dense 478 3D Landmark Extraction & Coordinate Conversion**:
   - Extracts all 478 canonical facial mesh landmarks without arbitrary omission or pruning.
   - Preserves original zero-based MediaPipe landmark indices ($0 \dots 477$).
   - Calculates exact pixel coordinates from normalized $[0.0, 1.0]$ values using the preprocessed image's dimensions:
     $$\text{pixel\_x} = \text{round}(x \times \text{width}, 2)$$
     $$\text{pixel\_y} = \text{round}(y \times \text{height}, 2)$$
   - Retains relative depth ($z$) coordinate for volumetric calculations in downstream phases.

4. **Dedicated RESTful Endpoint (`POST /api/faces/detect`)**:
   - Reuses Phase 1 image streaming and validation (rejecting empty files, oversized payloads $>10$ MB, corrupted images, and unsupported formats).
   - Reuses Phase 1 image preprocessing (EXIF rotation correction, 3-channel RGB conversion, and proportional downscaling to max 1024px).
   - Returns structured `FaceLandmarksResponse` containing `image_width`, `image_height`, `faces_detected`, and the ordered list of 478 `FacialLandmark` objects.

5. **Graceful Error & Missing-Model Handling**:
   - Implemented dedicated domain exceptions: `FaceDetectionError`, `NoFaceDetectedError`, `MultipleFacesDetectedError`, `ModelNotFoundError`, and `ModelLoadError`.
   - Missing model files produce `HTTP 503 Service Unavailable` with clear troubleshooting instructions.

---

## 3. Files Created or Modified

| File Path | Status | Description |
|---|---|---|
| `backend/models/face_landmarker.task` | Created | Official MediaPipe Face Landmarker Tasks model asset (3.75 MB) |
| `backend/schemas/landmark.py` | Created | Pydantic models for `FacialLandmark` and `FaceLandmarksResponse` |
| `backend/schemas/__init__.py` | Modified | Exported landmark schemas |
| `backend/services/face_detector.py` | Created | Face landmarker service, thread-safe caching, coordinate conversion, and single-face policy |
| `backend/services/image_processor.py` | Modified | Added `preprocess_to_pil()` helper to avoid redundant Base64 conversions |
| `backend/services/__init__.py` | Modified | Exported face detector service and custom domain exceptions |
| `backend/main.py` | Modified | Added lifespan model preloader, `FaceDetectionError` handler, and `POST /api/faces/detect` endpoint |
| `backend/requirements.txt` | Modified | Added `mediapipe>=0.10.14,<1.3.0` and `numpy>=1.26.0,<3.0.0` |
| `backend/tests/test_face_detection.py` | Created | 9 comprehensive tests covering detection, zero-face, multi-face, coordinate math, caching, and missing model handling |
| `docs/architecture.md` | Modified | Updated architecture diagram, component descriptions, and API contracts |
| `docs/implementation-roadmap.md` | Modified | Marked Phase 2 as Completed |
| `README.md` | Modified | Updated project structure, setup instructions, endpoints, and status |
| `docs/phase-reports/phase-2.md` | Created | Phase 2 verification report and deliverable audit |

---

## 4. Dependencies and Model Download Details

### 4.1 Python Dependencies Added
| Dependency | Version Specifier | Role in Phase 2 |
|---|---|---|
| `mediapipe` | `>=0.10.14,<1.3.0` | Google MediaPipe library providing the Face Landmarker Tasks API |
| `numpy` | `>=1.26.0,<3.0.0` | Matrix transformations and image array buffers for MediaPipe input |

### 4.2 Official Model Asset Details
- **Model Name**: MediaPipe Face Landmarker (float16)
- **Model Format**: `.task` (TensorFlow Lite Task Bundle)
- **File Location**: `backend/models/face_landmarker.task`
- **File Size**: 3,758,596 bytes (~3.75 MB)
- **Official Source URL**:
  `https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task`
- **Running Mode**: `RunningMode.IMAGE`
- **Key Capabilities**: 478 3D facial mesh landmarks with sub-pixel surface localization.

---

## 5. What MediaPipe Does vs. What It Does Not Do

A key requirement of this project is maintaining a clear understanding of the boundary between pretrained machine learning and classical art pedagogy:

### What MediaPipe Does:
1. **Detects Facial Features on the Skin Surface**: Identifies 478 distinct anatomic surface landmarks including eye contours, eyelids, pupils, nasal bridge, nostrils, lip boundaries, and jawline silhouette.
2. **Estimates Sub-pixel 3D Coordinates**: Outputs normalized relative coordinates ($x, y \in [0.0, 1.0]$ and relative depth $z$) relative to the head center.
3. **High-Efficiency Execution**: Completes inference in under 30 milliseconds on modern CPUs using TensorFlow Lite XNNPACK delegates.

### What MediaPipe DOES NOT Do:
1. **Does NOT Know What a Loomis Ball Is**: MediaPipe has zero awareness of Andrew Loomis, head construction geometry, cranium spheres, or fine art principles.
2. **Does NOT Model Cranial Volume Under Hair**: MediaPipe landmarks terminate at the forehead hairline. It cannot see the top of the skull, parietal bones, or occipital curvature beneath hair.
3. **Does NOT Draw Construction Lines**: It does not draw temporal cut planes, brow lines, central vertical axes, or facial thirds.
4. **Does NOT Generate Step-by-Step Drawing Stages**: MediaPipe outputs numerical floating-point coordinate tensors, not artistic drawing tutorials.
5. **Does NOT Provide Art Instruction**: It cannot tell the student how to construct proportions or place features.

*Bridging this divide is the exact purpose of the Loomis Construction Engine (Phase 4) and Drawing Generator (Phase 5).*

---

## 6. API Endpoint Details

### `POST /api/faces/detect`
- **Request**: `multipart/form-data` with `file` (JPEG, PNG, WebP up to 10 MB).
- **Processing**:
  1. Validates file content and MIME type via `validate_image_bytes()`.
  2. Auto-corrects EXIF orientation and normalizes to 3-channel RGB.
  3. Downscales proportionally if long edge $> 1024$px.
  4. Runs MediaPipe Face Landmarker inference.
  5. Enforces single-face constraint.
  6. Converts coordinates to pixel space and returns structured payload.
- **Success Response (`200 OK`)**:
```json
{
  "success": true,
  "message": "Face detected and landmarks extracted successfully.",
  "image_width": 400,
  "image_height": 400,
  "faces_detected": 1,
  "landmarks": [
    {
      "index": 0,
      "x": 0.506726,
      "y": 0.601664,
      "z": -0.065996,
      "pixel_x": 202.69,
      "pixel_y": 240.67
    },
    ...
    {
      "index": 477,
      "x": 0.589123,
      "y": 0.354112,
      "z": -0.012456,
      "pixel_x": 235.65,
      "pixel_y": 141.64
    }
  ]
}
```
- **Error Responses**:
  - `400 Bad Request`: Empty file, corrupted image, no face detected, or multiple faces detected.
  - `413 Content Too Large`: Upload exceeds 10 MB.
  - `415 Unsupported Media Type`: Unsupported format (e.g., GIF).
  - `503 Service Unavailable`: Model file missing from `backend/models/`.

---

## 7. Tests Executed and Actual Results

The complete automated test suite (`python -m pytest backend/tests -v`) was executed against Python 3.12.5.

```text
============================= test session starts =============================
platform win32 -- Python 3.12.5, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\shanm\OneDrive\Desktop\loomis-ai
plugins: anyio-4.12.1
collected 24 items

backend/tests/test_face_detection.py::test_successful_face_detection PASSED [  4%]
backend/tests/test_face_detection.py::test_no_face_detected_returns_400 PASSED [  8%]
backend/tests/test_face_detection.py::test_multiple_faces_rejected_under_single_face_policy PASSED [ 12%]
backend/tests/test_face_detection.py::test_invalid_image_inputs PASSED   [ 16%]
backend/tests/test_face_detection.py::test_correct_coordinate_conversion PASSED [ 20%]
backend/tests/test_face_detection.py::test_service_model_caching PASSED  [ 25%]
backend/tests/test_face_detection.py::test_missing_model_handling PASSED [ 29%]
backend/tests/test_face_detection.py::test_missing_model_api_error_response PASSED [ 33%]
backend/tests/test_face_detection.py::test_multi_face_primary_selection_policy PASSED [ 37%]
backend/tests/test_health.py::test_health_check_returns_200_and_expected_payload PASSED [ 41%]
backend/tests/test_image_upload.py::test_valid_jpeg_upload PASSED        [ 45%]
backend/tests/test_image_upload.py::test_valid_png_with_transparency_upload PASSED [ 50%]
backend/tests/test_image_upload.py::test_valid_webp_upload PASSED        [ 54%]
backend/tests/test_image_upload.py::test_image_resizing_larger_than_1024_landscape PASSED [ 58%]
backend/tests/test_image_upload.py::test_image_resizing_larger_than_1024_portrait PASSED [ 62%]
backend/tests/test_image_upload.py::test_image_resizing_smaller_than_1024_not_upscaled PASSED [ 66%]
backend/tests/test_image_upload.py::test_exif_orientation_transposition PASSED [ 70%]
backend/tests/test_image_upload.py::test_empty_file_upload_rejected PASSED [ 75%]
backend/tests/test_image_upload.py::test_unsupported_image_format_rejected PASSED [ 79%]
backend/tests/test_image_upload.py::test_mismatched_extension_detected_by_content PASSED [ 83%]
backend/tests/test_image_upload.py::test_non_image_text_file_rejected PASSED [ 87%]
backend/tests/test_image_upload.py::test_corrupted_image_bytes_rejected PASSED [ 91%]
backend/tests/test_image_upload.py::test_file_exceeding_10mb_limit_rejected PASSED [ 95%]
backend/tests/test_image_upload.py::test_excessive_dimensions_protection PASSED [100%]

============================= 24 passed in 4.38s ==============================
```

Live server execution was additionally verified on port 8009:
- Server preloaded model on startup.
- `GET /api/health`: Returned `200 OK` (version 0.2.0).
- `POST /api/faces/detect`: Processed synthetic portrait, detected 1 face, and returned all 478 landmarks with exact pixel coordinates.

---

## 8. Known Limitations

- **Single Face Focus**: By design, Loomis AI operates as an individualized portrait drawing tutor. Multi-person photos are flagged and rejected so the user receives unambiguous drawing instructions for a single subject.
- **Head Pose Estimation Deferred**: Computing 3D Euler angles (Pitch, Yaw, Roll) and head tilt classification is slated for Phase 3.
- **Surface Landmarks Only**: MediaPipe landmarks represent facial skin points and do not estimate the underlying cranium ball (which will be solved geometrically in Phase 4).

---

## 9. Status

- **Phase 2 Status**: **COMPLETED**
- **Verification Result**: 24 / 24 automated tests passing. Live endpoints verified.
- **Next Phase**: Phase 3 – Facial Landmarks and Head Pose Estimation (pending user review).

