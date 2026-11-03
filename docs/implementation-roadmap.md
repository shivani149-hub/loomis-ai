# Loomis AI – Implementation Roadmap

This roadmap defines the structured, phase-by-phase development lifecycle for the Loomis AI project. Development progresses linearly: each phase must be fully verified and documented in `docs/phase-reports/` before advancing to subsequent phases.

---

## Roadmap Overview

```
Phase 0 ──► Phase 1 ──► Phase 2 ──► Phase 3 ──► Phase 4 ──► Phase 5 ──► Phase 6 ──► Phase 7 ──► Phase 8 ──► Phase 9 ──► Phase 10
(Found.)    (Upload)    (Detect)    (Landmarks) (Loomis)    (Drawing)   (Tutorial)  (React Web) (E2E Test)  (Mobile)    (Adv. Imp.)
```

---

## Detailed Phase Breakdown

### Phase 0: Project Foundation (Completed)
- **Objective**: Establish the project directory skeleton, engineering standards, architecture blueprints, roadmap, and privacy-conscious version control configuration.
- **Key Deliverables**:
  - Clean modular directory layout (`backend/`, `frontend/`, `mobile/`, `docs/`, `tests/`).
  - Core project documentation (`README.md`, `project-overview.md`, `architecture.md`, `implementation-roadmap.md`, `ml-methodology.md`).
  - Rigorous `.gitignore` preventing user uploads, generated art, and environment files from leaking into Git.
  - Phase 0 verification report (`docs/phase-reports/phase-0.md`).
- **Acceptance Criteria**: All folders exist, documents are complete, Mermaid diagram is syntactically valid, and no application code or unused packages are prematurely introduced.
- **Status**: ✅ Completed.

---

### Phase 1: Image Upload and Preprocessing (Completed)
- **Objective**: Implement a robust in-memory image ingestion and preprocessing pipeline in FastAPI capable of receiving, validating, and normalizing portrait photographs.
- **Key Deliverables**:
  - FastAPI application entry point with `GET /api/health` and `POST /api/images/preprocess` endpoints.
  - Preprocessing service using Pillow:
    - Format validation (JPEG, PNG, WebP) based on file content, not headers.
    - EXIF orientation auto-correction using `ImageOps.exif_transpose`.
    - Long-edge dimension scaling (preserving aspect ratio) to a maximum dimension of 1024px.
    - Color profile and transparency normalization to standard 3-channel RGB.
    - Maximum upload size enforcement (10 MB) and decompression bomb protection (8192px max dim).
    - In-memory Base64 JPEG response serialization without persistent disk storage.
  - Unit tests covering 15 automated test cases across valid uploads, resizing, EXIF handling, and error states.
  - Phase 1 verification report (`docs/phase-reports/phase-1.md`).
- **Acceptance Criteria**: Uploaded photos are successfully decoded in memory, corrected for orientation, normalized in size, validated against corruption, and returned with metadata.
- **Status**: ✅ Completed.

---

### Phase 2: Face Detection
- **Objective**: Implement face detection and validation logic to verify portrait suitability before heavy processing.
- **Key Deliverables**:
  - Face detection service using MediaPipe / OpenCV.
  - Single-face constraint validation (detect and gracefully reject multi-person photos or scenes with zero faces).
  - Face bounding box extraction and framing validation (rejecting faces too small or severely cropped).
  - Clear user-facing error messages for rejected uploads.
- **Acceptance Criteria**: Pipeline reliably detects faces in reference test sets, passes valid single portraits, and rejects multi-face or zero-face images with precise error diagnostics.

---

### Phase 3: Facial Landmarks and Head Pose Estimation
- **Objective**: Extract dense 3D facial mesh coordinates and compute precise head rotation angles.
- **Key Deliverables**:
  - MediaPipe Face Landmarker integration (extracting 478 3D landmarks).
  - Landmark extraction service transforming raw normalized coordinates into metric pixel space.
  - Head pose estimation algorithm:
    - Deriving **Pitch** (vertical nod), **Yaw** (lateral turn), and **Roll** (in-plane tilt).
    - Categorizing pose into standard portrait angles (Frontal, Slight 3/4, Full 3/4, Profile, Upward/Downward tilt).
  - Visualization script saving landmark points over test portraits for visual inspection.
- **Acceptance Criteria**: Accurate 3D landmark coordinates and pose angles calculated and validated on frontal, 3/4, and tilted test portrait sets.

---

