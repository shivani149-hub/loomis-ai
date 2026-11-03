# Phase 1 Report: Image Upload and Preprocessing

## 1. Phase Objective

The objective of **Phase 1: Image Upload and Preprocessing** is to build a secure, robust, and in-memory image ingestion and preprocessing pipeline for **Loomis AI**.

In accordance with Phase 1 constraints:
- No face detection or landmark extraction models (such as MediaPipe) have been introduced yet.
- No Loomis geometry calculation or drawing stage generation has been implemented yet.
- No frontend UI has been built.
- All image operations are performed strictly in memory (`io.BytesIO`) without persisting uploaded portraits to disk.
- No sensitive image data or base64 strings are leaked into application logs.
- Strict validation protects against malformed files, unsupported formats, excessive dimensions, and oversized payloads.

---

## 2. Features Implemented

1. **FastAPI Application & Routing**:
   - Initialized the core application in `backend/main.py`.
   - Implemented `GET /api/health` providing service health status and versioning.
   - Implemented `POST /api/images/preprocess` accepting multipart portrait uploads.
   - Configured CORS middleware for seamless integration with future web and mobile clients.
   - Configured custom exception handlers mapping domain validation errors into standard HTTP error responses.

2. **Multi-Stage Image Validation (`backend/services/image_validator.py`)**:
   - **Content-Based Verification**: Validates image binary data using Pillow (`Image.open`, `verify()`, and pixel load) instead of trusting client-supplied filename extensions or `Content-Type` headers.
   - **Supported Formats**: Strictly allows JPEG, PNG, and WebP.
   - **Payload Size Ceiling**: Enforces a strict 10 MB upload ceiling via chunked stream monitoring, rejecting oversized files early (`413 Content Too Large`).
   - **Empty Payload Rejection**: Immediately detects 0-byte uploads (`400 Bad Request`).
   - **Decompression Bomb & Dimension Protection**: Blocks images with dimensions exceeding 8192px on either axis (`400 Bad Request`).
   - **Data Integrity & Truncation**: Catches damaged image headers, truncated streams, and malformed files.

3. **In-Memory Preprocessing Pipeline (`backend/services/image_processor.py`)**:
   - **EXIF Orientation Auto-Correction**: Extracts EXIF orientation tags (e.g. tag 6 for 90-degree portrait rotation from smartphones) and rotates pixels upright via `ImageOps.exif_transpose`.
   - **Color Channel Normalization**: Converts all image modes (RGBA, LA, P, CMYK, grayscale) to standard 3-channel RGB. Transparent pixels are cleanly flattened over a solid white backdrop.
   - **Proportional Scaling**: Downsizes images whose maximum dimension exceeds 1024px using high-fidelity Lanczos resampling while preserving exact aspect ratios (preventing facial distortion). Images already \(\le\) 1024px are preserved without upscaling.
   - **In-Memory Base64 JPEG Encoding**: Encodes the normalized image as JPEG (`quality=90`) directly into an in-memory byte buffer and encodes it to Base64 for the API response.
   - **Metadata Preservation**: Records original dimensions, processed dimensions, source format, and output format.

4. **Automated Testing Suite (`backend/tests/`)**:
   - Authored 15 comprehensive automated test cases with pytest covering all positive scenarios, boundary conditions, and error states.

---

## 3. Files Created or Modified

