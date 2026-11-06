"""Unit and integration tests for Head Pose Estimation (Phase 3)."""

import io
import pytest
from fastapi.testclient import TestClient
from PIL import Image, ImageDraw

from backend.main import app
from backend.schemas.landmark import FacialLandmark
from backend.schemas.pose import HeadOrientation
from backend.services.head_pose_estimator import (
    HeadPoseEstimatorService,
    InsufficientLandmarksError,
    PoseSolverError,
    classify_orientation,
    get_head_pose_estimator_service,
)

client = TestClient(app)


# ---------------------------------------------------------------------------
# Synthetic Test Image Fixtures (No personal images)
# ---------------------------------------------------------------------------


def _create_synthetic_frontal_face(size: tuple[int, int] = (400, 400)) -> bytes:
    """Generate a clean synthetic frontal portrait."""
    img = Image.new("RGB", size, color=(240, 240, 240))
    draw = ImageDraw.Draw(img)

    # Cranium / face oval
    draw.ellipse([100, 50, 300, 350], fill=(230, 190, 160), outline=(100, 70, 50), width=3)
    # Eyes (centered horizontally around x=200)
    draw.ellipse([140, 140, 170, 160], fill=(40, 40, 40))
    draw.ellipse([230, 140, 260, 160], fill=(40, 40, 40))
    # Eyebrows
    draw.line([(135, 130), (175, 130)], fill=(40, 40, 40), width=4)
    draw.line([(225, 130), (265, 130)], fill=(40, 40, 40), width=4)
    # Nose (centered at x=200)
    draw.polygon([(200, 170), (190, 220), (210, 220)], fill=(200, 150, 120))
    # Mouth (centered at x=200)
    draw.arc([160, 240, 240, 280], start=0, end=180, fill=(180, 50, 50), width=4)

    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def _create_synthetic_turned_right_face(size: tuple[int, int] = (400, 400)) -> bytes:
    """Generate a synthetic portrait turned toward viewer's right (subject's left)."""
    img = Image.new("RGB", size, color=(240, 240, 240))
    draw = ImageDraw.Draw(img)

    draw.ellipse([100, 50, 300, 350], fill=(230, 190, 160), outline=(100, 70, 50), width=3)
    # Features shifted rightward
    draw.ellipse([170, 140, 200, 160], fill=(40, 40, 40))
    draw.ellipse([250, 140, 275, 160], fill=(40, 40, 40))
    draw.line([(165, 130), (205, 130)], fill=(40, 40, 40), width=4)
    draw.line([(245, 130), (280, 130)], fill=(40, 40, 40), width=4)
    draw.polygon([(230, 170), (220, 220), (240, 220)], fill=(200, 150, 120))
    draw.arc([190, 240, 260, 280], start=0, end=180, fill=(180, 50, 50), width=4)

    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def _create_synthetic_turned_left_face(size: tuple[int, int] = (400, 400)) -> bytes:
    """Generate a synthetic portrait turned toward viewer's left (subject's right)."""
    img = Image.new("RGB", size, color=(240, 240, 240))
    draw = ImageDraw.Draw(img)

    draw.ellipse([100, 50, 300, 350], fill=(230, 190, 160), outline=(100, 70, 50), width=3)
    # Features shifted leftward
    draw.ellipse([125, 140, 150, 160], fill=(40, 40, 40))
    draw.ellipse([200, 140, 230, 160], fill=(40, 40, 40))
    draw.line([(120, 130), (155, 130)], fill=(40, 40, 40), width=4)
    draw.line([(195, 130), (235, 130)], fill=(40, 40, 40), width=4)
    draw.polygon([(170, 170), (160, 220), (180, 220)], fill=(200, 150, 120))
    draw.arc([140, 240, 210, 280], start=0, end=180, fill=(180, 50, 50), width=4)

    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def _create_blank_image(size: tuple[int, int] = (400, 400)) -> bytes:
    """Generate an image without human facial features."""
    img = Image.new("RGB", size, color="white")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


# ---------------------------------------------------------------------------
# API Integration Tests
# ---------------------------------------------------------------------------


