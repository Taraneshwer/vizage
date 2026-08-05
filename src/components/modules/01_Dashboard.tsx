 import React, { useState } from 'react';
import { 
  ShieldCheck, 
  Video, 
  Activity, 
  AlertTriangle, 
  CheckCircle2, 
  Scan, 
  Sparkles, 
  ArrowUpRight, 
  Radio, 
  Lock, 
  Zap, 
  Users, 
  UserPlus,
  Play,
  RefreshCw,
  Bell,
  Sliders,
  ShieldAlert
} from 'lucide-react';
import { SystemMetrics, CameraFeed, RecognitionEvent, AIAnalysisResponse } from '../../types';

interface DashboardModuleProps {
  metrics: SystemMetrics;
  cameras: CameraFeed[];
  logs: RecognitionEvent[];
  onNavigateToLive: () => void;
  onNavigateToLogs: () => void;
  onNavigateToEnrollment: () => void;
  onTriggerEmergencyAlert: () => void;
  emergencyActive: boolean;
}

export const DashboardModule: React.FC<DashboardModuleProps> = ({
  metrics,
  cameras,
  logs,
  onNavigateToLive,
  onNavigateToLogs,
  onNavigateToEnrollment,
  onTriggerEmergencyAlert,
  emergencyActive
}) => {
  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Top Banner Alert if Emergency Active */}
      {emergencyActive && (
        <div className="p-4 rounded-xl bg-rose-600 border border-rose-500 text-white flex items-center justify-between shadow-xl animate-pulse">
          <div className="flex items-center space-x-3">
            <ShieldAlert className="w-8 h-8 text-yellow-300" />
            <div>
              <h2 className="text-base font-bold uppercase tracking-wider font-mono">EMERGENCY LOCKDOWN SIGNAL ACTIVE</h2>
              <p className="text-xs text-rose-100">All turnstiles locked. Tactical security dispatched to Vault B & Bio Cleanroom.</p>
            </div>
          </div>
          <button
            onClick={onTriggerEmergencyAlert}
            className="px-4 py-2 bg-slate-900 text-white rounded-lg text-xs font-mono font-bold hover:bg-black cursor-pointer"
          >
            DISARM LOCKDOWN
          </button>
        </div>
      )}

      {/* Main Section: Hero Card */}
      <div className="bg-white border border-slate-200 rounded-2xl shadow-sm p-6 sm:p-8 flex flex-col justify-between space-y-6">
        {/* Top Section: Text & Action Buttons */}
        <div className="space-y-4">
          <div>
            <h1 className="text-3xl font-black tracking-wider text-slate-900 font-sans uppercase">
              VIZAGE
            </h1>
            <p className="text-base font-bold text-slate-800 mt-1">
              See Beyond the Mask.
            </p>
            <p className="text-xs text-slate-500 leading-relaxed mt-2 max-w-lg">
              Masked Face Recognition that identifies people even when they wear a mask.
            </p>
          </div>

          {/* Action Buttons */}
          <div className="pt-2 flex flex-col sm:flex-row gap-3">
            <button
              onClick={onNavigateToLive}
              className="px-5 py-2.5 bg-slate-900 hover:bg-slate-800 text-white rounded-lg text-xs font-bold font-mono flex items-center justify-center gap-2.5 shadow transition-all cursor-pointer border border-slate-900"
            >
              <Play className="w-3.5 h-3.5 fill-current text-white" />
              <span>Start Live Recognition</span>
            </button>

            <button
              onClick={onNavigateToEnrollment}
              className="px-5 py-2.5 bg-white hover:bg-slate-50 text-slate-900 border border-slate-300 rounded-lg text-xs font-bold font-mono flex items-center justify-center gap-2.5 transition-all cursor-pointer shadow-sm"
            >
              <UserPlus className="w-3.5 h-3.5 text-slate-700" />
              <span>Enroll New Identity</span>
            </button>
          </div>
        </div>

        {/* Bottom Feature Grid */}
        <div className="pt-4 border-t border-slate-200 grid grid-cols-2 sm:grid-cols-4 gap-3 text-center">
          <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-100 flex flex-col items-center justify-center space-y-1">
            <Zap className="w-4 h-4 text-slate-800" />
            <span className="text-[11px] font-bold text-slate-800">Real-time Recognition</span>
          </div>

          <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-100 flex flex-col items-center justify-center space-y-1">
            <Scan className="w-4 h-4 text-slate-800" />
            <span className="text-[11px] font-bold text-slate-800">Mask Detection</span>
          </div>

          <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-100 flex flex-col items-center justify-center space-y-1">
            <CheckCircle2 className="w-4 h-4 text-slate-800" />
            <span className="text-[11px] font-bold text-slate-800">High Accuracy</span>
          </div>

          <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-100 flex flex-col items-center justify-center space-y-1">
            <ShieldCheck className="w-4 h-4 text-slate-800" />
            <span className="text-[11px] font-bold text-slate-800">Secure & Private</span>
          </div>
        </div>
      </div>

      {/* Quick Commands */}
      <div className="bg-white border border-slate-200 p-5 rounded-2xl shadow-sm space-y-3">
        <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
          QUICK COMMANDS
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <button
            onClick={onNavigateToEnrollment}
            className="flex items-center justify-between p-3.5 rounded-xl bg-slate-50 hover:bg-indigo-50/50 hover:border-indigo-200 border border-slate-100 text-xs font-bold text-slate-800 transition-all cursor-pointer"
          >
            <div className="flex items-center gap-2.5">
              <Users className="w-4 h-4 text-indigo-600" />
              <span>Enroll New Subject Face</span>
            </div>
            <ArrowUpRight className="w-4 h-4 text-slate-400" />
          </button>

          <button
            onClick={onNavigateToLogs}
            className="flex items-center justify-between p-3.5 rounded-xl bg-slate-50 hover:bg-slate-100 border border-slate-100 text-xs font-bold text-slate-800 transition-all cursor-pointer"
          >
            <div className="flex items-center gap-2.5">
              <Sliders className="w-4 h-4 text-slate-500" />
              <span>Audit Security Logs</span>
            </div>
            <ArrowUpRight className="w-4 h-4 text-slate-400" />
          </button>
        </div>
      </div>

      {/* Bottom System Alert Banner (Professional Polish style) */}
      <div className="bg-indigo-900 text-white rounded-xl flex items-center px-8 py-4 justify-between gap-6 shadow-md">
        <div className="flex items-center gap-4">
          <span className="text-[10px] font-black uppercase text-indigo-300 tracking-[0.2em]">
            Station Alert
          </span>
          <p className="text-xs md:text-sm font-medium">
            Periocular feature vector model ResNet-102 running on GPU Node 01. Encryption AES-256 ACTIVE.
          </p>
        </div>
        <div className="flex items-center gap-4 shrink-0">
          <div className="text-right hidden sm:block">
            <p className="text-[10px] text-indigo-300 font-bold uppercase tracking-widest">Encryption</p>
            <p className="text-xs font-mono">AES-256 ACTIVE</p>
          </div>
          <button className="px-4 py-2 bg-indigo-600 rounded font-bold text-xs uppercase tracking-widest hover:bg-indigo-500 transition-colors cursor-pointer">
            Ack All
          </button>
        </div>
      </div>
    </div>
  );
};