### Phase 4: Loomis Construction Engine
- **Objective**: Develop the custom mathematical algorithm that converts 3D landmarks and pose data into Andrew Loomis geometric construction scaffolding.
- **Key Deliverables**:
  - Cranium sphere estimator: Calculates 3D center and radius fitted to cranial anchor landmarks.
  - Lateral temporal cut-plane solver: Projects side discs as ellipses on the sphere based on head yaw and pitch.
  - Facial grid calculation:
    - Central vertical axis (line of symmetry curving across the spherical volume).
    - Brow line (equator of the cranium).
    - Hairline level, nose base line, and chin level conforming to classical thirds.
  - Jawline cradle and chin box geometry linking temporal cut-planes to the gnathion.
- **Acceptance Criteria**: Geometric formulas produce anatomically convincing Loomis lines accurately aligned with ground-truth anatomical features across varied head poses.

---

### Phase 5: Progressive Drawing Generation
- **Objective**: Systematically generate progressive visual stages (from initial sphere to full outline) as clean, renderable visual layers.
- **Key Deliverables**:
  - Staged rendering engine outputting both vector SVG elements and raster PNG overlays.
  - Distinct drawing stages:
    - **Stage 1**: Cranium Sphere & Main Tilt Axis.
    - **Stage 2**: Lateral Temporal Discs & Crosshairs.
    - **Stage 3**: Central Division & Facial Thirds.
    - **Stage 4**: Jawline Cradle & Chin Plane.
    - **Stage 5**: Feature Placement Guides (Eye sockets, nose wedge, mouth line, ear envelope).
    - **Stage 6**: Refined Structural Contours.
  - High-contrast visual styling designed specifically for clarity in instructional drawing.
- **Acceptance Criteria**: High-resolution, multi-stage visual artifacts generated for test portraits and stored in session output directories.

---

### Phase 6: Drawing Tutorial Engine
- **Objective**: Build the pedagogical text and tutorial metadata service that pairs each visual stage with instructional guidance.
- **Key Deliverables**:
  - Context-aware instruction generator: Produces dynamic instructions customized to the subject's pose (e.g., explaining foreshortened features in 3/4 views).
  - Proportional self-check prompts (e.g., *"Verify that the distance from brow to nose base matches hairline to brow"*).
  - Structured JSON API response combining stage imagery, SVG paths, step numbers, and educational tips.
- **Acceptance Criteria**: Comprehensive API payload returned containing all progressive stages and accompanying instructional copy.

---

### Phase 7: React Web Interface
- **Objective**: Build an intuitive, responsive React web application that delivers the interactive drawing tutor experience.
- **Key Deliverables**:
  - Drag-and-drop image upload dropzone with real-time feedback.
  - Interactive stage stepper (Next / Previous / Jump to stage).
  - Canvas overlay component supporting:
    - Adjustable reference image opacity slider (0% to 100%).
    - Toggleable guide layers (Sphere, Thirds, Jaw, Features).
    - Side-by-side comparison mode.
  - Educational instructional card displaying tips and proportional checks for the current stage.
- **Acceptance Criteria**: Web client runs smoothly, connects to the backend API, and provides a delightful drawing session experience.

---

### Phase 8: Backend Integration and Testing
- **Objective**: Conduct rigorous end-to-end integration, performance benchmarking, and edge-case handling across the full stack.
- **Key Deliverables**:
  - Automated integration test suite covering the entire pipeline from upload to stage generation.
  - Performance profiling and optimization (ensuring total processing time < 2.5 seconds per portrait).
  - Edge-case resilience (unusual hairstyles, glasses, beards, extreme angles, low lighting).
  - Comprehensive API documentation and automated test verification reports.
- **Acceptance Criteria**: Test suite achieves >85% code coverage, pipeline processes test matrices without crashes, and responses stay within performance budgets.

---

### Phase 9: React Native Mobile Application
- **Objective**: Extend Loomis AI to mobile and tablet platforms with a touch-first React Native (Expo) application.
- **Key Deliverables**:
  - Expo-based React Native codebase inside `mobile/`.
  - Camera capture and photo library picker integration.
  - Touch-optimized stage stepper and gesture-driven canvas (pinch-to-zoom, pan).
  - Stylus-friendly drawing overlay mode designed for tablets (iPad with Apple Pencil, Android tablets with S-Pen).
- **Acceptance Criteria**: Mobile application compiles and runs on iOS and Android simulators, communicating seamlessly with the Loomis AI backend.

---

### Phase 10: Advanced Improvements
- **Objective**: Expand the tutor's capabilities with advanced artistic enhancements and intelligent sketch feedback.
- **Key Deliverables**:
  - Hair volume and massing geometric blocks.
  - Simplified planar shading and shadow shape indicators (Asaro head-inspired planar breakdown).
  - Stylized digital pencil and charcoal line rendering.
  - Experimental user drawing comparison: Allowing users to upload their sketch and receive alignment feedback against the Loomis construction lines.
- **Acceptance Criteria**: Experimental features documented, benchmarked, and optionally enabled via API flags.

