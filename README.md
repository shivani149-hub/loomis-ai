# Loomis AI – An AI-Powered Step-by-Step Portrait Drawing Tutor

An intelligent, computer-vision-assisted drawing tutor that decomposes any portrait photograph into progressive, step-by-step construction guidelines based on the classical **Andrew Loomis Head Construction Method**.

---

## 📌 Problem Statement

Drawing the human head accurately is one of the most demanding disciplines in representational art. Novices and aspiring artists frequently encounter fundamental roadblocks:

1. **Spatial & Proportional Misjudgment**: Translating a complex three-dimensional anatomical volume onto a flat two-dimensional surface leads to distorted proportions, misaligned facial features, and perspective warping.
2. **Abstract Application of Academic Methods**: Classical drawing literature—most notably Andrew Loomis's seminal text *Drawing the Head and Hands*—offers a rigorous geometric framework (the Loomis Method) based on a cranium sphere, flattened temporal planes, and divided facial thirds. However, beginners struggle to project these abstract geometric guides onto real-world portrait photographs with diverse facial structures, camera angles, and head tilts.
3. **Lack of Adaptive Step-by-Step Guidance**: Existing drawing apps either provide static, non-adaptive video tutorials or apply trivial edge-detection filters that trace final lines without teaching the underlying structure and volumetric construction.

---

## 🎯 Project Objectives

Loomis AI bridges classical fine art pedagogy and modern computer vision:

- **Automated Portrait Analysis**: Detect face orientation, 3D landmarks, and head rotation from user-uploaded portrait photos.
- **Parametric Loomis Construction**: Algorithmic calculation of the fundamental Loomis scaffolding (cranium sphere, lateral disc cutoffs, facial thirds axis, jaw cradle, and central vertical axis).
- **Progressive Stage Generation**: Systematically deconstruct the portrait into progressive drawing stages (from initial sphere to feature placement and outline contours).
- **Interactive Instruction**: Deliver bite-sized, contextual drawing steps with adjustable guide opacity to help students practice on paper or digital tablets.
- **Extensible Architecture**: Provide a high-performance Python/FastAPI backend, a responsive React web interface, and future React Native (Expo) mobile compatibility.

---

## 🚀 Planned Features

- **Photo Ingestion & Validation**: Quality checks, single-face validation, resolution normalization, and pose suitability detection.
- **3D Landmark & Pose Detection**: Sub-millimeter landmark extraction (MediaPipe Face Landmarker) and robust head pose estimation (pitch, yaw, and roll).
- **Loomis Geometric Synthesis Engine**: Custom algorithmic projection of 3D cranium spheres, side ellipses, brow lines, hairline, nose base, and jaw contours fitted precisely to the individual subject.
- **Progressive Multi-Stage Tutor**:
  - **Stage 1**: Cranium Sphere & Primary Tilt Axis.
  - **Stage 2**: Lateral Plane Flattening (Side Discs & Crosshairs).
  - **Stage 3**: Central Division & Facial Thirds (Hairline, Brow Line, Nose Base).
  - **Stage 4**: Jawline Cradle & Chin Block.
  - **Stage 5**: Feature Placement Guidelines (Eye Sockets, Nose Wedge, Mouth Axis, Ear Placement).
  - **Stage 6**: Final Structural Contours & Key Proportions.
- **Interactive Web Interface**: Stepper-based navigation, toggleable guide layers, reference photo opacity slider, and contextual drawing tips.
- **Future Mobile Support**: React Native with Expo for mobile and tablet drawing sessions.

---

## 🛠️ Technology Stack

| Layer | Technologies | Role / Description |
|---|---|---|
| **Backend** | Python 3.10+, FastAPI, Uvicorn | RESTful API service, pipeline orchestration |
| **Landmark Detection** | MediaPipe Face Landmarker (Tasks API) | 478 dense 3D facial mesh coordinates in IMAGE running mode |
| **Image & Geometry** | Pillow, OpenCV, NumPy | In-memory image processing, matrix transformations, coordinate scaling |
| **Drawing Engine** | Custom Geometry Algorithms | Mathematical Loomis cranium sphere and guide generation (Phase 4) |
| **Web Frontend** | React, Modern Bundler (Vite), CSS | Interactive drawing tutor UI, canvas overlays, step viewer (Phase 7) |
| **Mobile App (Future)** | React Native, Expo | Cross-platform tablet and mobile application (Phase 9) |
| **Testing & CI** | Pytest, FastAPI TestClient (HTTPX) | Automated backend test suite (24 passing tests) |

---

## 📁 Project Structure

