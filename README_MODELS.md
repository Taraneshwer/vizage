# Model Specifications

This document outlines the architecture, pipeline, and requirements for the AI models integrated into Vizage.

## 1. Inference Pipeline Overview
`Raw Frame -> YOLO (Detection) -> ByteTrack (Tracking) -> MediaPipe (Alignment) -> AdaFace (Recognition)`

## 2. Model Details

### YOLO Face Detector
- **Purpose**: Detect faces and masked faces accurately.
- **Architecture**: Ultralytics YOLOv11 (Nano/Small).
- **Optimization**: Exported to `.onnx` and `.engine` (TensorRT) with dynamic batching.
- **Classes**: `0: face`, `1: masked_face`.

### ByteTrack
- **Purpose**: Persistent tracking of individuals across frames.
- **Thresholds**: Configurable in `config.py` (`TRACK_THRESH`, `MATCH_THRESH`, `TRACK_BUFFER`).
- **Integration**: Handled directly via `TrackerService` wrapping Ultralytics tracking logic.

### MediaPipe FaceMesh
- **Purpose**: Extremely fast facial landmark extraction (468 points).
- **Usage**: Used to locate eye centers for ArcFace/AdaFace affine transformation alignment.

### AdaFace
- **Purpose**: Generate 512-dimensional robust face embeddings.
- **Architecture**: ResNet-based backbone (IR50/IR100) tuned with ArcFace Margin Loss.
- **Mask Robustness**: The pipeline conditionally feeds only the upper half of the face to AdaFace if a mask is detected, ensuring stable embeddings regardless of mask status.
- **Optimization**: Converted to ONNX using `onnxruntime` for accelerated CPU/GPU execution outside of PyTorch.

## 3. Final Model Sizes (Estimates)
- YOLO (v11n): ~12 MB (`.pt`), ~25 MB (`.onnx`)
- AdaFace (IR50): ~170 MB (`.pth`), ~170 MB (`.onnx`)

## 4. Required Formats for Production
For optimal real-time backend performance:
- Ensure you have the `.onnx` or `.engine` variations of the models.
- Place them in the configured model directories and update `.env` or `config.py` accordingly.
