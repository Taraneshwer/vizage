import { app } from 'electron';
import { WindowManager } from './windowManager';
import { BackendManager } from '../services/backendManager';
import { setupIpcHandlers } from '../ipc/handlers';
import { logger } from '../utils/logger';

const windowManager = new WindowManager();
const backendManager = new BackendManager();

async function bootstrap() {
  logger.info('Bootstrapping Electron application...');

  await app.whenReady();
  
  windowManager.createSplashWindow();
  
  setupIpcHandlers(windowManager);

  const isBackendReady = await backendManager.start();

  if (isBackendReady) {
    logger.info('Backend is ready. Launching main window.');
    windowManager.createMainWindow();
  } else {
    logger.error('Failed to start backend. Cannot proceed.');
    app.quit();
  }

  app.on('activate', () => {
    if (windowManager.getMainWindow() === null) {
      windowManager.createMainWindow();
    }
  });
}

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

let isQuitting = false;

app.on('before-quit', async (event) => {
  if (isQuitting) return;
  
  logger.info('Application is quitting. Cleaning up...');
  
  event.preventDefault();
  isQuitting = true;
  
  await backendManager.stop();
  app.exit(0);
});

bootstrap().catch((err) => {
  logger.error('Unhandled error during bootstrap:', err);
  app.quit();
});