| File Path | Status | Description |
|---|---|---|
| `backend/main.py` | Created | Core FastAPI application, route handlers, error handlers, and CORS setup |
| `backend/requirements.txt` | Created | Pinned Python dependencies for Phase 1 (FastAPI, Uvicorn, Pillow, Pytest, etc.) |
| `requirements.txt` | Created | Root pointer referencing `backend/requirements.txt` |
| `backend/README.md` | Created | Developer guide, virtual environment setup, and local execution instructions |
| `backend/schemas/health.py` | Created | Pydantic schema for `GET /api/health` |
| `backend/schemas/image.py` | Created | Pydantic schema for `POST /api/images/preprocess` response |
| `backend/schemas/__init__.py` | Created | Package export for schemas |
| `backend/services/image_validator.py` | Created | Multi-stage image content, format, size, and dimension validation service |
| `backend/services/image_processor.py` | Created | EXIF rotation, RGB normalization, aspect-ratio resizing, and Base64 encoder |
| `backend/services/__init__.py` | Created | Package export for domain services |
| `backend/tests/test_health.py` | Created | Unit test for health check endpoint |
| `backend/tests/test_image_upload.py` | Created | Comprehensive test suite for uploads, validation, resizing, and errors |
| `backend/tests/__init__.py` | Created | Package export for test suite |
| `docs/phase-reports/phase-1.md` | Created | Phase 1 milestone report and verification audit |
| `README.md` | Modified | Updated with Phase 1 completion, backend architecture, and setup instructions |
| `docs/implementation-roadmap.md` | Modified | Updated Phase 1 status to Completed |

---

## 4. Dependencies and Their Purpose

| Package | Version Specifier | Purpose in Phase 1 |
|---|---|---|
| `fastapi` | `>=0.110.0,<0.129.0` | High-performance asynchronous REST API framework |
| `uvicorn[standard]` | `>=0.28.0,<0.41.0` | Production ASGI web server running the FastAPI application |
| `python-multipart` | `>=0.0.9,<0.0.33` | Streaming multipart/form-data parser for file uploads |
| `pydantic` | `>=2.6.0,<2.13.0` | Request and response schema definition, validation, and serialization |
| `pydantic-settings` | `>=2.2.0,<2.16.0` | Environment settings and configuration management |
| `pillow` | `>=10.2.0,<14.0.0` | Pure-Python image processing (decoding, EXIF orientation, RGB, resizing, encoding) |
| `pytest` | `>=8.0.0,<10.0.0` | Automated test runner for unit and integration tests |
| `httpx` | `>=0.27.0,<0.29.0` | High-performance HTTP client used by FastAPI `TestClient` |

*Note: MediaPipe, OpenCV, and NumPy are deliberately excluded from this phase and will be added in Phase 2/3 for landmark and face detection.*

---

## 5. API Endpoint Details

### 5.1 Health Check
- **Endpoint**: `GET /api/health`
- **Auth**: None
- **Response**: `200 OK`
```json
{
  "status": "healthy",
  "service": "loomis-ai-backend",
  "version": "0.1.0"
}
```

### 5.2 Image Preprocessing
- **Endpoint**: `POST /api/images/preprocess`
- **Request Format**: `multipart/form-data`
- **Form Field**: `file` (binary image data)
- **Supported File Types**: JPEG, PNG, WebP
- **Maximum Size**: 10 MB (10,485,760 bytes)
- **Successful Response**: `200 OK`
```json
{
  "success": true,
  "message": "Image preprocessed successfully.",
  "original_width": 2048,
  "original_height": 1536,
  "processed_width": 1024,
  "processed_height": 768,
  "original_format": "JPEG",
  "processed_format": "JPEG",
  "image_base64": "/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0aHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/...",
  "processing_status": "success"
}
```
- **Error Responses**:
  - `400 Bad Request`: Empty file, corrupted image data, or dimensions exceeding 8192px.
  - `413 Content Too Large`: File exceeds 10 MB limit.
  - `415 Unsupported Media Type`: Non-supported image format (e.g. GIF, TIFF, BMP).

---

## 6. Image Preprocessing Explanation

### Step 1: Content Inspection
The service does not trust file extensions or HTTP headers. It passes the raw byte stream to `PIL.Image.open()`, inspects the internal format tag, and calls `verify()` to ensure file structure validity.

### Step 2: Orientation Correction
Mobile portraits frequently contain EXIF orientation metadata (e.g., orientation flag 6 indicates a 90° clockwise rotation). The service applies `ImageOps.exif_transpose()` to rotate pixel arrays upright, ensuring downstream computer vision processes canonical orientation.

