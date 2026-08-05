import { ipcMain, app } from 'electron';
import { WindowManager } from '../main/windowManager';

export function setupIpcHandlers(windowManager: WindowManager) {
  ipcMain.on('window:minimize', () => {
    windowManager.getMainWindow()?.minimize();
  });

  ipcMain.on('window:maximize', () => {
    const win = windowManager.getMainWindow();
    if (win) {
      if (win.isMaximized()) {
        win.unmaximize();
      } else {
        win.maximize();
      }
    }
  });

  ipcMain.on('window:close', () => {
    windowManager.getMainWindow()?.close();
  });

  ipcMain.handle('system:get-app-version', () => {
    return app.getVersion();
  });
}
