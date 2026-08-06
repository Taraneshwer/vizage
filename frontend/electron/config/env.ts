import isDev from 'electron-is-dev';
import path from 'path';

export const ENV = {
  isDev,
  
  reactDevUrl: 'http://localhost:5173',
  
  reactProdPath: path.join(__dirname, '..', '..', 'dist', 'index.html'),
  
  backendUrl: 'http://127.0.0.1:8000',
  backendHealthEndpoint: 'http://127.0.0.1:8000/health/live',
  
  pythonDevScript: path.join(__dirname, '..', '..', '..', 'backend', 'app', 'main.py'),
  pythonDevExecutable: path.join(__dirname, '..', '..', '..', 'backend', '.venv', 'Scripts', 'python.exe'),
  
  pythonProdExecutable: path.join(process.cwd(), 'resources', 'backend', 'maskshield_backend.exe'),
};
