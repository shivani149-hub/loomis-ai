"""Head pose estimation service for Loomis AI.

Derives 3D head orientation (Yaw, Pitch, Roll) and categorical classifications
from MediaPipe facial landmarks using a canonical anthropometric 3D head model
and Perspective-n-Point (solvePnP) geometry.
"""

from dataclasses import dataclass
import math
from typing import Dict, List, Optional, Tuple
import cv2
import numpy as np

from backend.schemas.landmark import FacialLandmark
from backend.schemas.pose import HeadOrientation, PoseQualityMetrics


# ---------------------------------------------------------------------------
# Canonical 3D Head Reference Model
# ---------------------------------------------------------------------------
# Model units are in millimeters with origin (0, 0, 0) at the nose tip.
# Coordinate frame:
# - X axis: points rightward from viewer's perspective (+X = viewer right / subject left)
# - Y axis: points downward from viewer's perspective (+Y = chin / down)
# - Z axis: points into the head (+Z = away from camera)
#
# Selected stable landmarks from MediaPipe 478 face mesh:
# - Index 1: Nose tip
# - Index 152: Chin (gnathion / menton)
# - Index 33: Left eye outer corner (viewer left)
# - Index 263: Right eye outer corner (viewer right)
# - Index 61: Left mouth corner (viewer left)
# - Index 291: Right mouth corner (viewer right)
# - Index 10: Forehead top / trichion midpoint
# - Index 168: Glabella / nasal bridge midpoint
CANONICAL_KEYPOINTS: Dict[int, Tuple[float, float, float]] = {
    1: (0.0, 0.0, 0.0),          # Nose tip
    152: (0.0, 110.0, 35.0),     # Chin
    33: (-65.0, -45.0, 30.0),    # Left eye outer corner
    263: (65.0, -45.0, 30.0),    # Right eye outer corner
    61: (-40.0, 50.0, 25.0),     # Left mouth corner
    291: (40.0, 50.0, 25.0),     # Right mouth corner
    10: (0.0, -120.0, 40.0),     # Forehead top
    168: (0.0, -50.0, 15.0),     # Glabella
}


# ---------------------------------------------------------------------------
# Domain Exceptions
# ---------------------------------------------------------------------------


class HeadPoseEstimationError(Exception):
    """Base exception for head pose estimation failures."""

    def __init__(self, message: str, status_code: int = 500):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class InsufficientLandmarksError(HeadPoseEstimationError):
    """Raised when the provided landmarks are missing or lack required stable keypoints."""

    def __init__(
        self,
        message: str = (
            "Insufficient or missing facial landmarks to calculate head pose. "
            "At least the 8 canonical facial keypoints must be present."
        ),
    ):
        super().__init__(message, status_code=422)


class PoseSolverError(HeadPoseEstimationError):
    """Raised when the numerical PnP optimization fails to converge."""

    def __init__(self, details: str):
        message = f"Head pose solver failed to compute valid orientation: {details}"
        super().__init__(message, status_code=500)


# ---------------------------------------------------------------------------
# Result Data Container
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class HeadPoseResult:
    """Immutable result container holding calculated angles, orientation, and diagnostics."""

    yaw_degrees: float
    pitch_degrees: float
    roll_degrees: float
    orientation: HeadOrientation
    confidence: float
    quality_metrics: PoseQualityMetrics
    rotation_vector: List[float]
    translation_vector: List[float]


# ---------------------------------------------------------------------------
# Mathematical Helper Functions
# ---------------------------------------------------------------------------


