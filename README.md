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
| **Landmark Detection** | MediaPipe Face Landmarker | High-density 3D facial mesh coordinate detection |
| **Image & Geometry** | OpenCV (`cv2`), NumPy | Image normalization, matrix transformations, geometric projections, line rendering |
| **Drawing Engine** | Custom Geometry Algorithms | Mathematical Loomis cranium sphere and guide generation |
| **Web Frontend** | React, Modern Bundler (Vite), CSS | Interactive drawing tutor UI, canvas overlays, step viewer |
| **Mobile App (Future)** | React Native, Expo | Cross-platform tablet and mobile application |
| **Testing & CI** | Pytest, Jest / Vitest | Automated backend and frontend test suites |

---

## 📁 Project Structure

```text
loomis-ai/
├── backend/
│   ├── models/            # Domain entities, schemas, and landmark data models
│   ├── services/          # Computer vision, geometry calculation, and stage generation services
│   ├── outputs/           # Temporary processed images and generated visual stages
│   └── tests/             # Backend unit and integration tests
├── frontend/
│   └── src/
│       ├── components/    # Reusable UI components (Canvas, Stepper, Opacity Slider)
│       ├── pages/         # Application views (Home, Tutorial View, Result View)
│       ├── services/      # API client and networking
│       ├── styles/        # Global styles and theme configurations
│       └── assets/        # Static assets, icons, and illustration resources
├── mobile/                # Future React Native / Expo application
├── docs/                  # Architecture, specifications, and ML methodology
│   └── phase-reports/     # Granular verification reports for each project phase
├── tests/                 # End-to-end integration tests
├── README.md              # Project documentation and setup guide
└── .gitignore             # Environment, build, and private data exclusion rules
```

---

## 🗺️ Development Roadmap

- **Phase 0: Project Foundation** *(Current)* – Directory structure, specifications, architecture blueprints, repository standards.
- **Phase 1: Image Upload and Preprocessing** – Secure file upload API, format validation, orientation correction, and image resizing.
- **Phase 2: Face Detection** – Face detection validation, bounding box extraction, and multi-face rejection.
- **Phase 3: Facial Landmarks and Head Pose Estimation** – MediaPipe Face Landmarker integration, 3D coordinate mapping, and pitch/yaw/roll computation.
- **Phase 4: Loomis Construction Engine** – Mathematical cranium sphere calculation, lateral cut plane fitting, and facial thirds line generation.
- **Phase 5: Progressive Drawing Generation** – Visual rendering of progressive drawing stages with vector and raster overlays.
- **Phase 6: Drawing Tutorial Engine** – Instructional copy synthesis, contextual drawing tips, and step-by-step guidance payload.
- **Phase 7: React Web Interface** – Modern web client with upload dropzone, interactive step player, and overlay opacity slider.
- **Phase 8: Backend Integration and Testing** – End-to-end API integration, automated testing, error recovery, and benchmark validation.
- **Phase 9: React Native Mobile Application** – Expo mobile application supporting phone and tablet drawing workflows.
- **Phase 10: Advanced Improvements** – Hair volume approximations, simplified plane shading guides, and user drawing feedback.

---

## 🚦 Current Development Status

- **Current Phase**: **Phase 0 – Project Foundation**
- **Status**: Completed
- **Next Phase**: Phase 1 – Image Upload and Preprocessing (pending review and approval)

