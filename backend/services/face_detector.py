"""Face detection and landmark extraction service for Loomis AI.

Uses MediaPipe Face Landmarker Tasks API in IMAGE running mode to detect faces,
extract 478 dense 3D facial landmarks, and calculate pixel coordinates.
"""

from dataclasses import dataclass
import os
import tempfile
import threading
from typing import List, Optional, Tuple

# Suppress matplotlib permission warning on Windows
os.environ.setdefault("MPLCONFIGDIR", tempfile.gettempdir())

import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import numpy as np
from PIL import Image

from backend.schemas.landmark import FacialLandmark
from backend.services.image_processor import preprocess_to_pil

DEFAULT_MODEL_PATH: str = os.path.join("backend", "models", "face_landmarker.task")


# ---------------------------------------------------------------------------
# Domain Exceptions
# ---------------------------------------------------------------------------


class FaceDetectionError(Exception):
    """Base exception for face detection and landmarking failures."""

    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class NoFaceDetectedError(FaceDetectionError):
    """Raised when no human face is found in the uploaded image."""

    def __init__(
        self,
        message: str = (
            "No human face detected in the uploaded image. "
            "Please provide a clear portrait photograph with a visible face."
        ),
    ):
        super().__init__(message, status_code=400)


class MultipleFacesDetectedError(FaceDetectionError):
    """Raised when more than one face is detected under strict single-face policy."""

    def __init__(
        self,
        face_count: int,
        message: Optional[str] = None,
    ):
        msg = message or (
            f"Multiple faces detected ({face_count}). "
            "Loomis AI currently requires an image with exactly one visible portrait."
        )
        super().__init__(msg, status_code=400)


class ModelNotFoundError(FaceDetectionError):
    """Raised when the Face Landmarker .task model file is missing."""

    def __init__(self, model_path: str):
        message = (
            f"Face Landmarker model file not found at: '{model_path}'. "
            "Please ensure the official face_landmarker.task model is downloaded."
        )
        super().__init__(message, status_code=503)


class ModelLoadError(FaceDetectionError):
    """Raised when initialization of the MediaPipe Face Landmarker fails."""

    def __init__(self, details: str):
        message = f"Failed to initialize Face Landmarker model: {details}"
        super().__init__(message, status_code=500)


# ---------------------------------------------------------------------------
# Result Data Container
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class FaceDetectionResult:
    """Immutable result container holding image dimensions and extracted landmarks."""

    image_width: int
    image_height: int
    faces_detected: int
    landmarks: List[FacialLandmark]


# ---------------------------------------------------------------------------
# Face Detector Service
# ---------------------------------------------------------------------------


