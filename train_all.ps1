$ErrorActionPreference = "Stop"

Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "  Vizage Full Training Pipeline Execution " -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan

$BASE_DIR = $PSScriptRoot
if ([string]::IsNullOrEmpty($BASE_DIR)) {
    $BASE_DIR = Get-Location
}

$VENV_DIR = Join-Path $BASE_DIR ".venv"
$REQ_FILE = Join-Path $BASE_DIR "maskshield-ai\requirements.txt"
$SCRIPTS_DIR = Join-Path $BASE_DIR "maskshield-ai\scripts"
$BACKEND_MODELS_DIR = Join-Path $BASE_DIR "backend\models"

# 1. Verify directories and create if missing
if (-not (Test-Path $SCRIPTS_DIR)) {
    Write-Error "Scripts directory not found at $SCRIPTS_DIR"
    exit 1
}

if (-not (Test-Path $BACKEND_MODELS_DIR)) {
    Write-Host "[INFO] Creating models directory at $BACKEND_MODELS_DIR" -ForegroundColor Green
    New-Item -ItemType Directory -Path $BACKEND_MODELS_DIR -Force | Out-Null
}

# 2. Environment Setup
if (-not (Test-Path $VENV_DIR)) {
    Write-Host "`n[Setup] Creating Python Virtual Environment (.venv)..." -ForegroundColor Cyan
    python -m venv $VENV_DIR
    if ($LASTEXITCODE -ne 0) { throw "Failed to create virtual environment." }
}

$ACTIVATE_SCRIPT = Join-Path $VENV_DIR "Scripts\Activate.ps1"
if (-not (Test-Path $ACTIVATE_SCRIPT)) {
    throw "Activation script not found: $ACTIVATE_SCRIPT"
}

# Source the activation script
. $ACTIVATE_SCRIPT

Write-Host "`n[Setup] Upgrading PIP..." -ForegroundColor Cyan
python -m pip install --upgrade pip | Out-Null

Write-Host "`n[Setup] Syncing Dependencies..." -ForegroundColor Cyan
pip install -r "$REQ_FILE"
if ($LASTEXITCODE -ne 0) { throw "Failed to install dependencies." }

# Navigate to scripts dir
Set-Location $SCRIPTS_DIR

# 3. Validation (Hardware & Dependencies)
Write-Host "`n[Setup] Running Hardware & Dependency Validation..." -ForegroundColor Cyan
python validate_env_datasets.py --step env
if ($LASTEXITCODE -ne 0) { throw "Environment validation failed." }

# 4. Data Preparation
Write-Host "`n[1/7] Running Data Preparation..." -ForegroundColor Cyan
python prepare_dataset.py
if ($LASTEXITCODE -ne 0) { throw "Data preparation failed." }

Write-Host "`n[Setup] Running Dataset Validation..." -ForegroundColor Cyan
python validate_env_datasets.py --step data
if ($LASTEXITCODE -ne 0) { throw "Dataset validation failed." }

# Read validation summary
$SUMMARY_PATH = Join-Path $BASE_DIR "maskshield-ai\validation_summary.json"
$summaryJson = ""
if (Test-Path $SUMMARY_PATH) {
    $summaryJson = Get-Content $SUMMARY_PATH | ConvertFrom-Json
}

# Run Dataset Audit
Write-Host "`n[Setup] Running Dataset Audit..." -ForegroundColor Cyan
python dataset_audit.py
if ($LASTEXITCODE -ne 0) { throw "Dataset audit failed." }

# Copy smoke models to smoke folder before starting production training
Write-Host "`n[Setup] Backing up smoke-test models..." -ForegroundColor Cyan
New-Item -Path "$BACKEND_MODELS_DIR/smoke" -ItemType Directory -Force | Out-Null
if (Test-Path "$BACKEND_MODELS_DIR/best_yolo.onnx") {
    Copy-Item -Path "$BACKEND_MODELS_DIR/best_yolo.onnx" -Destination "$BACKEND_MODELS_DIR/smoke/best_yolo.onnx" -Force
}
if (Test-Path "$BACKEND_MODELS_DIR/best_adaface.onnx") {
    Copy-Item -Path "$BACKEND_MODELS_DIR/best_adaface.onnx" -Destination "$BACKEND_MODELS_DIR/smoke/best_adaface.onnx" -Force
}

# 5. Training YOLO
Write-Host "`n[2/7] Training YOLOv11..." -ForegroundColor Cyan
python train_yolo.py --data ../datasets/processed/yolo/data.yaml --epochs 100 --batch 16 --imgsz 640
if ($LASTEXITCODE -ne 0) { throw "YOLO training failed." }

# 6. Train AdaFace
Write-Host "`n[4/7] Training AdaFace..." -ForegroundColor Cyan
python train_adaface.py --data ../datasets/processed/arcface --epochs 20 --batch 64
if ($LASTEXITCODE -ne 0) { throw "AdaFace training failed." }

