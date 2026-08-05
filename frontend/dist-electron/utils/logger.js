"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.logger = void 0;
const electron_log_1 = __importDefault(require("electron-log"));
electron_log_1.default.transports.file.level = 'info';
electron_log_1.default.transports.console.level = 'debug';
exports.logger = {
    info: (msg, ...args) => electron_log_1.default.info(msg, ...args),
    warn: (msg, ...args) => electron_log_1.default.warn(msg, ...args),
    error: (msg, ...args) => electron_log_1.default.error(msg, ...args),
    debug: (msg, ...args) => electron_log_1.default.debug(msg, ...args),
};
