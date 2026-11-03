"""Main FastAPI application for Loomis AI Backend.

Provides health inspection and image preprocessing API endpoints for Phase 1.
"""

import logging
from typing import Annotated

from fastapi import FastAPI, File, HTTPException, Request, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.schemas.health import HealthResponse
from backend.schemas.image import ImagePreprocessResponse
from backend.services.image_processor import preprocess_portrait
from backend.services.image_validator import (
    MAX_FILE_SIZE_BYTES,
    MAX_FILE_SIZE_MB,
    ImageValidationError,
)

# Configure structured, privacy-preserving logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("loomis-ai.backend")

app = FastAPI(
    title="Loomis AI Backend",
    description=(
        "AI-Powered Step-by-Step Portrait Drawing Tutor API. "
        "Phase 1: Image Ingestion, Validation, and Preprocessing."
    ),
    version="0.1.0",
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(ImageValidationError)
async def image_validation_handler(request: Request, exc: ImageValidationError):
    """Handle domain-specific image validation errors and map to standard HTTP responses."""
    logger.warning("Image validation failure: %s (HTTP %d)", exc.message, exc.status_code)
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message},
    )


@app.get(
    "/api/health",
    response_model=HealthResponse,
    summary="Health check",
    tags=["System"],
)
async def health_check() -> HealthResponse:
    """Return operational health status of the backend service."""
    return HealthResponse(
        status="healthy",
        service="loomis-ai-backend",
        version="0.1.0",
    )


@app.post(
    "/api/images/preprocess",
    response_model=ImagePreprocessResponse,
    status_code=status.HTTP_200_OK,
    summary="Preprocess portrait image",
    tags=["Images"],
)
async def preprocess_image(
    file: Annotated[UploadFile, File(description="Portrait image (JPEG, PNG, or WebP)")],
) -> ImagePreprocessResponse:
    """Validate, orient, normalize, resize, and return preprocessed portrait image.

    - Verifies content integrity and formats (JPEG, PNG, WebP).
    - Enforces 10 MB maximum upload size.
    - Applies EXIF orientation rotation.
    - Normalizes channels to 3-channel RGB.
    - Resizes to max dimension of 1024px while preserving aspect ratio.
    - Returns Base64-encoded JPEG and metadata in-memory without persistent disk storage.
    """
    logger.info(
        "Received image preprocessing request (filename: %s, declared_type: %s)",
        file.filename,
        file.content_type,
    )

    # 1. Stream file bytes with strict size limit enforcement to prevent memory exhaustion
    content = bytearray()
    chunk_size = 1024 * 1024  # 1 MB chunk

    try:
        while chunk := await file.read(chunk_size):
            content.extend(chunk)
            if len(content) > MAX_FILE_SIZE_BYTES:
                raise HTTPException(
                    status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                    detail=f"File size exceeds maximum allowed limit of {MAX_FILE_SIZE_MB} MB.",
                )
    finally:
        await file.close()

    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    file_bytes = bytes(content)

    # 2. Process image through domain service
    result = preprocess_portrait(file_bytes)

    logger.info(
        "Image preprocessed successfully: original=(%dx%d, %s) -> processed=(%dx%d, %s)",
        result.original_width,
        result.original_height,
        result.original_format,
        result.processed_width,
        result.processed_height,
        result.processed_format,
    )

    return ImagePreprocessResponse(
        success=True,
        message="Image preprocessed successfully.",
        original_width=result.original_width,
        original_height=result.original_height,
        processed_width=result.processed_width,
        processed_height=result.processed_height,
        original_format=result.original_format,
        processed_format=result.processed_format,
        image_base64=result.image_base64,
        processing_status=result.processing_status,
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
