import React from 'react';
import { Camera, Search, Bell, Moon, Settings as SettingsIcon } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export const Topbar: React.FC = () => {
  const navigate = useNavigate();
  return (
    <header className="h-16 border-b border-gray-200 bg-background/50 backdrop-blur-md flex items-center justify-between px-6 sticky top-0 z-10">
      
      {}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-gray-100 border border-gray-200">
          <Camera size={14} className="text-primary" />
          <span className="text-xs font-medium text-gray-700">Front Entrance Cam</span>
        </div>
        <div className="text-xs text-gray-600 flex items-center gap-2">
          <span>FPS: <span className="text-gray-900 font-mono">30.0</span></span>
          <span className="w-1 h-1 rounded-full bg-gray-600"/>
          <span>GPU: <span className="text-gray-900 font-mono">24%</span></span>
        </div>
      </div>

      {}
      <div className="flex items-center gap-3">
        <div className="relative group">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500 group-focus-within:text-primary transition-colors" />
          <input 
            type="text" 
            placeholder="Search identities..." 
            className="w-64 bg-gray-100 border border-gray-200 rounded-full py-1.5 pl-9 pr-4 text-sm text-gray-900 placeholder-gray-500 focus:outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/50 transition-all"
          />
        </div>
        
        <div className="h-6 w-px bg-gray-200 mx-2" />
        
        <button 
          onClick={() => navigate('/logs')}
          className="p-2 rounded-full hover:bg-gray-200 text-gray-600 hover:text-gray-900 transition-colors relative"
        >
          <Bell size={18} />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-primary rounded-full shadow-[0_0_8px_rgba(37,99,235,0.8)]" />
        </button>
        <button className="p-2 rounded-full hover:bg-gray-200 text-gray-600 hover:text-gray-900 transition-colors">
          <Moon size={18} />
        </button>
        <button 
          onClick={() => navigate('/settings')}
          className="p-2 rounded-full hover:bg-gray-200 text-gray-600 hover:text-gray-900 transition-colors"
        >
          <SettingsIcon size={18} />
        </button>
        
        <div className="ml-2 w-8 h-8 rounded-full bg-gradient-to-tr from-primary to-accent border border-white/20 flex items-center justify-center text-xs font-bold text-gray-900 shadow-lg">
          AD
        </div>
      </div>
    </header>
  );
};