class FaceDetectorService:
    """Encapsulates MediaPipe Face Landmarker model loading and inference.

    Maintains a cached, thread-safe model instance across requests to ensure
    high-throughput performance without redundant disk or GPU/CPU model reloads.
    """

    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path or os.getenv("FACE_LANDMARKER_MODEL_PATH", DEFAULT_MODEL_PATH)
        self._landmarker: Optional[vision.FaceLandmarker] = None
        self._load_lock = threading.Lock()
        self._inference_lock = threading.Lock()

    def is_model_loaded(self) -> bool:
        """Check if the Face Landmarker model is currently loaded in memory."""
        return self._landmarker is not None

    def load_model(self) -> None:
        """Load and initialize the MediaPipe Face Landmarker if not already loaded.

        Raises:
            ModelNotFoundError: If the model file does not exist on disk.
            ModelLoadError: If MediaPipe fails to create the landmarker from options.
        """
        if self._landmarker is not None:
            return

        with self._load_lock:
            # Double-check pattern for thread safety
            if self._landmarker is not None:
                return

            if not os.path.exists(self.model_path):
                raise ModelNotFoundError(self.model_path)

            try:
                base_options = python.BaseOptions(model_asset_path=self.model_path)
                options = vision.FaceLandmarkerOptions(
                    base_options=base_options,
                    running_mode=vision.RunningMode.IMAGE,
                    num_faces=3,  # Detect up to 3 to identify multi-face uploads
                    min_face_detection_confidence=0.5,
                    min_face_presence_confidence=0.5,
                    output_face_blendshapes=False,
                    output_facial_transformation_matrixes=False,
                )
                self._landmarker = vision.FaceLandmarker.create_from_options(options)
            except Exception as exc:
                raise ModelLoadError(str(exc)) from exc

    def _select_primary_face(
        self,
        faces_landmarks: List[List[object]],
        width: int,
        height: int,
    ) -> List[object]:
        """Select the primary face having the largest bounding box area."""
        def _face_area(landmarks: List[object]) -> float:
            xs = [getattr(lm, "x") for lm in landmarks]
            ys = [getattr(lm, "y") for lm in landmarks]
            w = (max(xs) - min(xs)) * width
            h = (max(ys) - min(ys)) * height
            return w * h

        return max(faces_landmarks, key=_face_area)

    def detect_landmarks(
        self,
        image: Image.Image,
        require_single_face: bool = True,
    ) -> FaceDetectionResult:
        """Run face detection and landmark extraction on a preprocessed PIL Image.

        Args:
            image: Preprocessed PIL Image in RGB format.
            require_single_face: When True, raises MultipleFacesDetectedError if >1 face is found.
                                When False, selects the primary (largest) face.

        Returns:
            FaceDetectionResult with image dimensions, face count, and 478 landmarks.

        Raises:
            NoFaceDetectedError: If zero faces are found.
            MultipleFacesDetectedError: If multiple faces are detected and require_single_face is True.
        """
        self.load_model()

        if image.mode != "RGB":
            image = image.convert("RGB")

        width, height = image.size
        rgb_array = np.array(image)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_array)

        # Thread-safe inference
        with self._inference_lock:
            detection_result = self._landmarker.detect(mp_image)

        face_landmarks_list = detection_result.face_landmarks
        faces_detected = len(face_landmarks_list)

        if faces_detected == 0:
            raise NoFaceDetectedError()

        if faces_detected > 1 and require_single_face:
            raise MultipleFacesDetectedError(face_count=faces_detected)

        # Select target face (either the single detected face or the primary face)
        if faces_detected == 1:
            target_landmarks = face_landmarks_list[0]
        else:
            target_landmarks = self._select_primary_face(face_landmarks_list, width, height)

        # Convert landmarks to structured models with both normalized and pixel coordinates
        landmarks: List[FacialLandmark] = []
        for idx, lm in enumerate(target_landmarks):
            norm_x = float(lm.x)
            norm_y = float(lm.y)
            norm_z = float(lm.z)

            # Convert to pixel space using preprocessed image dimensions
            pixel_x = round(norm_x * width, 2)
            pixel_y = round(norm_y * height, 2)

            landmarks.append(
                FacialLandmark(
                    index=idx,
                    x=norm_x,
                    y=norm_y,
                    z=norm_z,
                    pixel_x=pixel_x,
                    pixel_y=pixel_y,
                )
            )

        return FaceDetectionResult(
            image_width=width,
            image_height=height,
            faces_detected=faces_detected,
            landmarks=landmarks,
        )

    def detect_landmarks_from_bytes(
        self,
        file_bytes: bytes,
        require_single_face: bool = True,
    ) -> FaceDetectionResult:
        """Validate, preprocess, and detect landmarks directly from raw upload bytes.

        Reuses the Phase 1 image validation and preprocessing pipeline.

        Args:
            file_bytes: Raw binary bytes of uploaded image.
            require_single_face: Policy flag for handling multi-face portraits.

        Returns:
            FaceDetectionResult containing image metadata and landmarks.
        """
        processed_img, _, _, _ = preprocess_to_pil(file_bytes)
        return self.detect_landmarks(processed_img, require_single_face=require_single_face)


# ---------------------------------------------------------------------------
# Global Service Singleton
# ---------------------------------------------------------------------------

_global_face_detector_service: Optional[FaceDetectorService] = None
_service_init_lock = threading.Lock()


def get_face_detector_service(model_path: Optional[str] = None) -> FaceDetectorService:
    """Retrieve or initialize the singleton FaceDetectorService instance."""
    global _global_face_detector_service
    if _global_face_detector_service is None or (
        model_path is not None and _global_face_detector_service.model_path != model_path
    ):
        with _service_init_lock:
            if _global_face_detector_service is None or (
                model_path is not None and _global_face_detector_service.model_path != model_path
            ):
                _global_face_detector_service = FaceDetectorService(model_path=model_path)
    return _global_face_detector_service

