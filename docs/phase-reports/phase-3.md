# Phase 3 Report: Head Pose Estimation

## 1. Phase Objective

The objective of **Phase 3: Head Pose Estimation** is to calculate the 3D spatial orientation (Yaw, Pitch, and Roll) of the human head from the 2D facial landmarks extracted in Phase 2, and categorize the head pose into standard artistic portrait perspectives (`FRONT`, `THREE_QUARTER_LEFT`, `THREE_QUARTER_RIGHT`, `PROFILE_LEFT`, `PROFILE_RIGHT`).

In accordance with strict architectural and pedagogical principles:
- **No black-box ML pose models**: Orientation is derived purely from geometric relationships between MediaPipe landmarks and a canonical 3D anthropometric model.
- **No fabricated confidence**: Confidence scores are mathematically computed from geometric reprojection residuals and face scale.
- **Decoupled domain architecture**: Core pose mathematics live in `backend/services/head_pose_estimator.py`, exposed through a clean RESTful endpoint `POST /api/faces/pose`.
- **Strict scope boundaries**: No Loomis construction geometry, drawing stages, or frontend code were implemented prematurely.

---

## 2. Why Head Pose is Required for Loomis Construction

In classical art pedagogy (specifically the Andrew Loomis Method), drawing the head does not begin with surface features; it begins with a volumetric sphere (the cranium ball) and tilted structural planes:

1. **Orientation of the Cranial Ball**: The cranium is a 3D sphere, but its spatial orientation in the drawing depends directly on head tilt (Pitch, Yaw, and Roll).
2. **Central Meridian & Brow Equator**: The central vertical line dividing the face into symmetrical halves curves across the spherical surface in perspective. Its curve and foreshortening are mathematically defined by the head's **Yaw** and **Pitch**.
3. **Temporal Cut-off Discs (Side Planes)**: Loomis slices off the lateral sides of the sphere to represent the flattened temporal walls. When viewed in 3D perspective, each circular cutoff disc projects onto the 2D drawing plane as an **ellipse**. The eccentricity, rotation, and visibility of this ellipse are governed directly by **Yaw** and **Pitch**:
   - In a frontal pose ($|\text{yaw}| \le 15^\circ$), both side discs are seen edge-on as narrow slivers.
   - In a three-quarter pose ($15^\circ < |\text{yaw}| \le 45^\circ$), one side disc is prominently displayed as an open ellipse, while the opposite side disc is foreshortened or hidden.
   - In a profile view ($|\text{yaw}| > 45^\circ$), one temporal disc is seen almost face-on as a full circle, and the other is completely occluded.
4. **Facial Thirds Placement**: The hairline, brow line, nose base, and chin lines project along perspective arcs determined by the 3D rotation matrix.

Without accurate 3D pose angles, an automated drawing tutor cannot know how to construct the Loomis scaffolding.

---

## 3. How Landmarks are Used (Perspective-n-Point Geometry)

Rather than using an uninterpretable neural network, Loomis AI employs classical **Perspective-n-Point (PnP)** computer vision geometry (`cv2.solvePnP`):

### 3.1 Stable Anatomical Keypoints Selected
From MediaPipe's 478 dense landmarks, 8 structurally rigid anatomical landmarks were selected. These keypoints are minimally affected by soft tissue movement (expression changes) compared to mobile regions:

| Index | Anatomical Feature | Canonical 3D Point \((X, Y, Z)\) [mm] | Role in Pose Estimation |
|:---:|---|---|---|
| **1** | Nose Tip (*Pronasale*) | \((0.0, 0.0, 0.0)\) | Coordinate origin, primary depth anchor |
| **152** | Chin Tip (*Gnathion*) | \((0.0, 110.0, 35.0)\) | Vertical axis anchor, pitch calculation |
| **33** | Left Eye Outer Corner | \((-65.0, -45.0, 30.0)\) | Bilateral horizontal axis, roll & yaw |
| **263** | Right Eye Outer Corner | \((65.0, -45.0, 30.0)\) | Bilateral horizontal axis, roll & yaw |
| **61** | Left Mouth Corner (*Cheilion*) | \((-40.0, 50.0, 25.0)\) | Lower facial width & tilt verification |
| **291** | Right Mouth Corner (*Cheilion*) | \((40.0, 50.0, 25.0)\) | Lower facial width & tilt verification |
| **10** | Forehead Midpoint (*Trichion*) | \((0.0, -120.0, 40.0)\) | Upper cranial plane, pitch stabilization |
| **168** | Glabella (*Nasion / Bridge*) | \((0.0, -50.0, 15.0)\) | Sagittal symmetry plane anchor |

