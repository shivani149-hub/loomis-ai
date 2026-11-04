"""Image preprocessing service for Loomis AI.

Performs EXIF orientation correction, RGB conversion, proportional downscaling
(max dimension 1024px), and in-memory JPEG/Base64 encoding without disk persistence.
"""

import base64
from dataclasses import dataclass
import io
from typing import Tuple
from PIL import Image, ImageOps

from backend.services.image_validator import validate_image_bytes

MAX_TARGET_DIMENSION: int = 1024
DEFAULT_JPEG_QUALITY: int = 90


@dataclass(frozen=True)
class PreprocessingResult:
    """Immutable data container holding preprocessed image results and metadata."""

    original_width: int
    original_height: int
    processed_width: int
    processed_height: int
    original_format: str
    processed_format: str
    image_base64: str
    processing_status: str = "success"


def _normalize_orientation(image: Image.Image) -> Image.Image:
    """Apply EXIF orientation transposition if orientation tags are present.

    Args:
        image: Source PIL Image.

    Returns:
        Transposed PIL Image in proper visual orientation.
    """
    try:
        transposed = ImageOps.exif_transpose(image)
        return transposed if transposed is not None else image
    except Exception:
        # Fall back to original image if EXIF parsing fails
        return image


def _convert_to_rgb(image: Image.Image) -> Image.Image:
    """Ensure image is in RGB format, compositing any alpha channel over solid white.

    Args:
        image: Source PIL Image in any mode (RGBA, LA, P, CMYK, etc.).

    Returns:
        Clean 3-channel RGB PIL Image.
    """
    # Handle transparency in RGBA, LA, or Palette modes
    if image.mode in ("RGBA", "LA") or (
        image.mode == "P" and "transparency" in image.info
    ):
        rgba_image = image.convert("RGBA")
        background = Image.new("RGB", rgba_image.size, (255, 255, 255))
        # Use alpha channel as mask to paste foreground over white canvas
        background.paste(rgba_image, mask=rgba_image.split()[3])
        return background

    if image.mode != "RGB":
        return image.convert("RGB")

    return image.copy()


def _resize_aspect_ratio(
    image: Image.Image, max_dimension: int = MAX_TARGET_DIMENSION
) -> Image.Image:
    """Downscale image so its largest dimension does not exceed max_dimension.

    Preserves exact aspect ratio and avoids upscaling images that are already
    smaller than max_dimension.

    Args:
        image: Source RGB Image.
        max_dimension: Maximum allowed pixel size for long edge.

    Returns:
        Proportionally scaled PIL Image.
    """
    width, height = image.size

    # Avoid upscaling if image is already within bounds
    if max(width, height) <= max_dimension:
        return image.copy()

    if width >= height:
        new_width = max_dimension
        new_height = max(1, int(round((height * max_dimension) / width)))
    else:
        new_height = max_dimension
        new_width = max(1, int(round((width * max_dimension) / height)))

    return image.resize((new_width, new_height), Image.Resampling.LANCZOS)


def _encode_jpeg_base64(image: Image.Image, quality: int = DEFAULT_JPEG_QUALITY) -> str:
    """Encode PIL Image to JPEG format in memory and return Base64 string.

    Args:
        image: RGB PIL Image.
        quality: JPEG compression quality (1-100).

    Returns:
        Base64-encoded string representing the JPEG image bytes.
    """
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=quality, optimize=True)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def preprocess_to_pil(file_bytes: bytes) -> Tuple[Image.Image, str, int, int]:
    """Execute validation and preprocessing, returning the processed PIL Image in RGB.

    1. Validates file bytes, dimensions, and format.
    2. Corrects EXIF orientation.
    3. Normalizes color channels to standard RGB.
    4. Proportionally downsizes to 1024px maximum edge.

    Args:
        file_bytes: Raw binary bytes of uploaded portrait.

    Returns:
        Tuple of (processed_pil_image, detected_format, orig_width, orig_height).
    """
    # 1. Validate raw bytes first (raises ImageValidationError on failure)
    detected_format, _, _ = validate_image_bytes(file_bytes)

    # 2. Decode in memory safely
    with Image.open(io.BytesIO(file_bytes)) as raw_image:
        oriented_image = _normalize_orientation(raw_image)
        orig_width, orig_height = oriented_image.size
        rgb_image = _convert_to_rgb(oriented_image)
        processed_image = _resize_aspect_ratio(rgb_image, MAX_TARGET_DIMENSION)
        return processed_image, detected_format, orig_width, orig_height


def preprocess_portrait(file_bytes: bytes) -> PreprocessingResult:
    """Execute complete validation and preprocessing pipeline for a portrait upload.

    1. Validates file bytes, dimensions, and format.
    2. Corrects EXIF orientation.
    3. Normalizes color channels to standard RGB.
    4. Proportionally downsizes to 1024px maximum edge.
    5. Encodes result into in-memory Base64 JPEG.

    Args:
        file_bytes: Raw binary bytes of uploaded portrait.

    Returns:
        PreprocessingResult containing metadata and Base64-encoded image string.
    """
    processed_image, detected_format, orig_width, orig_height = preprocess_to_pil(file_bytes)
    proc_width, proc_height = processed_image.size
    base64_str = _encode_jpeg_base64(processed_image)

    return PreprocessingResult(
        original_width=orig_width,
        original_height=orig_height,
        processed_width=proc_width,
        processed_height=proc_height,
        original_format=detected_format,
        processed_format="JPEG",
        image_base64=base64_str,
        processing_status="success",
    )