```text
loomis-ai/
├── backend/
│   ├── main.py            # FastAPI application entry point, lifecycle management & route handlers
│   ├── requirements.txt   # Pinned Python backend dependencies
│   ├── README.md          # Backend guide and setup walkthrough
│   ├── models/            # MediaPipe model assets
│   │   ├── face_landmarker.task  # Official MediaPipe Face Landmarker Tasks model
│   │   └── .gitkeep
│   ├── schemas/           # Pydantic schemas
│   │   ├── health.py      # HealthResponse
│   │   ├── image.py       # ImagePreprocessResponse
│   │   └── landmark.py    # FacialLandmark & FaceLandmarksResponse
│   ├── services/          # Core domain services
│   │   ├── image_validator.py  # Content-based format, dimension, and size validation
│   │   ├── image_processor.py  # EXIF rotation, RGB normalization, aspect-ratio resizing
│   │   └── face_detector.py    # MediaPipe Face Landmarker inference & single-face policy
│   ├── outputs/           # Ephemeral processed session artifacts (git-ignored)
│   │   └── .gitkeep
│   └── tests/             # Automated test suite
│       ├── test_health.py           # Health check endpoint tests
│       ├── test_image_upload.py     # Image upload, validation, and resizing tests
│       └── test_face_detection.py   # Landmark extraction, error handling, coordinate math tests
├── frontend/
│   └── src/
│       ├── components/    # Reusable UI components (Canvas, Stepper, Opacity Slider)
│       ├── pages/         # Application views (Home, Tutorial View, Result View)
│       ├── services/      # API client and networking
│       ├── styles/        # Global styles and theme configurations
│       └── assets/        # Static assets, icons, and illustration resources
├── mobile/                # Future React Native / Expo application
├── docs/                  # Architecture, specifications, and ML methodology
│   ├── architecture.md
│   ├── implementation-roadmap.md
│   ├── ml-methodology.md
│   ├── project-overview.md
│   └── phase-reports/     # Granular verification reports for each project phase
│       ├── phase-0.md     # Phase 0 verification report
│       ├── phase-1.md     # Phase 1 verification report
│       └── phase-2.md     # Phase 2 verification report
├── tests/                 # End-to-end integration tests
├── requirements.txt       # Root convenience pointer to backend/requirements.txt
├── README.md              # Project documentation and setup guide
└── .gitignore             # Environment, build, and private data exclusion rules
```

---

## 💻 Local Setup & Development

### 1. Python Virtual Environment Setup

Ensure Python 3.10+ (tested on Python 3.12.5) is installed.

#### On Windows (PowerShell):
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt
```

#### On Windows (Command Prompt `cmd`):
```cmd
python -m venv .venv
.venv\Scripts\activate.bat
pip install -r backend/requirements.txt
```

#### On macOS / Linux:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```

### 2. MediaPipe Model Asset

The official MediaPipe Face Landmarker model asset is located at:
`backend/models/face_landmarker.task`

If downloading manually or configuring in CI/CD:
```bash
curl -o backend/models/face_landmarker.task https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task
```

### 3. Running the Backend Server

```bash
uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```
- API Base: `http://127.0.0.1:8000`
- Interactive API Docs (Swagger UI): `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

### 4. Running Automated Tests

```bash
python -m pytest backend/tests -v
```

---

## 📡 API Endpoints (Phase 2)

| Method | Endpoint | Description | Status Code |
|---|---|---|---|
| `GET` | `/api/health` | Service health status check | `200 OK` |
| `POST` | `/api/images/preprocess` | In-memory image ingestion, orientation correction, and resizing | `200 OK` |
| `POST` | `/api/faces/detect` | MediaPipe Face Landmarker detection, single-face validation, and 478 3D landmark extraction | `200 OK` |

---

## 🧠 What MediaPipe Does vs. What It Does Not Do

| Capability | MediaPipe Face Landmarker | Custom Loomis AI Engine (Phases 3–6) |
|---|:---:|:---:|
| 3D Surface Mesh Extraction (478 points) | ✅ YES | Uses MediaPipe coordinates |
| Real-time inference (<50ms on CPU) | ✅ YES | Integrated in pipeline |
| Cranium Sphere Estimation | ❌ NO | ✅ Custom 3D least-squares fitting |
| Lateral Temporal Cut-Planes | ❌ NO | ✅ Custom perspective ellipse projection |
| Classical Facial Thirds Axis | ❌ NO | ✅ Custom anatomical proportion solver |
| Progressive Step-by-Step Drawing Steps | ❌ NO | ✅ Staged rendering engine |
| Pedagogical Art Guidance & Instructions | ❌ NO | ✅ Contextual tutorial engine |

---

## 🗺️ Development Roadmap

- **Phase 0: Project Foundation** *(Completed)* – Directory structure, specifications, architecture blueprints, repository standards.
- **Phase 1: Image Upload and Preprocessing** *(Completed)* – Secure in-memory file upload API, content-based validation, EXIF orientation correction, and aspect-ratio-preserving resizing.
- **Phase 2: Face Detection and Landmark Extraction** *(Completed)* – MediaPipe Face Landmarker Tasks API integration, single-face policy validation, 478 dense 3D landmarks extraction, and normalized to pixel coordinate conversion.
- **Phase 3: Facial Landmarks and Head Pose Estimation** – 3D head pose orientation (pitch, yaw, roll) and facial symmetry vectors.
- **Phase 4: Loomis Construction Engine** – Mathematical cranium sphere calculation, lateral cut plane fitting, and facial thirds line generation.
- **Phase 5: Progressive Drawing Generation** – Visual rendering of progressive drawing stages with vector and raster overlays.
- **Phase 6: Drawing Tutorial Engine** – Instructional copy synthesis, contextual drawing tips, and step-by-step guidance payload.
- **Phase 7: React Web Interface** – Modern web client with upload dropzone, interactive step player, and overlay opacity slider.
- **Phase 8: Backend Integration and Testing** – End-to-end API integration, automated testing, error recovery, and benchmark validation.
- **Phase 9: React Native Mobile Application** – Expo mobile application supporting phone and tablet drawing workflows.
- **Phase 10: Advanced Improvements** – Hair volume approximations, simplified plane shading guides, and user drawing feedback.

---

## 🚦 Current Development Status

- **Current Phase**: **Phase 2 – Face Detection and Landmark Extraction**
- **Status**: Completed (24 / 24 automated tests passing; live endpoints verified)
- **Next Phase**: Phase 3 – Facial Landmarks and Head Pose Estimation (pending review and approval)
