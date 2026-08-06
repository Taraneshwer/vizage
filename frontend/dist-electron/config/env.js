"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.ENV = void 0;
const electron_is_dev_1 = __importDefault(require("electron-is-dev"));
const path_1 = __importDefault(require("path"));
exports.ENV = {
    isDev: electron_is_dev_1.default,
    reactDevUrl: 'http://localhost:5173',
    reactProdPath: path_1.default.join(__dirname, '..', '..', 'dist', 'index.html'),
    backendUrl: 'http://127.0.0.1:8000',
    backendHealthEndpoint: 'http://127.0.0.1:8000/health/live',
    pythonDevScript: path_1.default.join(__dirname, '..', '..', '..', 'backend', 'app', 'main.py'),
    pythonDevExecutable: path_1.default.join(__dirname, '..', '..', '..', 'backend', '.venv', 'Scripts', 'python.exe'),
    pythonProdExecutable: path_1.default.join(process.cwd(), 'resources', 'backend', 'maskshield_backend.exe'),
};
