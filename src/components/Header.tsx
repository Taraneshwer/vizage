import React, { useState, useEffect } from 'react';
import { 
  ShieldCheck, 
  Video, 
  Activity, 
  Bell, 
  Volume2, 
  VolumeX, 
  Sparkles, 
  User as UserIcon, 
  LogOut, 
  Key, 
  Sun, 
  Moon, 
  Clock,
  Radio,
  CheckCircle2,
  AlertTriangle
} from 'lucide-react';
import { SecurityUser, SystemMetrics } from '../types';

interface HeaderProps {
  user: SecurityUser;
  metrics: SystemMetrics;
  onOpenAuthModal: () => void;
  onOpenAICopilot: () => void;
  highContrast: boolean;
  onToggleHighContrast: () => void;
  soundEnabled: boolean;
  onToggleSound: () => void;
  unreadAlertCount: number;
}

export const Header: React.FC<HeaderProps> = ({
  user,
  metrics,
  onOpenAuthModal,
  onOpenAICopilot,
  highContrast,
  onToggleHighContrast,
  soundEnabled,
  onToggleSound,
  unreadAlertCount
}) => {
  const [timeString, setTimeString] = useState<string>('');
  const [userDropdownOpen, setUserDropdownOpen] = useState(false);

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setTimeString(now.toUTCString().replace('GMT', 'UTC'));
    };
    updateTime();
    const timer = setInterval(updateTime, 1000);
    return () => clearInterval(timer);
  }, []);

  return (
    <header className={`h-16 border-b transition-colors ${
      highContrast 
        ? 'bg-black text-white border-yellow-400' 
        : 'bg-white text-slate-900 border-slate-200'
    } sticky top-0 z-40 px-6 flex items-center justify-between shrink-0 shadow-sm`}>
      {/* Brand Identity */}
      <div className="flex items-center gap-4">
        <div className="bg-indigo-600 text-white font-bold px-2.5 py-1.5 rounded text-xs tracking-wider shadow-sm flex items-center gap-1.5">
          <ShieldCheck className="w-4 h-4 text-indigo-100" />
          
        </div>
        <div>
          <h1 className="text-lg font-semibold tracking-tight text-slate-800 uppercase flex items-center gap-2">
            VIZAGE
            <span className="text-[10px] font-bold font-mono px-1.5 py-0.5 bg-slate-100 text-slate-600 border border-slate-200 rounded">
              v4.2 PRO
            </span>
          </h1>
        </div>
      </div>

      {/* Center Telemetry & Status */}
      <div className="hidden lg:flex items-center gap-6">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.6)] animate-pulse" />
          <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">
            System: Online ({metrics.activeCameras}/{metrics.totalCameras} CAM)
          </span>
        </div>

        <div className="h-4 w-[1px] bg-slate-200" />

        <div className="flex items-center gap-2 text-xs font-mono text-slate-600">
          <Activity className="w-3.5 h-3.5 text-indigo-600" />
          <span>LATENCY: <strong className="text-slate-800">{metrics.avgInferenceLatencyMs}ms</strong></span>
        </div>

        <div className="h-4 w-[1px] bg-slate-200" />

        <div className="flex items-center gap-1.5 text-xs font-mono text-slate-600">
          <Clock className="w-3.5 h-3.5 text-indigo-600" />
          <span>{timeString || 'UTC Sync'}</span>
        </div>
      </div>

      {/* Right Controls & Profile */}
      <div className="flex items-center gap-4">
        {/* Sound Toggle */}
        <button
          onClick={onToggleSound}
          className={`p-2 rounded border text-xs transition-colors cursor-pointer ${
            soundEnabled 
              ? 'bg-slate-100 border-slate-300 text-indigo-600 hover:bg-slate-200' 
              : 'bg-white border-slate-200 text-slate-400 hover:bg-slate-50'
          }`}
          title={soundEnabled ? "Mute alert chimes" : "Enable alert chimes"}
        >
          {soundEnabled ? <Volume2 className="w-4 h-4" /> : <VolumeX className="w-4 h-4" />}
        </button>

        {/* High Contrast Toggle */}
        <button
          onClick={onToggleHighContrast}
          className={`p-2 rounded border text-xs transition-colors cursor-pointer ${
            highContrast 
              ? 'bg-yellow-400 text-black border-yellow-300 font-bold' 
              : 'bg-slate-100 border-slate-300 text-slate-600 hover:bg-slate-200'
          }`}
          title="Toggle High Contrast Mode"
        >
          {highContrast ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
        </button>

        {/* Bell Indicator */}
        <div className="relative">
          <button 
            className="p-2 rounded bg-slate-100 border border-slate-300 text-slate-600 hover:bg-slate-200 transition-colors cursor-pointer"
            title={`${unreadAlertCount} active security alerts`}
          >
            <Bell className="w-4 h-4 text-amber-500" />
            {unreadAlertCount > 0 && (
              <span className="absolute -top-1 -right-1 flex h-4 w-4 items-center justify-center rounded-full bg-rose-600 text-[10px] font-bold text-white font-mono">
                {unreadAlertCount}
              </span>
            )}
          </button>
        </div>
      </div>
    </header>
  );
};
