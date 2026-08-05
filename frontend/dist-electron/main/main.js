"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const electron_1 = require("electron");
const windowManager_1 = require("./windowManager");
const backendManager_1 = require("../services/backendManager");
const handlers_1 = require("../ipc/handlers");
const logger_1 = require("../utils/logger");
const windowManager = new windowManager_1.WindowManager();
const backendManager = new backendManager_1.BackendManager();
async function bootstrap() {
    logger_1.logger.info('Bootstrapping Electron application...');
    await electron_1.app.whenReady();
    windowManager.createSplashWindow();
    (0, handlers_1.setupIpcHandlers)(windowManager);
    const isBackendReady = await backendManager.start();
    if (isBackendReady) {
        logger_1.logger.info('Backend is ready. Launching main window.');
        windowManager.createMainWindow();
    }
    else {
        logger_1.logger.error('Failed to start backend. Cannot proceed.');
        electron_1.app.quit();
    }
    electron_1.app.on('activate', () => {
        if (windowManager.getMainWindow() === null) {
            windowManager.createMainWindow();
        }
    });
}
electron_1.app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        electron_1.app.quit();
    }
});
let isQuitting = false;
electron_1.app.on('before-quit', async (event) => {
    if (isQuitting)
        return;
    logger_1.logger.info('Application is quitting. Cleaning up...');
    event.preventDefault();
    isQuitting = true;
    await backendManager.stop();
    electron_1.app.exit(0);
});
bootstrap().catch((err) => {
    logger_1.logger.error('Unhandled error during bootstrap:', err);
    electron_1.app.quit();
});
