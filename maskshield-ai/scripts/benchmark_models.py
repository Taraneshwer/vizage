import os
import sys
import time
import psutil
import torch
import onnxruntime as ort
from pathlib import Path
import json

backend_dir = Path(__file__).resolve().parent.parent.parent / "backend"
sys.path.append(str(backend_dir))

def benchmark_pytorch(model_path: str, input_tensor: torch.Tensor, warmup=100, iters=500):
    try:
        from ultralytics import YOLO
        model = YOLO(model_path)
    except Exception as e:
        print(f"Failed to load PyTorch model {model_path}: {e}")
        return None
        
    # Warmup
    for _ in range(warmup):
        _ = model(input_tensor)
        
    # Benchmark
    start_time = time.time()
    for _ in range(iters):
        _ = model(input_tensor)
    end_time = time.time()
    
    latency = (end_time - start_time) / iters * 1000  # ms
    fps = 1000 / latency if latency > 0 else 0
    return {"latency_ms": latency, "fps": fps}

def benchmark_onnx(model_path: str, input_array, warmup=100, iters=500):
    try:
        session = ort.InferenceSession(model_path, providers=['CPUExecutionProvider'])
        input_name = session.get_inputs()[0].name
    except Exception as e:
        print(f"Failed to load ONNX model {model_path}: {e}")
        return None
        
    # Warmup
    for _ in range(warmup):
        _ = session.run(None, {input_name: input_array})
        
    # Benchmark
    start_time = time.time()
    for _ in range(iters):
        _ = session.run(None, {input_name: input_array})
    end_time = time.time()
    
    latency = (end_time - start_time) / iters * 1000  # ms
    fps = 1000 / latency if latency > 0 else 0
    return {"latency_ms": latency, "fps": fps}

def run_benchmarks():
    print("--- Model Benchmarking ---")
    process = psutil.Process(os.getpid())
    print(f"Initial RAM usage: {process.memory_info().rss / 1024**2:.2f} MB")
    
    yolo_pt = "yolo11n.pt"  # PyTorch
    yolo_onnx = str(backend_dir / "models" / "production" / "best_yolo.onnx")
    
    # 1x3x640x640 random tensor for YOLO
    dummy_input_pt = torch.rand(1, 3, 640, 640)
    dummy_input_np = dummy_input_pt.numpy()
    
    results = {}
    
    print("\nBenchmarking YOLO (PyTorch)...")
    res_pt = benchmark_pytorch(yolo_pt, dummy_input_pt)
    if res_pt:
        print(f"  PyTorch Latency: {res_pt['latency_ms']:.2f} ms | FPS: {res_pt['fps']:.2f}")
        results['PyTorch'] = res_pt
        
    print("\nBenchmarking YOLO (ONNX Runtime)...")
    res_onnx = benchmark_onnx(yolo_onnx, dummy_input_np)
    if res_onnx:
        print(f"  ONNX Latency: {res_onnx['latency_ms']:.2f} ms | FPS: {res_onnx['fps']:.2f}")
        results['ONNX'] = res_onnx
        
    print(f"\nFinal RAM usage: {process.memory_info().rss / 1024**2:.2f} MB")
    print(f"CPU Utilization: {psutil.cpu_percent()}%")
    
    with open('benchmark_results.json', 'w') as f:
        json.dump(results, f, indent=4)
        
    if results:
        best_format = min(results, key=lambda k: results[k]['latency_ms'])
        print(f"\n[DECISION] Optimal production format: {best_format}")
    else:
        print("\n[ERROR] Benchmarking failed for all formats.")

if __name__ == "__main__":
    run_benchmarks()
