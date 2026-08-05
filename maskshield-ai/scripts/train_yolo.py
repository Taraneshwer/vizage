import os
from pathlib import Path
import argparse
import logging

try:
    from ultralytics import YOLO
except ImportError:
    YOLO = None

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def train_yolo(data_yaml: str, epochs: int = 100, batch_size: int = 16, imgsz: int = 640, device: str = '', resume: bool = False, model_path: str = 'yolo11n.pt'):
    """
    Trains a YOLO model for face and masked face detection.
    """
    if YOLO is None:
        logger.error("Ultralytics package is not installed. Please install it using 'pip install ultralytics'.")
        return

    logger.info(f"Starting YOLO training. Model: {model_path}, Data: {data_yaml}, Epochs: {epochs}")
    
    # Check for existing checkpoint for auto-resume
    project_dir = Path('runs/train').absolute()
    last_pt = project_dir / 'yolo_mask_face' / 'weights' / 'last.pt'
    if last_pt.exists():
        logger.info(f"Found checkpoint at {last_pt}. Auto-resuming training...")
        model_path = str(last_pt)
        resume = True
    
    # Load a model
    model = YOLO(model_path) 
        
    # Train the model
    try:
        results = model.train(
            data=data_yaml,
            epochs=epochs,
            batch=batch_size,
            imgsz=imgsz,
            device=device,
            resume=resume,
            project=str(project_dir),
            name='yolo_mask_face',
            exist_ok=True,
            patience=15,          # Early stopping
            amp=True,             # Mixed precision
            workers=8,
            save_period=1         # Save checkpoint every epoch
        )
    except KeyboardInterrupt:
        logger.warning("Training interrupted by user. YOLO automatically saves last.pt gracefully.")
        return
    
    logger.info(f"Training completed. Results saved to {results.save_dir}")
    
    # Export the model
    logger.info("Exporting to ONNX and Engine...")
    try:
        model.export(format='onnx', dynamic=True)
    except Exception as e:
        logger.warning(f"Failed to export to ONNX: {e}")
        
    try:
        model.export(format='engine', dynamic=True, workspace=4, half=True)
    except Exception as e:
        logger.warning(f"Failed to export to TensorRT engine: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train YOLO for face/mask detection.")
    parser.add_argument('--data', type=str, default='../datasets/processed/yolo/data.yaml', help='Path to data.yaml')
    parser.add_argument('--epochs', type=int, default=100, help='Number of training epochs')
    parser.add_argument('--batch', type=int, default=16, help='Batch size')
    parser.add_argument('--imgsz', type=int, default=640, help='Image size')
    parser.add_argument('--device', type=str, default='', help='Device to run on (e.g., 0 or cpu)')
    parser.add_argument('--resume', action='store_true', help='Resume training')
    parser.add_argument('--model', type=str, default='yolo11n.pt', help='Base model path or name')
    
    args = parser.parse_args()
    
    data_yaml_path = Path(args.data).absolute()
    if not data_yaml_path.exists():
        logger.error(f"Data file not found: {data_yaml_path}. Please run prepare_dataset.py first.")
    else:
        train_yolo(
            data_yaml=str(data_yaml_path),
            epochs=args.epochs,
            batch_size=args.batch,
            imgsz=args.imgsz,
            device=args.device,
            resume=args.resume,
            model_path=args.model
        )
