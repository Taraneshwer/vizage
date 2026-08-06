import React from 'react';
import { Card } from '../components/common/Card';
import { Search, Download, Copy, AlertTriangle } from 'lucide-react';
import { Button } from '../components/common/Button';

export const Logs: React.FC = () => {
  return (
    <div className="h-full flex flex-col gap-4">
      <div className="flex justify-between items-end">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">System Logs</h2>
          <p className="text-sm text-gray-600 mt-1">Real-time terminal viewer for backend events.</p>
        </div>
        <div className="flex gap-2">
          <Button variant="secondary" size="sm"><Copy size={14} className="mr-2"/> Copy All</Button>
          <Button variant="secondary" size="sm"><Download size={14} className="mr-2"/> Download</Button>
        </div>
      </div>

      <Card className="flex-1 bg-black border-gray-300 flex flex-col overflow-hidden font-mono text-sm relative">
        
        {}
        <div className="bg-secondary/80 border-b border-gray-200 p-2 flex items-center justify-between z-10">
           <div className="flex gap-2 px-2">
             <div className="w-3 h-3 rounded-full bg-danger/80" />
             <div className="w-3 h-3 rounded-full bg-warning/80" />
             <div className="w-3 h-3 rounded-full bg-success/80" />
           </div>
           <div className="flex gap-2">
             <select className="bg-white border border-gray-300 text-gray-900 rounded px-2 py-1 text-xs outline-none">
               <option>All Levels</option>
               <option>ERROR</option>
               <option>WARNING</option>
               <option>INFO</option>
             </select>
             <div className="relative">
               <Search size={12} className="absolute left-2 top-1/2 -translate-y-1/2 text-gray-500" />
               <input type="text" placeholder="Grep..." className="bg-white border border-gray-300 rounded px-2 py-1 pl-6 text-xs text-gray-900 outline-none w-48" />
             </div>
           </div>
        </div>

        {}
        <div className="flex-1 overflow-y-auto p-4 space-y-1 text-gray-300">
           <div className="flex gap-4 hover:bg-gray-100/10 px-2 py-0.5 rounded">
             <span className="text-gray-500 shrink-0">14:38:22.102</span>
             <span className="text-success font-bold w-12 shrink-0">INFO</span>
             <span className="text-primary w-24 shrink-0">[Main]</span>
             <span className="break-all">Application startup complete. Listening on 0.0.0.0:8000</span>
           </div>
           <div className="flex gap-4 hover:bg-gray-100/10 px-2 py-0.5 rounded">
             <span className="text-gray-500 shrink-0">14:38:23.004</span>
             <span className="text-success font-bold w-12 shrink-0">INFO</span>
             <span className="text-primary w-24 shrink-0">[Camera]</span>
             <span className="break-all">Connecting to RTSP stream...</span>
           </div>
           <div className="flex gap-4 hover:bg-gray-100/10 px-2 py-0.5 rounded bg-warning/10 text-warning">
             <span className="text-gray-500 shrink-0">14:38:24.402</span>
             <span className="font-bold w-12 shrink-0">WARN</span>
             <span className="text-primary w-24 shrink-0">[CUDA]</span>
             <span className="break-all">High memory usage detected (85%). Consider reducing batch size.</span>
           </div>
           <div className="flex gap-4 hover:bg-gray-100/10 px-2 py-0.5 rounded">
             <span className="text-gray-500 shrink-0">14:38:25.112</span>
             <span className="text-success font-bold w-12 shrink-0">INFO</span>
             <span className="text-primary w-24 shrink-0">[Inference]</span>
             <span className="break-all">Face detected. Sim: 0.942. Identity: EMP-8492.</span>
           </div>
           <div className="flex gap-4 hover:bg-gray-100/10 px-2 py-0.5 rounded bg-danger/10 text-danger">
             <span className="text-gray-500 shrink-0">14:38:28.991</span>
             <span className="font-bold w-12 shrink-0">ERROR</span>
             <span className="text-primary w-24 shrink-0">[Database]</span>
             <span className="break-all">Connection timeout while updating metrics. Retrying (1/3)...</span>
           </div>
        </div>
      </Card>
    </div>
  );
};
