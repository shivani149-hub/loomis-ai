"""Head pose estimation response and diagnostic schemas."""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class HeadOrientation(str, Enum):
    """Categorical classification of head rotation angles."""

    FRONT = "FRONT"
    THREE_QUARTER_LEFT = "THREE_QUARTER_LEFT"
    THREE_QUARTER_RIGHT = "THREE_QUARTER_RIGHT"
    PROFILE_LEFT = "PROFILE_LEFT"
    PROFILE_RIGHT = "PROFILE_RIGHT"


class PoseQualityMetrics(BaseModel):
    """Diagnostic metrics reflecting landmark geometric quality and PnP stability."""

    mean_reprojection_error_px: float = Field(
        ...,
        description="Mean reprojection residual in pixels between 2D landmarks and projected 3D model",
        ge=0.0,
        examples=[4.25],
    )
    face_width_px: float = Field(
        ...,
        description="Estimated face bounding box width in pixels",
        ge=0.0,
        examples=[320.0],
    )
    face_height_px: float = Field(
        ...,
        description="Estimated face bounding box height in pixels",
        ge=0.0,
        examples=[380.0],
    )
    landmarks_used_count: int = Field(
        ...,
        description="Number of stable anatomical keypoints utilized in the PnP solver",
        ge=4,
        examples=[8],
    )


class HeadPoseResponse(BaseModel):
    """API response payload for head pose estimation."""

    success: bool = Field(
        default=True,
        description="Whether head pose estimation succeeded",
    )
    message: str = Field(
        default="Head pose estimated successfully.",
        description="Descriptive status message",
    )
    yaw_degrees: float = Field(
        ...,
        description=(
            "Yaw angle in degrees (-180 to +180). "
            "Positive = turned toward viewer's left (subject's right). "
            "Negative = turned toward viewer's right (subject's left)."
        ),
        examples=[0.4],
    )
    pitch_degrees: float = Field(
        ...,
        description=(
            "Pitch angle in degrees (-90 to +90). "
            "Negative = head tilted downwards. "
            "Positive = head tilted upwards."
        ),
        examples=[-11.4],
    )
    roll_degrees: float = Field(
        ...,
        description=(
            "Roll angle in degrees (-180 to +180). "
            "Positive = in-plane clockwise tilt. "
            "Negative = in-plane counter-clockwise tilt."
        ),
        examples=[0.3],
    )
    orientation: HeadOrientation = Field(
        ...,
        description="Categorical head orientation classification based on yaw thresholds",
        examples=[HeadOrientation.FRONT],
    )
    confidence: float = Field(
        ...,
        description="Estimated confidence score [0.0, 1.0] derived from reprojection residuals and scale",
        ge=0.0,
        le=1.0,
        examples=[0.85],
    )
    quality_metrics: Optional[PoseQualityMetrics] = Field(
        default=None,
        description="Detailed diagnostic metrics explaining the confidence score",
    )
    rotation_vector: Optional[List[float]] = Field(
        default=None,
        description="PnP 3D rotation vector (Rodrigues format) for downstream geometric projections",
    )
    translation_vector: Optional[List[float]] = Field(
        default=None,
        description="PnP 3D translation vector (X, Y, Z in camera space) for downstream geometric projections",
    )

