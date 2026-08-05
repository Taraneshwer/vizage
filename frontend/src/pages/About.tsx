import React from 'react';
import { Card } from '../components/common/Card';

export const About = () => {
  return (
    <div className="h-full flex items-center justify-center p-6">
      <Card className="max-w-2xl w-full p-8 flex flex-col items-center text-center">
        <div className="w-20 h-20 bg-primary text-white flex items-center justify-center text-4xl font-bold rounded-lg shadow-lg mb-6">
          M
        </div>
        <h2 className="text-3xl font-bold tracking-tight text-white mb-2">MaskShield AI</h2>
        <p className="text-gray-400 mb-8 uppercase tracking-widest text-sm">Enterprise Security System</p>
        
        <div className="grid grid-cols-2 gap-4 w-full text-left bg-black/20 p-6 rounded-lg border border-white/5">
          <div>
            <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">Version</p>
            <p className="font-mono text-sm text-gray-200">1.0.0-rc1 (Build 8421)</p>
          </div>
          <div>
            <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">License</p>
            <p className="font-mono text-sm text-gray-200">Enterprise Commercial License</p>
          </div>
          <div>
            <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">Frontend Stack</p>
            <p className="font-mono text-sm text-gray-200">React, TypeScript, Vite, Tailwind</p>
          </div>
          <div>
            <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">Backend Stack</p>
            <p className="font-mono text-sm text-gray-200">FastAPI, PyTorch, FAISS, CUDA</p>
          </div>
        </div>
        
        <div className="mt-8 text-xs text-gray-500">
          &copy; 2026 MaskShield AI Inc. All rights reserved.
        </div>
      </Card>
    </div>
  );
};