### 3.2 Camera Intrinsic Assumptions
In portrait photography without lens calibration metadata, the camera is modeled as an ideal pinhole camera:
- Focal length: $f_x = f_y \approx \text{image\_width}$ (corresponding to typical 50–60° portrait field-of-view).
- Principal point (optical center): $c_x = \text{width} / 2.0$, $c_y = \text{height} / 2.0$.
- Distortion: $\mathbf{D} = [0, 0, 0, 0]$ (preprocessed images assume negligible radial/tangential distortion).

$$\mathbf{K} = \begin{bmatrix} W & 0 & W/2 \\ 0 & W & H/2 \\ 0 & 0 & 1 \end{bmatrix}$$

---

## 4. How Yaw, Pitch, and Roll are Calculated

1. **PnP Solution**: `cv2.solvePnP` with iterative Levenberg-Marquardt optimization solves for the 3D rotation vector $\mathbf{r}$ and translation vector $\mathbf{t}$. An initial extrinsic guess anchored towards the frontal view eliminates $180^\circ$ mirror ambiguities.
2. **Rotation Matrix**: $\mathbf{r}$ is converted to a $3 \times 3$ orthogonal rotation matrix $\mathbf{R}$ via the Rodrigues formula:
   $$\mathbf{R} = \text{Rodrigues}(\mathbf{r})$$
3. **Euler Angle Extraction**: Decomposing $\mathbf{R}$ into Tait-Bryan angles:
   $$\text{Pitch} = \text{atan2}(R_{21}, R_{22})$$
   $$\text{Yaw} = \text{atan2}(-R_{20}, \sqrt{R_{00}^2 + R_{10}^2})$$
   $$\text{Roll} = \text{atan2}(R_{10}, R_{00})$$

---

## 5. Coordinate Conventions

The coordinate frame aligns with standard computer vision and artistic drawing conventions:

- **Yaw (Rotation around vertical axis)**:
  - $\text{Yaw} = 0^\circ$: Direct front-facing orientation.
  - $\text{Yaw} > 0^\circ$: Head turned toward the **viewer's left** (subject's right).
  - $\text{Yaw} < 0^\circ$: Head turned toward the **viewer's right** (subject's left).
- **Pitch (Rotation around horizontal axis)**:
  - $\text{Pitch} = 0^\circ$: Level eye line.
  - $\text{Pitch} < 0^\circ$: Head tilted slightly downwards (looking down).
  - $\text{Pitch} > 0^\circ$: Head tilted upwards (looking up).
- **Roll (In-plane lateral tilt)**:
  - $\text{Roll} = 0^\circ$: Perfectly level head.
  - $\text{Roll} > 0^\circ$: In-plane clockwise tilt.
  - $\text{Roll} < 0^\circ$: In-plane counter-clockwise tilt.

---

## 6. Classification Thresholds

Head orientations are categorized according to yaw rotation:

| Classification | Angular Condition | Description |
|---|:---:|---|
| **`FRONT`** | $|\text{yaw}| \le 15.0^\circ$ | Frontal portrait; both eyes and ears symmetrically visible. |
| **`THREE_QUARTER_LEFT`** | $15.0^\circ < \text{yaw} \le 45.0^\circ$ | Subject turned toward viewer's left; left temporal disc opens. |
| **`THREE_QUARTER_RIGHT`** | $-45.0^\circ \le \text{yaw} < -15.0^\circ$ | Subject turned toward viewer's right; right temporal disc opens. |
| **`PROFILE_LEFT`** | $\text{yaw} > 45.0^\circ$ | Near or full profile facing left. |
| **`PROFILE_RIGHT`** | $\text{yaw} < -45.0^\circ$ | Near or full profile facing right. |

---

## 7. Confidence & Diagnostic Quality Metrics

Confidence is not a static or fabricated number. It is calculated directly from geometric residuals:

