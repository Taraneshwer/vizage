import React, { useState, useEffect, useMemo, useRef, useCallback } from 'react';
import { CameraFeed } from '../components/specialized/CameraFeed';
import { Card } from '../components/common/Card';
import { StatusBadge } from '../components/common/StatusBadge';
import { ShieldCheck, Target, Clock, User, Fingerprint, RefreshCcw, Activity, Upload, X, ImageIcon, CheckCircle, AlertTriangle, Loader2, Camera } from 'lucide-react';
import { useCameraStream, useRecognitionStream } from '../hooks/useWebSocket';
import type { WSRecognitionMessage } from '../hooks/useWebSocket';
import { useBackendHealth, useRecognizeSingle } from '../utils/api';
import type { RecognitionResultModel } from '../utils/api';
import { ErrorState } from '../components/common/ErrorState';
import { EmptyState } from '../components/common/EmptyState';
import { motion, AnimatePresence } from 'framer-motion';

/* ─── Upload Recognition Panel ─────────────────────────────────────────── */

const UploadRecognitionPanel: React.FC = () => {
  const [dragActive, setDragActive] = useState(false);
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [result, setResult] = useState<RecognitionResultModel | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const imgRef = useRef<HTMLImageElement>(null);
  const [imgSize, setImgSize] = useState<{ w: number; h: number } | null>(null);

  const { mutate: recognize, isPending } = useRecognizeSingle();

  const loadFile = useCallback((file: File) => {
    setResult(null);
    setErrorMsg(null);
    setImgSize(null);
    setImageFile(file);
    const url = URL.createObjectURL(file);
    setImageUrl(url);
  }, []);

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(false);
    const file = e.dataTransfer.files[0];
    if (file && file.type.startsWith('image/')) loadFile(file);
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) loadFile(file);
  };

  const handleRecognize = () => {
    if (!imageFile) return;
    setErrorMsg(null);
    recognize(imageFile, {
      onSuccess: (data) => setResult(data),
      onError: (err: any) => {
        const msg = err?.response?.data?.detail || err?.message || 'Recognition failed';
        setErrorMsg(msg);
      },
    });
  };

  const handleClear = () => {
    setImageFile(null);
    setImageUrl(null);
    setResult(null);
    setErrorMsg(null);
    setImgSize(null);
    if (inputRef.current) inputRef.current.value = '';
  };

  // Compute bbox overlay percentages once image natural size is known
  const bboxStyle = useMemo(() => {
    if (!result?.bbox || !imgSize) return null;
    const { x1, y1, x2, y2 } = result.bbox;
    return {
      left: `${(x1 / imgSize.w) * 100}%`,
      top: `${(y1 / imgSize.h) * 100}%`,
      width: `${((x2 - x1) / imgSize.w) * 100}%`,
      height: `${((y2 - y1) / imgSize.h) * 100}%`,
    };
  }, [result, imgSize]);

  const isKnown = result && !result.is_unknown;

  return (
    <div className="flex gap-4 h-full min-h-0">
      {/* Left: drop zone + image preview */}
      <div className="flex-[3] flex flex-col gap-3 min-h-0">
        {/* Drop zone */}
        {!imageUrl ? (
          <div
            id="recognition-upload-dropzone"
            onDragOver={(e) => { e.preventDefault(); setDragActive(true); }}
            onDragLeave={() => setDragActive(false)}
            onDrop={handleDrop}
            onClick={() => inputRef.current?.click()}
            className={`flex-1 flex flex-col items-center justify-center border-2 border-dashed rounded-lg cursor-pointer transition-all duration-200 select-none
              ${dragActive ? 'border-primary bg-primary/10 scale-[1.01]' : 'border-gray-300 bg-gray-50 hover:border-primary hover:bg-primary/5'}`}
          >
            <input ref={inputRef} type="file" accept="image/*" className="hidden" onChange={handleFileInput} id="recognition-file-input" />
            <motion.div
              animate={dragActive ? { scale: 1.15 } : { scale: 1 }}
              transition={{ type: 'spring', stiffness: 300 }}
              className="flex flex-col items-center gap-3 text-gray-400"
            >
              <Upload size={48} strokeWidth={1.5} className={dragActive ? 'text-primary' : ''} />
              <div className="text-center">
                <p className="text-sm font-semibold text-gray-700">Drop an image here</p>
                <p className="text-xs text-gray-400 mt-1">or click to browse — JPG, PNG, WEBP</p>
              </div>
            </motion.div>
          </div>
        ) : (
          <div className="flex-1 relative bg-black rounded-lg overflow-hidden flex items-center justify-center min-h-0">
            <img
              ref={imgRef}
              src={imageUrl}
              alt="uploaded"
              className="max-w-full max-h-full object-contain"
              onLoad={(e) => {
                const img = e.currentTarget;
                setImgSize({ w: img.naturalWidth, h: img.naturalHeight });
              }}
            />

            {/* BBox overlay */}
            <AnimatePresence>
              {bboxStyle && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className={`absolute border-2 ${isKnown ? 'border-success' : 'border-warning'} pointer-events-none`}
                  style={bboxStyle}
                >
                  <motion.div
                    animate={{ opacity: [0.1, 0.3, 0.1] }}
                    transition={{ duration: 1.5, repeat: Infinity }}
                    className={`w-full h-full ${isKnown ? 'bg-success/20' : 'bg-warning/20'}`}
                  />
                </motion.div>
              )}
            </AnimatePresence>

            {/* Top bar */}
            <div className="absolute top-2 left-2 right-2 flex items-center justify-between">
              <span className="text-[10px] text-white/70 bg-black/60 px-2 py-0.5 rounded font-mono truncate max-w-[60%]">
                {imageFile?.name}
              </span>
              <button
                onClick={handleClear}
                className="bg-black/60 hover:bg-black/80 text-white rounded p-1 transition-colors"
                title="Clear"
              >
                <X size={14} />
              </button>
            </div>
          </div>
        )}

        {/* Action row */}
        {imageUrl && (
          <div className="flex gap-2 shrink-0">
            <button
              id="recognition-upload-btn"
              onClick={handleRecognize}
              disabled={isPending}
              className="flex-1 flex items-center justify-center gap-2 bg-primary text-white text-sm font-semibold py-2.5 px-4 rounded-lg hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            >
              {isPending ? (
                <><Loader2 size={16} className="animate-spin" /> Recognizing...</>
              ) : (
                <><Fingerprint size={16} /> Run Recognition</>
              )}
            </button>
            <button
              onClick={() => inputRef.current?.click()}
              className="px-3 py-2 border border-gray-300 text-gray-600 rounded-lg hover:bg-gray-50 transition-colors text-sm"
              title="Change image"
            >
              <ImageIcon size={16} />
            </button>
            <input ref={inputRef} type="file" accept="image/*" className="hidden" onChange={handleFileInput} />
          </div>
        )}

        {/* Error */}
        <AnimatePresence>
          {errorMsg && (
            <motion.div
              initial={{ opacity: 0, y: -6 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="flex items-center gap-2 text-sm text-red-600 bg-red-50 border border-red-200 px-3 py-2 rounded-lg shrink-0"
            >
              <AlertTriangle size={14} /> {errorMsg}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Right: result panel */}
      <div className="w-72 shrink-0 flex flex-col gap-3">
        <Card className="p-0 border-primary/40 overflow-hidden flex flex-col flex-1">
          <div className="bg-primary/15 px-3 py-2.5 border-b border-primary/25 flex items-center justify-between">
            <h3 className="font-bold text-gray-900 text-sm uppercase tracking-wider">Result</h3>
            {result && (
              <StatusBadge status={isKnown ? 'success' : 'warning'} dot>
                {isKnown ? 'Identified' : 'Unknown'}
              </StatusBadge>
            )}
          </div>

          <AnimatePresence mode="wait">
            {!result && !isPending && (
              <motion.div key="empty" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="flex-1">
                <EmptyState icon={Fingerprint} title="No Result" description="Upload an image and run recognition" />
              </motion.div>
            )}

            {isPending && (
              <motion.div key="loading" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                className="flex-1 flex flex-col items-center justify-center gap-3 p-6"
              >
                <Loader2 size={36} className="animate-spin text-primary" />
                <p className="text-sm text-gray-500">Analyzing face...</p>
              </motion.div>
            )}

            {result && (
              <motion.div key="result" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="flex-1 flex flex-col">
                {/* Avatar + name */}
                <div className="p-4 flex flex-col items-center border-b border-gray-200 bg-secondary/30 text-center">
                  <div className={`w-20 h-20 rounded border-2 overflow-hidden mb-3 ${isKnown ? 'border-success' : 'border-warning'}`}>
                    <img
                      src={`https://api.dicebear.com/7.x/avataaars/svg?seed=${result.candidate?.identity_id ?? 'unknown'}`}
                      className="w-full h-full object-cover bg-black"
                    />
                  </div>
                  <h2 className="text-base font-bold text-gray-900 truncate max-w-full px-2">
                    {isKnown ? (result.candidate?.name ?? result.candidate?.identity_id) : 'Unknown Person'}
                  </h2>
                  {result.candidate?.identity_id && (
                    <p className="text-[10px] text-primary font-mono mt-1 truncate">{result.candidate.identity_id}</p>
                  )}
                </div>

                {/* Metrics */}
                <div className="p-4 space-y-3 text-sm">
                  <div className="flex items-center justify-between">
                    <span className="text-gray-500 flex items-center gap-1.5"><Target size={13}/> Confidence</span>
                    <span className={`font-mono font-bold ${isKnown ? 'text-success' : 'text-warning'}`}>
                      {(result.verification_score * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-gray-500 flex items-center gap-1.5"><ShieldCheck size={13}/> Mask</span>
                    <span className={result.has_mask ? 'text-warning' : 'text-gray-700'}>
                      {result.has_mask ? 'Detected' : 'None'}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-gray-500 flex items-center gap-1.5"><Clock size={13}/> Inference</span>
                    <span className="text-gray-700 font-mono">{result.processing_time_ms.toFixed(0)} ms</span>
                  </div>
                  <div className="flex items-center justify-between border-t border-gray-100 pt-3">
                    <span className="text-gray-500">State</span>
                    <span className="text-[10px] bg-accent/20 text-accent px-1.5 py-0.5 rounded font-mono">{result.state}</span>
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </Card>
      </div>
    </div>
  );
};

/* ─── Main Recognition Page ─────────────────────────────────────────────── */

export const Recognition: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'live' | 'upload'>('live');
  const { data: cameraStream, isConnected: isCameraConnected } = useCameraStream();
  const { data: recognitionStream, isConnected: isRecognitionConnected } = useRecognitionStream();
  const { data: health } = useBackendHealth();

  const [trackedFaces, setTrackedFaces] = useState<Map<string, WSRecognitionMessage>>(new Map());
  const [timeline, setTimeline] = useState<WSRecognitionMessage[]>([]);

  const FRAME_WIDTH = 640;
  const FRAME_HEIGHT = 480;

  const latencyMs = useMemo(() => {
    if (!cameraStream || !cameraStream.capture_timestamp) return undefined;
    const diff = (Date.now() / 1000) - cameraStream.capture_timestamp;
    return Math.max(0, diff * 1000);
  }, [cameraStream]);

  useEffect(() => {
    if (recognitionStream) {
      const now = Date.now();
      setTrackedFaces(prev => {
        const newMap = new Map(prev);
        newMap.set(recognitionStream.tracking_id, recognitionStream);
        return newMap;
      });
      setTimeline(prev => {
        const isDuplicate = prev.length > 0 &&
                            prev[0].identity_id === recognitionStream.identity_id &&
                            (now/1000 - prev[0].timestamp) < 2.0;
        if (isDuplicate) return prev;
        return [recognitionStream, ...prev].slice(0, 30);
      });
    }
  }, [recognitionStream]);

  useEffect(() => {
    const interval = setInterval(() => {
      const now = Date.now() / 1000;
      setTrackedFaces(prev => {
        let changed = false;
        const newMap = new Map();
        prev.forEach((value, key) => {
          if (now - value.timestamp < 1.5) {
            newMap.set(key, value);
          } else {
            changed = true;
          }
        });
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
            message="Cannot connect to the AI Engine. Please check if the Python backend is running."
          />
        </div>
      )}

      {/* Tab bar */}
      <div className="flex gap-1 p-1 bg-gray-100 rounded-lg w-fit shrink-0">
        <button
          id="recognition-tab-live"
          onClick={() => setActiveTab('live')}
          className={`flex items-center gap-2 px-4 py-1.5 text-sm font-medium rounded-md transition-all
            ${activeTab === 'live' ? 'bg-white text-primary shadow-sm' : 'text-gray-500 hover:text-gray-700'}`}
        >
          <Camera size={14} /> Live Camera
        </button>
        <button
          id="recognition-tab-upload"
          onClick={() => setActiveTab('upload')}
          className={`flex items-center gap-2 px-4 py-1.5 text-sm font-medium rounded-md transition-all
            ${activeTab === 'upload' ? 'bg-white text-primary shadow-sm' : 'text-gray-500 hover:text-gray-700'}`}
        >
          <Upload size={14} /> Upload Image
        </button>
      </div>

      <AnimatePresence mode="wait">
        {activeTab === 'live' ? (
          <motion.div key="live" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="flex-1 flex flex-col gap-4 min-h-0">
            {/* Live feed + sidebar */}
            <div className="flex-1 flex gap-4 min-h-0">
              {/* Camera */}
              <div className="flex-[3] flex flex-col h-full relative border border-gray-200 rounded overflow-hidden bg-black">
                <div className="absolute top-4 left-4 z-50">
                  <StatusBadge status={isLive ? 'success' : 'warning'} dot>
                    {isLive ? 'LIVE' : 'CONNECTING...'}
                  </StatusBadge>
                </div>
                <CameraFeed
                  className="w-full h-full border-none rounded-none"
                  isOnline={isCameraConnected}
                  streamUrl={cameraStream ? `data:image/jpeg;base64,${cameraStream.image_base64}` : undefined}
                  latencyMs={latencyMs}
                  overlays={
                    <div className="absolute inset-0 pointer-events-none">
                      {Array.from(trackedFaces.values()).map(face => {
                        const isUnknown = face.identity_id === 'Unknown';
                        const color = isUnknown ? 'border-warning text-warning' : 'border-success text-success';
                        const bg = isUnknown ? 'bg-warning/20' : 'bg-success/20';
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
                            <motion.div
                              animate={isUnknown ? { opacity: [0.1, 0.4, 0.1] } : { opacity: 0.2 }}
                              transition={{ duration: 1.5, repeat: Infinity }}
                              className={`w-full h-full ${bg} pointer-events-none`}
                            />
                            <motion.div
                              initial={{ opacity: 0, x: -10 }}
                              animate={{ opacity: 1, x: 0 }}
                              className="absolute -right-48 top-0 bg-black/80 border border-white/20 p-2 w-44 backdrop-blur-sm text-[10px] font-mono space-y-1 shadow-xl"
                            >
                              <div className={`font-bold text-xs border-b border-gray-300 pb-1 mb-1 ${isUnknown ? 'text-warning' : 'text-success'}`}>
                                {face.identity_id}
                              </div>
                              <div className="flex justify-between">
                                <span className="text-gray-600">ID:</span><span className="text-gray-900">{face.tracking_id}</span>
                              </div>
                              {!isUnknown && (
                                <div className="flex justify-between">
                                  <span className="text-gray-600">Conf:</span><span className="text-gray-900">{(face.verification_score * 100).toFixed(1)}%</span>
                                </div>
                              )}
                              <div className="flex justify-between">
                                <span className="text-gray-600">Mask:</span><span className={face.mask_status ? 'text-warning' : 'text-gray-600'}>{face.mask_status ? 'YES' : 'NO'}</span>
                              </div>
                              <div className="flex justify-between">
                                <span className="text-gray-600">Time:</span><span className="text-gray-900">{face.processing_time_ms.toFixed(0)}ms</span>
                              </div>
                              <div className="flex justify-between">
                                <span className="text-gray-600">Mode:</span><span className="text-gray-900 truncate max-w-[80px] text-right">{face.recognition_mode}</span>
                              </div>
                            </motion.div>
                          </motion.div>
                        );
                      })}
                    </div>
                  }
                />
              </div>

              {/* Current Match sidebar */}
              <div className="w-80 flex flex-col gap-4 h-full overflow-y-auto pr-1">
                <Card className="p-0 border-primary/50 overflow-hidden flex flex-col">
                  <div className="bg-primary/20 p-3 border-b border-primary/30 flex items-center justify-between">
                    <h3 className="font-bold text-gray-900 text-sm uppercase tracking-wider">Current Match</h3>
                    <StatusBadge status={currentMatch ? (currentMatch.identity_id === 'Unknown' ? 'warning' : 'success') : 'neutral'} dot>
                      {currentMatch ? (currentMatch.identity_id === 'Unknown' ? 'Unverified' : 'Verified') : 'Waiting'}
                    </StatusBadge>
                  </div>
                  {currentMatch ? (
                    <motion.div key={currentMatch.timestamp} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="flex-1 flex flex-col">
                      <div className="p-4 flex flex-col items-center border-b border-gray-200 bg-secondary/30 text-center">
                        <div className={`w-24 h-24 rounded border-2 overflow-hidden mb-3 ${currentMatch.identity_id === 'Unknown' ? 'border-warning' : 'border-primary'}`}>
                          <img src={`https://api.dicebear.com/7.x/avataaars/svg?seed=${currentMatch.identity_id}`} className="w-full h-full object-cover bg-black" />
                        </div>
                        <h2 className="text-lg font-bold text-gray-900">{currentMatch.identity_id}</h2>
                        <p className="text-xs text-primary font-mono mt-1">{currentMatch.tracking_id}</p>
                        <span className="mt-2 text-[10px] text-gray-600 bg-gray-100 px-2 py-0.5 rounded border border-gray-300 uppercase">
                          {new Date(currentMatch.timestamp * 1000).toLocaleTimeString()}
                        </span>
                      </div>
                      <div className="p-4 space-y-3">
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-gray-600 flex items-center gap-2"><Target size={14}/> Confidence</span>
                          <span className={currentMatch.identity_id === 'Unknown' ? 'text-warning font-mono' : 'text-success font-mono font-bold'}>
                            {(currentMatch.verification_score * 100).toFixed(1)}%
                          </span>
                        </div>
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-gray-600 flex items-center gap-2"><ShieldCheck size={14}/> Mask Status</span>
                          <span className={currentMatch.mask_status ? 'text-warning' : 'text-gray-900'}>
                            {currentMatch.mask_status ? 'Wearing Mask' : 'No Mask'}
                          </span>
                        </div>
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-gray-600 flex items-center gap-2"><Clock size={14}/> Inference</span>
                          <span className="text-gray-900 font-mono">{currentMatch.processing_time_ms.toFixed(0)}ms</span>
                        </div>
                        <div className="flex items-center justify-between text-sm border-t border-gray-200 pt-3 mt-1">
                          <span className="text-gray-600">Mode</span>
                          <span className="text-[10px] bg-accent/20 text-accent px-1.5 py-0.5 rounded font-mono truncate max-w-[120px]">
                            {currentMatch.recognition_mode}
                          </span>
                        </div>
                      </div>
                    </motion.div>
                  ) : (
                    <EmptyState icon={User} title="No Match" description="Waiting for recognition..." />
                  )}
                </Card>
              </div>
            </div>

            {/* Timeline */}
            <Card className="h-40 shrink-0 flex flex-col overflow-hidden">
              <div className="px-4 py-2 bg-secondary border-b border-gray-200 flex items-center justify-between">
                <h3 className="text-xs font-semibold text-gray-600 uppercase tracking-wider">Recognition Timeline</h3>
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
                        className="flex gap-3 items-center min-w-[220px] border-r border-gray-200 pr-4 last:border-0"
                      >
                        <div className={`w-10 h-10 rounded border overflow-hidden shrink-0 ${event.identity_id === 'Unknown' ? 'border-warning' : 'border-success'}`}>
                          <img src={`https://api.dicebear.com/7.x/avataaars/svg?seed=${event.identity_id}`} className="w-full h-full bg-secondary object-cover" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className={`text-sm font-medium truncate ${event.identity_id === 'Unknown' ? 'text-warning' : 'text-gray-900'}`}>
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
          </motion.div>
        ) : (
          <motion.div key="upload" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="flex-1 min-h-0">
            <UploadRecognitionPanel />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};