def test_valid_front_facing_portrait():
    """Verify pose estimation on a frontal portrait returns 200 OK and FRONT orientation."""
    image_bytes = _create_synthetic_frontal_face()

    response = client.post(
        "/api/faces/pose",
        files={"file": ("front.jpg", image_bytes, "image/jpeg")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["orientation"] == HeadOrientation.FRONT.value

    # Frontal yaw should be close to 0 (|yaw| <= 15 deg)
    assert abs(data["yaw_degrees"]) <= 15.0

    # Confidence should be reasonable
    assert 0.0 <= data["confidence"] <= 1.0
    assert data["confidence"] > 0.4

    # Check quality metrics presence
    assert "quality_metrics" in data
    assert data["quality_metrics"]["mean_reprojection_error_px"] >= 0.0
    assert data["quality_metrics"]["landmarks_used_count"] == 8


def test_valid_turned_right_portrait():
    """Verify pose estimation on face turned toward viewer's right returns THREE_QUARTER_RIGHT."""
    image_bytes = _create_synthetic_turned_right_face()

    response = client.post(
        "/api/faces/pose",
        files={"file": ("right.jpg", image_bytes, "image/jpeg")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["orientation"] in (
        HeadOrientation.THREE_QUARTER_RIGHT.value,
        HeadOrientation.PROFILE_RIGHT.value,
    )
    # Turned right corresponds to negative yaw
    assert data["yaw_degrees"] < -15.0


def test_valid_turned_left_portrait():
    """Verify pose estimation on face turned toward viewer's left returns THREE_QUARTER_LEFT."""
    image_bytes = _create_synthetic_turned_left_face()

    response = client.post(
        "/api/faces/pose",
        files={"file": ("left.jpg", image_bytes, "image/jpeg")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["orientation"] in (
        HeadOrientation.THREE_QUARTER_LEFT.value,
        HeadOrientation.PROFILE_LEFT.value,
    )
    # Turned left corresponds to positive yaw
    assert data["yaw_degrees"] > 15.0


def test_no_face_image_returns_400():
    """Verify that uploading an image without a face returns HTTP 400 Bad Request."""
    blank_bytes = _create_blank_image()

    response = client.post(
        "/api/faces/pose",
        files={"file": ("blank.jpg", blank_bytes, "image/jpeg")},
    )

    assert response.status_code == 400
    data = response.json()
    assert "no human face detected" in data["detail"].lower()


def test_invalid_image_inputs():
    """Verify that empty, corrupted, and unsupported files return appropriate errors."""
    # 1. Empty file -> 400
    r_empty = client.post(
        "/api/faces/pose",
        files={"file": ("empty.jpg", b"", "image/jpeg")},
    )
    assert r_empty.status_code == 400
    assert "empty" in r_empty.json()["detail"].lower()

    # 2. Corrupted file -> 400
    r_corrupt = client.post(
        "/api/faces/pose",
        files={"file": ("corrupt.jpg", b"invalidcorruptedimagebytes", "image/jpeg")},
    )
    assert r_corrupt.status_code == 400

    # 3. Unsupported format (GIF) -> 415
    gif_img = Image.new("RGB", (100, 100), color="red")
    buf = io.BytesIO()
    gif_img.save(buf, format="GIF")
    r_gif = client.post(
        "/api/faces/pose",
        files={"file": ("anim.gif", buf.getvalue(), "image/gif")},
    )
    assert r_gif.status_code == 415


def test_output_schema_and_numeric_ranges():
    """Verify complete output schema fields and strict numeric boundary compliance."""
    image_bytes = _create_synthetic_frontal_face()

    response = client.post(
        "/api/faces/pose",
        files={"file": ("portrait.jpg", image_bytes, "image/jpeg")},
    )

    assert response.status_code == 200
    data = response.json()

    # Required fields
    for field in [
        "success",
        "message",
        "yaw_degrees",
        "pitch_degrees",
        "roll_degrees",
        "orientation",
        "confidence",
        "quality_metrics",
        "rotation_vector",
        "translation_vector",
    ]:
        assert field in data, f"Missing field: {field}"

    # Numeric range validations
    assert -180.0 <= data["yaw_degrees"] <= 180.0
    assert -90.0 <= data["pitch_degrees"] <= 90.0
    assert -180.0 <= data["roll_degrees"] <= 180.0
    assert 0.0 <= data["confidence"] <= 1.0

    # Quality metrics
    qm = data["quality_metrics"]
    assert qm["mean_reprojection_error_px"] >= 0.0
    assert qm["face_width_px"] > 0.0
    assert qm["face_height_px"] > 0.0
    assert qm["landmarks_used_count"] == 8

    # Vectors
    assert len(data["rotation_vector"]) == 3
    assert len(data["translation_vector"]) == 3


# ---------------------------------------------------------------------------
# Unit Tests for HeadPoseEstimatorService
# ---------------------------------------------------------------------------


def test_orientation_classification_thresholds():
    """Verify categorical classification thresholds across yaw angles."""
    # Front: |yaw| <= 15
    assert classify_orientation(0.0) == HeadOrientation.FRONT
    assert classify_orientation(10.5) == HeadOrientation.FRONT
    assert classify_orientation(-14.9) == HeadOrientation.FRONT
    assert classify_orientation(15.0) == HeadOrientation.FRONT
    assert classify_orientation(-15.0) == HeadOrientation.FRONT

    # Three-quarter left: 15 < yaw <= 45
    assert classify_orientation(15.1) == HeadOrientation.THREE_QUARTER_LEFT
    assert classify_orientation(30.0) == HeadOrientation.THREE_QUARTER_LEFT
    assert classify_orientation(45.0) == HeadOrientation.THREE_QUARTER_LEFT

    # Profile left: yaw > 45
    assert classify_orientation(45.1) == HeadOrientation.PROFILE_LEFT
    assert classify_orientation(75.0) == HeadOrientation.PROFILE_LEFT

    # Three-quarter right: -45 <= yaw < -15
    assert classify_orientation(-15.1) == HeadOrientation.THREE_QUARTER_RIGHT
    assert classify_orientation(-30.0) == HeadOrientation.THREE_QUARTER_RIGHT
    assert classify_orientation(-45.0) == HeadOrientation.THREE_QUARTER_RIGHT

    # Profile right: yaw < -45
    assert classify_orientation(-45.1) == HeadOrientation.PROFILE_RIGHT
    assert classify_orientation(-80.0) == HeadOrientation.PROFILE_RIGHT


def test_missing_or_insufficient_landmarks():
    """Verify that InsufficientLandmarksError is raised when required keypoints are missing."""
    service = get_head_pose_estimator_service()

    # 1. Empty landmarks list
    with pytest.raises(InsufficientLandmarksError):
        service.estimate_pose(landmarks=[], image_width=400, image_height=400)

    # 2. Only 3 landmarks (missing required 8 keypoints)
    partial_landmarks = [
        FacialLandmark(index=1, x=0.5, y=0.5, z=0.0, pixel_x=200.0, pixel_y=200.0),
        FacialLandmark(index=152, x=0.5, y=0.8, z=0.0, pixel_x=200.0, pixel_y=320.0),
        FacialLandmark(index=33, x=0.35, y=0.35, z=0.0, pixel_x=140.0, pixel_y=140.0),
    ]
    with pytest.raises(InsufficientLandmarksError):
        service.estimate_pose(landmarks=partial_landmarks, image_width=400, image_height=400)


def test_pose_solver_error_handling():
    """Verify that PoseSolverError is raised when PnP calculation encounters invalid coordinates."""
    nan_landmarks = [
        FacialLandmark(
            index=idx,
            x=float("nan"),
            y=float("nan"),
            z=0.0,
            pixel_x=float("nan"),
            pixel_y=float("nan"),
        )
        for idx in [1, 152, 33, 263, 61, 291, 10, 168]
    ]

    service = get_head_pose_estimator_service()
    with pytest.raises(PoseSolverError):
        service.estimate_pose(nan_landmarks, image_width=400, image_height=400)
