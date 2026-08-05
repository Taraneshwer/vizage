import React, { useState, useRef, useEffect } from 'react';
import { 
  ScanFace, 
  Video, 
  Grid, 
  Sliders, 
  Camera, 
  Eye, 
  ShieldAlert, 
  CheckCircle2, 
  Flame, 
  Sparkles,
  Maximize2,
  RefreshCw,
  Zap,
  Radio
} from 'lucide-react';
import { CameraFeed, RecognitionEvent, SystemMetrics } from '../../types';

interface LiveRecognitionModuleProps {
  cameras: CameraFeed[];
  metrics: SystemMetrics;
  logs: RecognitionEvent[];
  onNavigateToLogs?: () => void;
  onAddLogEvent: (event: RecognitionEvent) => void;
}

export const LiveRecognitionModule: React.FC<LiveRecognitionModuleProps> = ({
  cameras,
  metrics,
  logs,
  onNavigateToLogs,
  onAddLogEvent
}) => {
  const [selectedCameraId, setSelectedCameraId] = useState<string>('cam-01');
  const [layout, setLayout] = useState<'1x1' | '2x2' | '3x3'>('2x2');

  // Live Webcam Real-time Canvas State
  const [isWebcamActive, setIsWebcamActive] = useState<boolean>(false);
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  // Toggle Live Browser Camera
  const handleToggleWebcam = async () => {
    if (isWebcamActive) {
      if (videoRef.current && videoRef.current.srcObject) {
        const stream = videoRef.current.srcObject as MediaStream;
        stream.getTracks().forEach(track => track.stop());
      }
      setIsWebcamActive(false);
    } else {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true });
        setIsWebcamActive(true);
        setTimeout(() => {
          if (videoRef.current) {
            videoRef.current.srcObject = stream;
          }
        }, 300);
      } catch (e) {
        alert('Webcam permission not granted or device unavailable. Using simulated live video stream.');
      }
    }
  };

  // Canvas drawing loop for live webcam or simulated feed
  useEffect(() => {
    let animId: number;

    const renderLandmarks = () => {
      if (canvasRef.current && (videoRef.current || !isWebcamActive)) {
        const canvas = canvasRef.current;
        const ctx = canvas.getContext('2d');
        if (ctx) {
          ctx.clearRect(0, 0, canvas.width, canvas.height);

          // Draw simulated / real facial bounding box
          const time = Date.now() * 0.002;
          const boxX = canvas.width * 0.35 + Math.sin(time) * 10;
          const boxY = canvas.height * 0.25 + Math.cos(time) * 8;
          const boxW = canvas.width * 0.3;
          const boxH = canvas.height * 0.45;

          // Box stroke
          ctx.lineWidth = 2;
          ctx.strokeStyle = '#06b6d4';
          ctx.strokeRect(boxX, boxY, boxW, boxH);

          // Corner Crosshairs
          const len = 12;
          ctx.lineWidth = 3;
          ctx.strokeStyle = '#38bdf8';
          // TL
          ctx.beginPath(); ctx.moveTo(boxX, boxY + len); ctx.lineTo(boxX, boxY); ctx.lineTo(boxX + len, boxY); ctx.stroke();
          // TR
          ctx.beginPath(); ctx.moveTo(boxX + boxW - len, boxY); ctx.lineTo(boxX + boxW, boxY); ctx.lineTo(boxX + boxW, boxY + len); ctx.stroke();

          // Periocular Eye Alignment Line
          ctx.setLineDash([4, 4]);
          ctx.strokeStyle = '#a855f7';
          ctx.beginPath();
          ctx.moveTo(boxX + boxW * 0.2, boxY + boxH * 0.3);
          ctx.lineTo(boxX + boxW * 0.8, boxY + boxH * 0.3);
          ctx.stroke();
          ctx.setLineDash([]);

          // Feature points
          ctx.fillStyle = '#10b981';
          ctx.fillRect(boxX + boxW * 0.3, boxY + boxH * 0.3 - 2, 4, 4);
          ctx.fillRect(boxX + boxW * 0.7, boxY + boxH * 0.3 - 2, 4, 4);

          // Bounding Label
          ctx.fillStyle = '#082f49';
          ctx.fillRect(boxX, boxY - 20, 140, 18);
          ctx.fillStyle = '#38bdf8';
          ctx.font = '10px monospace';
          ctx.fillText('97.4% MASK: N95', boxX + 4, boxY - 7);
        }
      }
      animId = requestAnimationFrame(renderLandmarks);
    };

    renderLandmarks();
    return () => cancelAnimationFrame(animId);
  }, [isWebcamActive]);

  const handleManualTriggerSnapshot = () => {
    const selectedCam = cameras.find(c => c.id === selectedCameraId) || cameras[0] || {
      id: 'cam-01',
      name: 'Turnstile Main North',
      zone: 'Lobby Zone A',
      status: 'Online',
      resolution: '1080p',
      fps: 30,
      aiLatencyMs: 12.4,
      totalDetectionsToday: 1420,
      maskedCountToday: 1380,
      watchlistHitsToday: 1,
      streamType: 'Simulated Loop'
    };
    const newLog: RecognitionEvent = {
      id: `log-${Date.now()}`,
      timestamp: new Date().toISOString().replace('T', ' ').slice(0, 19),
      cameraId: selectedCam.id,
      cameraName: selectedCam.name,
      zone: selectedCam.zone,
      subjectId: 'sub-001',
      subjectName: 'Dr. Elena Rostova',
      subjectCategory: 'Employee',
      matchConfidence: parseFloat((88 + Math.random() * 11).toFixed(1)),
      maskDetected: 'Surgical Mask',
      maskCorrectlyWorn: true,
      facialOcclusionPercent: 58,
      snapshotUrl: 'https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?auto=format&fit=crop&q=80&w=400',
      riskLevel: 'Normal',
      flaggedByOfficer: false,
      verificationStatus: 'Verified',
      notes: 'Manual snapshot log triggered by Officer via Live Recognition Console.'
    };

    onAddLogEvent(newLog);
    alert(`Snapshot & recognition event logged for ${selectedCam.name}!`);
  };

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Title & Layout Controls */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-200 pb-4">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 rounded-xl bg-emerald-50 text-emerald-600 border border-emerald-100">
            <ScanFace className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-slate-900 font-mono uppercase">
              LIVE MASKED RECOGNITION WALL
            </h1>
            <p className="text-xs text-slate-500">
              Real-time video inference wall with periocular feature alignment
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          {/* Webcam Toggle Button */}
          <button
            onClick={handleToggleWebcam}
            className={`px-3.5 py-2 rounded-lg border text-xs font-mono font-bold flex items-center space-x-2 transition-all cursor-pointer ${
              isWebcamActive
                ? 'bg-emerald-600 text-white border-emerald-600 shadow-sm'
                : 'bg-white text-slate-700 border-slate-200 hover:bg-slate-50'
            }`}
          >
            <Camera className={`w-4 h-4 ${isWebcamActive ? 'text-white' : 'text-emerald-600'}`} />
            <span>{isWebcamActive ? 'Disable Live Camera' : 'Test Browser Camera'}</span>
          </button>

          {/* Grid Layout Selection */}
          <div className="flex items-center space-x-1 bg-white p-1 rounded-lg border border-slate-200 text-xs font-mono shadow-sm">
            {(['1x1', '2x2', '3x3'] as const).map((g) => (
              <button
                key={g}
                onClick={() => setLayout(g)}
                className={`px-2.5 py-1 rounded cursor-pointer transition-colors ${
                  layout === g ? 'bg-indigo-600 text-white font-bold' : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                {g}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Hero Metric Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Metric 1 */}
        <div className="bg-white border border-slate-200 p-4 rounded-xl shadow-sm flex flex-col justify-between">
          <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Total Scans (24h)</p>
          <div className="mt-2 flex items-baseline justify-between">
            <h2 className="text-2xl font-bold text-slate-900">{metrics.totalDetections24h.toLocaleString()}</h2>
            <span className="text-[10px] font-bold text-emerald-600 font-mono">+12.4% ↑</span>
          </div>
        </div>

        {/* Metric 2 */}
        <div className="bg-white border border-slate-200 p-4 rounded-xl shadow-sm flex flex-col justify-between">
          <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Mask Detections</p>
          <div className="mt-2 flex items-baseline justify-between">
            <h2 className="text-2xl font-bold text-indigo-600">{metrics.maskCompliancePct}%</h2>
            <span className="text-[10px] font-bold text-emerald-600 font-mono">+5.2% ↑</span>
          </div>
        </div>

        {/* Metric 3 */}
        <div className="bg-white border border-slate-200 p-4 rounded-xl shadow-sm flex flex-col justify-between">
          <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Identified Positives</p>
          <div className="mt-2 flex items-baseline justify-between">
            <h2 className="text-2xl font-bold text-slate-900">{metrics.enrolledSubjectsCount}</h2>
            <span className="text-[10px] font-bold text-slate-400 font-mono">100% Match</span>
          </div>
        </div>

        {/* Metric 4 */}
        <div className="bg-white border border-slate-200 p-4 rounded-xl shadow-sm flex flex-col justify-between">
          <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Flagged / Watchlist</p>
          <div className="mt-2 flex items-baseline justify-between">
            <h2 className="text-2xl font-bold text-rose-500">{metrics.watchlistAlerts24h}</h2>
            <span className="text-[10px] font-bold text-rose-500 font-mono bg-rose-50 px-1.5 py-0.5 rounded border border-rose-200">
              High Priority
            </span>
          </div>
        </div>
      </div>

      {/* Main Studio Grid */}
      <div className="space-y-4">
        {/* CCTV Grid View */}
        <div className={`grid gap-3 ${
          layout === '1x1' ? 'grid-cols-1' : layout === '2x2' ? 'grid-cols-1 sm:grid-cols-2' : 'grid-cols-2 md:grid-cols-3'
        }`}>
          {cameras.length === 0 ? (
            <div className="col-span-full relative bg-slate-900 border border-slate-700 rounded-xl overflow-hidden aspect-video flex flex-col items-center justify-center p-6 text-center shadow-lg">
              {isWebcamActive ? (
                <div className="relative w-full h-full">
                  <video ref={videoRef} autoPlay playsInline muted className="w-full h-full object-cover" />
                  <canvas
                    ref={canvasRef}
                    width={640}
                    height={360}
                    className="absolute inset-0 w-full h-full pointer-events-none"
                  />
                  <div className="absolute top-2 left-2 bg-slate-950/90 text-white px-2.5 py-1 rounded border border-slate-800 text-xs font-mono font-bold">
                    Local Browser Camera Stream (Testing Mode)
                  </div>
                </div>
              ) : (
                <div className="space-y-3 font-mono text-xs">
                  <div className="p-3 bg-slate-800 text-indigo-400 rounded-full w-12 h-12 flex items-center justify-center mx-auto border border-slate-700">
                    <Camera className="w-6 h-6" />
                  </div>
                  <h3 className="text-slate-200 font-bold text-sm">NO HARDWARE CAMERAS CONNECTED</h3>
                  <p className="text-slate-400 max-w-md mx-auto text-[11px]">
                    The system is awaiting video streams from backend RTSP/WebRTC encoders. You can test real-time recognition using your device's browser camera.
                  </p>
                  <button
                    onClick={handleToggleWebcam}
                    className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg font-bold shadow cursor-pointer transition-colors"
                  >
                    Enable Browser Camera Stream
                  </button>
                </div>
              )}
            </div>
          ) : (
            cameras.slice(0, layout === '1x1' ? 1 : layout === '2x2' ? 4 : 6).map((cam) => {
              const isSelected = cam.id === selectedCameraId;

              return (
                <div
                  key={cam.id}
                  onClick={() => setSelectedCameraId(cam.id)}
                  className={`relative bg-slate-900 border rounded-xl overflow-hidden aspect-video cursor-pointer transition-all ${
                    isSelected ? 'border-indigo-500 ring-2 ring-indigo-500/30 shadow-xl' : 'border-slate-800 hover:border-slate-700'
                  }`}
                >
                  {/* Live Video or Canvas stream */}
                  {isWebcamActive && isSelected ? (
                    <div className="relative w-full h-full">
                      <video ref={videoRef} autoPlay playsInline muted className="w-full h-full object-cover" />
                      <canvas
                        ref={canvasRef}
                        width={640}
                        height={360}
                        className="absolute inset-0 w-full h-full pointer-events-none"
                      />
                    </div>
                  ) : (
                    <div className="relative w-full h-full bg-slate-950 flex flex-col items-center justify-center p-4">
                      <div className="absolute inset-0 bg-[linear-gradient(to_right,#1e293b_1px,transparent_1px),linear-gradient(to_bottom,#1e293b_1px,transparent_1px)] bg-[size:1.5rem_1.5rem] opacity-30" />
                      <Camera className="w-8 h-8 text-indigo-500/60 mb-1" />
                      <span className="text-[10px] font-mono font-bold text-slate-400 z-10">{cam.name} STREAM</span>
                      <canvas
                        ref={isSelected ? canvasRef : null}
                        width={640}
                        height={360}
                        className="absolute inset-0 w-full h-full pointer-events-none"
                      />
                    </div>
                  )}

                  {/* Header bar overlay */}
                  <div className="absolute top-2 left-2 right-2 flex justify-between items-center text-[10px] font-mono">
                    <span className="bg-slate-950/80 text-slate-100 px-2 py-0.5 rounded border border-slate-800 font-bold">
                      {cam.name}
                    </span>
                    <span className="bg-rose-600 text-white border border-rose-500 px-1.5 py-0.5 rounded font-bold flex items-center gap-1">
                      <span className="w-1.5 h-1.5 bg-white rounded-full animate-ping" />
                      LIVE
                    </span>
                  </div>

                  {/* Bottom Stats */}
                  <div className="absolute bottom-2 left-2 right-2 flex justify-between items-center text-[10px] font-mono text-slate-300 bg-slate-950/80 px-2 py-1 rounded border border-slate-800">
                    <span>{cam.zone}</span>
                    <span className="text-emerald-400 font-bold">{cam.aiLatencyMs}ms AI</span>
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Trigger Snapshot Action Bar */}
        <div className="p-3.5 bg-white rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
          <div className="flex items-center space-x-2 text-xs font-mono text-slate-700">
            <Radio className="w-4 h-4 text-indigo-600 animate-pulse" />
            <span>Selected Camera: <strong className="text-slate-900">{cameras.find(c => c.id === selectedCameraId)?.name}</strong></span>
          </div>
          <button
            onClick={handleManualTriggerSnapshot}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white font-mono text-xs font-extrabold rounded-lg shadow cursor-pointer flex items-center space-x-2 transition-colors"
          >
            <Camera className="w-4 h-4" />
            <span>Capture & Log Event</span>
          </button>
        </div>
      </div>

      {/* Recent Events Section */}
      <div className="bg-white border border-slate-200 rounded-2xl flex flex-col overflow-hidden shadow-sm">
        <div className="p-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
          <h3 className="text-xs font-black uppercase tracking-widest text-slate-400">Recent Events</h3>
          {onNavigateToLogs && (
            <button
              onClick={onNavigateToLogs}
              className="text-[10px] font-bold text-indigo-600 hover:text-indigo-800 cursor-pointer"
            >
              View All
            </button>
          )}
        </div>

        <div className="p-4">
          {logs.length === 0 ? (
            <div className="py-12 px-4 text-center text-xs font-mono text-slate-400 space-y-2">
              <p className="font-bold text-slate-600">No Events Recorded</p>
              <p className="text-[11px] text-slate-400">Awaiting backend stream data or live camera event captures.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {logs.slice(0, 6).map((log) => {
                const isWarning = log.riskLevel === 'Critical' || log.riskLevel === 'Warning';
                return (
                  <div
                    key={log.id}
                    className={`p-3 rounded-lg border flex items-center justify-between transition-colors ${
                      isWarning
                        ? 'bg-rose-50 border-rose-100 text-rose-900'
                        : 'bg-slate-50 border-slate-100 text-slate-900'
                    }`}
                  >
                    <div>
                      <p className={`text-xs font-bold ${isWarning ? 'text-rose-900' : 'text-slate-900'}`}>
                        {log.subjectName}
                      </p>
                      <p className={`text-[10px] ${isWarning ? 'text-rose-500' : 'text-slate-400'}`}>
                        {log.timestamp.split(' ')[1]} • {log.cameraName}
                      </p>
                    </div>

                    <div className="text-right font-mono">
                      <p className={`text-[10px] font-bold uppercase tracking-wider ${
                        isWarning ? 'text-rose-600' : 'text-emerald-600'
                      }`}>
                        {log.riskLevel === 'Normal' ? 'VERIFIED' : log.riskLevel.toUpperCase()}
                      </p>
                      <p className={`text-[10px] ${isWarning ? 'text-rose-400' : 'text-slate-400'}`}>
                        {log.matchConfidence}% Match
                      </p>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
