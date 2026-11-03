"""Image validation service for Loomis AI.

Validates uploaded portrait image files for size, supported MIME/format types,
data integrity, and dimension limits without relying on untrusted client headers.
"""

import io
from typing import Set, Tuple
from PIL import Image, UnidentifiedImageError

# Constraints
MAX_FILE_SIZE_MB: int = 10
MAX_FILE_SIZE_BYTES: int = MAX_FILE_SIZE_MB * 1024 * 1024  # 10 MB in bytes
MAX_IMAGE_DIMENSION: int = 8192  # Prevent decompression bomb attacks
ALLOWED_FORMATS: Set[str] = {"JPEG", "PNG", "WEBP"}


class ImageValidationError(Exception):
    """Base exception for image validation failures."""

    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class EmptyFileError(ImageValidationError):
    """Raised when an uploaded file is 0 bytes."""

    def __init__(self, message: str = "Uploaded file is empty."):
        super().__init__(message, status_code=400)


class FileSizeLimitExceededError(ImageValidationError):
    """Raised when an uploaded file exceeds the maximum size limit."""

    def __init__(
        self,
        message: str = f"File size exceeds maximum allowed limit of {MAX_FILE_SIZE_MB} MB.",
    ):
        super().__init__(message, status_code=413)


class UnsupportedImageFormatError(ImageValidationError):
    """Raised when an uploaded file is a valid image but an unsupported format."""

    def __init__(self, format_name: str):
        message = (
            f"Unsupported image format: '{format_name}'. "
            f"Allowed formats are: {', '.join(sorted(ALLOWED_FORMATS))}."
        )
        super().__init__(message, status_code=415)


class CorruptedImageError(ImageValidationError):
    """Raised when file content cannot be decoded or is damaged."""

    def __init__(
        self,
        message: str = "Uploaded file is corrupted or not a valid image.",
    ):
        super().__init__(message, status_code=400)


class ExcessiveDimensionError(ImageValidationError):
    """Raised when image dimensions exceed safe rendering limits."""

    def __init__(self, width: int, height: int, max_dim: int = MAX_IMAGE_DIMENSION):
        message = (
            f"Image dimensions ({width}x{height}px) exceed the maximum "
            f"allowed limit of {max_dim}x{max_dim}px."
        )
        super().__init__(message, status_code=400)


def validate_image_bytes(file_bytes: bytes) -> Tuple[str, int, int]:
    """Inspect and validate the raw byte payload of an uploaded portrait.

    This function does NOT trust client headers or file extensions. It verifies
    the underlying binary content using Pillow.

    Args:
        file_bytes: Raw binary bytes of the uploaded file.

    Returns:
        Tuple of (detected_format, width, height).

    Raises:
        EmptyFileError: If file_bytes is empty.
        FileSizeLimitExceededError: If file exceeds MAX_FILE_SIZE_BYTES.
        UnsupportedImageFormatError: If format is not JPEG, PNG, or WebP.
        CorruptedImageError: If the file is not an image or is corrupted.
        ExcessiveDimensionError: If width or height exceeds MAX_IMAGE_DIMENSION.
    """
    if not file_bytes or len(file_bytes) == 0:
        raise EmptyFileError()

    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        raise FileSizeLimitExceededError()

    # Step 1: Open stream and check format & header integrity
    try:
        with Image.open(io.BytesIO(file_bytes)) as img:
            detected_format = (img.format or "").upper()
            if not detected_format or detected_format not in ALLOWED_FORMATS:
                raise UnsupportedImageFormatError(detected_format or "Unknown")

            # verify() checks file header and blocks without decoding pixels
            img.verify()
    except ImageValidationError:
        raise
    except (UnidentifiedImageError, OSError, SyntaxError, ValueError):
        raise CorruptedImageError("Uploaded file is corrupted or not a valid image.")
    except Exception as exc:
        raise CorruptedImageError(f"Failed to verify image data: {exc}") from exc

    # Step 2: Re-open to read dimensions and force decode to catch truncated data
    try:
        with Image.open(io.BytesIO(file_bytes)) as img:
            width, height = img.size

            if width <= 0 or height <= 0:
                raise CorruptedImageError("Image has invalid or non-positive dimensions.")

            if width > MAX_IMAGE_DIMENSION or height > MAX_IMAGE_DIMENSION:
                raise ExcessiveDimensionError(width, height, MAX_IMAGE_DIMENSION)

            # Force pixel load to detect truncated or damaged image streams
            img.load()

            return detected_format, width, height
    except ImageValidationError:
        raise
    except (OSError, SyntaxError, ValueError):
        raise CorruptedImageError("Uploaded image is truncated or corrupted.")
    except Exception as exc:
        raise CorruptedImageError(f"Failed to decode image data: {exc}") from exc
