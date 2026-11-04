"""Unit and integration tests for Face Detection and Landmark Extraction (Phase 2)."""

import io
import pytest
from fastapi.testclient import TestClient
from PIL import Image, ImageDraw

from backend.main import app
from backend.services.face_detector import (
    FaceDetectorService,
    ModelNotFoundError,
    MultipleFacesDetectedError,
    NoFaceDetectedError,
    get_face_detector_service,
)

client = TestClient(app)


# ---------------------------------------------------------------------------
# Test Image Helpers (Synthetic drawing, zero personal data)
# ---------------------------------------------------------------------------


def _create_synthetic_face_image(size: tuple[int, int] = (400, 400)) -> bytes:
    """Generate a clean synthetic portrait image recognizable by MediaPipe."""
    img = Image.new("RGB", size, color=(240, 240, 240))
    draw = ImageDraw.Draw(img)

    # Cranium / face oval
    draw.ellipse([100, 50, 300, 350], fill=(230, 190, 160), outline=(100, 70, 50), width=3)
    # Eyes
    draw.ellipse([140, 140, 170, 160], fill=(40, 40, 40))
    draw.ellipse([230, 140, 260, 160], fill=(40, 40, 40))
    # Eyebrows
    draw.line([(135, 130), (175, 130)], fill=(40, 40, 40), width=4)
    draw.line([(225, 130), (265, 130)], fill=(40, 40, 40), width=4)
    # Nose
    draw.polygon([(200, 170), (190, 220), (210, 220)], fill=(200, 150, 120))
    # Mouth
    draw.arc([160, 240, 240, 280], start=0, end=180, fill=(180, 50, 50), width=4)

    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def _create_synthetic_multi_face_image(size: tuple[int, int] = (600, 400)) -> bytes:
    """Generate a synthetic image with two distinct faces."""
    img = Image.new("RGB", size, color=(240, 240, 240))
    draw = ImageDraw.Draw(img)

    def draw_face(offset_x: int):
        draw.ellipse([offset_x + 20, 50, offset_x + 220, 350], fill=(230, 190, 160), outline=(100, 70, 50), width=3)
        draw.ellipse([offset_x + 60, 140, offset_x + 90, 160], fill=(40, 40, 40))
        draw.ellipse([offset_x + 150, 140, offset_x + 180, 160], fill=(40, 40, 40))
        draw.line([(offset_x + 55, 130), (offset_x + 95, 130)], fill=(40, 40, 40), width=4)
        draw.line([(offset_x + 145, 130), (offset_x + 185, 130)], fill=(40, 40, 40), width=4)
        draw.polygon([(offset_x + 120, 170), (offset_x + 110, 220), (offset_x + 130, 220)], fill=(200, 150, 120))
        draw.arc([offset_x + 80, 240, offset_x + 160, 280], start=0, end=180, fill=(180, 50, 50), width=4)

    draw_face(20)
    draw_face(320)

    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def _create_blank_image(size: tuple[int, int] = (400, 400), color: str = "white") -> bytes:
    """Generate an image without any human facial features."""
    img = Image.new("RGB", size, color=color)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


# ---------------------------------------------------------------------------
# API Endpoint Integration Tests
# ---------------------------------------------------------------------------


