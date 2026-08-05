"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.setupIpcHandlers = setupIpcHandlers;
const electron_1 = require("electron");
function setupIpcHandlers(windowManager) {
    electron_1.ipcMain.on('window:minimize', () => {
        windowManager.getMainWindow()?.minimize();
    });
    electron_1.ipcMain.on('window:maximize', () => {
        const win = windowManager.getMainWindow();
        if (win) {
            if (win.isMaximized()) {
                win.unmaximize();
            }
            else {
                win.maximize();
            }
        }
    });
    electron_1.ipcMain.on('window:close', () => {
        windowManager.getMainWindow()?.close();
    });
    electron_1.ipcMain.handle('system:get-app-version', () => {
        return electron_1.app.getVersion();
    });
}
