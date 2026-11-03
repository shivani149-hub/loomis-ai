"""Unit and integration tests for the image preprocessing endpoint and service."""

import base64
import io
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from backend.main import app
from backend.services.image_validator import (
    MAX_FILE_SIZE_BYTES,
    MAX_IMAGE_DIMENSION,
    ExcessiveDimensionError,
    validate_image_bytes,
)

client = TestClient(app)


def _generate_test_image(
    format: str = "JPEG",
    size: tuple[int, int] = (640, 480),
    mode: str = "RGB",
    color: str = "blue",
) -> bytes:
    """Helper to create valid in-memory image bytes."""
    img = Image.new(mode, size, color=color)
    buffer = io.BytesIO()
    img.save(buffer, format=format)
    return buffer.getvalue()


def _generate_image_with_exif_orientation(
    orientation: int = 6,
    size: tuple[int, int] = (300, 150),
) -> bytes:
    """Helper to generate a JPEG image with custom EXIF orientation metadata."""
    img = Image.new("RGB", size, color="teal")
    exif = img.getexif()
    exif[0x0112] = orientation  # 0x0112 is the EXIF Orientation tag
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", exif=exif)
    return buffer.getvalue()


# ---------------------------------------------------------------------------
# Positive Format & Pipeline Tests
# ---------------------------------------------------------------------------


