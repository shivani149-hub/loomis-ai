# Loomis AI – Backend Setup & Guide

## Phase 1: Image Upload and Preprocessing

The Loomis AI backend is built with **FastAPI** and **Pillow**, designed to ingest portrait photographs, validate their structural integrity, apply orientation corrections, and produce normalized images for downstream computer vision and geometric processing.

---

## 🐍 Python Virtual Environment Setup Guide

### 1. Prerequisites
- Python 3.10+ (tested on Python 3.12.5)
- `pip` package manager

### 2. Creating a Virtual Environment

Open a terminal in the project root (`loomis-ai/`):

#### On Windows (PowerShell):
```powershell
# Create the virtual environment inside .venv
python -m venv .venv

# Activate the virtual environment
.venv\Scripts\Activate.ps1
```

*(If script execution is disabled in PowerShell, run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` once).*

#### On Windows (Command Prompt `cmd`):
```cmd
python -m venv .venv
.venv\Scripts\activate.bat
```

#### On macOS / Linux (bash/zsh):
```bash
python3 -m venv .venv
source .venv/bin/activate
```

---

## 📦 Installing Dependencies

Once the virtual environment is activated, install the required packages:

```bash
# From repository root
pip install -r backend/requirements.txt

# Or from within the backend/ folder
cd backend
pip install -r requirements.txt
```

---

## 🚀 Running the Backend Server

Start the local development server using Uvicorn:

```bash
# From repository root
uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

The server will be accessible at:
- **API Base URL**: `http://127.0.0.1:8000`
- **Interactive OpenAPI Documentation (Swagger UI)**: `http://127.0.0.1:8000/docs`
- **Alternative ReDoc Documentation**: `http://127.0.0.1:8000/redoc`

---

## 🧪 Running the Test Suite

Execute the automated test suite with `pytest`:

```bash
# Run all backend tests with verbose output
python -m pytest backend/tests -v
```

---

## 📡 API Endpoints (Phase 1)

### 1. Health Check
- **Route**: `GET /api/health`
- **Description**: Verifies that the backend API service is running and healthy.
- **Response**: `200 OK`
  ```json
  {
    "status": "healthy",
    "service": "loomis-ai-backend",
    "version": "0.1.0"
  }
  ```

### 2. Image Preprocessing
- **Route**: `POST /api/images/preprocess`
- **Description**: Ingests a portrait photograph, validates content integrity, auto-rotates EXIF orientation, converts color space to RGB, proportionally downsizes to a maximum dimension of 1024px, and returns a Base64-encoded JPEG in memory.
- **Request**: `multipart/form-data` with field `file` (JPEG, PNG, or WebP).
- **Constraints**:
  - Maximum upload size: 10 MB.
  - Allowed image formats: JPEG, PNG, WebP.
  - Decompression bomb guard: 8192px maximum dimension.
- **Response**: `200 OK`
  ```json
  {
    "success": true,
    "message": "Image preprocessed successfully.",
    "original_width": 2000,
    "original_height": 1000,
    "processed_width": 1024,
    "processed_height": 512,
    "original_format": "JPEG",
    "processed_format": "JPEG",
    "image_base64": "/9j/4AAQSkZJRgABAQAAAQABAAD...",
    "processing_status": "success"
  }
  ```

