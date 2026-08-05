import React, { useState, useEffect } from 'react';
import { Cpu, HardDrive, Camera, Activity, Server, Clock } from 'lucide-react';

export const BottomBar: React.FC = () => {
  const [time, setTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const StatusItem = ({ icon: Icon, label, value, status }: { icon: any, label: string, value: string, status: 'ok' | 'warn' | 'err' }) => {
    const colors = {
      ok: 'text-success',
      warn: 'text-warning',
      err: 'text-danger'
    };
    return (
      <div className="flex items-center gap-2 text-xs border-r border-gray-300 px-4 last:border-0 h-full">
        <Icon size={12} className={colors[status]} />
        <span className="text-gray-600">{label}:</span>
        <span className="font-mono text-gray-200">{value}</span>
      </div>
    );
  };

  return (
    <footer className="h-8 bg-secondary border-t border-gray-200 flex items-center justify-between shrink-0 select-none">
      <div className="flex items-center h-full">
        <StatusItem icon={Cpu} label="GPU" value="24%" status="ok" />
        <StatusItem icon={HardDrive} label="CUDA" value="Active" status="ok" />
        <StatusItem icon={Camera} label="Camera" value="Online" status="ok" />
        <StatusItem icon={Server} label="Backend" value="Connected" status="ok" />
        <StatusItem icon={Activity} label="Engine" value="Idle" status="ok" />
        <StatusItem icon={Activity} label="FPS" value="30.0" status="ok" />
      </div>
      <div className="flex items-center gap-4 text-xs text-gray-500 pr-4">
        <div className="flex items-center gap-1.5 font-mono">
          <Clock size={12} />
          {time.toLocaleTimeString()}
        </div>
        <span>v1.0.0 (Enterprise Build)</span>
      </div>
    </footer>
  );
};