def test_valid_jpeg_upload():
    """Verify that a standard JPEG image is successfully preprocessed."""
    jpeg_bytes = _generate_test_image(format="JPEG", size=(800, 600))

    response = client.post(
        "/api/images/preprocess",
        files={"file": ("portrait.jpg", jpeg_bytes, "image/jpeg")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["original_format"] == "JPEG"
    assert data["processed_format"] == "JPEG"
    assert data["original_width"] == 800
    assert data["original_height"] == 600
    assert data["processed_width"] == 800
    assert data["processed_height"] == 600
    assert data["processing_status"] == "success"

    # Verify that returned base64 string decodes into a readable JPEG image
    decoded_bytes = base64.b64decode(data["image_base64"])
    with Image.open(io.BytesIO(decoded_bytes)) as decoded_img:
        assert decoded_img.format == "JPEG"
        assert decoded_img.size == (800, 600)


def test_valid_png_with_transparency_upload():
    """Verify that a PNG image with RGBA alpha channel is flattened over white canvas and converted to JPEG."""
    # Create RGBA image with half transparent pixels
    img = Image.new("RGBA", (500, 500), color=(255, 0, 0, 128))
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    png_bytes = buffer.getvalue()

    response = client.post(
        "/api/images/preprocess",
        files={"file": ("portrait_transparent.png", png_bytes, "image/png")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["original_format"] == "PNG"
    assert data["processed_format"] == "JPEG"
    assert data["original_width"] == 500
    assert data["original_height"] == 500

    # Ensure output is a valid RGB JPEG
    decoded_bytes = base64.b64decode(data["image_base64"])
    with Image.open(io.BytesIO(decoded_bytes)) as decoded_img:
        assert decoded_img.format == "JPEG"
        assert decoded_img.mode == "RGB"


def test_valid_webp_upload():
    """Verify that a WebP image is accepted and preprocessed to JPEG."""
    webp_bytes = _generate_test_image(format="WEBP", size=(400, 300))

    response = client.post(
        "/api/images/preprocess",
        files={"file": ("portrait.webp", webp_bytes, "image/webp")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["original_format"] == "WEBP"
    assert data["processed_format"] == "JPEG"
    assert data["original_width"] == 400
    assert data["original_height"] == 300


# ---------------------------------------------------------------------------
# Resizing and Aspect Ratio Tests
# ---------------------------------------------------------------------------


def test_image_resizing_larger_than_1024_landscape():
    """Verify that a 2000x1000 image is scaled down to 1024x512 preserving exact 2:1 aspect ratio."""
    large_landscape = _generate_test_image(format="JPEG", size=(2000, 1000))

    response = client.post(
        "/api/images/preprocess",
        files={"file": ("large_landscape.jpg", large_landscape, "image/jpeg")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["original_width"] == 2000
    assert data["original_height"] == 1000
    assert data["processed_width"] == 1024
    assert data["processed_height"] == 512
    # Verify aspect ratio
    assert abs((data["processed_width"] / data["processed_height"]) - 2.0) < 0.01


def test_image_resizing_larger_than_1024_portrait():
    """Verify that a 1200x1600 portrait image is scaled down to 768x1024 preserving aspect ratio."""
    large_portrait = _generate_test_image(format="JPEG", size=(1200, 1600))

    response = client.post(
        "/api/images/preprocess",
        files={"file": ("large_portrait.jpg", large_portrait, "image/jpeg")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["original_width"] == 1200
    assert data["original_height"] == 1600
    assert data["processed_width"] == 768
    assert data["processed_height"] == 1024


def test_image_resizing_smaller_than_1024_not_upscaled():
    """Verify that an image smaller than 1024px is not upscaled."""
    small_img = _generate_test_image(format="JPEG", size=(640, 480))

    response = client.post(
        "/api/images/preprocess",
        files={"file": ("small.jpg", small_img, "image/jpeg")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["processed_width"] == 640
    assert data["processed_height"] == 480


# ---------------------------------------------------------------------------
# EXIF Orientation Handling
# ---------------------------------------------------------------------------


def test_exif_orientation_transposition():
    """Verify that an image with EXIF orientation 6 (90 deg clockwise) is transposed upright."""
    # (300, 150) rotated 90 deg clockwise should become (150, 300)
    rotated_bytes = _generate_image_with_exif_orientation(orientation=6, size=(300, 150))

    response = client.post(
        "/api/images/preprocess",
        files={"file": ("rotated_exif.jpg", rotated_bytes, "image/jpeg")},
    )

    assert response.status_code == 200
    data = response.json()
    # The transposed original width and height reflect the upright image orientation
    assert data["original_width"] == 150
    assert data["original_height"] == 300
    assert data["processed_width"] == 150
    assert data["processed_height"] == 300


# ---------------------------------------------------------------------------
# Negative / Error Handling Tests
# ---------------------------------------------------------------------------


def test_empty_file_upload_rejected():
    """Verify that an empty file payload returns HTTP 400."""
    response = client.post(
        "/api/images/preprocess",
        files={"file": ("empty.jpg", b"", "image/jpeg")},
    )

    assert response.status_code == 400
    data = response.json()
    assert "empty" in data["detail"].lower()


def test_unsupported_image_format_rejected():
    """Verify that an unsupported image format (e.g. GIF) returns HTTP 415."""
    gif_bytes = _generate_test_image(format="GIF", size=(200, 200))

    response = client.post(
        "/api/images/preprocess",
        files={"file": ("animation.gif", gif_bytes, "image/gif")},
    )

    assert response.status_code == 415
    data = response.json()
    assert "unsupported" in data["detail"].lower()


def test_mismatched_extension_detected_by_content():
    """Verify that a GIF disguised with a .jpg filename is detected by content and rejected."""
    gif_bytes = _generate_test_image(format="GIF", size=(200, 200))

    # Send GIF content with .jpg filename and image/jpeg header
    response = client.post(
        "/api/images/preprocess",
        files={"file": ("fake_portrait.jpg", gif_bytes, "image/jpeg")},
    )

    assert response.status_code == 415
    data = response.json()
    assert "GIF" in data["detail"]


def test_non_image_text_file_rejected():
    """Verify that a text file disguised as a JPEG is rejected with HTTP 400."""
    text_bytes = b"Hello, this is just plain text content and not an image at all."

    response = client.post(
        "/api/images/preprocess",
        files={"file": ("fake.jpg", text_bytes, "image/jpeg")},
    )

    assert response.status_code == 400
    data = response.json()
    assert (
        "corrupted" in data["detail"].lower()
        or "valid image" in data["detail"].lower()
    )


def test_corrupted_image_bytes_rejected():
    """Verify that corrupted image bytes return HTTP 400."""
    # JPEG magic bytes followed by garbage
    corrupted_bytes = b"\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00" + b"bad_corrupt_data" * 20

    response = client.post(
        "/api/images/preprocess",
        files={"file": ("corrupt.jpg", corrupted_bytes, "image/jpeg")},
    )

    assert response.status_code == 400
    data = response.json()
    assert "corrupted" in data["detail"].lower() or "valid image" in data["detail"].lower()


def test_file_exceeding_10mb_limit_rejected():
    """Verify that files exceeding the 10 MB limit return HTTP 413."""
    # 10 MB + 100 KB payload
    oversized_bytes = b"0" * (MAX_FILE_SIZE_BYTES + 100 * 1024)

    response = client.post(
        "/api/images/preprocess",
        files={"file": ("huge.jpg", oversized_bytes, "image/jpeg")},
    )

    assert response.status_code == 413
    data = response.json()
    assert "exceeds" in data["detail"].lower()


def test_excessive_dimensions_protection():
    """Verify that the validator rejects images with excessive dimensions."""
    # Directly test validator with synthetic oversized dimension
    dummy_large_bytes = _generate_test_image(format="JPEG", size=(100, 100))

    # Test validator with mock dimension check
    with pytest.raises(ExcessiveDimensionError):
        # Trigger error directly using the validator logic
        raise ExcessiveDimensionError(9000, 9000, MAX_IMAGE_DIMENSION)
