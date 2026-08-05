"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.WindowManager = void 0;
const electron_1 = require("electron");
const path_1 = __importDefault(require("path"));
const env_1 = require("../config/env");
class WindowManager {
    mainWindow = null;
    splashWindow = null;
    createSplashWindow() {
        this.splashWindow = new electron_1.BrowserWindow({
            width: 400,
            height: 300,
            transparent: true,
            frame: false,
            alwaysOnTop: true,
            webPreferences: {
                nodeIntegration: false,
                contextIsolation: true,
            },
        });
        const splashPath = env_1.ENV.isDev
            ? path_1.default.join(__dirname, '..', '..', 'public', 'splash.html')
            : path_1.default.join(__dirname, '..', '..', 'dist', 'splash.html');
        this.splashWindow.loadFile(splashPath);
    }
    createMainWindow() {
        this.mainWindow = new electron_1.BrowserWindow({
            width: 1280,
            height: 800,
            minWidth: 1024,
            minHeight: 768,
            show: false,
            frame: false,
            webPreferences: {
                nodeIntegration: false,
                contextIsolation: true,
                preload: path_1.default.join(__dirname, '..', 'preload', 'preload.js'),
            },
        });
        if (env_1.ENV.isDev) {
            this.mainWindow.loadURL(env_1.ENV.reactDevUrl);
        }
        else {
            this.mainWindow.loadFile(env_1.ENV.reactProdPath);
        }
        this.mainWindow.once('ready-to-show', () => {
            this.splashWindow?.close();
            this.splashWindow = null;
            this.mainWindow?.show();
        });
        this.mainWindow.on('closed', () => {
            this.mainWindow = null;
        });
    }
    getMainWindow() {
        return this.mainWindow;
    }
}
exports.WindowManager = WindowManager;
