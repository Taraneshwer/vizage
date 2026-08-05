import React, { useState } from 'react';
import { 
  Settings, 
  Cpu, 
  Video, 
  Bell, 
  ShieldCheck, 
  Sliders, 
  Key, 
  Sun, 
  Moon, 
  Volume2, 
  Globe, 
  CheckCircle2, 
  Save,
  Radio,
  Lock
} from 'lucide-react';

interface SettingsModuleProps {
  highContrast: boolean;
  onToggleHighContrast: () => void;
  soundEnabled: boolean;
  onToggleSound: () => void;
  onOpenAuthModal: () => void;
}

export const SettingsModule: React.FC<SettingsModuleProps> = ({
  highContrast,
  onToggleHighContrast,
  soundEnabled,
  onToggleSound,
  onOpenAuthModal
}) => {
  const [webhookUrl, setWebhookUrl] = useState('https://security-mesh.internal/hooks/watchlist-alerts');
  const [saveSuccess, setSaveSuccess] = useState(false);

  const handleSaveSettings = () => {
    setSaveSuccess(true);
    setTimeout(() => setSaveSuccess(false), 2500);
  };

  return (
    <div className="p-6 space-y-6 max-w-4xl mx-auto">
      {/* Title */}
      <div className={`flex items-center space-x-3 border-b pb-4 ${
        highContrast ? 'border-yellow-400' : 'border-slate-200'
      }`}>
        <div className={`p-2.5 rounded-xl border ${
          highContrast ? 'bg-yellow-400 text-black border-yellow-300' : 'bg-indigo-50 text-indigo-600 border-indigo-100'
        }`}>
          <Settings className="w-6 h-6" />
        </div>
        <div>
          <h1 className={`text-lg font-bold font-mono uppercase ${
            highContrast ? 'text-yellow-400' : 'text-slate-900'
          }`}>
            SYSTEM CONFIGURATION & ACCESS CONTROL
          </h1>
          <p className={`text-xs ${highContrast ? 'text-slate-300' : 'text-slate-500'}`}>
            AI inference backbones, accessibility standards, alert webhooks, and OAuth policies
          </p>
        </div>
      </div>

      {/* Save Success Banner */}
      {saveSuccess && (
        <div className={`p-3 rounded-lg font-mono text-xs flex items-center space-x-2 border ${
          highContrast
            ? 'bg-yellow-400 text-black border-yellow-300'
            : 'bg-emerald-50 border-emerald-200 text-emerald-800'
        }`}>
          <CheckCircle2 className="w-4 h-4 text-emerald-600" />
          <span>System configuration parameters saved and committed to edge nodes!</span>
        </div>
      )}

      {/* Settings Grid */}
      <div className="space-y-6 font-mono text-xs">

        {/* Section 2: Accessibility & Display Standards */}
        <div className={`p-5 rounded-xl border space-y-4 shadow-sm ${
          highContrast 
            ? 'bg-black border-yellow-400 text-white' 
            : 'bg-white border-slate-200 text-slate-800'
        }`}>
          <div className={`flex items-center space-x-2 pb-2 border-b font-bold ${
            highContrast ? 'border-yellow-400 text-yellow-400' : 'border-slate-100 text-amber-600'
          }`}>
            <Sun className="w-4 h-4" />
            <span>02 / ACCESSIBILITY & CONSOLE CONTRAST</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <button
              onClick={onToggleHighContrast}
              className={`p-3 rounded-lg border flex items-center justify-between cursor-pointer transition-all ${
                highContrast 
                  ? 'bg-yellow-400 text-black border-yellow-300 font-bold' 
                  : 'bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100'
              }`}
            >
              <div className="flex items-center space-x-2">
                <Sun className="w-4 h-4" />
                <span>High Contrast Guard Room Mode</span>
              </div>
              <span className="text-[10px] uppercase font-bold">{highContrast ? 'ACTIVE' : 'OFF'}</span>
            </button>

            <button
              onClick={onToggleSound}
              className={`p-3 rounded-lg border flex items-center justify-between cursor-pointer transition-all ${
                soundEnabled 
                  ? highContrast
                    ? 'bg-yellow-400 text-black border-yellow-300 font-bold'
                    : 'bg-indigo-50 text-indigo-700 border-indigo-200 font-bold' 
                  : 'bg-slate-50 text-slate-400 border-slate-200'
              }`}
            >
              <div className="flex items-center space-x-2">
                <Volume2 className="w-4 h-4" />
                <span>Audio Alert Chimes & Beeps</span>
              </div>
              <span className="text-[10px] uppercase font-bold">{soundEnabled ? 'ENABLED' : 'MUTED'}</span>
            </button>
          </div>
        </div>

        {/* Section 3: Webhooks & OAuth Access Control */}
        <div className={`p-5 rounded-xl border space-y-4 shadow-sm ${
          highContrast 
            ? 'bg-black border-yellow-400 text-white' 
            : 'bg-white border-slate-200 text-slate-800'
        }`}>
          <div className={`flex items-center space-x-2 pb-2 border-b font-bold ${
            highContrast ? 'border-yellow-400 text-yellow-400' : 'border-slate-100 text-purple-600'
          }`}>
            <Globe className="w-4 h-4" />
            <span>03 / WEBHOOKS & SECURITY OFFICER AUTHENTICATION</span>
          </div>

          <div className="space-y-3">
            <div>
              <label className={`block mb-1.5 font-semibold text-[11px] ${
                highContrast ? 'text-slate-300' : 'text-slate-600'
              }`}>
                INCIDENT DISPATCH WEBHOOK ENDPOINT
              </label>
              <input
                type="text"
                value={webhookUrl}
                onChange={(e) => setWebhookUrl(e.target.value)}
                className={`w-full rounded-lg p-2.5 text-xs font-mono focus:outline-none border ${
                  highContrast
                    ? 'bg-slate-900 border-yellow-400 text-yellow-300'
                    : 'bg-slate-50 border-slate-200 text-slate-900 focus:border-indigo-600'
                }`}
              />
            </div>

            <div className={`p-3.5 rounded-lg border flex flex-col sm:flex-row sm:items-center justify-between gap-3 ${
              highContrast ? 'bg-slate-900 border-yellow-400' : 'bg-slate-50 border-slate-200'
            }`}>
              <div>
                <div className={`font-bold ${highContrast ? 'text-yellow-300' : 'text-slate-900'}`}>
                  OAuth 2.0 & YubiKey Session Management
                </div>
                <div className={`text-[11px] ${highContrast ? 'text-slate-400' : 'text-slate-500'}`}>
                  Enforce hardware MFA token verification every 8 hours
                </div>
              </div>

              <button
                onClick={onOpenAuthModal}
                className={`px-3.5 py-2 rounded text-xs font-bold cursor-pointer transition-colors ${
                  highContrast
                    ? 'bg-yellow-400 text-black hover:bg-yellow-300'
                    : 'bg-purple-600 hover:bg-purple-500 text-white shadow-sm'
                }`}
              >
                Configure SSO Provider
              </button>
            </div>
          </div>
        </div>

        {/* Save Button */}
        <div className="flex justify-end">
          <button
            onClick={handleSaveSettings}
            className={`px-6 py-2.5 rounded-lg font-bold shadow-md cursor-pointer flex items-center space-x-2 transition-all ${
              highContrast
                ? 'bg-yellow-400 text-black hover:bg-yellow-300'
                : 'bg-indigo-600 hover:bg-indigo-500 text-white'
            }`}
          >
            <Save className="w-4 h-4" />
            <span>Save System Parameters</span>
          </button>
        </div>
      </div>
    </div>
  );
};

