import React from 'react';
import { Card } from '../common/Card';
import { CameraOff, Maximize2, Settings2 } from 'lucide-react';
import { StatusBadge } from '../common/StatusBadge';

interface CameraFeedProps {
  streamUrl?: string;
  isOnline?: boolean;
  className?: string;
  overlays?: React.ReactNode;
}

export const CameraFeed: React.FC<CameraFeedProps> = ({ 
  streamUrl, 
  isOnline = true, 
  className,
  overlays
}) => {
  return (
    <Card className={`relative overflow-hidden group flex flex-col ${className || ''}`}>
      {/* Top overlay bar */}
      <div className="absolute top-0 inset-x-0 h-16 bg-gradient-to-b from-black/80 to-transparent z-10 flex items-start justify-between p-4 opacity-0 group-hover:opacity-100 transition-opacity">
        <StatusBadge status={isOnline ? 'success' : 'danger'} dot>
          {isOnline ? 'LIVE' : 'OFFLINE'}
        </StatusBadge>
        <div className="flex gap-2">
          <button className="p-1.5 rounded bg-black/50 hover:bg-white/20 text-white backdrop-blur transition-colors">
            <Settings2 size={16} />
          </button>
          <button className="p-1.5 rounded bg-black/50 hover:bg-white/20 text-white backdrop-blur transition-colors">
            <Maximize2 size={16} />
          </button>
        </div>
      </div>

      {/* Video Content */}
      <div className="flex-1 w-full h-full bg-black flex items-center justify-center relative">
        {isOnline && streamUrl ? (
          <img 
            src={streamUrl} 
            alt="Live Feed" 
            className="w-full h-full object-contain"
          />
        ) : isOnline ? (
           // Placeholder for demo purposes since we don't have a real stream yet
           <div className="w-full h-full bg-secondary flex items-center justify-center relative overflow-hidden">
             {/* Simulated subtle scanning effect */}
             <div className="absolute inset-0 bg-primary/5 opacity-20" />
             <div className="absolute top-0 inset-x-0 h-1 bg-primary/40 shadow-[0_0_15px_rgba(37,99,235,0.8)] animate-[scan_3s_ease-in-out_infinite]" />
             
             <span className="text-gray-500 font-mono text-sm z-10">Stream Simulation Active</span>
           </div>
        ) : (
          <div className="flex flex-col items-center text-gray-500 gap-3">
            <CameraOff size={48} className="opacity-50" />
            <p className="text-sm">Camera Disconnected</p>
          </div>
        )}
        
        {/* Custom overlays (bounding boxes, etc.) */}
        {overlays && (
          <div className="absolute inset-0 z-20 pointer-events-none">
            {overlays}
          </div>
        )}
      </div>
      
      {/* Bottom overlay bar */}
      <div className="absolute bottom-0 inset-x-0 p-3 bg-gradient-to-t from-black/80 to-transparent z-10 flex justify-between text-[10px] uppercase tracking-wider font-mono text-gray-300">
        <span>Res: 1920x1080</span>
        <span>Delay: 12ms</span>
      </div>
    </Card>
  );
};
