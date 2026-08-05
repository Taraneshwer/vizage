import React, { useState, useEffect, useMemo } from 'react';
import { CameraFeed } from '../components/specialized/CameraFeed';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Play, Pause, Download, UserPlus, FileText, Server, Cpu, Database, Activity } from 'lucide-react';
import { StatusBadge } from '../components/common/StatusBadge';
import { ErrorState } from '../components/common/ErrorState';
import { EmptyState } from '../components/common/EmptyState';
import { motion, AnimatePresence } from 'framer-motion';
import { useRuntimeStream, useSystemStream, useCameraStream, useRecognitionStream } from '../hooks/useWebSocket';
import type { WSRecognitionMessage } from '../hooks/useWebSocket';
import { useRuntimeStats, useSystemInfo, useBackendHealth, useStartRuntime, useStopRuntime } from '../utils/api';
import { useNavigate } from 'react-router-dom';

export const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const startMutation = useStartRuntime();
  const stopMutation = useStopRuntime();
  const { data: initialRuntime } = useRuntimeStats();
  const { data: initialSystem } = useSystemInfo();
  const { data: health } = useBackendHealth();

  const { data: runtimeStream, isConnected: isRuntimeConnected } = useRuntimeStream();
  const { data: systemStream, isConnected: isSystemConnected } = useSystemStream();
  const { data: cameraStream, isConnected: isCameraConnected } = useCameraStream();
  const { data: recognitionStream } = useRecognitionStream();

  const [recognitions, setRecognitions] = useState<WSRecognitionMessage[]>([]);

  useEffect(() => {
    if (recognitionStream) {
      setRecognitions(prev => [recognitionStream, ...prev].slice(0, 50));
    }
  }, [recognitionStream]);

  const runtimeData = runtimeStream || initialRuntime;
  const systemData = systemStream || initialSystem;

  const formatSeconds = (sec?: number) => {
    if (!sec) return '00:00:00';
    const h = Math.floor(sec / 3600);
    const m = Math.floor((sec % 3600) / 60);
    const s = Math.floor(sec % 60);
    return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  const latencyMs = useMemo(() => {
    if (!cameraStream || !cameraStream.capture_timestamp) return undefined;
    const diff = (Date.now() / 1000) - cameraStream.capture_timestamp;
    return Math.max(0, diff * 1000);
  }, [cameraStream]);

  const isLive = isRuntimeConnected && isSystemConnected;

  return (
    <div className="h-full flex flex-col gap-4">
      {/* Top Health Indicator */}
      {!health && (
        <div className="absolute inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center">
          <ErrorState 
            title="Backend Offline"
            message="Cannot connect to the AI Engine. Please check if the Python backend is running."
          />
        </div>
      )}

      <div className="flex-1 flex gap-4 min-h-0">
        
        {/* Left Column: Camera (60%) */}
        <div className="flex-[3] flex flex-col gap-4 h-full">
          <div className="flex items-center justify-between">
             <h2 className="text-lg font-bold">Live Recognition</h2>
             <div className="flex gap-2">
               <StatusBadge status={isLive ? 'success' : 'warning'} dot>
                 {isLive ? 'STREAMING' : 'CONNECTING'}
               </StatusBadge>
               <Button size="sm" variant="primary" onClick={() => startMutation.mutate()} disabled={startMutation.isPending}><Play size={14} className="mr-2"/> Start</Button>
               <Button size="sm" variant="secondary" onClick={() => stopMutation.mutate()} disabled={stopMutation.isPending}><Pause size={14} className="mr-2"/> Pause</Button>
             </div>
          </div>
          
          <CameraFeed 
            className="flex-1 border-white/10" 
            isOnline={isCameraConnected} 
            streamUrl={cameraStream ? `data:image/jpeg;base64,${cameraStream.image_base64}` : undefined}
            latencyMs={latencyMs}
            overlays={
               <div className="w-full h-full p-4 relative pointer-events-none">
                 {/* Raw bounding boxes are hard to map without resolution, so we just show latest recognition info */}
                 {recognitionStream && (
                   <div className="absolute top-4 left-4 bg-black/60 backdrop-blur border border-white/10 p-3 rounded shadow-xl">
                     <p className="text-xs text-gray-400 mb-1">Latest Detection</p>
                     <p className="text-sm font-bold text-success">
                       {recognitionStream.identity_id !== 'Unknown' ? recognitionStream.identity_id : 'Unknown Face'} 
                       <span className="ml-2 text-white/70 font-mono text-xs">{(recognitionStream.verification_score * 100).toFixed(1)}%</span>
                     </p>
                     {recognitionStream.mask_status && (
                       <span className="inline-block mt-1 bg-warning text-black text-[10px] px-1.5 py-0.5 font-bold rounded">MASK</span>
                     )}
                   </div>
                 )}
               </div>
            }
          />
        </div>

        {/* Right Column: Status & Timeline (40%) */}
        <div className="flex-[2] flex flex-col gap-4 h-full min-w-0">
          
          <Card className="p-4">
            <h3 className="text-sm font-semibold text-gray-300 mb-4 border-b border-white/5 pb-2 flex items-center justify-between">
              Recognition Session
              <span className="text-[10px] font-mono text-gray-500">{runtimeData?.state || 'OFFLINE'}</span>
            </h3>
            <div className="grid grid-cols-2 gap-y-4 gap-x-2">
               <div>
                  <p className="text-xs text-gray-500">Live FPS</p>
                  <p className="text-sm font-mono text-white mt-1">{runtimeData?.average_fps?.toFixed(1) || '0.0'}</p>
               </div>
               <div>
                  <p className="text-xs text-gray-500">Runtime</p>
                  <p className="text-sm font-mono text-white mt-1">{formatSeconds(runtimeData?.uptime_seconds)}</p>
               </div>
               <div>
                  <p className="text-xs text-gray-500">Frames Processed</p>
                  <p className="text-sm font-mono text-white mt-1">{runtimeData?.total_frames_processed?.toLocaleString() || 0}</p>
               </div>
               <div>
                  <p className="text-xs text-gray-500">Recognitions</p>
                  <p className="text-sm font-mono text-white mt-1">{runtimeData?.total_recognitions?.toLocaleString() || 0}</p>
               </div>
               <div>
                  <p className="text-xs text-gray-500">Unknown Faces</p>
                  <p className="text-sm font-mono text-warning mt-1">{runtimeData?.total_unknowns?.toLocaleString() || 0}</p>
               </div>
               <div>
                  <p className="text-xs text-gray-500">Dropped Frames</p>
                  <p className="text-sm font-mono text-danger mt-1">{(runtimeData as any)?.dropped_frames?.toLocaleString() || ((runtimeData as any)?.errors?.toLocaleString() || 0)}</p>
               </div>
            </div>
          </Card>

          {/* System Health Widget */}
          <Card className="p-4">
            <h3 className="text-sm font-semibold text-gray-300 mb-4 border-b border-white/5 pb-2 flex items-center">
              <Server size={14} className="mr-2"/> System Health
            </h3>
            <div className="space-y-3">
              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-gray-400 flex items-center"><Cpu size={12} className="mr-1"/> GPU VRAM</span>
                  <span className="text-white font-mono">
                    {systemData?.gpu?.vram_used_mb || 0} / {systemData?.gpu?.vram_total_mb || 0} MB
                  </span>
                </div>
                <div className="w-full bg-secondary h-1.5 rounded-full overflow-hidden">
                  <div 
                    className="bg-primary h-full" 
                    style={{ width: `${((systemData?.gpu?.vram_used_mb || 0) / (systemData?.gpu?.vram_total_mb || 1)) * 100}%` }}
                  />
                </div>
              </div>
              
              <div className="pt-2 grid grid-cols-2 gap-2">
                {systemData?.models?.map((model: any, i: number) => (
                  <div key={i} className="bg-secondary/50 rounded p-2 border border-white/5">
                    <p className="text-[10px] text-gray-500 uppercase tracking-wider">{model.name}</p>
                    <div className="flex justify-between items-end mt-1">
                      <span className="text-xs text-success font-medium">{model.status}</span>
                      <span className="text-[10px] text-gray-400 font-mono">{model.latency_ms}ms</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </Card>

          {/* Quick Actions */}
          <div className="grid grid-cols-2 gap-2">
             <Button variant="secondary" className="h-12" onClick={() => navigate('/enrollment')}><UserPlus size={16} className="mr-2 text-gray-400"/> Enroll</Button>
             <Button variant="secondary" className="h-12" onClick={() => navigate('/logs')}><FileText size={16} className="mr-2 text-gray-400"/> Logs</Button>
          </div>

          <Card className="flex-1 flex flex-col p-4 min-h-0">
            <h3 className="text-sm font-semibold text-gray-300 mb-4 border-b border-white/5 pb-2">Recent Timeline</h3>
            <div className="flex-1 overflow-y-auto space-y-3 pr-2">
              {recognitions.length === 0 ? (
                <EmptyState 
                  icon={Activity}
                  title="No Recognitions"
                  description="Waiting for faces..."
                />
              ) : (
                <AnimatePresence initial={false}>
                  {recognitions.map((rec, i) => (
                    <motion.div 
                      key={`${rec.timestamp}-${i}`}
                      initial={{ opacity: 0, height: 0, scale: 0.95 }}
                      animate={{ opacity: 1, height: 'auto', scale: 1 }}
                      transition={{ duration: 0.3 }}
                      className="flex gap-3 items-start relative pb-4 border-l border-white/10 ml-3 pl-4"
                    >
                      <div className={`absolute -left-1.5 top-1 w-3 h-3 rounded-full ring-4 ring-card ${rec.identity_id === 'Unknown' ? 'bg-warning' : 'bg-success'}`} />
                      <img src={`https://api.dicebear.com/7.x/avataaars/svg?seed=${rec.identity_id}`} className="w-8 h-8 rounded bg-secondary shrink-0" />
                      <div className="flex-1 min-w-0">
                        <div className="flex justify-between items-baseline">
                          <p className="text-sm font-medium text-white truncate">{rec.identity_id}</p>
                          <span className="text-[10px] text-gray-500 font-mono">
                            {new Date(rec.timestamp * 1000).toLocaleTimeString([], { hour12: true, hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                          </span>
                        </div>
                        <p className="text-xs text-gray-400">Match: {(rec.verification_score * 100).toFixed(1)}% • Latency: {rec.processing_time_ms.toFixed(0)}ms</p>
                      </div>
                    </motion.div>
                  ))}
                </AnimatePresence>
              )}
            </div>
          </Card>

        </div>
      </div>
    </div>
  );
};