1. **Mean Reprojection Error (MRE)**:
   The 3D model points are projected back into 2D camera coordinates using the solved $(\mathbf{r}, \mathbf{t})$. The Euclidean pixel distance between projected points and actual detected 2D landmarks is averaged:
   $$\text{mre} = \frac{1}{N} \sum_{i=1}^N \|\mathbf{p}_i^{\text{actual}} - \mathbf{p}_i^{\text{proj}}\|$$
   A low MRE ($< 10$ px) indicates high geometric alignment.
2. **Face Scale Quality**:
   Landmarking accuracy depends on face size in the frame. A face spanning $>150$ px receives full scale weighting ($q_{\text{scale}} = 1.0$).
3. **Composite Confidence**:
   $$\text{confidence} = \text{round}(0.75 \times \max(0, 1 - \text{mre}/25.0) + 0.25 \times \min(1, \text{face\_width}/150.0), 2)$$
   Strictly bounded within $[0.0, 1.0]$.

---

## 8. API Endpoint Details

### `POST /api/faces/pose`
- **Request**: `multipart/form-data` with `file` (JPEG, PNG, WebP up to 10 MB).
- **Processing Flow**:
  1. Image validation & normalization (Phase 1).
  2. MediaPipe face detection & 478 landmark extraction (Phase 2).
  3. Stable 8-point landmark filtering and PnP solving (Phase 3).
  4. Euler angle extraction, classification, and quality computation.
- **Success Response (`200 OK`)**:
```json
{
  "success": true,
  "message": "Head pose estimated successfully.",
  "yaw_degrees": -4.91,
  "pitch_degrees": -6.88,
  "roll_degrees": 1.16,
  "orientation": "FRONT",
  "confidence": 0.79,
  "quality_metrics": {
    "mean_reprojection_error_px": 6.93,
    "face_width_px": 195.6,
    "face_height_px": 250.2,
    "landmarks_used_count": 8
  },
  "rotation_vector": [-0.1192, -0.0869, 0.0151],
  "translation_vector": [4.93, 1.99, 340.49]
}
```
- **Error Responses**:
  - `400 Bad Request`: Empty, corrupt, or unsupported images; zero faces or multiple faces.
  - `413 Content Too Large`: Payload $>10$ MB.
  - `422 Unprocessable Entity`: Missing required anatomical keypoints.
  - `500 Internal Server Error`: Numerical solver failure.
  - `503 Service Unavailable`: Missing model asset.

---

## 9. Tests Executed and Actual Results

The complete automated test suite (`python -m pytest backend/tests -v`) executed with **100% pass rate (33 / 33 tests passed)**:

```text
============================= test session starts =============================
platform win32 -- Python 3.12.5, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\shanm\OneDrive\Desktop\loomis-ai
plugins: anyio-4.12.1
collected 33 items

backend/tests/test_face_detection.py::test_successful_face_detection PASSED [  3%]
backend/tests/test_face_detection.py::test_no_face_detected_returns_400 PASSED [  6%]
backend/tests/test_face_detection.py::test_multiple_faces_rejected_under_single_face_policy PASSED [  9%]
backend/tests/test_face_detection.py::test_invalid_image_inputs PASSED   [ 12%]
backend/tests/test_face_detection.py::test_correct_coordinate_conversion PASSED [ 15%]
backend/tests/test_face_detection.py::test_service_model_caching PASSED  [ 18%]
backend/tests/test_face_detection.py::test_missing_model_handling PASSED [ 21%]
backend/tests/test_face_detection.py::test_missing_model_api_error_response PASSED [ 24%]
backend/tests/test_face_detection.py::test_multi_face_primary_selection_policy PASSED [ 27%]
backend/tests/test_head_pose.py::test_valid_front_facing_portrait PASSED [ 30%]
backend/tests/test_head_pose.py::test_valid_turned_right_portrait PASSED [ 33%]
backend/tests/test_head_pose.py::test_valid_turned_left_portrait PASSED  [ 36%]
backend/tests/test_head_pose.py::test_no_face_image_returns_400 PASSED   [ 39%]
backend/tests/test_head_pose.py::test_invalid_image_inputs PASSED        [ 42%]
backend/tests/test_head_pose.py::test_output_schema_and_numeric_ranges PASSED [ 45%]
backend/tests/test_head_pose.py::test_orientation_classification_thresholds PASSED [ 48%]
backend/tests/test_head_pose.py::test_missing_or_insufficient_landmarks PASSED [ 51%]
backend/tests/test_head_pose.py::test_pose_solver_error_handling PASSED  [ 54%]
backend/tests/test_health.py::test_health_check_returns_200_and_expected_payload PASSED [ 57%]
backend/tests/test_image_upload.py::test_valid_jpeg_upload PASSED        [ 60%]
backend/tests/test_image_upload.py::test_valid_png_with_transparency_upload PASSED [ 63%]
backend/tests/test_image_upload.py::test_valid_webp_upload PASSED        [ 66%]
backend/tests/test_image_upload.py::test_image_resizing_larger_than_1024_landscape PASSED [ 69%]
backend/tests/test_image_upload.py::test_image_resizing_larger_than_1024_portrait PASSED [ 72%]
backend/tests/test_image_upload.py::test_image_resizing_smaller_than_1024_not_upscaled PASSED [ 75%]
backend/tests/test_image_upload.py::test_exif_orientation_transposition PASSED [ 78%]
backend/tests/test_image_upload.py::test_empty_file_upload_rejected PASSED [ 81%]
backend/tests/test_image_upload.py::test_unsupported_image_format_rejected PASSED [ 84%]
backend/tests/test_image_upload.py::test_mismatched_extension_detected_by_content PASSED [ 87%]
backend/tests/test_image_upload.py::test_non_image_text_file_rejected PASSED [ 90%]
backend/tests/test_image_upload.py::test_corrupted_image_bytes_rejected PASSED [ 93%]
backend/tests/test_image_upload.py::test_file_exceeding_10mb_limit_rejected PASSED [ 96%]
backend/tests/test_image_upload.py::test_excessive_dimensions_protection PASSED [100%]

============================= 33 passed in 5.38s ==============================
```

