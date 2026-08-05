import React from 'react';
import { Card } from '../components/common/Card';
import { Cpu, HardDrive, Database as DatabaseIcon, Activity, Camera, Box, Server } from 'lucide-react';
import { StatusBadge } from '../components/common/StatusBadge';

const ServiceCard = ({ title, icon: Icon, status, metrics }: any) => (
  <Card className="p-5 flex flex-col gap-4 border-white/5">
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-2">
        <Icon size={18} className="text-gray-400" />
        <h3 className="font-semibold text-white">{title}</h3>
      </div>
      <StatusBadge status={status === 'Online' ? 'success' : 'danger'} dot>{status}</StatusBadge>
    </div>
    <div className="space-y-2 border-t border-white/5 pt-3">
      {metrics.map((m: any, i: number) => (
        <div key={i} className="flex justify-between text-xs">
          <span className="text-gray-400">{m.label}</span>
          <span className="text-white font-mono">{m.value}</span>
        </div>
      ))}
    </div>
  </Card>
);

export const System: React.FC = () => {
  return (
    <div className="h-full flex flex-col gap-4 overflow-y-auto pb-4">
      <div>
        <h2 className="text-2xl font-bold tracking-tight">Diagnostics Dashboard</h2>
        <p className="text-sm text-gray-400 mt-1">Live service health and hardware metrics.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        <ServiceCard 
          title="NVIDIA CUDA" 
          icon={Cpu} 
          status="Online" 
          metrics={[
            { label: 'Device', value: 'RTX 4090' },
            { label: 'Utilization', value: '24%' },
            { label: 'Memory', value: '4.2/24 GB' },
            { label: 'Temp', value: '54°C' }
          ]} 
        />
        <ServiceCard 
          title="YOLO11 Face" 
          icon={Box} 
          status="Online" 
          metrics={[
            { label: 'Backend', value: 'ONNX/TensorRT' },
            { label: 'Avg Infer', value: '12ms' },
            { label: 'Batch Size', value: '4' }
          ]} 
        />
        <ServiceCard 
          title="AdaFace Embedder" 
          icon={Activity} 
          status="Online" 
          metrics={[
            { label: 'Backbone', value: 'ResNet100' },
            { label: 'Avg Infer', value: '28ms' },
            { label: 'Precision', value: 'FP16' }
          ]} 
        />
        <ServiceCard 
          title="FAISS Vector Store" 
          icon={DatabaseIcon} 
          status="Online" 
          metrics={[
            { label: 'Index Type', value: 'FlatL2' },
            { label: 'Total Vectors', value: '1,248' },
            { label: 'Search Time', value: '1.2ms' }
          ]} 
        />
        <ServiceCard 
          title="Primary Camera" 
          icon={Camera} 
          status="Online" 
          metrics={[
            { label: 'Source', value: 'RTSP Stream' },
            { label: 'Resolution', value: '1920x1080' },
            { label: 'FPS', value: '30.0' },
            { label: 'Buffer', value: '14 frames' }
          ]} 
        />
        <ServiceCard 
          title="SQLite Database" 
          icon={HardDrive} 
          status="Online" 
          metrics={[
            { label: 'State', value: 'Read/Write' },
            { label: 'Size', value: '142 MB' },
            { label: 'Connections', value: '5' }
          ]} 
        />
        <ServiceCard 
          title="MediaPipe Mesh" 
          icon={Box} 
          status="Online" 
          metrics={[
            { label: 'Task', value: 'Face Landmark' },
            { label: 'Avg Infer', value: '8ms' }
          ]} 
        />
        <ServiceCard 
          title="FastAPI Backend" 
          icon={Server} 
          status="Online" 
          metrics={[
            { label: 'Uptime', value: '2d 4h 12m' },
            { label: 'Workers', value: '4' },
            { label: 'Req/sec', value: '24' }
          ]} 
        />
      </div>
    </div>
  );
};
