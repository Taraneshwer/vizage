import { spawn, ChildProcess } from 'child_process';
import axios from 'axios';
import treeKill from 'tree-kill';
import { ENV } from '../config/env';
import { logger } from '../utils/logger';

export class BackendManager {
  private backendProcess: ChildProcess | null = null;
  private isShuttingDown: boolean = false;

  async start(): Promise<boolean> {
    logger.info('Starting backend process...');
    
    if (this.backendProcess) {
      logger.warn('Backend process is already running.');
      return true;
    }

    try {
      if (ENV.isDev) {
        const backendDir = require('path').join(__dirname, '..', '..', '..', 'backend');
        this.backendProcess = spawn(ENV.pythonDevExecutable, [
          '-m', 'uvicorn', 'app.main:app',
          '--host', '127.0.0.1',
          '--port', '8000'
        ], {
          cwd: backendDir,
          env: process.env,
        });
      } else {
        this.backendProcess = spawn(ENV.pythonProdExecutable, [], {
          cwd: process.cwd(),
          env: process.env,
        });
      }

      this.backendProcess.stdout?.on('data', (data) => {
        logger.debug(`[Backend]: ${data.toString().trim()}`);
      });

      this.backendProcess.stderr?.on('data', (data) => {
        logger.warn(`[Backend ERR]: ${data.toString().trim()}`);
      });

      this.backendProcess.on('close', (code) => {
        logger.info(`Backend process exited with code ${code}`);
        this.backendProcess = null;
        if (!this.isShuttingDown) {
          logger.error('Backend crashed unexpectedly.');
        }
      });

      return await this.waitForHealth();
    } catch (error) {
      logger.error('Failed to spawn backend process:', error);
      return false;
    }
  }

  async stop(): Promise<void> {
    logger.info('Stopping backend process...');
    this.isShuttingDown = true;
    
    return new Promise((resolve) => {
      if (!this.backendProcess || !this.backendProcess.pid) {
        logger.info('No backend process running.');
        resolve();
        return;
      }

      treeKill(this.backendProcess.pid, 'SIGKILL', (err) => {
        if (err) {
          logger.error('Error killing backend process tree:', err);
        } else {
          logger.info('Backend process tree killed successfully.');
        }
        this.backendProcess = null;
        resolve();
      });
    });
  }

  private async waitForHealth(retries = 30, delayMs = 1000): Promise<boolean> {
    logger.info(`Waiting for backend health check at ${ENV.backendHealthEndpoint}...`);
    for (let i = 0; i < retries; i++) {
      try {
        const response = await axios.get(ENV.backendHealthEndpoint);
        if (response.status === 200) {
          logger.info('Backend is healthy and ready.');
          return true;
        }
      } catch (error) {
        logger.debug(`Health check failed (attempt ${i + 1}/${retries}). Waiting...`);
      }
      await new Promise((resolve) => setTimeout(resolve, delayMs));
    }
    
    logger.error('Backend health check timed out.');
    return false;
  }
}
