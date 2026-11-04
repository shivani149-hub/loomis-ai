"""Main FastAPI application for Loomis AI Backend.

Provides health inspection, image preprocessing, and face landmark detection endpoints.
"""

from contextlib import asynccontextmanager
import logging
from typing import Annotated

from fastapi import Depends, FastAPI, File, HTTPException, Request, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.schemas.health import HealthResponse
from backend.schemas.image import ImagePreprocessResponse
from backend.schemas.landmark import FaceLandmarksResponse
from backend.services.face_detector import (
    FaceDetectionError,
    FaceDetectorService,
    get_face_detector_service,
)
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup preloading and graceful shutdown."""
    logger.info("Initializing Loomis AI Backend services...")
    # Attempt to preload Face Landmarker model on startup if present
    detector = get_face_detector_service()
    try:
        detector.load_model()
        logger.info("Face landmarker model preloaded successfully on startup.")
    except Exception as exc:
        logger.warning(
            "Face landmarker model could not be preloaded on startup: %s. "
            "It will be loaded on first request.",
            exc,
        )
    yield
    logger.info("Shutting down Loomis AI Backend.")


app = FastAPI(
    title="Loomis AI Backend",
    description=(
        "AI-Powered Step-by-Step Portrait Drawing Tutor API. "
        "Phase 2: Face Detection and Landmark Extraction using MediaPipe Face Landmarker."
    ),
    version="0.2.0",
    lifespan=lifespan,
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


@app.exception_handler(FaceDetectionError)
async def face_detection_handler(request: Request, exc: FaceDetectionError):
    """Handle face detection and landmarking errors and map to standard HTTP responses."""
    logger.warning("Face detection failure: %s (HTTP %d)", exc.message, exc.status_code)
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message},
    )


async def _read_upload_file_safely(file: UploadFile) -> bytes:
    """Read uploaded file stream while enforcing strict 10 MB payload boundaries."""
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

    return bytes(content)


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
        version="0.2.0",
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

    file_bytes = await _read_upload_file_safely(file)
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


@app.post(
    "/api/faces/detect",
    response_model=FaceLandmarksResponse,
    status_code=status.HTTP_200_OK,
    summary="Detect face and extract landmarks",
    tags=["Face Detection"],
)
async def detect_face(
    file: Annotated[UploadFile, File(description="Portrait image (JPEG, PNG, or WebP)")],
    detector: Annotated[FaceDetectorService, Depends(get_face_detector_service)],
) -> FaceLandmarksResponse:
    """Detect single primary face and extract 478 dense 3D facial mesh landmarks.

    - Reuses Phase 1 image validation and preprocessing pipeline.
    - Detects facial presence using MediaPipe Face Landmarker Tasks API.
    - Enforces single-face constraint (rejects 0 faces or multiple faces).
    - Converts normalized landmark coordinates to exact pixel coordinates.
    - Preserves all 478 landmark indices in canonical sequence.
    """
    logger.info(
        "Received face detection request (filename: %s, declared_type: %s)",
        file.filename,
        file.content_type,
    )

    file_bytes = await _read_upload_file_safely(file)
    result = detector.detect_landmarks_from_bytes(file_bytes, require_single_face=True)

    logger.info(
        "Face landmarks extracted successfully: %d landmarks on %dx%d image (%d face detected)",
        len(result.landmarks),
        result.image_width,
        result.image_height,
        result.faces_detected,
    )

    return FaceLandmarksResponse(
        success=True,
        message="Face detected and landmarks extracted successfully.",
        image_width=result.image_width,
        image_height=result.image_height,
        faces_detected=result.faces_detected,
        landmarks=result.landmarks,
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
