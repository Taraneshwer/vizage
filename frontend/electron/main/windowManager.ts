import { BrowserWindow } from 'electron';
import path from 'path';
import { ENV } from '../config/env';

export class WindowManager {
  private mainWindow: BrowserWindow | null = null;
  private splashWindow: BrowserWindow | null = null;

  createSplashWindow() {
    this.splashWindow = new BrowserWindow({
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
    
    const splashPath = ENV.isDev
      ? path.join(__dirname, '..', '..', 'public', 'splash.html')
      : path.join(__dirname, '..', '..', 'dist', 'splash.html');
      
    this.splashWindow.loadFile(splashPath);
  }

  createMainWindow() {
    this.mainWindow = new BrowserWindow({
      width: 1280,
      height: 800,
      minWidth: 1024,
      minHeight: 768,
      show: false,
      frame: false,
      webPreferences: {
        nodeIntegration: false,
        contextIsolation: true,
        preload: path.join(__dirname, '..', 'preload', 'preload.js'),
      },
    });

    if (ENV.isDev) {
      this.mainWindow.loadURL(ENV.reactDevUrl);
    } else {
      this.mainWindow.loadFile(ENV.reactProdPath);
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