def classify_orientation(yaw_deg: float) -> HeadOrientation:
    """Classify head orientation into standard portrait categories based on yaw angle.

    Thresholds:
    - FRONT: |yaw| <= 15.0 deg
    - THREE_QUARTER_LEFT: 15.0 deg < yaw <= 45.0 deg (subject facing viewer's left)
    - PROFILE_LEFT: yaw > 45.0 deg
    - THREE_QUARTER_RIGHT: -45.0 deg <= yaw < -15.0 deg (subject facing viewer's right)
    - PROFILE_RIGHT: yaw < -45.0 deg

    Args:
        yaw_deg: Yaw rotation in degrees.

    Returns:
        HeadOrientation category.
    """
    if abs(yaw_deg) <= 15.0:
        return HeadOrientation.FRONT
    elif 15.0 < yaw_deg <= 45.0:
        return HeadOrientation.THREE_QUARTER_LEFT
    elif yaw_deg > 45.0:
        return HeadOrientation.PROFILE_LEFT
    elif -45.0 <= yaw_deg < -15.0:
        return HeadOrientation.THREE_QUARTER_RIGHT
    else:  # yaw_deg < -45.0
        return HeadOrientation.PROFILE_RIGHT


def rotation_matrix_to_euler_angles(R: np.ndarray) -> Tuple[float, float, float]:
    """Decompose 3x3 rotation matrix into Tait-Bryan Euler angles (Pitch, Yaw, Roll).

    Coordinate convention:
    - Camera looks along +Z (into the scene) with +X right and +Y down.
    - Pitch (around X axis): vertical nod (- = down, + = up).
    - Yaw (around Y axis): lateral turn (+ = turned to viewer's left, - = turned to viewer's right).
    - Roll (around Z axis): in-plane tilt (+ = clockwise, - = counter-clockwise).

    Args:
        R: 3x3 orthogonal rotation matrix.

    Returns:
        Tuple of (pitch_deg, yaw_deg, roll_deg).
    """
    sy = math.sqrt(R[0, 0] * R[0, 0] + R[1, 0] * R[1, 0])
    singular = sy < 1e-6

    if not singular:
        pitch = math.atan2(R[2, 1], R[2, 2])
        yaw = math.atan2(-R[2, 0], sy)
        roll = math.atan2(R[1, 0], R[0, 0])
    else:
        pitch = math.atan2(-R[1, 2], R[1, 1])
        yaw = math.atan2(-R[2, 0], sy)
        roll = 0.0

    return (
        float(np.degrees(pitch)),
        float(np.degrees(yaw)),
        float(np.degrees(roll)),
    )


# ---------------------------------------------------------------------------
# Head Pose Estimator Service
# ---------------------------------------------------------------------------


