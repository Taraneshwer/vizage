import React, { useState, useEffect, useMemo, useRef } from 'react';
import { CameraFeed } from '../components/specialized/CameraFeed';
import { Card } from '../components/common/Card';
import { StatusBadge } from '../components/common/StatusBadge';
import { ShieldCheck, Target, Clock, User, Fingerprint, RefreshCcw, Activity } from 'lucide-react';
import { useCameraStream, useRecognitionStream } from '../hooks/useWebSocket';
import type { WSRecognitionMessage } from '../hooks/useWebSocket';
import { useBackendHealth } from '../utils/api';
import { ErrorState } from '../components/common/ErrorState';
import { EmptyState } from '../components/common/EmptyState';
import { motion, AnimatePresence } from 'framer-motion';

export const Recognition: React.FC = () => {
  const { data: cameraStream, isConnected: isCameraConnected } = useCameraStream();
  const { data: recognitionStream, isConnected: isRecognitionConnected } = useRecognitionStream();
  const { data: health } = useBackendHealth();

  // Track active faces on screen
  const [trackedFaces, setTrackedFaces] = useState<Map<string, WSRecognitionMessage>>(new Map());
  // Track all recognitions for the timeline
  const [timeline, setTimeline] = useState<WSRecognitionMessage[]>([]);
  
  // Ref for the camera container to compute relative bbox if needed (assuming 640x480 for now)
  const FRAME_WIDTH = 640;
  const FRAME_HEIGHT = 480;

  useEffect(() => {
    if (recognitionStream) {
      const now = Date.now();
      
      setTrackedFaces(prev => {
        const newMap = new Map(prev);
        newMap.set(recognitionStream.tracking_id, recognitionStream);
        return newMap;
      });

      setTimeline(prev => {
        // Prevent duplicate spam in timeline by same person
        const isDuplicate = prev.length > 0 && 
                            prev[0].identity_id === recognitionStream.identity_id && 
                            (now/1000 - prev[0].timestamp) < 2.0;
        if (isDuplicate) return prev;
        
        return [recognitionStream, ...prev].slice(0, 30);
      });
    }
  }, [recognitionStream]);

  // Clean up stale tracking boxes (older than 1.5 seconds)
  useEffect(() => {
    const interval = setInterval(() => {
      setTrackedFaces(prev => {
        let changed = false;
        const newMap = new Map(prev);
        const now = Date.now() / 1000;
        
        for (const [id, face] of newMap.entries()) {
          if (now - face.timestamp > 1.5) {
            newMap.delete(id);
            changed = true;
          }
        }
        return changed ? newMap : prev;
      });
    }, 500);
    return () => clearInterval(interval);
  }, []);

  const currentMatch = timeline.length > 0 ? timeline[0] : null;
  const isLive = isCameraConnected && isRecognitionConnected;

  return (
    <div className="h-full flex flex-col gap-4">
      
      {!health && (
        <div className="absolute inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center">
          <ErrorState 
            title="Backend Offline"
            message="Cannot connect to the AI Engine. Recognition paused."
          />
        </div>
      )}

      {/* Top Main Section */}
      <div className="flex-1 flex gap-4 min-h-0">
        
        {/* Main CCTV Feed (Left) */}
        <div className="flex-[3] flex flex-col h-full bg-black border border-white/10 rounded-md relative overflow-hidden">
          {/* Status Indicator */}
          <div className="absolute top-4 left-4 z-50">
             <StatusBadge status={isLive ? 'success' : 'warning'} dot>
                {isLive ? 'LIVE' : 'CONNECTING...'}
             </StatusBadge>
          </div>

          <CameraFeed 
            className="w-full h-full border-none rounded-none" 
            isOnline={isCameraConnected} 
            streamUrl={cameraStream ? `data:image/jpeg;base64,${cameraStream.image_base64}` : undefined}
            overlays={
              <div className="absolute inset-0 pointer-events-none">
                {Array.from(trackedFaces.values()).map(face => {
                  const isUnknown = face.identity_id === 'Unknown';
                  const color = isUnknown ? 'border-warning text-warning' : 'border-success text-success';
                  const bg = isUnknown ? 'bg-warning/20' : 'bg-success/20';
                  
                  // Map [x, y, w, h] to percentages based on assumed 640x480. 
                  // If backend sends [x1, y1, x2, y2], width = x2 - x1.
                  // Most systems send [x, y, w, h]. Let's assume [x, y, w, h].
                  const [x, y, w, h] = face.bbox;
                  const left = `${(x / FRAME_WIDTH) * 100}%`;
                  const top = `${(y / FRAME_HEIGHT) * 100}%`;
                  const width = `${(w / FRAME_WIDTH) * 100}%`;
                  const height = `${(h / FRAME_HEIGHT) * 100}%`;

                  return (
                    <motion.div 
                      key={face.tracking_id}
                      initial={{ opacity: 0, scale: 0.9 }}
                      animate={{ opacity: 1, scale: 1 }}
                      exit={{ opacity: 0 }}
                      transition={{ duration: 0.15 }}
                      className={`absolute border-[2px] ${color}`}
                      style={{ left, top, width, height }}
                    >
                      {/* Bounding Box inner highlight */}
                      <motion.div 
                        animate={isUnknown ? { opacity: [0.1, 0.4, 0.1] } : { opacity: 0.2 }}
                        transition={{ duration: 1.5, repeat: Infinity }}
                        className={`w-full h-full ${bg} pointer-events-none`} 
                      />

                      {/* Floating Metadata Panel */}
                      <motion.div 
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        className="absolute -right-48 top-0 bg-black/80 border border-white/20 p-2 w-44 backdrop-blur-sm text-[10px] font-mono space-y-1 shadow-xl"
                      >
                        <div className={`font-bold text-xs border-b border-white/10 pb-1 mb-1 ${isUnknown ? 'text-warning' : 'text-success'}`}>
                          {face.identity_id}
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-400">ID:</span><span className="text-white">{face.tracking_id}</span>
                        </div>
                        {!isUnknown && (
                          <div className="flex justify-between">
                            <span className="text-gray-400">Conf:</span><span className="text-white">{(face.verification_score * 100).toFixed(1)}%</span>
                          </div>
                        )}
                        <div className="flex justify-between">
                          <span className="text-gray-400">Mask:</span><span className={face.mask_status ? 'text-warning' : 'text-gray-400'}>{face.mask_status ? 'YES' : 'NO'}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-400">Time:</span><span className="text-white">{face.processing_time_ms.toFixed(0)}ms</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-400">Mode:</span><span className="text-white truncate max-w-[80px] text-right">{face.recognition_mode}</span>
                        </div>
                      </motion.div>
                    </motion.div>
                  );
                })}
              </div>
            }
          />
        </div>

        {/* Right Panel: Current Match */}
        <div className="w-80 flex flex-col gap-4 h-full overflow-y-auto pr-1">
          <Card className="p-0 border-primary/50 overflow-hidden flex flex-col">
            <div className="bg-primary/20 p-3 border-b border-primary/30 flex items-center justify-between">
              <h3 className="font-bold text-white text-sm uppercase tracking-wider">Current Match</h3>
              <StatusBadge status={currentMatch ? (currentMatch.identity_id === 'Unknown' ? 'warning' : 'success') : 'neutral'} dot>
                {currentMatch ? (currentMatch.identity_id === 'Unknown' ? 'Unverified' : 'Verified') : 'Waiting'}
              </StatusBadge>
            </div>
            
            {currentMatch ? (
              <motion.div 
                key={currentMatch.timestamp}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex-1 flex flex-col"
              >
                <div className="p-4 flex flex-col items-center border-b border-white/5 bg-secondary/30 text-center">
                  <div className={`w-24 h-24 rounded border-2 overflow-hidden mb-3 ${currentMatch.identity_id === 'Unknown' ? 'border-warning' : 'border-primary'}`}>
                    <img src={`https://api.dicebear.com/7.x/avataaars/svg?seed=${currentMatch.identity_id}`} className="w-full h-full object-cover bg-black" />
                  </div>
                  <h2 className="text-lg font-bold text-white">{currentMatch.identity_id}</h2>
                  <p className="text-xs text-primary font-mono mt-1">{currentMatch.tracking_id}</p>
                  <span className="mt-2 text-[10px] text-gray-400 bg-white/5 px-2 py-0.5 rounded border border-white/10 uppercase">
                    {new Date(currentMatch.timestamp * 1000).toLocaleTimeString()}
                  </span>
                </div>

                <div className="p-4 space-y-3">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-400 flex items-center gap-2"><Target size={14}/> Confidence</span>
                    <span className={currentMatch.identity_id === 'Unknown' ? 'text-warning font-mono' : 'text-success font-mono font-bold'}>
                      {(currentMatch.verification_score * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-400 flex items-center gap-2"><ShieldCheck size={14}/> Mask Status</span>
                    <span className={currentMatch.mask_status ? 'text-warning' : 'text-white'}>
                      {currentMatch.mask_status ? 'Wearing Mask' : 'No Mask'}
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-400 flex items-center gap-2"><Clock size={14}/> Inference</span>
                    <span className="text-white font-mono">{currentMatch.processing_time_ms.toFixed(0)}ms</span>
                  </div>
                  <div className="flex items-center justify-between text-sm border-t border-white/5 pt-3 mt-1">
                    <span className="text-gray-400">Mode</span>
                    <span className="text-[10px] bg-accent/20 text-accent px-1.5 py-0.5 rounded font-mono truncate max-w-[120px]">
                      {currentMatch.recognition_mode}
                    </span>
                  </div>
                </div>
              </motion.div>
            ) : (
              <EmptyState 
                icon={User}
                title="No Match"
                description="Waiting for recognition..."
              />
            )}
          </Card>
        </div>
      </div>

      {/* Bottom Timeline */}
      <Card className="h-40 shrink-0 flex flex-col overflow-hidden">
         <div className="px-4 py-2 bg-secondary border-b border-white/5 flex items-center justify-between">
           <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Recognition Timeline</h3>
         </div>
         <div className="flex-1 p-4 flex gap-4 overflow-x-auto items-center">
            {timeline.length === 0 ? (
              <div className="w-full flex items-center justify-center text-gray-500 gap-2">
                <Activity size={16}/> No events yet...
              </div>
            ) : (
              <AnimatePresence initial={false}>
                {timeline.map((event, i) => (
                  <motion.div 
                    key={`${event.tracking_id}-${event.timestamp}`} 
                    initial={{ opacity: 0, x: -20, scale: 0.9 }}
                    animate={{ opacity: 1, x: 0, scale: 1 }}
                    transition={{ duration: 0.3 }}
                    className="flex gap-3 items-center min-w-[220px] border-r border-white/5 pr-4 last:border-0"
                  >
                    <div className={`w-10 h-10 rounded border overflow-hidden shrink-0 ${event.identity_id === 'Unknown' ? 'border-warning' : 'border-success'}`}>
                      <img src={`https://api.dicebear.com/7.x/avataaars/svg?seed=${event.identity_id}`} className="w-full h-full bg-secondary object-cover" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className={`text-sm font-medium truncate ${event.identity_id === 'Unknown' ? 'text-warning' : 'text-white'}`}>
                        {event.identity_id}
                      </p>
                      <p className="text-[10px] text-gray-500 font-mono">
                        {new Date(event.timestamp * 1000).toLocaleTimeString([], { hour12: true, hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                      </p>
                    </div>
                    <div className="flex flex-col items-end text-[10px] font-mono">
                      <span className={event.identity_id === 'Unknown' ? 'text-warning' : 'text-success'}>
                        {(event.verification_score * 100).toFixed(1)}%
                      </span>
                      <span className="text-gray-500">{event.processing_time_ms.toFixed(0)}ms</span>
                    </div>
                  </motion.div>
                ))}
              </AnimatePresence>
            )}
         </div>
      </Card>

    </div>
  );
};
