# Training the AI Models

This guide covers how to prepare the datasets, fine-tune the YOLO detector, and fine-tune the AdaFace model using the provided MaskShield-AI scripts.

## 1. Dataset Preparation

Before training, you must process the raw datasets to clean, align, and format them for both YOLO and AdaFace.

1. Ensure `archive (1).zip` (Masked faces) and `archive (2).zip` (LFW) are extracted into `maskshield-ai/datasets/`.
2. Run the preparation script:
```bash
cd maskshield-ai/scripts
python prepare_dataset.py
```
This script will:
- Remove duplicates based on MD5 hashes.
- Filter out corrupt and highly blurry images.
- Align faces using MediaPipe (for ArcFace format).
- Create a `processed/yolo` directory with `data.yaml` and YOLO labels.
- Create a `processed/arcface` directory containing aligned faces grouped by identity.

## 2. Training YOLO (Face & Mask Detection)

We use Ultralytics YOLOv11 for real-time face and masked-face detection.

1. Start training using the generated `data.yaml`:
```bash
python train_yolo.py --data ../datasets/processed/yolo/data.yaml --epochs 100 --batch 16
```
2. The script will output the best weights to `runs/train/yolo_mask_face/weights/best.pt`.
3. It will automatically attempt to export the model to ONNX and TensorRT formats.

## 3. Training AdaFace (Recognition)

We use an ArcFace-style training loop for AdaFace using the aligned LFW and Masked dataset.

1. Start training:
```bash
python train_adaface.py --data ../datasets/processed/arcface --epochs 20 --batch 64
```
2. The script applies mixed-precision training (if CUDA is available).
3. The best model is saved to `runs/adaface/best_adaface.pth` and automatically exported to `best_adaface.onnx`.

## 4. Evaluation

To evaluate the models and compute metrics (mAP, ROC, etc.):

```bash
python evaluate.py --task all
```

You can also evaluate individual models by setting `--task yolo` or `--task adaface`.