### Step 3: Color Normalization
Various formats contain alpha transparency channels (PNG RGBA) or index palettes ('P' mode). To prevent black artifact borders, images with alpha channels are composited over a clean white background canvas (`RGB(255, 255, 255)`) and converted to 3-channel RGB.

### Step 4: Proportional Resizing
Face landmark detection algorithms operate optimally on images standardized to a consistent scale. Images with any dimension exceeding 1024px are downscaled using high-quality Lanczos interpolation. The scale factor is calculated uniformly:
$$\text{scale} = \frac{1024}{\max(\text{width}, \text{height})}$$
$$\text{new\_width} = \text{round}(\text{width} \times \text{scale}), \quad \text{new\_height} = \text{round}(\text{height} \times \text{scale})$$
Aspect ratio is strictly preserved, preventing anatomical distortion. Images already smaller than 1024px are left untouched to prevent artificial blurring from upscaling.

### Step 5: Memory-Only Base64 Encoding
The processed image is saved as a JPEG stream into `io.BytesIO()` with `quality=90` and `optimize=True`. It is immediately converted to a Base64 string and delivered in the response payload. No temporary or permanent files are written to the filesystem.

---

## 7. Tests Executed and Actual Results

The automated test suite in `backend/tests/` was executed against Python 3.12.5.

```text
============================= test session starts =============================
platform win32 -- Python 3.12.5, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\shanm\OneDrive\Desktop\loomis-ai
plugins: anyio-4.12.1
collected 15 items

backend/tests/test_health.py::test_health_check_returns_200_and_expected_payload PASSED [  6%]
backend/tests/test_image_upload.py::test_valid_jpeg_upload PASSED        [ 13%]
backend/tests/test_image_upload.py::test_valid_png_with_transparency_upload PASSED [ 20%]
backend/tests/test_image_upload.py::test_valid_webp_upload PASSED        [ 26%]
backend/tests/test_image_upload.py::test_image_resizing_larger_than_1024_landscape PASSED [ 33%]
backend/tests/test_image_upload.py::test_image_resizing_larger_than_1024_portrait PASSED [ 40%]
backend/tests/test_image_upload.py::test_image_resizing_smaller_than_1024_not_upscaled PASSED [ 46%]
backend/tests/test_image_upload.py::test_exif_orientation_transposition PASSED [ 53%]
backend/tests/test_image_upload.py::test_empty_file_upload_rejected PASSED [ 60%]
backend/tests/test_image_upload.py::test_unsupported_image_format_rejected PASSED [ 66%]
backend/tests/test_image_upload.py::test_mismatched_extension_detected_by_content PASSED [ 73%]
backend/tests/test_image_upload.py::test_non_image_text_file_rejected PASSED [ 80%]
backend/tests/test_image_upload.py::test_corrupted_image_bytes_rejected PASSED [ 86%]
backend/tests/test_image_upload.py::test_file_exceeding_10mb_limit_rejected PASSED [ 93%]
backend/tests/test_image_upload.py::test_excessive_dimensions_protection PASSED [100%]

============================= 15 passed in 1.79s ==============================
```

Live server execution was also verified by starting a Uvicorn instance on port 8008 and issuing real HTTP requests:
- `GET /api/health`: Returned `200 OK` with valid health payload.
- `POST /api/images/preprocess`: Processed a 1600x1200 JPEG, returning `200 OK` and downscaling to 1024x768 with exact aspect ratio preserved.

---

## 8. Known Limitations

- **No Face Detection Yet**: In accordance with the Phase 1 scope, the endpoint does not verify whether the uploaded image contains a face. Non-face images (e.g. landscape photos) will be successfully resized; face validation will be added in Phase 2.
- **Base64 Payload Size**: For Phase 1, images are returned inline as Base64 strings. For larger production volumes, session-based ephemeral URLs or object storage caching may be introduced.

---

## 9. Phase Completion Status

- **Status**: **COMPLETED**
- **Verification Result**: 15 / 15 tests passed. Live server verified.
- **Next Phase**: Phase 2 – Face Detection (pending user review).

