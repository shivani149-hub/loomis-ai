"""Facial landmark and face detection response schemas."""

from typing import List
from pydantic import BaseModel, Field


class FacialLandmark(BaseModel):
    """Single 3D facial landmark with both normalized and pixel coordinates."""

    index: int = Field(
        ...,
        description="Original MediaPipe landmark index (0-477)",
        ge=0,
        examples=[0],
    )
    x: float = Field(
        ...,
        description="Normalized X coordinate in range [0.0, 1.0]",
        examples=[0.506726],
    )
    y: float = Field(
        ...,
        description="Normalized Y coordinate in range [0.0, 1.0]",
        examples=[0.601664],
    )
    z: float = Field(
        ...,
        description="Normalized Z coordinate (depth relative to face center)",
        examples=[-0.065996],
    )
    pixel_x: float = Field(
        ...,
        description="Pixel X coordinate within the preprocessed image dimension",
        examples=[518.89],
    )
    pixel_y: float = Field(
        ...,
        description="Pixel Y coordinate within the preprocessed image dimension",
        examples=[616.10],
    )


class FaceLandmarksResponse(BaseModel):
    """API response payload for face detection and landmark extraction."""

    success: bool = Field(
        default=True,
        description="Whether face detection and landmark extraction succeeded",
    )
    message: str = Field(
        default="Face detected and landmarks extracted successfully.",
        description="Descriptive status message",
    )
    image_width: int = Field(
        ...,
        description="Pixel width of the preprocessed image used for coordinate conversion",
        ge=1,
        examples=[1024],
    )
    image_height: int = Field(
        ...,
        description="Pixel height of the preprocessed image used for coordinate conversion",
        ge=1,
        examples=[1024],
    )
    faces_detected: int = Field(
        ...,
        description="Total number of faces detected in the image",
        ge=0,
        examples=[1],
    )
    landmarks: List[FacialLandmark] = Field(
        ...,
        description="Dense 478 3D facial mesh landmarks with preserved original indices",
    )

