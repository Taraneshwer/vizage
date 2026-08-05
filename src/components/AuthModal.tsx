import React, { useState } from 'react';
import { 
  X, 
  Key, 
  ShieldCheck, 
  Lock, 
  BadgeCheck, 
  CheckCircle2, 
  Globe, 
  UserCheck, 
  Fingerprint,
  Building2,
  Sparkles
} from 'lucide-react';
import { SecurityUser } from '../types';

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  currentUser: SecurityUser;
  onUpdateUser: (newUser: SecurityUser) => void;
}

export const AuthModal: React.FC<AuthModalProps> = ({
  isOpen,
  onClose,
  currentUser,
  onUpdateUser
}) => {
  const [selectedMethod, setSelectedMethod] = useState<SecurityUser['loginMethod']>('OAuth Google');
  const [badgeInput, setBadgeInput] = useState('SEC-88029');
  const [pinInput, setPinInput] = useState('••••');
  const [isAuthenticating, setIsAuthenticating] = useState(false);
  const [authSuccess, setAuthSuccess] = useState(false);

  if (!isOpen) return null;

  const handleSimulateLogin = (role: SecurityUser['role'], name: string, badge: string) => {
    setIsAuthenticating(true);
    setAuthSuccess(false);

    setTimeout(() => {
      setIsAuthenticating(false);
      setAuthSuccess(true);

      const updatedUser: SecurityUser = {
        ...currentUser,
        id: `usr-${Math.floor(10000 + Math.random() * 90000)}`,
        name,
        badgeNumber: badge,
        role,
        loginMethod: selectedMethod,
        mfaVerified: true,
        lastLogin: 'Just now (' + new Date().toLocaleTimeString() + ')',
      };

      setTimeout(() => {
        onUpdateUser(updatedUser);
        setAuthSuccess(false);
        onClose();
      }, 800);
    }, 1200);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-md p-4">
      <div className="w-full max-w-lg bg-slate-900 border border-slate-700 rounded-xl shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        {/* Modal Header */}
        <div className="flex items-center justify-between px-6 py-4 bg-slate-950 border-b border-slate-800">
          <div className="flex items-center space-x-2.5">
            <div className="p-2 rounded-lg bg-cyan-950 text-cyan-400 border border-cyan-800">
              <Key className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-100">Security Officer Authentication</h3>
              <p className="text-xs text-slate-400">OAuth 2.0 / SSO Gateway & Badge Clearance</p>
            </div>
          </div>
          <button 
            onClick={onClose}
            className="p-1 rounded bg-slate-800 text-slate-400 hover:text-slate-100 transition-colors cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 space-y-6">
          {/* Method Selector */}
          <div>
            <label className="block text-xs font-mono font-semibold text-slate-400 mb-2">
              AUTHENTICATION PROVIDER METHOD
            </label>
            <div className="grid grid-cols-2 gap-2.5">
              {[
                { id: 'OAuth Google', label: 'Google Workspace OAuth', icon: Globe },
                { id: 'Okta SSO', label: 'Okta Enterprise SSO', icon: Building2 },
                { id: 'Smart Card', label: 'PIV / CAC Smart Card', icon: BadgeCheck },
                { id: 'PIN', label: 'Officer Tactical PIN', icon: Fingerprint },
              ].map((m) => {
                const Icon = m.icon;
                const isSelected = selectedMethod === m.id;
                return (
                  <button
                    key={m.id}
                    onClick={() => setSelectedMethod(m.id as SecurityUser['loginMethod'])}
                    className={`flex items-center space-x-2.5 p-3 rounded-lg border text-left text-xs transition-all cursor-pointer ${
                      isSelected
                        ? 'bg-cyan-950/90 border-cyan-500 text-cyan-200 shadow-sm shadow-cyan-500/20'
                        : 'bg-slate-950 border-slate-800 text-slate-400 hover:border-slate-700 hover:text-slate-200'
                    }`}
                  >
                    <Icon className={`w-4 h-4 ${isSelected ? 'text-cyan-400' : 'text-slate-500'}`} />
                    <span className="font-medium leading-tight">{m.label}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Preset Officer Profiles */}
          <div>
            <label className="block text-xs font-mono font-semibold text-slate-400 mb-2">
              SELECT OFFICER PROFILE TO AUTHENTICATE
            </label>

            <div className="space-y-2.5">
              <button
                disabled={isAuthenticating}
                onClick={() => handleSimulateLogin('Security Officer', 'Officer Jonathan Vance', 'SEC-88029')}
                className="w-full flex items-center justify-between p-3 rounded-lg bg-slate-950 border border-slate-800 hover:border-cyan-500/50 hover:bg-slate-800/50 transition-all text-left cursor-pointer group"
              >
                <div className="flex items-center space-x-3">
                  <img
                    src="https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&q=80&w=300"
                    alt="Vance"
                    className="w-9 h-9 rounded-full object-cover border border-cyan-500"
                  />
                  <div>
                    <div className="text-xs font-bold text-slate-200 group-hover:text-cyan-300">Officer Jonathan Vance</div>
                    <div className="text-[11px] text-slate-400">Global Tactical Command • SEC-88029</div>
                  </div>
                </div>
                <span className="text-[11px] font-mono text-cyan-400 bg-cyan-950 px-2 py-1 rounded border border-cyan-800">
                  Select
                </span>
              </button>

              <button
                disabled={isAuthenticating}
                onClick={() => handleSimulateLogin('Admin', 'Commander Sarah Miller', 'SEC-00001')}
                className="w-full flex items-center justify-between p-3 rounded-lg bg-slate-950 border border-slate-800 hover:border-cyan-500/50 hover:bg-slate-800/50 transition-all text-left cursor-pointer group"
              >
                <div className="flex items-center space-x-3">
                  <img
                    src="https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?auto=format&fit=crop&q=80&w=300"
                    alt="Miller"
                    className="w-9 h-9 rounded-full object-cover border border-purple-500"
                  />
                  <div>
                    <div className="text-xs font-bold text-slate-200 group-hover:text-purple-300">Commander Sarah Miller</div>
                    <div className="text-[11px] text-slate-400">Chief Security Administrator • SEC-00001</div>
                  </div>
                </div>
                <span className="text-[11px] font-mono text-purple-400 bg-purple-950 px-2 py-1 rounded border border-purple-800">
                  Select (Admin)
                </span>
              </button>
            </div>
          </div>

          {/* MFA Hardware Verification Simulation */}
          <div className="p-3.5 rounded-lg bg-slate-950 border border-slate-800 flex items-center justify-between text-xs font-mono">
            <div className="flex items-center space-x-2 text-slate-300">
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
              <span>YubiKey FIPS 140-2 MFA Hardware Token:</span>
            </div>
            <span className="text-emerald-400 font-bold">CONNECTED</span>
          </div>

          {/* Status Message */}
          {isAuthenticating && (
            <div className="p-3 rounded-lg bg-cyan-950/80 border border-cyan-800 flex items-center justify-center space-x-2 text-cyan-300 text-xs font-mono">
              <Sparkles className="w-4 h-4 animate-spin text-cyan-400" />
              <span>Validating OAuth OAuth2 Token & Badge Credentials...</span>
            </div>
          )}

          {authSuccess && (
            <div className="p-3 rounded-lg bg-emerald-950/80 border border-emerald-800 flex items-center justify-center space-x-2 text-emerald-300 text-xs font-mono">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              <span>Authentication Granted! Redirecting to Console...</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
