import React, { useState, useEffect, useMemo } from 'react';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Search, Filter, Download, ChevronLeft, ChevronRight, AlertTriangle, X, Trash2, Clock, CheckCircle } from 'lucide-react';
import { StatusBadge } from '../components/common/StatusBadge';
import { useHistory, useClearHistory, useDeleteHistoryEvent } from '../utils/api';
import type { HistoryRecord } from '../utils/api';
import { useHistoryStream } from '../hooks/useWebSocket';
import { EmptyState } from '../components/common/EmptyState';
import { motion, AnimatePresence } from 'framer-motion';

export const History = () => {
  const [page, setPage] = useState(0);
  const limit = 50;
  const [search, setSearch] = useState('');
  
  const { data: historyData, isLoading, refetch } = useHistory(limit, page * limit, search);
  const { data: streamData } = useHistoryStream();
  
  const clearMutation = useClearHistory();
  const deleteMutation = useDeleteHistoryEvent();

  const [liveEvents, setLiveEvents] = useState<HistoryRecord[]>([]);
  const [selectedEvent, setSelectedEvent] = useState<HistoryRecord | null>(null);
  const [showClearConfirm, setShowClearConfirm] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState<string | null>(null);

  // When search or page changes, clear live events to avoid confusion,
  // or only apply live events if on page 0 and no search.
  useEffect(() => {
    setLiveEvents([]);
  }, [page, search]);

  useEffect(() => {
    if (streamData && page === 0 && !search) {
      // Map WSHistoryMessage to HistoryRecord
      const newEvent: HistoryRecord = {
        history_id: streamData.history_id,
        timestamp: streamData.event_timestamp,
        identity_id: streamData.identity_id,
        name: streamData.name,
        department: streamData.department,
        verification_score: streamData.verification_score,
        mode: streamData.mode,
        camera_id: streamData.camera_id,
        tracking_id: streamData.tracking_id,
        processing_time_ms: streamData.processing_time_ms,
        state: streamData.state,
        has_mask: streamData.has_mask,
      };
      setLiveEvents(prev => [newEvent, ...prev]);
    }
  }, [streamData]);

  const displayedEvents = useMemo(() => {
    const base = historyData?.records || [];
    if (page === 0 && !search) {
      // Deduplicate live events that might have been fetched in base
      const baseIds = new Set(base.map(e => e.history_id));
      const newLive = liveEvents.filter(e => !baseIds.has(e.history_id));
      return [...newLive, ...base].slice(0, limit);
    }
    return base;
  }, [historyData, liveEvents, page, search]);

  const totalRecords = historyData?.total || 0;
  const totalPages = Math.ceil(totalRecords / limit);

  const formatTime = (isoStr: string) => {
    const d = new Date(isoStr);
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  };
  
  const formatDate = (isoStr: string) => {
    const d = new Date(isoStr);
    return d.toLocaleDateString();
  };

  const handleExport = () => {
    window.location.href = 'http://127.0.0.1:8000/api/v1/history/export';
  };

  const handleClearAll = () => {
    clearMutation.mutate(undefined, {
      onSuccess: () => {
        setShowClearConfirm(false);
        setLiveEvents([]);
        refetch();
        setSelectedEvent(null);
      }
    });
  };

  const handleDeleteEvent = () => {
    if (!showDeleteConfirm) return;
    deleteMutation.mutate(showDeleteConfirm, {
      onSuccess: () => {
        setShowDeleteConfirm(null);
        if (selectedEvent?.history_id === showDeleteConfirm) {
          setSelectedEvent(null);
        }
        setLiveEvents(prev => prev.filter(e => e.history_id !== showDeleteConfirm));
        refetch();
      }
    });
  };

  return (
    <div className="h-full flex gap-4">
      <div className="flex-1 flex flex-col gap-4">
        
        <div className="flex justify-between items-end">
          <div>
            <h2 className="text-2xl font-bold tracking-tight">Recognition History</h2>
            <p className="text-sm text-gray-400 mt-1">Live timeline of all system recognitions.</p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" className="text-danger border-danger/20 hover:bg-danger/20" onClick={() => setShowClearConfirm(true)}>Clear All</Button>
            <Button variant="secondary" onClick={handleExport}><Download size={14} className="mr-2"/> Export CSV</Button>
          </div>
        </div>

        {/* Statistics Bar */}
        <div className="grid grid-cols-4 gap-4">
          <Card className="p-4 flex items-center gap-4">
             <div className="p-3 bg-primary/10 rounded"><CheckCircle className="text-primary"/></div>
             <div>
               <p className="text-xs text-gray-400 uppercase">Total Records</p>
               <p className="text-xl font-bold">{totalRecords}</p>
             </div>
          </Card>
          <Card className="p-4 flex items-center gap-4">
             <div className="p-3 bg-danger/10 rounded"><AlertTriangle className="text-danger"/></div>
             <div>
               <p className="text-xs text-gray-400 uppercase">Unknowns (approx)</p>
               <p className="text-xl font-bold font-mono">
                 {displayedEvents.filter(e => e.state === 'UNKNOWN').length}
               </p>
             </div>
          </Card>
          <Card className="p-4 flex items-center gap-4">
             <div className="p-3 bg-accent/10 rounded"><Clock className="text-accent"/></div>
             <div>
               <p className="text-xs text-gray-400 uppercase">Avg Pipeline Time</p>
               <p className="text-xl font-bold font-mono">
                  {displayedEvents.length > 0 ? (displayedEvents.reduce((acc, curr) => acc + curr.processing_time_ms, 0) / displayedEvents.length).toFixed(1) : 0} ms
               </p>
             </div>
          </Card>
        </div>

        <Card className="p-3 flex gap-3 items-center bg-black/20">
          <div className="relative flex-1 max-w-md">
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
            <input 
              type="text" 
              placeholder="Search by name, ID, or camera..." 
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="w-full bg-black/40 border border-white/10 rounded-md py-1.5 pl-9 pr-4 text-sm text-white focus:outline-none focus:border-primary/50"
            />
          </div>
          <Button variant="outline" size="sm"><Filter size={14} className="mr-2"/> Filters</Button>
        </Card>

        <Card className="flex-1 overflow-y-auto p-0 border-white/5 relative">
          {displayedEvents.length === 0 ? (
             <EmptyState 
               icon={Clock}
               title="No History"
               description="No recognition events have been recorded yet."
             />
          ) : (
            <div className="flex flex-col">
              <AnimatePresence initial={false}>
                {displayedEvents.map((event, index) => {
                  const isNew = page === 0 && !search && liveEvents.some(e => e.history_id === event.history_id);
                  const isUnknown = event.state === 'UNKNOWN';
                  return (
                    <motion.div 
                      key={event.history_id}
                      layout="position"
                      initial={{ opacity: 0, height: 0, scale: 0.95 }}
                      animate={{ opacity: 1, height: 'auto', scale: 1 }}
                      transition={{ duration: 0.3 }}
                      onClick={() => setSelectedEvent(event)}
                      className={`flex items-stretch border-b border-white/5 cursor-pointer transition-colors
                        ${isUnknown ? 'hover:bg-danger/10' : 'hover:bg-white/5'}
                        ${isNew ? 'bg-success/5' : ''}
                        ${selectedEvent?.history_id === event.history_id ? 'bg-white/10' : ''}
                      `}
                    >
                    {/* Timeline Node */}
                    <div className="w-16 flex flex-col items-center py-4 relative shrink-0">
                        <div className="w-px h-full bg-white/10 absolute top-0" />
                        <div className={`w-3 h-3 rounded-full relative z-10 ${isUnknown ? 'bg-danger shadow-[0_0_8px_rgba(239,68,68,0.8)]' : 'bg-primary'}`} />
                    </div>
                    
                    {/* Event Details */}
                    <div className="flex-1 py-4 pr-6 flex items-center justify-between">
                      <div className="flex items-center gap-4">
                          <div className="w-12 h-12 rounded bg-black overflow-hidden border border-white/10 shrink-0">
                            {!isUnknown && event.identity_id ? (
                                <img src={`https://api.dicebear.com/7.x/avataaars/svg?seed=${event.identity_id}`} className="w-full h-full object-cover" />
                            ) : (
                                <div className="w-full h-full flex items-center justify-center bg-danger/20 text-danger"><AlertTriangle size={24}/></div>
                            )}
                          </div>
                          <div className="min-w-0">
                            <div className="flex items-center gap-2">
                              <h4 className={`text-base font-medium truncate ${isUnknown ? 'text-danger' : 'text-white'}`}>{event.name || 'Unknown Person'}</h4>
                            </div>
                            <div className="text-xs text-gray-400 mt-0.5 flex flex-wrap gap-3">
                              <span className="font-mono">{formatDate(event.timestamp)} {formatTime(event.timestamp)}</span>
                              <span>{event.camera_id}</span>
                              <span>{event.has_mask ? 'Face + Mask' : 'Face Detection'}</span>
                            </div>
                          </div>
                      </div>
                      
                      <div className="text-right pl-4">
                          {!isUnknown ? (
                            <StatusBadge status="success" dot={false} className="font-mono">{event.verification_score}%</StatusBadge>
                          ) : (
                            <StatusBadge status="danger" dot={false}>Unknown</StatusBadge>
                          )}
                      </div>
                      </div>
                    </motion.div>
                  );
                })}
              </AnimatePresence>
            </div>
          )}
        </Card>

        {/* Pagination */}
        <div className="flex justify-between items-center text-sm text-gray-400 shrink-0">
          <span>Showing {displayedEvents.length} of {totalRecords} events</span>
          <div className="flex gap-1">
            <Button variant="outline" size="sm" className="px-2" onClick={() => setPage(p => Math.max(0, p - 1))} disabled={page === 0}><ChevronLeft size={16} /></Button>
            <span className="px-3 flex items-center">Page {page + 1} of {Math.max(1, totalPages)}</span>
            <Button variant="outline" size="sm" className="px-2" onClick={() => setPage(p => Math.min(totalPages - 1, p + 1))} disabled={page >= totalPages - 1}><ChevronRight size={16} /></Button>
          </div>
        </div>

      </div>

      {/* Details Side Panel */}
      <AnimatePresence>
        {selectedEvent && (
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 20 }}
            className="w-80 border-l border-white/5 flex flex-col relative shrink-0 bg-card rounded-md overflow-hidden"
          >
          <div className="p-4 border-b border-white/5 flex items-center justify-between">
            <h3 className="font-semibold text-white">Event Details</h3>
            <button onClick={() => setSelectedEvent(null)} className="text-gray-400 hover:text-white"><X size={16} /></button>
          </div>
          
          <div className="p-6 flex flex-col gap-6 flex-1 overflow-y-auto">
            <div className="flex flex-col items-center gap-3">
               <div className={`w-24 h-24 rounded-full border-2 overflow-hidden ${selectedEvent.state === 'UNKNOWN' ? 'border-danger' : 'border-primary'}`}>
                 {selectedEvent.state !== 'UNKNOWN' && selectedEvent.identity_id ? (
                   <img src={`https://api.dicebear.com/7.x/avataaars/svg?seed=${selectedEvent.identity_id}`} className="w-full h-full object-cover" />
                 ) : (
                   <div className="w-full h-full flex items-center justify-center bg-danger/20 text-danger"><AlertTriangle size={32}/></div>
                 )}
               </div>
               <div className="text-center">
                 <h2 className={`text-xl font-bold ${selectedEvent.state === 'UNKNOWN' ? 'text-danger' : 'text-white'}`}>{selectedEvent.name || 'Unknown Person'}</h2>
                 {selectedEvent.identity_id && <p className="text-sm text-gray-400 font-mono">{selectedEvent.identity_id}</p>}
               </div>
            </div>

            <div className="space-y-4 text-sm">
              <div className="flex justify-between border-b border-white/5 pb-2">
                <span className="text-gray-400">Timestamp</span>
                <span className="text-white text-right font-mono text-xs">{formatDate(selectedEvent.timestamp)}<br/>{formatTime(selectedEvent.timestamp)}</span>
              </div>
              <div className="flex justify-between border-b border-white/5 pb-2">
                <span className="text-gray-400">Verification Score</span>
                <span className={selectedEvent.state === 'UNKNOWN' ? 'text-danger font-mono' : 'text-success font-mono'}>
                  {selectedEvent.state === 'UNKNOWN' ? 'N/A' : `${selectedEvent.verification_score}%`}
                </span>
              </div>
              <div className="flex justify-between border-b border-white/5 pb-2">
                <span className="text-gray-400">Camera</span>
                <span className="text-white">{selectedEvent.camera_id}</span>
              </div>
              <div className="flex justify-between border-b border-white/5 pb-2">
                <span className="text-gray-400">Tracking ID</span>
                <span className="text-white font-mono">{selectedEvent.tracking_id}</span>
              </div>
              <div className="flex justify-between border-b border-white/5 pb-2">
                <span className="text-gray-400">Recognition Mode</span>
                <span className="text-white">{selectedEvent.mode}</span>
              </div>
              <div className="flex justify-between border-b border-white/5 pb-2">
                <span className="text-gray-400">Pipeline Time</span>
                <span className="text-accent font-mono">{selectedEvent.processing_time_ms} ms</span>
              </div>
            </div>

            <div className="mt-auto pt-4 flex gap-2">
              <Button variant="outline" className="flex-1 text-danger hover:bg-danger/20 hover:text-danger border-danger/20" onClick={() => setShowDeleteConfirm(selectedEvent.history_id)}>
                <Trash2 size={14} className="mr-2"/> Delete Event
              </Button>
            </div>
          </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Delete Modals */}
      <AnimatePresence>
        {showClearConfirm && (
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center"
          >
            <motion.div
              initial={{ scale: 0.95 }}
              animate={{ scale: 1 }}
              exit={{ scale: 0.95 }}
            >
              <Card className="w-96 p-6 flex flex-col gap-4 border-danger/20">
                <h3 className="text-xl font-bold text-white">Clear All History?</h3>
                <p className="text-sm text-gray-400">
                  This will permanently delete all recognition history events. This cannot be undone.
                </p>
                <div className="flex gap-2 justify-end mt-2">
                  <Button variant="ghost" onClick={() => setShowClearConfirm(false)}>Cancel</Button>
                  <Button className="bg-danger hover:bg-danger/80 text-white" onClick={handleClearAll} disabled={clearMutation.isPending}>
                    {clearMutation.isPending ? "Clearing..." : "Clear All"}
                  </Button>
                </div>
              </Card>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {showDeleteConfirm && (
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center"
          >
            <motion.div
              initial={{ scale: 0.95 }}
              animate={{ scale: 1 }}
              exit={{ scale: 0.95 }}
            >
              <Card className="w-96 p-6 flex flex-col gap-4 border-danger/20">
                <h3 className="text-xl font-bold text-white">Delete Event?</h3>
                <p className="text-sm text-gray-400">
                  This will permanently delete this recognition event.
                </p>
                <div className="flex gap-2 justify-end mt-2">
                  <Button variant="ghost" onClick={() => setShowDeleteConfirm(null)}>Cancel</Button>
                  <Button className="bg-danger hover:bg-danger/80 text-white" onClick={handleDeleteEvent} disabled={deleteMutation.isPending}>
                    {deleteMutation.isPending ? "Deleting..." : "Delete Event"}
                  </Button>
                </div>
              </Card>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

    </div>
  );
};
