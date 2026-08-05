import React from 'react';
import { NavLink } from 'react-router-dom';
import { 
  LayoutDashboard, ScanFace, UserPlus, History, 
  Database, Activity, Settings, Terminal, Info, Video
} from 'lucide-react';
import { cn } from '../../utils/cn';

const navItems = [
  { icon: LayoutDashboard, label: 'Dashboard', path: '/' },
  { icon: ScanFace, label: 'Recognition', path: '/recognition' },
  { icon: UserPlus, label: 'Enrollment', path: '/enrollment' },
  { icon: History, label: 'History', path: '/history' },
  { icon: Database, label: 'Database', path: '/database' },
  { icon: Video, label: 'Cameras', path: '/cameras' },
  { icon: Activity, label: 'System', path: '/system' },
  { icon: Settings, label: 'Settings', path: '/settings' },
  { icon: Terminal, label: 'Logs', path: '/logs' },
  { icon: Info, label: 'About', path: '/about' },
];

export const Sidebar: React.FC = () => {
  return (
    <aside className="w-64 h-full bg-secondary border-r border-gray-200 flex flex-col justify-between overflow-hidden shrink-0">
      <div>
        <div className="p-5 flex items-center gap-3 border-b border-gray-200 bg-background/50">
          <div className="w-8 h-8 rounded bg-primary text-gray-900 flex items-center justify-center font-bold text-sm">
            V
          </div>
          <div>
            <h1 className="text-base font-bold tracking-tight text-gray-900 leading-tight">Vizage</h1>
            <p className="text-[10px] text-gray-600 tracking-wider">Enterprise Security</p>
          </div>
        </div>
        
        <nav className="p-3 space-y-0.5 overflow-y-auto">
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) => cn(
                "flex items-center gap-3 px-3 py-2 rounded text-sm transition-colors group",
                isActive 
                  ? "bg-primary/10 text-primary font-medium" 
                  : "text-gray-600 hover:text-gray-200 hover:bg-gray-100"
              )}
            >
              {({ isActive }) => (
                <>
                  <item.icon size={16} className={cn("transition-colors", isActive ? "text-primary" : "text-gray-500 group-hover:text-gray-600")} />
                  {item.label}
                </>
              )}
            </NavLink>
          ))}
        </nav>
      </div>
    </aside>
  );
};