class HeadPoseEstimatorService:
    """Estimates head pose orientation from 2D facial landmarks using 3D PnP geometry."""

    def __init__(self, keypoints_model: Optional[Dict[int, Tuple[float, float, float]]] = None):
        self.keypoints_model = keypoints_model or CANONICAL_KEYPOINTS

    def estimate_pose(
        self,
        landmarks: List[FacialLandmark],
        image_width: int,
        image_height: int,
    ) -> HeadPoseResult:
        """Calculate head pose orientation, Euler angles, and quality diagnostics.

        Args:
            landmarks: Dense facial mesh landmarks from Phase 2 detector.
            image_width: Pixel width of preprocessed portrait image.
            image_height: Pixel height of preprocessed portrait image.

        Returns:
            HeadPoseResult holding yaw, pitch, roll, category, confidence, and metrics.

        Raises:
            InsufficientLandmarksError: If landmarks list is empty or lacks required keypoints.
            PoseSolverError: If numerical PnP optimization fails.
        """
        if not landmarks or len(landmarks) < len(self.keypoints_model):
            raise InsufficientLandmarksError()

        # Build landmark index lookup
        lm_by_index: Dict[int, FacialLandmark] = {lm.index: lm for lm in landmarks}

        # Verify all required keypoints exist
        for idx in self.keypoints_model:
            if idx not in lm_by_index:
                raise InsufficientLandmarksError(
                    f"Required anatomical landmark index {idx} not found in landmark set."
                )

        # Assemble corresponding 3D and 2D point arrays
        sorted_indices = sorted(self.keypoints_model.keys())
        model_points = np.array([self.keypoints_model[idx] for idx in sorted_indices], dtype=np.float64)
        image_points = np.array(
            [[lm_by_index[idx].pixel_x, lm_by_index[idx].pixel_y] for idx in sorted_indices],
            dtype=np.float64,
        )

        if np.isnan(image_points).any() or np.isinf(image_points).any():
            raise PoseSolverError("Landmark coordinates contain invalid NaN or infinite values.")

        # Approximate pinhole camera intrinsic matrix
        # Focal length set to image width (typical for ~50-60 deg portrait FOV)
        focal_length = float(image_width)
        camera_matrix = np.array(
            [
                [focal_length, 0.0, float(image_width) / 2.0],
                [0.0, focal_length, float(image_height) / 2.0],
                [0.0, 0.0, 1.0],
            ],
            dtype=np.float64,
        )
        dist_coeffs = np.zeros((4, 1), dtype=np.float64)

        # Initialize extrinsic guess to frontal face position
        rvec_guess = np.zeros((3, 1), dtype=np.float64)
        tvec_guess = np.array([0.0, 0.0, float(image_width)], dtype=np.float64)

        try:
            success, rvec, tvec = cv2.solvePnP(
                model_points,
                image_points,
                camera_matrix,
                dist_coeffs,
                rvec=rvec_guess,
                tvec=tvec_guess,
                useExtrinsicGuess=True,
                flags=cv2.SOLVEPNP_ITERATIVE,
            )
        except Exception as exc:
            raise PoseSolverError(str(exc)) from exc

        if not success:
            raise PoseSolverError("PnP numerical convergence failed.")

        # Convert rotation vector to rotation matrix
        rmat, _ = cv2.Rodrigues(rvec)

        # Extract Euler angles in degrees
        pitch_deg, yaw_deg, roll_deg = rotation_matrix_to_euler_angles(rmat)

        # Categorize orientation based on yaw
        orientation = classify_orientation(yaw_deg)

        # Calculate geometric reprojection error
        projected_points, _ = cv2.projectPoints(
            model_points,
            rvec,
            tvec,
            camera_matrix,
            dist_coeffs,
        )
        residuals = np.linalg.norm(image_points - projected_points.reshape(-1, 2), axis=1)
        mean_reprojection_error = float(np.mean(residuals))

        # Calculate face bounding box scale
        all_xs = [lm.pixel_x for lm in landmarks]
        all_ys = [lm.pixel_y for lm in landmarks]
        face_width = float(max(all_xs) - min(all_xs))
        face_height = float(max(all_ys) - min(all_ys))

        # Legitimate confidence score based on residual error and face scale
        # 1. Reprojection quality: 0 px error = 1.0, 25 px error = 0.0
        q_reprojection = max(0.0, min(1.0, 1.0 - (mean_reprojection_error / 25.0)))
        # 2. Scale quality: ensures face is large enough for reliable landmarking (>150px)
        q_scale = max(0.0, min(1.0, face_width / 150.0))
        # Weighted combination
        confidence = round(float(0.75 * q_reprojection + 0.25 * q_scale), 2)
        confidence = max(0.0, min(1.0, confidence))

        quality_metrics = PoseQualityMetrics(
            mean_reprojection_error_px=round(mean_reprojection_error, 2),
            face_width_px=round(face_width, 1),
            face_height_px=round(face_height, 1),
            landmarks_used_count=len(sorted_indices),
        )

        return HeadPoseResult(
            yaw_degrees=round(yaw_deg, 2),
            pitch_degrees=round(pitch_deg, 2),
            roll_degrees=round(roll_deg, 2),
            orientation=orientation,
            confidence=confidence,
            quality_metrics=quality_metrics,
            rotation_vector=[round(float(v), 4) for v in rvec.ravel()],
            translation_vector=[round(float(v), 2) for v in tvec.ravel()],
        )


# ---------------------------------------------------------------------------
# Global Singleton
# ---------------------------------------------------------------------------

_global_head_pose_service: Optional[HeadPoseEstimatorService] = None


def get_head_pose_estimator_service() -> HeadPoseEstimatorService:
    """Retrieve or initialize the singleton HeadPoseEstimatorService instance."""
    global _global_head_pose_service
    if _global_head_pose_service is None:
        _global_head_pose_service = HeadPoseEstimatorService()
    return _global_head_pose_service
