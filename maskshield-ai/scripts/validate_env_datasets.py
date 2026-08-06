import os
import sys
import subprocess
import argparse
import json
from pathlib import Path

def ensure_dependencies():
    required = ["cv2", "torch", "ultralytics", "onnxruntime", "numpy", "pandas", "sklearn", "tqdm", "PIL", "matplotlib", "albumentations", "timm", "yaml", "mediapipe", "psutil"]
    missing = []
    for req in required:
        try:
            __import__(req)
        except ImportError:
            missing.append(req)
    
    if missing:
        print(f"[INFO] Missing dependencies detected: {missing}. Attempting automatic installation...")
        req_file = Path(__file__).resolve().parent.parent / "requirements.txt"
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", str(req_file)])
                           
            for req in required:
                __import__(req)
            print("[INFO] All dependencies successfully installed and verified.")
        except Exception as e:
            print(f"[ERROR] Dependency installation failed: {e}")
            sys.exit(1)
    else:
        print("[INFO] All required Python dependencies are present.")

                                                       
ensure_dependencies()

import torch
import psutil
import cv2
import yaml
from ultralytics import YOLO

def gather_hardware_info():
    info = {}
    info['python_version'] = sys.version.split(' ')[0]
    info['pytorch_version'] = torch.__version__
    info['cuda_available'] = torch.cuda.is_available()
    info['cuda_version'] = torch.version.cuda if info['cuda_available'] else "N/A"
    info['cudnn_version'] = torch.backends.cudnn.version() if info['cuda_available'] else "N/A"
    
    if info['cuda_available']:
        info['gpu_name'] = torch.cuda.get_device_name(0)
        info['gpu_memory_gb'] = round(torch.cuda.get_device_properties(0).total_memory / (1024**3), 2)
    else:
        info['gpu_name'] = "N/A"
        info['gpu_memory_gb'] = "N/A"

    info['ram_gb'] = round(psutil.virtual_memory().total / (1024**3), 2)
    info['cpu_cores'] = psutil.cpu_count(logical=True)
    return info

def generate_pseudo_labels(images_dir, labels_dir):
    print("[WARNING] YOLO labels are missing. Generating pseudo-labels using pretrained YOLOv8n-face...")
    os.makedirs(labels_dir, exist_ok=True)
                                                                                                             
                                                                                                              
    model = YOLO("yolov8n.pt") 
    
    image_paths = list(Path(images_dir).glob("*.jpg")) + list(Path(images_dir).glob("*.png"))
    if not image_paths:
        print("[ERROR] No images found to pseudo-label.")
        sys.exit(1)
        
    for img_path in image_paths:
        results = model(str(img_path), classes=[0], verbose=False)              
        label_path = Path(labels_dir) / f"{img_path.stem}.txt"
        with open(label_path, 'w') as f:
            for r in results:
                boxes = r.boxes
                for box in boxes:
                                                             
                    x, y, w, h = box.xywhn[0]
                    f.write(f"0 {x:.6f} {y:.6f} {w:.6f} {h:.6f}\n")
    print(f"[INFO] Generated pseudo-labels for {len(image_paths)} images.")

def verify_datasets(base_path):
    stats = {}
    
                               
    yolo_dir = base_path / "processed" / "yolo"
    yolo_images = yolo_dir / "images" / "train"
    yolo_labels = yolo_dir / "labels" / "train"
    yolo_yaml = yolo_dir / "data.yaml"
    
    if not yolo_yaml.exists():
        print("[ERROR] YOLO data.yaml is missing.")
        sys.exit(1)
        
    if not yolo_images.exists():
        print(f"[ERROR] YOLO images directory {yolo_images} is missing.")
        sys.exit(1)
        
    if not yolo_labels.exists() or len(list(yolo_labels.glob("*.txt"))) == 0:
        generate_pseudo_labels(yolo_images, yolo_labels)
        
    num_yolo_images = len(list(yolo_images.glob("*.jpg"))) + len(list(yolo_images.glob("*.png")))
    num_yolo_labels = len(list(yolo_labels.glob("*.txt")))
    
    stats['yolo_train_images'] = num_yolo_images
    stats['yolo_train_labels'] = num_yolo_labels
    
                                  
    arcface_dir = base_path / "processed" / "arcface" / "train"
    if not arcface_dir.exists():
        print(f"[ERROR] AdaFace identity directory {arcface_dir} is missing.")
        sys.exit(1)
        
    identities = [d for d in arcface_dir.iterdir() if d.is_dir()]
    valid_identities = 0
    total_identity_images = 0
    for identity in identities:
        imgs = list(identity.glob("*.jpg")) + list(identity.glob("*.png"))
        if len(imgs) >= 1:
            valid_identities += 1
            total_identity_images += len(imgs)
        else:
            print(f"[WARNING] Identity folder {identity.name} contains no images.")
            
    if valid_identities == 0:
        print("[ERROR] No valid identities found for AdaFace training.")
        sys.exit(1)
        
    stats['adaface_identities'] = valid_identities
    stats['adaface_images'] = total_identity_images
    
    return stats

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-gpu", action="store_true", help="Abort if GPU is not available.")
    parser.add_argument("--step", type=str, choices=["env", "data"], default="env", help="Which validation step to run.")
    args = parser.parse_args()

    if args.step == "env":
        print("\n--- Hardware & Environment Summary ---")
        hw_info = gather_hardware_info()
        for k, v in hw_info.items():
            print(f"{k}: {v}")
            
        if not hw_info['cuda_available']:
            print("\n[WARNING] CUDA is NOT available. Operations will fall back to CPU.")
            if args.require_gpu:
                print("[ERROR] --require-gpu was specified, but no CUDA GPU was found. Aborting.")
                sys.exit(1)
            print("[INFO] Proceeding with CPU. Mixed precision will be disabled by framework defaults.")
        else:
            print("\n[INFO] CUDA is available. GPU execution and mixed precision enabled.")
            
        summary_path = Path(__file__).resolve().parent.parent / "validation_summary.json"
        summary = {"hardware": hw_info, "datasets": {}}
        with open(summary_path, "w") as f:
            json.dump(summary, f, indent=4)
        print("[INFO] Environment validation complete.")

    elif args.step == "data":
        print("\n--- Dataset Verification ---")
        base_path = Path(__file__).resolve().parent.parent / "datasets"
        dataset_stats = verify_datasets(base_path)
        
        for k, v in dataset_stats.items():
            print(f"{k}: {v}")

        summary_path = Path(__file__).resolve().parent.parent / "validation_summary.json"
        if summary_path.exists():
            with open(summary_path, "r") as f:
                summary = json.load(f)
        else:
            summary = {"hardware": {}, "datasets": {}}
            
        summary["datasets"] = dataset_stats
        
        with open(summary_path, "w") as f:
            json.dump(summary, f, indent=4)
            
        print("[INFO] Dataset validation complete. Ready for training.")

if __name__ == "__main__":
    main()
