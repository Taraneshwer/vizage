import React from 'react';
import { 
  LayoutDashboard, 
  UserPlus, 
  ScanFace, 
  Users, 
  History, 
  BarChart3, 
  Settings, 
  AlertOctagon,
  ShieldAlert,
  ChevronRight
} from 'lucide-react';
import { NavigationModule } from '../types';

interface SidebarProps {
  activeModule: NavigationModule;
  onSelectModule: (module: NavigationModule) => void;
  highContrast: boolean;
  onTriggerEmergencyAlert: () => void;
  emergencyActive: boolean;
}

interface NavItem {
  id: NavigationModule;
  number: string;
  label: string;
  icon: React.ElementType;
  badge?: string;
  badgeColor?: string;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeModule,
  onSelectModule,
  highContrast,
  onTriggerEmergencyAlert,
  emergencyActive
}) => {
  const navItems: NavItem[] = [
    { id: 'dashboard', number: '01', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'enrollment', number: '02', label: 'Enrollment', icon: UserPlus },
    { id: 'live-recognition', number: '03', label: 'Live Recognition', icon: ScanFace, badge: 'LIVE', badgeColor: 'bg-emerald-500 text-slate-950 font-bold' },
    { id: 'identity-gallery', number: '04', label: 'Identity Gallery', icon: Users },
    { id: 'history', number: '05', label: 'History & Logs', icon: History },
    { id: 'analytics', number: '06', label: 'Analytics', icon: BarChart3 },
    { id: 'settings', number: '07', label: 'Settings', icon: Settings },
  ];

  return (
    <aside className={`w-64 flex-shrink-0 flex flex-col justify-between transition-colors ${
      highContrast 
        ? 'bg-black text-white border-r border-yellow-400' 
        : 'bg-slate-900 text-slate-300'
    }`}>
      {/* Navigation Links */}
      <div className="py-6">
        <div className="px-6 pb-3 text-[10px] font-mono font-bold tracking-widest uppercase text-slate-500">
          NAVIGATION MENU
        </div>

        <ul className="space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeModule === item.id;

            return (
              <li key={item.id}>
                <button
                  onClick={() => onSelectModule(item.id)}
                  className={`w-full flex items-center justify-between px-6 py-3 text-sm font-semibold tracking-wide transition-colors cursor-pointer ${
                    isActive
                      ? highContrast
                        ? 'bg-yellow-400 text-black font-bold border-r-4 border-black'
                        : 'bg-indigo-600/10 text-indigo-400 border-r-4 border-indigo-500'
                      : 'hover:bg-slate-800 hover:text-white text-slate-400'
                  }`}
                >
                  <div className="flex items-center gap-4">
                    <span className="text-[10px] font-mono opacity-50 font-bold">
                      {item.number}
                    </span>
                    <div className="flex items-center gap-2.5">
                      <Icon className="w-4 h-4 opacity-80" />
                      <span>{item.label}</span>
                    </div>
                  </div>

                  {item.badge && (
                    <span className={`px-1.5 py-0.5 text-[9px] font-mono uppercase rounded ${
                      item.badgeColor || 'bg-slate-800 text-indigo-400 border border-slate-700'
                    }`}>
                      {item.badge}
                    </span>
                  )}
                </button>
              </li>
            );
          })}
        </ul>
      </div>

      {/* DB Storage Widget & Emergency Trigger */}
      <div className="mt-auto p-6 border-t border-slate-800/80 space-y-4">
        {/* DB Storage Widget */}
        <div className="bg-slate-800/50 p-4 rounded-lg border border-slate-700/50">
          <p className="text-[10px] font-bold text-slate-400 uppercase mb-2 tracking-wider">
            DB STORAGE CAPACITY
          </p>
          <div className="w-full bg-slate-700 h-1.5 rounded-full overflow-hidden">
            <div className="bg-indigo-500 h-full w-[64%]" />
          </div>
          <div className="flex justify-between items-center text-[10px] mt-2 text-slate-400 font-mono">
            <span>642.1 GB / 1 TB</span>
            <span className="text-indigo-400 font-bold">64%</span>
          </div>
        </div>

        {/* Emergency Alert Button */}
        <button
          onClick={onTriggerEmergencyAlert}
          className={`w-full flex items-center justify-center gap-2 px-3 py-2.5 rounded-lg text-xs font-bold font-mono uppercase tracking-wider transition-all cursor-pointer shadow-md ${
            emergencyActive
              ? 'bg-rose-600 hover:bg-rose-700 text-white animate-pulse'
              : 'bg-rose-950/60 hover:bg-rose-900/80 text-rose-300 border border-rose-800/60'
          }`}
        >
          <AlertOctagon className="w-4 h-4 text-rose-400" />
          <span>{emergencyActive ? 'EMERGENCY ACTIVE' : 'LOCKDOWN ALERT'}</span>
        </button>
      </div>
    </aside>
  );
};
