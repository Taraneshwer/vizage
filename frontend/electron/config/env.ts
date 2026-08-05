import isDev from 'electron-is-dev';
import path from 'path';

export const ENV = {
  isDev,
  // Vite dev server URL
  reactDevUrl: 'http://localhost:5173',
  // Packaged React HTML
  reactProdPath: path.join(__dirname, '..', '..', 'dist', 'index.html'),
  // Python backend endpoints
  backendUrl: 'http://127.0.0.1:8000',
  backendHealthEndpoint: 'http://127.0.0.1:8000/health/live',
  // Path to python executable or script for development
  pythonDevScript: path.join(__dirname, '..', '..', '..', 'backend', 'app', 'main.py'),
  pythonDevExecutable: path.join(__dirname, '..', '..', '..', 'backend', '.venv', 'Scripts', 'python.exe'),
  // Path to packaged backend executable
  pythonProdExecutable: path.join(process.cwd(), 'resources', 'backend', 'maskshield_backend.exe'),
};