def test_successful_face_detection():
    """Verify successful detection of a single face and 478 landmark extractions."""
    image_bytes = _create_synthetic_face_image()

    response = client.post(
        "/api/faces/detect",
        files={"file": ("portrait.jpg", image_bytes, "image/jpeg")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["faces_detected"] == 1
    assert data["image_width"] == 400
    assert data["image_height"] == 400

    landmarks = data["landmarks"]
    assert len(landmarks) == 478

    # Verify first and last landmark indices and structure
    first_lm = landmarks[0]
    assert first_lm["index"] == 0
    assert "x" in first_lm and "y" in first_lm and "z" in first_lm
    assert "pixel_x" in first_lm and "pixel_y" in first_lm

    last_lm = landmarks[477]
    assert last_lm["index"] == 477


def test_no_face_detected_returns_400():
    """Verify that uploading an image without a face returns HTTP 400."""
    blank_bytes = _create_blank_image()

    response = client.post(
        "/api/faces/detect",
        files={"file": ("blank.jpg", blank_bytes, "image/jpeg")},
    )

    assert response.status_code == 400
    data = response.json()
    assert "no human face detected" in data["detail"].lower()


def test_multiple_faces_rejected_under_single_face_policy():
    """Verify that uploading an image with multiple faces returns HTTP 400 under the single-face policy."""
    multi_face_bytes = _create_synthetic_multi_face_image()

    response = client.post(
        "/api/faces/detect",
        files={"file": ("two_faces.jpg", multi_face_bytes, "image/jpeg")},
    )

    assert response.status_code == 400
    data = response.json()
    assert "multiple faces detected" in data["detail"].lower()


def test_invalid_image_inputs():
    """Verify that empty, corrupted, and unsupported files are rejected with appropriate error codes."""
    # 1. Empty file
    r_empty = client.post(
        "/api/faces/detect",
        files={"file": ("empty.jpg", b"", "image/jpeg")},
    )
    assert r_empty.status_code == 400
    assert "empty" in r_empty.json()["detail"].lower()

    # 2. Corrupted file
    r_corrupt = client.post(
        "/api/faces/detect",
        files={"file": ("corrupt.jpg", b"badcorruptbytes12345", "image/jpeg")},
    )
    assert r_corrupt.status_code == 400
    assert "valid image" in r_corrupt.json()["detail"].lower() or "corrupted" in r_corrupt.json()["detail"].lower()

    # 3. Unsupported format (GIF)
    gif_img = Image.new("RGB", (100, 100), color="blue")
    buf = io.BytesIO()
    gif_img.save(buf, format="GIF")
    r_gif = client.post(
        "/api/faces/detect",
        files={"file": ("anim.gif", buf.getvalue(), "image/gif")},
    )
    assert r_gif.status_code == 415
    assert "unsupported" in r_gif.json()["detail"].lower()


def test_correct_coordinate_conversion():
    """Verify mathematical correctness of normalized to pixel coordinate conversions."""
    image_bytes = _create_synthetic_face_image(size=(500, 400))

    response = client.post(
        "/api/faces/detect",
        files={"file": ("portrait.jpg", image_bytes, "image/jpeg")},
    )

    assert response.status_code == 200
    data = response.json()
    w = data["image_width"]
    h = data["image_height"]
    assert w == 500
    assert h == 400

    landmarks = data["landmarks"]
    assert len(landmarks) == 478

    for idx, lm in enumerate(landmarks):
        # Index integrity
        assert lm["index"] == idx

        # Normalized coordinates should be within reasonable proximity of unit square
        assert -0.2 <= lm["x"] <= 1.2
        assert -0.2 <= lm["y"] <= 1.2

        # Pixel coordinate conversion math verification: pixel = round(norm * dimension, 2)
        expected_px = round(lm["x"] * w, 2)
        expected_py = round(lm["y"] * h, 2)
        assert abs(lm["pixel_x"] - expected_px) < 0.05
        assert abs(lm["pixel_y"] - expected_py) < 0.05


# ---------------------------------------------------------------------------
# Unit Tests for FaceDetectorService
# ---------------------------------------------------------------------------


def test_service_model_caching():
    """Verify that the service caches the model and does not reload on subsequent calls."""
    service = get_face_detector_service()
    service.load_model()
    first_instance = service._landmarker

    # Call again
    service.load_model()
    second_instance = service._landmarker

    assert first_instance is second_instance
    assert service.is_model_loaded() is True


def test_missing_model_handling():
    """Verify that specifying a non-existent model file raises ModelNotFoundError."""
    invalid_service = FaceDetectorService(model_path="backend/models/non_existent_model.task")

    with pytest.raises(ModelNotFoundError) as exc_info:
        invalid_service.load_model()

    assert "not found at" in str(exc_info.value)
    assert exc_info.value.status_code == 503


def test_missing_model_api_error_response():
    """Verify that when model is missing, the API endpoint returns HTTP 503."""
    # Temporarily override dependency with missing model service
    invalid_service = FaceDetectorService(model_path="backend/models/missing.task")
    app.dependency_overrides[get_face_detector_service] = lambda: invalid_service

    try:
        image_bytes = _create_synthetic_face_image()
        response = client.post(
            "/api/faces/detect",
            files={"file": ("test.jpg", image_bytes, "image/jpeg")},
        )
        assert response.status_code == 503
        assert "model file not found" in response.json()["detail"].lower()
    finally:
        app.dependency_overrides.clear()


def test_multi_face_primary_selection_policy():
    """Verify that when require_single_face is False, the service selects the primary face."""
    service = get_face_detector_service()
    multi_face_bytes = _create_synthetic_multi_face_image()

    result = service.detect_landmarks_from_bytes(multi_face_bytes, require_single_face=False)

    assert result.faces_detected == 2
    assert len(result.landmarks) == 478
    assert result.image_width == 600
    assert result.image_height == 400

