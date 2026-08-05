import React, { useState } from 'react';
import { 
  NavigationModule, 
  SecurityUser, 
  SystemMetrics, 
  CameraFeed, 
  EnrolledSubject, 
  RecognitionEvent 
} from './types';
import { 
  INITIAL_SECURITY_USER, 
  INITIAL_METRICS, 
  INITIAL_CAMERAS, 
  INITIAL_ENROLLED_SUBJECTS, 
  INITIAL_LOGS 
} from './data/mockData';

import { Header } from './components/Header';
import { Sidebar } from './components/Sidebar';
import { AuthModal } from './components/AuthModal';
import { AICopilotModal } from './components/AICopilotModal';

import { DashboardModule } from './components/modules/01_Dashboard';
import { EnrollmentModule } from './components/modules/02_Enrollment';
import { LiveRecognitionModule } from './components/modules/03_LiveRecognition';
import { IdentityGalleryModule } from './components/modules/04_IdentityGallery';
import { HistoryLogsModule } from './components/modules/05_HistoryLogs';
import { AnalyticsModule } from './components/modules/06_Analytics';
import { SettingsModule } from './components/modules/07_Settings';

export default function App() {
  const [activeModule, setActiveModule] = useState<NavigationModule>('dashboard');

  // Core System State
  const [user, setUser] = useState<SecurityUser>(INITIAL_SECURITY_USER);
  const [cameras, setCameras] = useState<CameraFeed[]>(INITIAL_CAMERAS);
  const [subjects, setSubjects] = useState<EnrolledSubject[]>(INITIAL_ENROLLED_SUBJECTS);
  const [logs, setLogs] = useState<RecognitionEvent[]>(INITIAL_LOGS);

  // Dynamic System Metrics derived from actual state
  const metrics: SystemMetrics = {
    activeCameras: cameras.filter(c => c.status === 'Online').length,
    totalCameras: cameras.length,
    aiEngineLoadPct: cameras.length > 0 ? 12.5 : 0,
    avgInferenceLatencyMs: cameras.length > 0 ? 14.2 : 0,
    maskedAccuracyPct: logs.length > 0 ? 98.5 : 0,
    totalDetections24h: logs.length,
    maskCompliancePct: logs.length > 0 
      ? Math.round((logs.filter(l => l.maskCorrectlyWorn).length / logs.length) * 100) 
      : 0,
    watchlistAlerts24h: logs.filter(l => l.subjectCategory === 'Watchlist' || l.riskLevel === 'Critical').length,
    enrolledSubjectsCount: subjects.length,
  };

  // Settings & Toggles
  const [highContrast, setHighContrast] = useState<boolean>(false);
  const [soundEnabled, setSoundEnabled] = useState<boolean>(true);
  const [emergencyActive, setEmergencyActive] = useState<boolean>(false);

  // Modals
  const [authModalOpen, setAuthModalOpen] = useState<boolean>(false);
  const [aiCopilotOpen, setAiCopilotOpen] = useState<boolean>(false);

  // Sound chime helper
  const playAlertChime = () => {
    if (!soundEnabled) return;
    try {
      const audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)();
      const osc = audioCtx.createOscillator();
      const gain = audioCtx.createGain();
      osc.type = 'sine';
      osc.frequency.setValueAtTime(880, audioCtx.currentTime); // A5 note
      gain.gain.setValueAtTime(0.1, audioCtx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.3);
      osc.connect(gain);
      gain.connect(audioCtx.destination);
      osc.start();
      osc.stop(audioCtx.currentTime + 0.3);
    } catch (e) {
      // AudioContext fallback
    }
  };

  const handleTriggerEmergency = () => {
    const nextState = !emergencyActive;
    setEmergencyActive(nextState);
    if (nextState) {
      playAlertChime();
    }
  };

  const handleAddSubject = (newSubject: EnrolledSubject) => {
    setSubjects(prev => [newSubject, ...prev]);
  };

  const handleUpdateSubject = (updated: EnrolledSubject) => {
    setSubjects(prev => prev.map(s => s.id === updated.id ? updated : s));
  };

  const handleAddLogEvent = (newEvent: RecognitionEvent) => {
    setLogs(prev => [newEvent, ...prev]);
    playAlertChime();
  };

  const handleUpdateLog = (updated: RecognitionEvent) => {
    setLogs(prev => prev.map(l => l.id === updated.id ? updated : l));
  };

  return (
    <div className={`min-h-screen flex flex-col font-sans transition-colors ${
      highContrast 
        ? 'bg-black text-white selection:bg-yellow-400 selection:text-black' 
        : 'bg-slate-50 text-slate-900 selection:bg-indigo-500 selection:text-white'
    }`}>
      {/* Top Header */}
      <Header
        user={user}
        metrics={metrics}
        onOpenAuthModal={() => setAuthModalOpen(true)}
        onOpenAICopilot={() => setAiCopilotOpen(true)}
        highContrast={highContrast}
        onToggleHighContrast={() => setHighContrast(!highContrast)}
        soundEnabled={soundEnabled}
        onToggleSound={() => setSoundEnabled(!soundEnabled)}
        unreadAlertCount={logs.filter(l => l.riskLevel === 'Critical' || l.riskLevel === 'Warning').length}
      />

      {/* Main Body Area: Sidebar + Active Module View */}
      <div className="flex-1 flex overflow-hidden">
        <Sidebar
          activeModule={activeModule}
          onSelectModule={(mod) => setActiveModule(mod)}
          highContrast={highContrast}
          onTriggerEmergencyAlert={handleTriggerEmergency}
          emergencyActive={emergencyActive}
        />

        {/* Dynamic View Content Container */}
        <main className={`flex-1 overflow-y-auto ${highContrast ? 'bg-black text-white' : 'bg-slate-50 text-slate-900'}`}>
          {activeModule === 'dashboard' && (
            <DashboardModule
              metrics={metrics}
              cameras={cameras}
              logs={logs}
              onNavigateToLive={() => setActiveModule('live-recognition')}
              onNavigateToLogs={() => setActiveModule('history')}
              onNavigateToEnrollment={() => setActiveModule('enrollment')}
              onTriggerEmergencyAlert={handleTriggerEmergency}
              emergencyActive={emergencyActive}
            />
          )}

          {activeModule === 'enrollment' && (
            <EnrollmentModule
              onAddSubject={handleAddSubject}
              onNavigateToGallery={() => setActiveModule('identity-gallery')}
            />
          )}

          {activeModule === 'live-recognition' && (
            <LiveRecognitionModule
              cameras={cameras}
              metrics={metrics}
              logs={logs}
              onNavigateToLogs={() => setActiveModule('history')}
              onAddLogEvent={handleAddLogEvent}
            />
          )}

          {activeModule === 'identity-gallery' && (
            <IdentityGalleryModule
              subjects={subjects}
              onUpdateSubject={handleUpdateSubject}
              onNavigateToEnrollment={() => setActiveModule('enrollment')}
            />
          )}

          {activeModule === 'history' && (
            <HistoryLogsModule
              logs={logs}
              onUpdateLog={handleUpdateLog}
            />
          )}

          {activeModule === 'analytics' && (
            <AnalyticsModule logs={logs} />
          )}

          {activeModule === 'settings' && (
            <SettingsModule
              highContrast={highContrast}
              onToggleHighContrast={() => setHighContrast(!highContrast)}
              soundEnabled={soundEnabled}
              onToggleSound={() => setSoundEnabled(!soundEnabled)}
              onOpenAuthModal={() => setAuthModalOpen(true)}
            />
          )}
        </main>
      </div>

      {/* Modals */}
      <AuthModal
        isOpen={authModalOpen}
        onClose={() => setAuthModalOpen(false)}
        currentUser={user}
        onUpdateUser={(u) => setUser(u)}
      />

      <AICopilotModal
        isOpen={aiCopilotOpen}
        onClose={() => setAiCopilotOpen(false)}
        logs={logs}
      />
    </div>
  );
}
