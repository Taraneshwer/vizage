import React, { useState, useEffect } from 'react';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { LoadingState } from '../components/common/LoadingState';
import { ErrorState } from '../components/common/ErrorState';
import { useSettings, useUpdateSettings } from '../utils/api';
import type { SettingsModel } from '../utils/api';

export const Settings = () => {
  const { data: settings, isLoading, error, refetch } = useSettings();
  const updateSettings = useUpdateSettings();
  const [localSettings, setLocalSettings] = useState<Partial<SettingsModel>>({});

  useEffect(() => {
    if (settings) {
      setLocalSettings(settings);
    }
  }, [settings]);

  if (isLoading) {
    return <LoadingState message="Loading configuration..." />;
  }

  if (error || !settings) {
    return <ErrorState title="Failed to load settings" message={error?.message} onRetry={refetch} />;
  }

  const handleChange = (field: keyof SettingsModel, value: any) => {
    setLocalSettings(prev => ({ ...prev, [field]: value }));
  };

  const handleSave = () => {
    updateSettings.mutate(localSettings, {
      onSuccess: () => {
        refetch();
        // Optional: show toast notification
      }
    });
  };

  const handleReset = () => {
    setLocalSettings(settings);
  };

  return (
    <div className="h-full flex flex-col gap-6 overflow-y-auto pr-2 pb-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight">Application Settings</h2>
        <p className="text-sm text-gray-400 mt-1">Configure global application behavior and AI parameters.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="p-6 space-y-4">
          <h3 className="font-semibold text-white border-b border-white/5 pb-2">General</h3>
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-300">Theme</span>
              <select 
                value={localSettings.theme || "Dark (Enterprise)"}
                onChange={e => handleChange('theme', e.target.value)}
                className="bg-black border border-white/10 rounded px-2 py-1 text-sm text-white outline-none">
                <option>Dark (Enterprise)</option>
                <option>Light</option>
                <option>System Default</option>
              </select>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-300">Language</span>
              <select 
                value={localSettings.language || "English"}
                onChange={e => handleChange('language', e.target.value)}
                className="bg-black border border-white/10 rounded px-2 py-1 text-sm text-white outline-none">
                <option>English</option>
                <option>Spanish</option>
                <option>Japanese</option>
              </select>
            </div>
          </div>
        </Card>

        <Card className="p-6 space-y-4">
          <h3 className="font-semibold text-white border-b border-white/5 pb-2">Recognition</h3>
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-300">Confidence Threshold</span>
              <div className="flex items-center gap-2">
                <span className="text-xs text-gray-400">{localSettings.confidence_threshold || 98}%</span>
                <input 
                  type="range" min="0" max="100" 
                  value={localSettings.confidence_threshold || 98} 
                  onChange={e => handleChange('confidence_threshold', parseFloat(e.target.value))}
                  className="w-24" />
              </div>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-300">Tracking Strategy</span>
              <select 
                value={localSettings.tracking_strategy || "ByteTrack (High Accuracy)"}
                onChange={e => handleChange('tracking_strategy', e.target.value)}
                className="bg-black border border-white/10 rounded px-2 py-1 text-sm text-white outline-none">
                <option>ByteTrack (High Accuracy)</option>
                <option>DeepSORT (Balanced)</option>
              </select>
            </div>
          </div>
        </Card>

        <Card className="p-6 space-y-4">
          <h3 className="font-semibold text-white border-b border-white/5 pb-2">Camera</h3>
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-300">Default Source</span>
              <select 
                value={localSettings.default_source || "RTSP: Front Entrance"}
                onChange={e => handleChange('default_source', e.target.value)}
                className="bg-black border border-white/10 rounded px-2 py-1 text-sm text-white outline-none">
                <option>RTSP: Front Entrance</option>
                <option>Webcam: Reception</option>
                <option>RTSP: Backdoor</option>
              </select>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-300">Auto-Reconnect Delay</span>
              <input 
                type="number" 
                value={localSettings.camera_reconnect_delay_sec || 5} 
                onChange={e => handleChange('camera_reconnect_delay_sec', parseFloat(e.target.value))}
                className="bg-black border border-white/10 rounded px-2 py-1 text-sm text-white w-20 outline-none" />
            </div>
          </div>
        </Card>

        <Card className="p-6 space-y-4">
          <h3 className="font-semibold text-white border-b border-white/5 pb-2">Storage</h3>
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-300">Log Retention</span>
              <select 
                value={localSettings.log_retention || "30 Days"}
                onChange={e => handleChange('log_retention', e.target.value)}
                className="bg-black border border-white/10 rounded px-2 py-1 text-sm text-white outline-none">
                <option>30 Days</option>
                <option>90 Days</option>
                <option>1 Year</option>
              </select>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-300">Save Unknown Faces</span>
              <input 
                type="checkbox" 
                checked={localSettings.save_unknown_faces ?? true}
                onChange={e => handleChange('save_unknown_faces', e.target.checked)}
                className="accent-primary" />
            </div>
          </div>
        </Card>
      </div>

      <div className="flex justify-end gap-2 mt-4">
        <Button variant="outline" onClick={handleReset} disabled={updateSettings.isPending}>Reset Changes</Button>
        <Button variant="primary" onClick={handleSave} disabled={updateSettings.isPending}>
          {updateSettings.isPending ? 'Saving...' : 'Save Configuration'}
        </Button>
      </div>
    </div>
  );
};
