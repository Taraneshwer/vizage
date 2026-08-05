# Vizage
Offline AI-powered Masked Face Recognition Desktop Application.

## Milestone 1: Backend Foundation
This repository contains the backend infrastructure for the Vizage application.

### Setup
```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### Run
```bash
uvicorn app.main:app --reload
```