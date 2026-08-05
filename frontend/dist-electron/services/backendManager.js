"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.BackendManager = void 0;
const child_process_1 = require("child_process");
const axios_1 = __importDefault(require("axios"));
const tree_kill_1 = __importDefault(require("tree-kill"));
const env_1 = require("../config/env");
const logger_1 = require("../utils/logger");
class BackendManager {
    backendProcess = null;
    isShuttingDown = false;
    async start() {
        logger_1.logger.info('Starting backend process...');
        if (this.backendProcess) {
            logger_1.logger.warn('Backend process is already running.');
            return true;
        }
        try {
            if (env_1.ENV.isDev) {
                this.backendProcess = (0, child_process_1.spawn)(env_1.ENV.pythonDevExecutable, [env_1.ENV.pythonDevScript], {
                    cwd: process.cwd(),
                    env: process.env,
                });
            }
            else {
                this.backendProcess = (0, child_process_1.spawn)(env_1.ENV.pythonProdExecutable, [], {
                    cwd: process.cwd(),
                    env: process.env,
                });
            }
            this.backendProcess.stdout?.on('data', (data) => {
                logger_1.logger.debug(`[Backend]: ${data.toString().trim()}`);
            });
            this.backendProcess.stderr?.on('data', (data) => {
                logger_1.logger.warn(`[Backend ERR]: ${data.toString().trim()}`);
            });
            this.backendProcess.on('close', (code) => {
                logger_1.logger.info(`Backend process exited with code ${code}`);
                this.backendProcess = null;
                if (!this.isShuttingDown) {
                    logger_1.logger.error('Backend crashed unexpectedly.');
                }
            });
            return await this.waitForHealth();
        }
        catch (error) {
            logger_1.logger.error('Failed to spawn backend process:', error);
            return false;
        }
    }
    async stop() {
        logger_1.logger.info('Stopping backend process...');
        this.isShuttingDown = true;
        return new Promise((resolve) => {
            if (!this.backendProcess || !this.backendProcess.pid) {
                logger_1.logger.info('No backend process running.');
                resolve();
                return;
            }
            (0, tree_kill_1.default)(this.backendProcess.pid, 'SIGKILL', (err) => {
                if (err) {
                    logger_1.logger.error('Error killing backend process tree:', err);
                }
                else {
                    logger_1.logger.info('Backend process tree killed successfully.');
                }
                this.backendProcess = null;
                resolve();
            });
        });
    }
    async waitForHealth(retries = 30, delayMs = 1000) {
        logger_1.logger.info(`Waiting for backend health check at ${env_1.ENV.backendHealthEndpoint}...`);
        for (let i = 0; i < retries; i++) {
            try {
                const response = await axios_1.default.get(env_1.ENV.backendHealthEndpoint);
                if (response.status === 200) {
                    logger_1.logger.info('Backend is healthy and ready.');
                    return true;
                }
            }
            catch (error) {
                logger_1.logger.debug(`Health check failed (attempt ${i + 1}/${retries}). Waiting...`);
            }
            await new Promise((resolve) => setTimeout(resolve, delayMs));
        }
        logger_1.logger.error('Backend health check timed out.');
        return false;
    }
}
exports.BackendManager = BackendManager;
