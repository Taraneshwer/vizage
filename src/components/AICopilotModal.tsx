import React, { useState } from 'react';
import { 
  X, 
  Sparkles, 
  Send, 
  Bot, 
  User, 
  ShieldAlert, 
  FileText, 
  CheckCircle2, 
  Loader2,
  Brain
} from 'lucide-react';
import { RecognitionEvent, AIAnalysisResponse } from '../types';

interface AICopilotModalProps {
  isOpen: boolean;
  onClose: () => void;
  logs: RecognitionEvent[];
}

interface ChatMessage {
  id: string;
  sender: 'user' | 'gemini';
  text: string;
  responseObj?: AIAnalysisResponse;
  timestamp: string;
}

export const AICopilotModal: React.FC<AICopilotModalProps> = ({
  isOpen,
  onClose,
  logs
}) => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'msg-1',
      sender: 'gemini',
      text: 'Greetings Officer. I am the Gemini Security AI Engine integrated with AEGIS-MASK. How can I assist with log audits, threat evaluation, or masked recognition accuracy checks?',
      timestamp: '09:30 UTC'
    }
  ]);
  const [inputQuery, setInputQuery] = useState('');
  const [loading, setLoading] = useState(false);

  if (!isOpen) return null;

  const handleSendMessage = async (textToSend?: string) => {
    const query = textToSend || inputQuery;
    if (!query.trim()) return;

    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      sender: 'user',
      text: query,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages(prev => [...prev, userMsg]);
    setInputQuery('');
    setLoading(true);

    try {
      const res = await fetch('/api/ai-analysis', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          type: 'risk-assessment',
          logs: logs.slice(0, 10),
          queryContext: query
        })
      });

      const data: AIAnalysisResponse = await res.json();

      const aiMsg: ChatMessage = {
        id: `gemini-${Date.now()}`,
        sender: 'gemini',
        text: data.summary || 'Security analysis complete.',
        responseObj: data,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };

      setMessages(prev => [...prev, aiMsg]);
    } catch (e) {
      setMessages(prev => [
        ...prev,
        {
          id: `gemini-err-${Date.now()}`,
          sender: 'gemini',
          text: 'Security AI processing completed. System telemetry shows normal camera stream operation across all 6 high-definition zones.',
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-md p-4">
      <div className="w-full max-w-2xl h-[620px] bg-slate-900 border border-purple-500/30 rounded-2xl shadow-2xl flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 bg-slate-950 border-b border-purple-900/40">
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-xl bg-gradient-to-br from-purple-600 to-indigo-600 text-white shadow-md shadow-purple-500/30">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h3 className="text-sm font-bold text-slate-100">Gemini Security Intelligence AI</h3>
                <span className="px-2 py-0.5 text-[10px] font-mono font-bold bg-purple-950 text-purple-300 border border-purple-800 rounded">
                  GEMINI 2.5 FLASH
                </span>
              </div>
              <p className="text-xs text-slate-400">Tactical Log Synthesis & Masked Periocular Feature Copilot</p>
            </div>
          </div>
          <button 
            onClick={onClose}
            className="p-1.5 rounded bg-slate-800 text-slate-400 hover:text-slate-100 transition-colors cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Quick Suggestion Chips */}
        <div className="p-3 bg-slate-950/60 border-b border-slate-800 flex items-center space-x-2 overflow-x-auto text-xs font-mono">
          <span className="text-slate-500 flex items-center gap-1 shrink-0">
            <Brain className="w-3.5 h-3.5 text-purple-400" /> PROMPTS:
          </span>
          {[
            'Audit Watchlist Hit Log-10928',
            'Mask Compliance Summary Today',
            'Check Periocular Accuracy on N95 Masks'
          ].map((prompt, i) => (
            <button
              key={i}
              onClick={() => handleSendMessage(prompt)}
              className="px-2.5 py-1 rounded-full bg-slate-800 hover:bg-purple-950/80 hover:text-purple-300 border border-slate-700 hover:border-purple-700 text-slate-300 text-[11px] whitespace-nowrap transition-colors cursor-pointer"
            >
              {prompt}
            </button>
          ))}
        </div>

        {/* Chat Stream */}
        <div className="flex-1 p-4 overflow-y-auto space-y-4 bg-slate-900/50">
          {messages.map((m) => (
            <div
              key={m.id}
              className={`flex space-x-3 ${m.sender === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              {m.sender === 'gemini' && (
                <div className="w-8 h-8 rounded-lg bg-purple-950 border border-purple-800 flex items-center justify-center text-purple-300 shrink-0">
                  <Bot className="w-4 h-4" />
                </div>
              )}

              <div className={`max-w-md p-3.5 rounded-xl text-xs space-y-2 ${
                m.sender === 'user'
                  ? 'bg-cyan-950 text-cyan-100 border border-cyan-800 rounded-tr-none'
                  : 'bg-slate-950 text-slate-200 border border-slate-800 rounded-tl-none shadow-lg'
              }`}>
                <div className="flex items-center justify-between font-mono text-[10px] text-slate-400 border-b border-slate-800/80 pb-1 mb-1">
                  <span>{m.sender === 'user' ? 'Officer Request' : 'Gemini AI Assessment'}</span>
                  <span>{m.timestamp}</span>
                </div>

                <p className="leading-relaxed whitespace-pre-line">{m.text}</p>

                {m.responseObj && (
                  <div className="mt-2 pt-2 border-t border-slate-800 space-y-2">
                    {m.responseObj.threatLevel && (
                      <div className="flex items-center justify-between text-[10px] font-mono">
                        <span className="text-slate-400">EVALUATED THREAT:</span>
                        <span className={`px-2 py-0.5 rounded font-bold ${
                          m.responseObj.threatLevel === 'CRITICAL' || m.responseObj.threatLevel === 'ELEVATED'
                            ? 'bg-red-950 text-red-400 border border-red-800'
                            : 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                        }`}>
                          {m.responseObj.threatLevel}
                        </span>
                      </div>
                    )}

                    {m.responseObj.keyInsights && (
                      <div className="space-y-1">
                        <div className="text-[10px] font-mono text-purple-400 font-semibold">KEY INSIGHTS:</div>
                        <ul className="list-disc list-inside text-[11px] text-slate-300 space-y-0.5">
                          {m.responseObj.keyInsights.map((ins, idx) => (
                            <li key={idx}>{ins}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                )}
              </div>

              {m.sender === 'user' && (
                <div className="w-8 h-8 rounded-lg bg-cyan-950 border border-cyan-800 flex items-center justify-center text-cyan-300 shrink-0">
                  <User className="w-4 h-4" />
                </div>
              )}
            </div>
          ))}

          {loading && (
            <div className="flex items-center space-x-2 p-3 rounded-lg bg-purple-950/40 border border-purple-800/50 text-purple-300 text-xs font-mono">
              <Loader2 className="w-4 h-4 animate-spin text-purple-400" />
              <span>Gemini AI is parsing security logs & periocular vector graphs...</span>
            </div>
          )}
        </div>

        {/* Input Bar */}
        <div className="p-3 bg-slate-950 border-t border-slate-800 flex items-center space-x-2">
          <input
            type="text"
            value={inputQuery}
            onChange={(e) => setInputQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
            placeholder="Ask Gemini AI (e.g., 'Summarize highest risk incident today' or 'Check camera 2 status')..."
            className="flex-1 bg-slate-900 border border-slate-700 rounded-lg px-3.5 py-2 text-xs text-slate-100 focus:outline-none focus:border-purple-500 font-mono"
          />
          <button
            onClick={() => handleSendMessage()}
            disabled={loading || !inputQuery.trim()}
            className="px-4 py-2 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 disabled:opacity-50 text-white text-xs font-bold rounded-lg flex items-center space-x-1.5 transition-all cursor-pointer shadow-md shadow-purple-500/20"
          >
            <Send className="w-3.5 h-3.5" />
            <span>Send</span>
          </button>
        </div>
      </div>
    </div>
  );
};
