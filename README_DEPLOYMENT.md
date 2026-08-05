# Vizage Deployment Guide

## 1. Hardware Requirements

### Minimum (CPU-only)
- CPU: 4+ Cores (e.g., Intel i5 / AMD Ryzen 5)
- RAM: 8 GB
- OS: Windows 10/11 or Linux
- Expected Performance: ~5-10 FPS (depending on ONNX optimization)

### Recommended (GPU)
- CPU: 8+ Cores
- RAM: 16 GB
- GPU: NVIDIA RTX 3060 or better (with CUDA & TensorRT support)
- Expected Performance: 30+ FPS (Real-time)

## 2. Environment Setup

1. Create a Python Virtual Environment:
```bash
python -m venv .venv
source .venv/Scripts/activate  # Windows
```

2. Install Requirements:
```bash
pip install -r backend/requirements.txt
```

3. Configure `.env` file in the `backend/` directory:
```env
YOLO_MODEL_PATH=models/best_yolo.onnx
ADAFACE_MODEL_PATH=models/best_adaface.onnx
EXECUTION_PROVIDER=CUDA
TRACK_THRESH=0.5
```

## 3. Optimizations for Real-Time

To ensure the backend runs at maximum FPS:
1. **Execution Provider**: Set `EXECUTION_PROVIDER=CUDA` or `TensorRT` in your environment.
2. **ONNX Runtime**: The backend automatically falls back to ONNX Runtime for AdaFace and YOLO (if `.onnx` weights are provided), bypassing PyTorch overhead.
3. **Lazy Loading**: The `ModelManager` handles memory loading gracefully. If VRAM is exceeded, it will error safely without crashing the OS.
4. **FP16 Inference**: If using TensorRT, models are automatically cast to FP16.

## 4. Running the Backend

```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1
```
*(Note: We use 1 worker for the AI backend to prevent VRAM duplication. Concurrency is handled asynchronously by FastAPI).*

## 5. Running the Frontend

```bash
cd frontend
npm install
npm run dev
```

## 6. Manual Steps Remaining
- The backend relies on an active SQLite DB. Ensure `vizage.db` is correctly migrated.
- Ensure CUDA and cuDNN versions match your ONNX Runtime / PyTorch installations.
