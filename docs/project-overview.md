# Loomis AI – Project Overview

## 1. Executive Summary & Vision

**Loomis AI** is an intelligent, computer-vision-assisted drawing tutor designed to help artists, illustrators, and beginners master the art of portrait drawing. By translating any portrait photograph into progressive, step-by-step structural guidelines based on the renowned **Andrew Loomis Head Construction Method**, the system transforms complex anatomy into intuitive, constructible geometric forms.

Unlike traditional photo filters that merely generate edge traces or posterized outlines, Loomis AI teaches the **underlying three-dimensional volume** of the human head, fostering genuine artistic comprehension and spatial drawing skills.

---

## 2. Artistic Background: The Andrew Loomis Method

Developed by American illustrator and art educator Andrew Loomis in his classic 1943 treatise *Drawing the Head and Hands*, the Loomis Method remains one of the gold standards of academic portraiture:

1. **The Cranial Sphere**: The cranium is conceptualized as a solid sphere, representing the cranial ball.
2. **Flattened Temporal Sides**: Because the human head is narrower on the sides than from front-to-back, the lateral walls of the sphere are sliced off, producing flat circular planes (the temporal/ear planes).
3. **The Facial Axis & Brow Line**: A brow line wraps around the sphere horizontally, intersecting a vertical central axis dividing the face into bilateral halves.
4. **The Rule of Thirds**: The lower two-thirds of the head and the jaw are established by dividing the face into three equal measurements:
   - **Hairline to Brow Line**
   - **Brow Line to Bottom of the Nose**
   - **Bottom of the Nose to Tip of the Chin**
5. **Jaw and Facial Plane Droop**: From the temporal discs, lines drop down to cradle the jaw and establish the chin block.
6. **Feature Anchoring**: Features (eyes, nose wedge, mouth, ears) are placed along the structural intersections.

While simple in concept, novices frequently struggle when trying to apply this method to arbitrary reference photos because real faces have distinct tilts, camera perspectives, asymmetrical angles, and varying facial proportions. Loomis AI automates this geometric projection mathematically while preserving Loomis's pedagogical logic.

---

## 3. Expected User Workflow

The end-to-end user experience is designed to be streamlined, intuitive, and focused on drawing practice:

```
[User Uploads Photo]
        │
        ▼
[Image Validation & Quality Check] ───(If Invalid)──► [Prompt with clear error/advice]
        │
        ▼ (Valid)
[3D Landmark Detection (MediaPipe)]
        │
        ▼
[Pose & Loomis Geometry Synthesis]
        │
        ▼
[Progressive Stage Generation (1-6)]
        │
        ▼
[Interactive Web / Mobile Drawing Tutor View]
        │
        ├── Step navigation (Stage 1 through Stage 6)
        ├── Opacity adjustment slider (Reference photo vs. Guidelines)
        ├── Guideline visibility toggles (Cranium, Thirds, Facial Features)
        └── Pedagogical drawing tips per stage
        │
        ▼
[Practice & Optional Export (PNG/SVG/PDF)]
```

### Step 1: Image Ingestion
- The user uploads a portrait photograph (via drag-and-drop on the web or gallery/camera picker on mobile).
- The system checks that the image contains a clear, single face with adequate illumination and reasonable orientation.

### Step 2: Computer Vision & Geometric Analysis
- The backend normalizes the image, detects 3D facial landmarks using the MediaPipe Face Landmarker, and estimates the head's rotational pose (pitch, yaw, and roll).
- The custom Loomis engine computes the center, radius, and orientation of the cranium sphere, locates the temporal cut planes, and calculates the facial thirds lines.

### Step 3: Progressive Stage Generation
- The backend synthesizes 6 progressive drawing stages, each accompanied by concise, beginner-friendly instructional text explaining what to draw and what spatial landmarks to observe.

### Step 4: Interactive Drawing Session
- The user is presented with the interactive tutorial interface.
- They can flip through stages 1 to 6 as they sketch on paper or in digital software.
- The user can adjust an opacity slider comparing their reference photo directly beneath the Loomis guides, or toggle specific guidelines on and off.

### Step 5: Export & Archive
- Users can export the step-by-step sheets or composite overlays as PNG or SVG files to use on drawing tablets or print for physical tracing and practice.

---

## 4. Key Application Features

### A. Intelligent Portrait Ingestion & Verification
- Validates file type, image resolution, and single-face presence.
- Flags severe occlusions, extreme lighting, or multiple faces, providing actionable feedback (e.g., *"Please provide a well-lit photo with a single visible face"*).

### B. Parametric Loomis Geometry Engine
- Extracts 3D facial landmarks and derives the head pose.
- Derives the 3D cranium sphere center and radius fitted to cranial landmarks.
- Computes the side plane cut-offs (represented as perspective ellipses based on yaw and pitch).
- Generates the brow line, hair line, nose base, and chin level conforming to the subject's unique anatomy while highlighting classical proportional ideals.

### C. 6-Stage Progressive Drawing Breakdown
- **Stage 1 – Cranium Ball**: Draw the basic sphere and the primary tilt axis.
- **Stage 2 – Side Plane & Temporal Disc**: Cut off the lateral side of the sphere and mark the temporal ellipse.
- **Stage 3 – Face Grid & Thirds**: Establish the central vertical line, brow line, hairline, and nose line.
- **Stage 4 – Jawline & Chin Frame**: Extend the jawlines down from the side disc to construct the chin box.
- **Stage 5 – Facial Feature Placement**: Anchor the eye sockets, nose pyramid, lips centerline, and ear placement.
- **Stage 6 – Contour & Characteristic Shapes**: Add refined facial contours, cheekbone curves, and primary feature outlines.

### D. Interactive Drawing Tutor UI
- **Stage Stepper**: Easily move forward and backward through construction stages.
- **Dual Display Modes**:
  - *Side-by-Side Mode*: Original photo on the left, current drawing stage on the right.
  - *Overlay Mode*: Construction lines superimposed directly over the reference photograph.
- **Opacity Slider**: Smoothly adjust reference photo opacity from 0% (pure construction lines) to 100% (full reference visibility).
- **Layer Toggles**: Individually enable or disable cranium sphere, facial grid, jaw structure, and feature anchors.
- **Educational Guidance Cards**: Clear, contextual instruction for each stage describing the artistic intent, common pitfalls, and proportional checks.

### E. Privacy-First Architecture
- Ephemeral backend storage: Uploaded images and generated temporary stages are held only for the duration of the tutorial session and automatically purged.
- No user biometric data or private photos are retained or used for model training.

