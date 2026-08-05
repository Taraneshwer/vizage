import React, { useState } from 'react';
import { 
  History, 
  Camera,
  Search, 
  Download, 
  Filter, 
  Sparkles, 
  CheckCircle2, 
  AlertTriangle, 
  X, 
  FileSpreadsheet, 
  Eye, 
  ShieldAlert,
  SlidersHorizontal
} from 'lucide-react';
import { RecognitionEvent, AIAnalysisResponse } from '../../types';

interface HistoryLogsModuleProps {
  logs: RecognitionEvent[];
  onUpdateLog: (updated: RecognitionEvent) => void;
}

export const HistoryLogsModule: React.FC<HistoryLogsModuleProps> = ({
  logs,
  onUpdateLog
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [riskFilter, setRiskFilter] = useState<string>('ALL');
  const [maskFilter, setMaskFilter] = useState<string>('ALL');
  const [inspectLog, setInspectLog] = useState<RecognitionEvent | null>(null);

  const [aiAnalysis, setAiAnalysis] = useState<AIAnalysisResponse | null>(null);
  const [loadingAi, setLoadingAi] = useState(false);

  const filteredLogs = logs.filter((l) => {
    const matchesSearch = l.subjectName.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          l.cameraName.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          l.zone.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesRisk = riskFilter === 'ALL' || l.riskLevel === riskFilter;
    const matchesMask = maskFilter === 'ALL' || l.maskDetected.includes(maskFilter);
    return matchesSearch && matchesRisk && matchesMask;
  });

  const handleExportCSV = () => {
    const headers = 'ID,Timestamp,Camera,Zone,Subject,Category,Confidence,Mask,Risk,Status\n';
    const rows = filteredLogs.map(l => 
      `"${l.id}","${l.timestamp}","${l.cameraName}","${l.zone}","${l.subjectName}","${l.subjectCategory}",${l.matchConfidence}%,"${l.maskDetected}","${l.riskLevel}","${l.verificationStatus}"`
    ).join('\n');

    const blob = new Blob([headers + rows], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `Security_Audit_Logs_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleRunAiAudit = async () => {
    setLoadingAi(true);
    try {
      const res = await fetch('/api/ai-analysis', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          type: 'log-audit',
          logs: filteredLogs.slice(0, 10),
          queryContext: 'Security history log pattern audit'
        })
      });
      const data = await res.json();
      setAiAnalysis(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoadingAi(false);
    }
  };

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Title */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-200 pb-4">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 rounded-xl bg-purple-50 text-purple-600 border border-purple-100">
            <History className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-slate-900 font-mono uppercase">
              SECURITY AUDIT LOGS & EVENT HISTORY
            </h1>
            <p className="text-xs text-slate-500">
              Complete chronological ledger of facial matches, mask detections, and security flags
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          {/* Gemini Audit Button */}
          <button
            onClick={handleRunAiAudit}
            disabled={loadingAi}
            className="px-3.5 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-mono text-xs font-bold flex items-center space-x-2 transition-all cursor-pointer shadow-sm"
          >
            <Sparkles className="w-4 h-4 text-yellow-300" />
            <span>{loadingAi ? 'Synthesizing...' : 'Gemini AI Log Audit'}</span>
          </button>

          <button
            onClick={handleExportCSV}
            className="px-3.5 py-2 bg-white hover:bg-slate-50 text-slate-700 font-mono text-xs font-bold rounded-lg flex items-center space-x-2 cursor-pointer border border-slate-200 shadow-sm"
          >
            <Download className="w-4 h-4 text-slate-500" />
            <span>Export CSV</span>
          </button>
        </div>
      </div>

      {/* AI Log Audit Result Box if triggered */}
      {aiAnalysis && (
        <div className="p-4 rounded-xl bg-indigo-50/80 border border-indigo-200 space-y-3 font-mono text-xs text-slate-800 shadow-sm">
          <div className="flex justify-between items-center pb-2 border-b border-indigo-200">
            <span className="font-bold text-indigo-900 flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-indigo-600" />
              GEMINI AUTOMATED INCIDENT AUDIT REPORT
            </span>
            <button onClick={() => setAiAnalysis(null)} className="text-slate-400 hover:text-slate-600 cursor-pointer">
              <X className="w-4 h-4" />
            </button>
          </div>

          <p className="leading-relaxed text-slate-700">{aiAnalysis.summary}</p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-1">
            <div className="space-y-1 bg-white p-2.5 rounded-lg border border-indigo-100">
              <div className="text-[10px] text-indigo-600 font-bold">KEY AUDIT INSIGHTS:</div>
              <ul className="list-disc list-inside text-[11px] space-y-0.5 text-slate-700">
                {aiAnalysis.keyInsights?.map((k, i) => <li key={i}>{k}</li>)}
              </ul>
            </div>
            <div className="space-y-1 bg-white p-2.5 rounded-lg border border-indigo-100">
              <div className="text-[10px] text-indigo-600 font-bold">RECOMMENDED PROCEDURES:</div>
              <ul className="list-disc list-inside text-[11px] space-y-0.5 text-slate-700">
                {aiAnalysis.recommendedActions?.map((a, i) => <li key={i}>{a}</li>)}
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div className="relative">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search logs by subject, camera, or zone..."
            className="w-full bg-white border border-slate-200 rounded-lg pl-9 pr-4 py-2 text-xs text-slate-900 focus:outline-none focus:border-indigo-600 font-mono shadow-sm"
          />
        </div>

        <div className="flex items-center space-x-2">
          <span className="text-xs font-mono text-slate-500">RISK:</span>
          <select
            value={riskFilter}
            onChange={(e) => setRiskFilter(e.target.value)}
            className="flex-1 bg-white border border-slate-200 rounded-lg px-3 py-2 text-xs text-slate-900 focus:outline-none focus:border-indigo-600 font-mono shadow-sm"
          >
            <option value="ALL">All Risk Levels</option>
            <option value="Normal">Normal</option>
            <option value="Warning">Warning</option>
            <option value="Critical">Critical</option>
          </select>
        </div>

        <div className="flex items-center space-x-2">
          <span className="text-xs font-mono text-slate-500">MASK:</span>
          <select
            value={maskFilter}
            onChange={(e) => setMaskFilter(e.target.value)}
            className="flex-1 bg-white border border-slate-200 rounded-lg px-3 py-2 text-xs text-slate-900 focus:outline-none focus:border-indigo-600 font-mono shadow-sm"
          >
            <option value="ALL">All Mask Types</option>
            <option value="N95">N95 Respirator</option>
            <option value="Surgical">Surgical Mask</option>
            <option value="Cloth">Cloth Mask</option>
            <option value="Balaclava">Balaclava / Gaiter</option>
            <option value="Improper">Improper / Partial</option>
          </select>
        </div>
      </div>

      {/* Logs Table */}
      <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead>
              <tr className="border-b border-slate-200 text-slate-500 text-[10px] uppercase bg-slate-50/80">
                <th className="py-3 px-4">TIMESTAMP</th>
                <th className="py-3 px-4">CAMERA / ZONE</th>
                <th className="py-3 px-4">SUBJECT NAME</th>
                <th className="py-3 px-4">CONFIDENCE</th>
                <th className="py-3 px-4">MASK TYPE</th>
                <th className="py-3 px-4">RISK</th>
                <th className="py-3 px-4">ACTION</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filteredLogs.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-12 px-4 text-center text-xs font-mono text-slate-400">
                    <p className="font-bold text-slate-600 mb-1">NO LOGS OR EVENT HISTORY RECORDED</p>
                    <p className="text-[11px] text-slate-400">Events will appear automatically as backend feeds or live camera detections are logged.</p>
                  </td>
                </tr>
              ) : (
                filteredLogs.map((log) => (
                  <tr key={log.id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="py-3 px-4 text-slate-500">{log.timestamp}</td>
                    <td className="py-3 px-4">
                      <span className="font-bold text-slate-800 block">{log.cameraName}</span>
                      <span className="text-[10px] text-slate-400">{log.zone}</span>
                    </td>
                    <td className="py-3 px-4">
                      <span className="font-bold text-slate-900 block">{log.subjectName}</span>
                      <span className="text-[10px] text-indigo-600">{log.subjectCategory}</span>
                    </td>
                    <td className="py-3 px-4">
                      <span className={`font-bold ${log.matchConfidence > 90 ? 'text-emerald-600' : 'text-amber-600'}`}>
                        {log.matchConfidence}%
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <span className="px-2 py-0.5 rounded bg-slate-50 border border-slate-200 text-slate-700 text-[10px]">
                        {log.maskDetected}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        log.riskLevel === 'Critical'
                          ? 'bg-rose-50 text-rose-700 border border-rose-200 animate-pulse'
                          : log.riskLevel === 'Warning'
                          ? 'bg-amber-50 text-amber-700 border border-amber-200'
                          : 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                      }`}>
                        {log.riskLevel}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <button
                        onClick={() => setInspectLog(log)}
                        className="px-2.5 py-1 bg-slate-100 hover:bg-slate-200 text-indigo-600 rounded font-semibold cursor-pointer transition-colors"
                      >
                        Inspect
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Inspect Log Modal */}
      {inspectLog && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-sm p-4">
          <div className="w-full max-w-lg bg-white border border-slate-200 rounded-xl p-6 space-y-4 font-mono text-xs shadow-2xl">
            <div className="flex justify-between items-center border-b border-slate-100 pb-2">
              <h3 className="font-bold text-slate-900">LOG ENTRY INSPECTOR (#{inspectLog.id})</h3>
              <button onClick={() => setInspectLog(null)} className="text-slate-400 hover:text-slate-600 cursor-pointer">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="aspect-video bg-slate-900 rounded-lg overflow-hidden relative border border-slate-800 flex items-center justify-center">
              {inspectLog.snapshotUrl ? (
                <img src={inspectLog.snapshotUrl} alt="Snapshot" className="w-full h-full object-cover" />
              ) : (
                <div className="w-full h-full flex flex-col items-center justify-center text-slate-400 font-mono text-xs">
                  <div className="absolute inset-0 bg-[linear-gradient(to_right,#1e293b_1px,transparent_1px),linear-gradient(to_bottom,#1e293b_1px,transparent_1px)] bg-[size:1.5rem_1.5rem] opacity-30 pointer-events-none" />
                  <Camera className="w-8 h-8 text-indigo-500 mb-1" />
                  <span>EVENT SNAPSHOT CAPTURE</span>
                </div>
              )}
              <div className="absolute top-3 left-3 bg-black/80 p-2 rounded border border-slate-700 text-white text-[10px]">
                Match: {inspectLog.matchConfidence}% • Mask: {inspectLog.maskDetected}
              </div>
            </div>

            <div className="space-y-1 bg-slate-50 p-3 rounded-lg border border-slate-200 text-slate-800">
              <div><strong>Subject:</strong> {inspectLog.subjectName} ({inspectLog.subjectCategory})</div>
              <div><strong>Camera:</strong> {inspectLog.cameraName}</div>
              <div><strong>Zone:</strong> {inspectLog.zone}</div>
              <div><strong>Notes:</strong> {inspectLog.notes}</div>
            </div>

            <div className="flex justify-end space-x-2 pt-2 border-t border-slate-100">
              <button
                onClick={() => {
                  onUpdateLog({ ...inspectLog, verificationStatus: 'Verified' });
                  setInspectLog(null);
                }}
                className="px-3.5 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded font-bold cursor-pointer transition-colors"
              >
                Verify Match
              </button>
              <button
                onClick={() => setInspectLog(null)}
                className="px-3.5 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded cursor-pointer transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
