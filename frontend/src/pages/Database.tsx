import React, { useState, useMemo } from 'react';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Search, Filter, Edit2, Trash2, Download, Users, HardDrive, ShieldCheck, X, RefreshCcw, Save } from 'lucide-react';
import { useIdentities, useUpdateIdentity, useDeleteIdentity } from '../utils/api';
import type { IdentityModel } from '../utils/api';
import { LoadingState } from '../components/common/LoadingState';
import { ErrorState } from '../components/common/ErrorState';
import { EmptyState } from '../components/common/EmptyState';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';

export const Database: React.FC = () => {
  const navigate = useNavigate();
  const { data: identities, isLoading, isError, refetch } = useIdentities();
  const updateMutation = useUpdateIdentity();
  const deleteMutation = useDeleteIdentity();

  const [search, setSearch] = useState('');
  const [selectedPerson, setSelectedPerson] = useState<IdentityModel | null>(null);
  
  // Edit State
  const [isEditing, setIsEditing] = useState(false);
  const [editForm, setEditForm] = useState({ name: '', department: '', notes: '' });

  // Delete State
  const [showDeleteConfirm, setShowDeleteConfirm] = useState<string | null>(null);

  const filteredPeople = useMemo(() => {
    if (!identities) return [];
    const lowerSearch = search.toLowerCase();
    return identities.filter(p => 
      p.name.toLowerCase().includes(lowerSearch) || 
      p.identity_id.toLowerCase().includes(lowerSearch) ||
      (p.department && p.department.toLowerCase().includes(lowerSearch))
    );
  }, [identities, search]);

  const handleEditClick = (person: IdentityModel, e: React.MouseEvent) => {
    e.stopPropagation();
    setSelectedPerson(person);
    setIsEditing(true);
    setEditForm({ name: person.name, department: person.department || '', notes: person.notes || '' });
  };

  const handleSaveEdit = () => {
    if (!selectedPerson) return;
    updateMutation.mutate(
      { id: selectedPerson.identity_id, data: editForm },
      {
        onSuccess: () => {
          setIsEditing(false);
          refetch();
          setSelectedPerson(prev => prev ? { ...prev, ...editForm } : null);
        }
      }
    );
  };

  const handleDeleteClick = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setShowDeleteConfirm(id);
  };

  const confirmDelete = () => {
    if (!showDeleteConfirm) return;
    deleteMutation.mutate(showDeleteConfirm, {
      onSuccess: () => {
        setShowDeleteConfirm(null);
        if (selectedPerson?.identity_id === showDeleteConfirm) {
          setSelectedPerson(null);
        }
        refetch();
      }
    });
  };

  const formatDate = (isoStr: string) => {
    const d = new Date(isoStr);
    return d.toLocaleDateString() + ' ' + d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  if (isLoading) {
    return <LoadingState message="Loading database..." />;
  }

  if (isError) {
    return <ErrorState onRetry={() => refetch()} />;
  }

  return (
    <div className="h-full flex gap-4">
      <div className="flex-1 flex flex-col gap-4">
        
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold tracking-tight">Identity Database</h2>
            <p className="text-sm text-gray-400 mt-1">Manage registered identities and facial embeddings.</p>
          </div>
          <div className="flex gap-2">
            <Button variant="secondary" onClick={() => window.location.href = 'http://127.0.0.1:8000/api/v1/enrollment/export'}><Download size={14} className="mr-2"/> Export CSV</Button>
            <Button variant="primary" onClick={() => navigate('/enrollment')}>Add Person</Button>
          </div>
        </div>

        <div className="grid grid-cols-4 gap-4">
          <Card className="p-4 flex items-center gap-4">
            <div className="p-3 bg-primary/10 rounded"><Users className="text-primary"/></div>
            <div>
              <p className="text-xs text-gray-400 uppercase">Total People</p>
              <p className="text-xl font-bold">{identities?.length || 0}</p>
            </div>
          </Card>
          <Card className="p-4 flex items-center gap-4">
            <div className="p-3 bg-accent/10 rounded"><HardDrive className="text-accent"/></div>
            <div>
              <p className="text-xs text-gray-400 uppercase">Recognitions</p>
              <p className="text-xl font-bold font-mono">
                {identities?.reduce((acc, curr) => acc + curr.recognition_count, 0) || 0}
              </p>
            </div>
          </Card>
        </div>

        <Card className="p-3 flex gap-3 items-center bg-black/20">
          <div className="relative flex-1 max-w-md">
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
            <input 
              type="text" 
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by name, ID, or department..." 
              className="w-full bg-black/40 border border-white/10 rounded-md py-1.5 pl-9 pr-4 text-sm text-white focus:outline-none focus:border-primary/50"
            />
          </div>
          <Button variant="outline" size="sm"><Filter size={14} className="mr-2"/> Filters</Button>
        </Card>

        {filteredPeople.length === 0 ? (
           <EmptyState 
             icon={Users}
             title="No Identities Found"
             description={search ? "No matches for your search criteria." : "The database is empty."}
           />
        ) : (
          <div className="flex-1 overflow-y-auto pb-4">
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
              {filteredPeople.map((person) => (
                <Card 
                  key={person.identity_id} 
                  className={`p-4 flex flex-col gap-4 hover:border-white/20 transition-colors group relative cursor-pointer ${selectedPerson?.identity_id === person.identity_id ? 'border-primary' : 'border-white/5'}`}
                  onClick={() => { setSelectedPerson(person); setIsEditing(false); }}
                >
                  <div className="flex gap-4">
                    <div className="w-14 h-14 rounded overflow-hidden border border-white/10 bg-black shrink-0">
                      <img src={`https://api.dicebear.com/7.x/avataaars/svg?seed=${person.identity_id}`} alt={person.name} className="w-full h-full object-cover" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <h3 className="text-base font-semibold text-white truncate pr-6">{person.name}</h3>
                      <p className="text-xs text-gray-400 font-mono mt-0.5">{person.identity_id}</p>
                      <div className="mt-1">
                         <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] bg-white/5 text-gray-300 border border-white/10">
                           {person.department || 'None'}
                         </span>
                      </div>
                    </div>
                  </div>
                  
                  <div className="space-y-1.5 border-t border-white/5 pt-3 text-xs text-gray-400">
                    <div className="flex justify-between">
                      <span>Enrolled:</span><span className="text-white truncate max-w-[140px]">{formatDate(person.enrollment_date)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Recognitions:</span><span className="text-success font-mono">{person.recognition_count}</span>
                    </div>
                  </div>

                  <div className="absolute top-4 right-4 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button onClick={(e) => handleEditClick(person, e)} className="p-1 hover:bg-white/10 rounded text-gray-400 hover:text-white"><Edit2 size={14}/></button>
                    <button onClick={(e) => handleDeleteClick(person.identity_id, e)} className="p-1 hover:bg-danger/20 rounded text-gray-400 hover:text-danger"><Trash2 size={14}/></button>
                  </div>
                </Card>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Side Panel */}
      <AnimatePresence>
        {selectedPerson && (
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 20 }}
            className="w-80 border-l border-white/5 flex flex-col relative shrink-0 bg-card rounded-md overflow-hidden"
          >
            <div className="p-4 border-b border-white/5 flex items-center justify-between">
              <h3 className="font-semibold text-white">Identity Details</h3>
              <button onClick={() => setSelectedPerson(null)} className="text-gray-400 hover:text-white"><X size={16} /></button>
            </div>
            
            <div className="p-6 flex flex-col gap-6 flex-1 overflow-y-auto">
              <div className="flex flex-col items-center gap-3">
                 <div className="w-24 h-24 rounded-full border-2 border-primary overflow-hidden">
                   <img src={`https://api.dicebear.com/7.x/avataaars/svg?seed=${selectedPerson.identity_id}`} className="w-full h-full object-cover" />
                 </div>
                 <div className="text-center">
                   <h2 className="text-xl font-bold text-white">{selectedPerson.name}</h2>
                   <p className="text-sm text-gray-400 font-mono">{selectedPerson.identity_id}</p>
                 </div>
              </div>

              {isEditing ? (
                <div className="space-y-4">
                  <div>
                    <label className="text-xs text-gray-400">Name</label>
                    <input type="text" value={editForm.name} onChange={e => setEditForm(f => ({ ...f, name: e.target.value }))} className="w-full bg-black border border-white/10 rounded px-2 py-1 text-sm text-white mt-1" />
                  </div>
                  <div>
                    <label className="text-xs text-gray-400">Department</label>
                    <input type="text" value={editForm.department} onChange={e => setEditForm(f => ({ ...f, department: e.target.value }))} className="w-full bg-black border border-white/10 rounded px-2 py-1 text-sm text-white mt-1" />
                  </div>
                  <div>
                    <label className="text-xs text-gray-400">Notes</label>
                    <textarea value={editForm.notes} onChange={e => setEditForm(f => ({ ...f, notes: e.target.value }))} className="w-full bg-black border border-white/10 rounded px-2 py-1 text-sm text-white mt-1 h-20" />
                  </div>
                  <div className="flex gap-2 pt-2">
                    <Button variant="outline" size="sm" className="flex-1" onClick={() => setIsEditing(false)}>Cancel</Button>
                    <Button variant="primary" size="sm" className="flex-1" onClick={handleSaveEdit} disabled={updateMutation.isPending}>
                      {updateMutation.isPending ? "Saving..." : "Save"}
                    </Button>
                  </div>
                </div>
              ) : (
                <div className="space-y-4 text-sm">
                  <div className="flex justify-between border-b border-white/5 pb-2">
                    <span className="text-gray-400">Department</span>
                    <span className="text-white">{selectedPerson.department || '-'}</span>
                  </div>
                  <div className="flex justify-between border-b border-white/5 pb-2">
                    <span className="text-gray-400">Enrolled</span>
                    <span className="text-white text-right max-w-[140px] truncate">{formatDate(selectedPerson.enrollment_date)}</span>
                  </div>
                  <div className="flex justify-between border-b border-white/5 pb-2">
                    <span className="text-gray-400">Total Recognitions</span>
                    <span className="text-success font-mono">{selectedPerson.recognition_count}</span>
                  </div>
                  <div className="flex justify-between border-b border-white/5 pb-2">
                    <span className="text-gray-400">Last Seen</span>
                    <span className="text-white text-right max-w-[140px] truncate">{selectedPerson.last_seen ? formatDate(selectedPerson.last_seen) : 'Never'}</span>
                  </div>
                  <div>
                    <span className="text-gray-400 block mb-1">Notes</span>
                    <p className="text-gray-300 text-xs bg-black/20 p-2 rounded">{selectedPerson.notes || 'No notes available.'}</p>
                  </div>
                  <div className="pt-4 flex gap-2">
                    <Button variant="outline" className="flex-1" onClick={() => setIsEditing(true)}>Edit</Button>
                  </div>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Delete Confirmation Modal */}
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
                <h3 className="text-xl font-bold text-white">Delete Identity?</h3>
                <p className="text-sm text-gray-400">
                  This will permanently remove the biometric embedding and history for <strong className="text-white">{showDeleteConfirm}</strong>. This cannot be undone.
                </p>
                <div className="flex gap-2 justify-end mt-2">
                  <Button variant="ghost" onClick={() => setShowDeleteConfirm(null)}>Cancel</Button>
                  <Button className="bg-danger hover:bg-danger/80 text-white" onClick={confirmDelete} disabled={deleteMutation.isPending}>
                    {deleteMutation.isPending ? "Deleting..." : "Delete Permanently"}
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
