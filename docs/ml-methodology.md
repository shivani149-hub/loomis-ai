# Loomis AI – Machine Learning & Geometric Methodology

## 1. Overview & Core Philosophy

A central design principle of **Loomis AI** is the deliberate distinction between **empirical landmark observation** and **parametric geometric construction**:

- Machine learning (MediaPipe) is used strictly for **observing what is there** (detecting anatomical landmarks and surface feature locations).
- Custom 3D geometry algorithms (NumPy & OpenCV) are used for **constructing what must be drawn** (synthesizing the Andrew Loomis cranial sphere, side planes, facial thirds, and progressive construction scaffolds).

This hybrid approach ensures high mathematical precision, deterministic reproducibility, lightning-fast inference (<100ms on CPU), and strict adherence to classical art pedagogy without relying on black-box generative models for structural calculations.

---

## 2. Planned Roles of Libraries & Algorithms

| Tool / Technology | Primary Responsibility | Technical Role in Loomis AI |
|---|---|---|
| **MediaPipe Face Landmarker** | Empirical 3D Landmark Detection | Detects 478 3D facial mesh points (x, y, z in canonical coordinate space). Identifies key anatomical points (glabella, pupils, nasion, subnasale, gnathion, tragus, temples). |
| **OpenCV (`cv2`)** | Image I/O, Processing & Rendering | Image decoding, color normalization, EXIF rotation handling, affine transformation, drawing vector lines, anti-aliased curves, ellipses, and alpha-blending overlays. |
| **NumPy** | Vector Math & 3D Projections | Matrix transformations, Euler angle computations (pitch, yaw, roll), 3D-to-2D perspective projection, least-squares sphere fitting, and ellipse parameter estimation. |
| **Custom Geometry Engine** | Loomis Construction Synthesis | Bridges observed facial landmarks and Loomis geometric theory to compute the cranium sphere, temporal slice discs, central meridian, facial thirds, and progressive steps. |

---

## 3. Critical Distinction: Landmark Detection vs. Loomis Construction

It is vital to understand what pretrained computer vision models provide and where our custom algorithmic work begins:

```
+─────────────────────────────────────────────────────────+
│         MediaPipe Face Landmarker (Pretrained ML)       │
│                                                         │
│  - Outputs 478 localized 3D surface points.             │
│  - Knows where the nose tip, eyelids, and lips sit.     │
│  - Operates purely on visible facial skin surface.      │
+────────────────────────────┬────────────────────────────+
                             │ Raw Landmark Vectors
                             ▼
+─────────────────────────────────────────────────────────+
│        Custom Loomis Construction Engine (NumPy)        │
│                                                         │
│  - DOES NOT exist in MediaPipe.                         │
│  - MediaPipe cannot draw a Loomis ball or side plane.   │
│  - Solves 3D Cranium Sphere center (Xc, Yc, Zc) & R.    │
│  - Calculates temporal plane cutoff ellipses.           │
│  - Computes central facial meridian & facial thirds.   │
│  - Synthesizes jaw cradle connecting ears to chin.      │
│  - Sequentially renders 6 progressive drawing stages.   │
+─────────────────────────────────────────────────────────+
```

### What MediaPipe Does:
- Localizes surface facial features with high sub-pixel precision.
- Estimates the rigid transformation and rotation matrix of the head.
- Provides relative depth (\(z\)) coordinates for landmarks.

### What MediaPipe DOES NOT Do:
- **Does not detect the cranial ball**: The human cranium extends significantly above and behind the hairline and ears. MediaPipe landmarks terminate near the hairline and do not calculate cranial volume or skull structure beneath hair.
- **Does not generate Loomis construction lines**: MediaPipe has no concept of Andrew Loomis's method, side disc cutoffs, facial thirds guidelines, or progressive drawing stages.
- **Does not teach drawing**: It outputs raw floating-point coordinates, not pedagogical visual guidance.

### What Our Custom Geometry Engine Solves:
1. **Skull Extrapolation**: Uses anthropometric ratios and landmark anchors (glabella, tragus, temporal points) to calculate the full 3D cranium sphere, estimating the crown and occiput volume even when covered by hair.
2. **Side Disc Projections**: Calculates the plane equation of the flattened temporal sides and projects the resulting circles into 2D perspective ellipses according to the head's yaw and pitch.
3. **Harmonic Thirds Division**: Maps the classical thirds (hairline to brow, brow to nose base, nose base to chin) onto the curved volume of the head.
4. **Pedagogical Deconstruction**: Converts continuous 3D geometric coordinates into sequential, discrete 2D drawing layers that an artist can easily replicate on paper.

---

## 4. Mathematical Principles of the Loomis Engine

### 4.1 Head Pose Estimation
From key facial landmarks (pupils, nose tip, chin tip, mouth corners, ear tragi), we compute the head rotation matrix \(\mathbf{R}\) using either Perspective-n-Point (PnP) fitting against a canonical 3D facial model or direct eigenvector analysis of bilateral landmark vectors:
$$\mathbf{R} = \mathbf{R}_z(\text{roll}) \cdot \mathbf{R}_y(\text{yaw}) \cdot \mathbf{R}_x(\text{pitch})$$

### 4.2 Cranium Sphere Parameterization
The cranium sphere is defined by its center \(\mathbf{C} = (x_c, y_c, z_c)\) and radius \(R\):
- The center \(\mathbf{C}\) is offset backward along the head pose normal vector from the midpoint between the temples and brow line.
- The radius \(R\) is derived from the bizygomatic diameter and brow-to-chin distance scaled according to classical Loomis anatomical proportions.

### 4.3 Temporal Cutoff Discs
Andrew Loomis cuts off the sides of the cranial ball by approximately one-sixth of the sphere's diameter on each side:
- The side cut produces a circle of radius \(r_{side} = R \cdot \frac{\sqrt{3}}{2} \approx 0.866 R\).
- In 2D perspective projection, this circle appears as an ellipse whose eccentricity and orientation are governed by the head's yaw and pitch angles.
- The center of the side disc corresponds to the location of the ear / temporal fossa.

### 4.4 The Facial Thirds Grid
The vertical face axis follows the spherical meridian:
- **Brow Line (Equator)**: The horizontal centerline passing through the brow ridge and temporal discs.
- **Hairline**: Placed one cranial third above the brow line along the sphere's surface.
- **Nose Base Line**: Placed one unit below the brow line, tangent to the base of the cranium sphere.
- **Chin Line**: Extended one unit below the nose line, establishing the baseline for the jawline.

---

## 5. Advanced Considerations & Future Techniques

While the core Loomis engine relies on geometric projection, certain advanced artistic components may benefit from specialized computational techniques in future phases:

### 5.1 Hair Volume & Massing
- Facial landmarks terminate at the skin surface. Natural hair has substantial volume, loft, and varying silhouette.
- In **Phase 10**, hair massing will be modeled either through secondary semantic segmentation models (e.g., segmenting the hair mask to compute a volume envelope) or bounding convex hulls that surround the cranium sphere.

### 5.2 Planar Shading & Light Direction (Asaro Head)
- To help artists understand lighting, estimating the primary directional light source and projecting simplified planar light/shadow polygons (inspired by John Asaro's Planes of the Head) can be explored using surface normal analysis from 3D mesh vectors.

### 5.3 Non-Photorealistic Rendering (NPR) & Pencil Simulation
- Converting sharp mathematical vector lines into organic, human-looking pencil sketches, chalk lines, or charcoal strokes requires stroke stylization shaders, procedural noise generation, or non-photorealistic rendering (NPR) filters in OpenCV and SVG path styling.

