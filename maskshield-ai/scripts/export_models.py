import argparse
import logging
from pathlib import Path
import shutil

try:
    from ultralytics import YOLO
except ImportError:
    YOLO = None

try:
    import torch
except ImportError:
    torch = None

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def export_yolo(model_path: str, output_dir: str):
    if YOLO is None:
        logger.error("ultralytics is not installed.")
        return
        
    logger.info(f"Exporting YOLO Model: {model_path}")
    model = YOLO(model_path)
    
                 
    try:
        onnx_path = model.export(format='onnx', dynamic=True)
        shutil.copy(onnx_path, Path(output_dir) / 'best_yolo.onnx')
        logger.info(f"YOLO ONNX exported to {output_dir}/best_yolo.onnx")
    except Exception as e:
        logger.error(f"Failed to export YOLO ONNX: {e}")
        
                     
    try:
        engine_path = model.export(format='engine', dynamic=True, workspace=4, half=True)
        shutil.copy(engine_path, Path(output_dir) / 'best_yolo.engine')
        logger.info(f"YOLO Engine exported to {output_dir}/best_yolo.engine")
    except Exception as e:
        logger.warning(f"Failed to export YOLO TensorRT (might require Linux/CUDA with TRT installed): {e}")

def export_adaface(model_path: str, output_dir: str):
    if torch is None:
        logger.error("PyTorch is not installed.")
        return
        
    logger.info(f"Exporting AdaFace Model: {model_path}")
    
                                                   
    import torchvision.models as models
    import torch.nn as nn
    
    model = models.resnet50(pretrained=False)
    model.fc = nn.Linear(model.fc.in_features, 512)
    
    try:
        model.load_state_dict(torch.load(model_path, map_location='cpu'))
    except Exception as e:
        logger.error(f"Failed to load AdaFace weights: {e}")
        return
        
    model.eval()
    dummy_input = torch.randn(1, 3, 112, 112)
    
    onnx_path = Path(output_dir) / 'best_adaface.onnx'
    
    try:
        torch.onnx.export(model, dummy_input, onnx_path,
                          input_names=['input'], output_names=['output'],
                          dynamic_axes={'input': {0: 'batch_size'}, 'output': {0: 'batch_size'}})
        logger.info(f"AdaFace ONNX exported to {onnx_path}")
    except Exception as e:
        logger.error(f"Failed to export AdaFace ONNX: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export models to ONNX/TensorRT.")
    parser.add_argument('--yolo_model', type=str, default='runs/train/yolo_mask_face/weights/best.pt')
    parser.add_argument('--adaface_model', type=str, default='runs/adaface/best_adaface.pth')
    parser.add_argument('--output_dir', type=str, default='../models')
    
    args = parser.parse_args()
    
    Path(args.output_dir).mkdir(parents=True, exist_ok=True)
    
    if Path(args.yolo_model).exists():
        export_yolo(args.yolo_model, args.output_dir)
    else:
        logger.warning(f"YOLO model not found at {args.yolo_model}")
        
    if Path(args.adaface_model).exists():
        export_adaface(args.adaface_model, args.output_dir)
    else:
        logger.warning(f"AdaFace model not found at {args.adaface_model}")