Live HTTP verification was also conducted on port 8010:
- `POST /api/faces/pose`: Received synthetic portrait, verified model inference, and returned valid pose estimation JSON (`yaw: -4.91°`, `pitch: -6.88°`, `roll: 1.16°`, `orientation: FRONT`, `confidence: 0.79`).

---

## 10. Known Limitations

1. **Extreme Profile Self-Occlusion**:
   MediaPipe Face Landmarker is trained primarily on poses with yaw within $\pm 60^\circ$. Beyond $60^\circ$, self-occluded anatomical landmarks (such as the far eye or mouth corner) are hallucinated or extrapolated by the mesh model. Consequently, for `PROFILE_LEFT` and `PROFILE_RIGHT`, the confidence score reflects higher reprojection residual errors.
2. **Canonical Anthropometric Model**:
   The 3D reference model uses standard anatomical head proportions. Minor personal variations (e.g., an elongated chin, wide mouth) introduce small geometric residuals (typically 4–8 px), which is documented and expected in non-calibrated monocular vision.
3. **Estimated Camera Intrinsics**:
   Without EXIF camera focal length data, the focal length is estimated as the image width ($f = W$). This standard computer vision approximation introduces minimal error in angular orientation across standard portrait focal lengths (50mm–85mm equivalent).

---

## 11. Files Changed or Created

| File Path | Status | Description |
|---|---|---|
| `backend/schemas/pose.py` | Created | Response schemas: `HeadOrientation`, `PoseQualityMetrics`, `HeadPoseResponse` |
| `backend/schemas/__init__.py` | Modified | Exported pose schemas |
| `backend/services/head_pose_estimator.py` | Created | PnP solver, canonical 3D model, Euler extraction, and classification |
| `backend/services/__init__.py` | Modified | Exported head pose estimator service and exceptions |
| `backend/main.py` | Modified | Added `POST /api/faces/pose` endpoint and `HeadPoseEstimationError` handler; updated version to 0.3.0 |
| `backend/tests/test_head_pose.py` | Created | 9 comprehensive tests for head pose estimation, classification, and error cases |
| `docs/architecture.md` | Modified | Updated architecture diagram and component interaction descriptions for Phase 3 |
| `docs/implementation-roadmap.md` | Modified | Marked Phase 3 as Completed |
| `README.md` | Modified | Updated project structure, API endpoints, roadmap, and status |
| `docs/phase-reports/phase-3.md` | Created | Comprehensive Phase 3 verification report |

---

## 12. Status

- **Phase 3 Status**: **COMPLETED**
- **Verification Result**: 33 / 33 automated tests passing. Live endpoint verified.
- **Next Phase**: Phase 4 – Loomis Construction Engine (pending user review).