# 7. Export Models
Write-Host "`n[4/7] Exporting Models to ONNX / TensorRT..." -ForegroundColor Cyan
python export_models.py --output_dir $BACKEND_MODELS_DIR
if ($LASTEXITCODE -ne 0) { throw "Model export failed." }

# 8. Evaluate Models
Write-Host "`n[5/7] Evaluating Models..." -ForegroundColor Cyan
python evaluate.py --task all > training_report.txt
if ($LASTEXITCODE -ne 0) { throw "Evaluation failed." }

Write-Host "`n[Setup] Benchmarking PyTorch vs ONNX..." -ForegroundColor Cyan
python benchmark_models.py > benchmark_report.txt
if ($LASTEXITCODE -ne 0) { throw "Benchmarking failed." }

# 9. Copy Models to Backend
Write-Host "`n[Setup] Copying Models to Backend..." -ForegroundColor Cyan
New-Item -Path "$BACKEND_MODELS_DIR/production" -ItemType Directory -Force | Out-Null
Copy-Item -Path "runs/train/yolo_mask_face/weights/best.onnx" -Destination "$BACKEND_MODELS_DIR/production/best_yolo.onnx" -Force
Copy-Item -Path "runs/adaface/best_adaface.onnx" -Destination "$BACKEND_MODELS_DIR/production/best_adaface.onnx" -Force

# 10. Run End-to-End Smoke Test
Write-Host "`n[6/7] Running End-to-End Smoke Test..." -ForegroundColor Cyan
python smoke_test.py
if ($LASTEXITCODE -ne 0) { throw "Smoke test failed." }

# 11. Generate Report
Write-Host "`n[7/7] Generating Final Report..." -ForegroundColor Cyan
$REPORT_PATH = Join-Path $BASE_DIR "PRODUCTION_TRAINING_REPORT.md"

$reportLines = @()
$reportLines += "# Vizage Training Final Report"
$reportLines += ""
$reportLines += "## Hardware & Environment Summary"
if ($summaryJson) {
    $reportLines += "- **Python Version**: $($summaryJson.hardware.python_version)"
    $reportLines += "- **PyTorch Version**: $($summaryJson.hardware.pytorch_version)"
    $reportLines += "- **CUDA Enabled**: $($summaryJson.hardware.cuda_available)"
    $reportLines += "- **GPU**: $($summaryJson.hardware.gpu_name) ($($summaryJson.hardware.gpu_memory_gb) GB)"
    $reportLines += "- **System RAM**: $($summaryJson.hardware.ram_gb) GB"
    $reportLines += "- **Logical Cores**: $($summaryJson.hardware.cpu_cores)"
    $reportLines += ""
    $reportLines += "## Dataset Summary"
    $reportLines += "- **YOLO Images**: $($summaryJson.datasets.yolo_train_images)"
    $reportLines += "- **YOLO Annotations**: $($summaryJson.datasets.yolo_train_labels)"
    $reportLines += "- **AdaFace Identities**: $($summaryJson.datasets.adaface_identities)"
    $reportLines += "- **AdaFace Identity Images**: $($summaryJson.datasets.adaface_images)"
}

$reportLines += ""
$reportLines += "## Exported Models"
$reportLines += "Models were successfully generated and integrated into the backend configuration:"
$reportLines += "- YOLO: backend/models/best_yolo.onnx"
$reportLines += "- AdaFace: backend/models/best_adaface.onnx"
$reportLines += ""
$reportLines += "## Evaluation Metrics"
$reportLines += "Below is a summary of the evaluation generated from the testing splits:"
$reportLines += ""

if (Test-Path "training_report.txt") {
    $reportLines += Get-Content "training_report.txt" -Raw
} else {
    $reportLines += "No evaluation report found."
}

$reportLines += ""
$reportLines += "## Model Benchmarking"
if (Test-Path "benchmark_report.txt") {
    $reportLines += Get-Content "benchmark_report.txt" -Raw
} else {
    $reportLines += "No benchmarking report found."
}

$reportLines += ""
$reportLines += "## Dataset Audit"
if (Test-Path "dataset_audit.md") {
    $reportLines += Get-Content "dataset_audit.md" -Raw
} else {
    $reportLines += "No dataset audit found."
}

Set-Content -Path $REPORT_PATH -Value ($reportLines -join "`r`n") -Encoding UTF8

# Return to original directory
Set-Location $BASE_DIR

Write-Host "`n=============================================" -ForegroundColor Green
Write-Host " Training pipeline completed successfully!" -ForegroundColor Green
Write-Host " Final report generated: FINAL_TRAINING_REPORT.md" -ForegroundColor Green
Write-Host " The backend is now ready to use the new models." -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Green
