import React, { useState } from 'react';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { LoadingState } from '../components/common/LoadingState';
import { ErrorState } from '../components/common/ErrorState';
import { EmptyState } from '../components/common/EmptyState';
import { useCameras, useAddCamera, useSetActiveCamera, useDeleteCamera } from '../utils/api';
import { Video, Plus, Trash2, PlayCircle, AlertCircle } from 'lucide-react';

export const Cameras: React.FC = () => {
  const { data: cameras, isLoading, isError, refetch } = useCameras();
  const addMutation = useAddCamera();
  const setActiveMutation = useSetActiveCamera();
  const deleteMutation = useDeleteCamera();

  const [isAdding, setIsAdding] = useState(false);
  const [formData, setFormData] = useState({ name: '', source_type: 'RTSP', connection_url: '' });

  const handleAdd = () => {
    addMutation.mutate(formData, {
      onSuccess: () => {
        setIsAdding(false);
        setFormData({ name: '', source_type: 'RTSP', connection_url: '' });
        refetch();
      }
    });
  };

  const handleSetActive = (id: string) => {
    setActiveMutation.mutate(id, {
      onSuccess: () => {
        refetch();
      }
    });
  };

  const handleDelete = (id: string) => {
    if (confirm("Are you sure you want to delete this camera?")) {
      deleteMutation.mutate(id, {
        onSuccess: () => {
          refetch();
        }
      });
    }
  };

  if (isLoading) return <LoadingState message="Loading camera sources..." />;
  if (isError) return <ErrorState title="Failed to load cameras" onRetry={refetch} />;

  return (
    <div className="h-full flex flex-col gap-6 overflow-y-auto pr-2 pb-8">
      <div className="flex justify-between items-end">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Camera Management</h2>
          <p className="text-sm text-gray-600 mt-1">Configure RTSP and Webcam sources for recognition.</p>
        </div>
        <Button variant="primary" onClick={() => setIsAdding(true)} disabled={isAdding}>
          <Plus size={16} className="mr-2" /> Add Camera
        </Button>
      </div>

      {isAdding && (
        <Card className="p-6 border-primary/50">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Add New Camera</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
            <div>
              <label className="block text-xs text-gray-600 mb-1">Camera Name</label>
              <input 
                type="text" 
                value={formData.name}
                onChange={e => setFormData({ ...formData, name: e.target.value })}
                className="w-full bg-black border border-gray-300 rounded px-3 py-2 text-gray-900 focus:border-primary outline-none" 
                placeholder="e.g. Front Entrance"
              />
            </div>
            <div>
              <label className="block text-xs text-gray-600 mb-1">Source Type</label>
              <select 
                value={formData.source_type}
                onChange={e => setFormData({ ...formData, source_type: e.target.value })}
                className="w-full bg-black border border-gray-300 rounded px-3 py-2 text-gray-900 focus:border-primary outline-none"
              >
                <option value="RTSP">RTSP Stream (IP Camera)</option>
                <option value="WEBCAM">USB Webcam (Local)</option>
              </select>
            </div>
            <div>
              <label className="block text-xs text-gray-600 mb-1">Connection URL / Device ID</label>
              <input 
                type="text" 
                value={formData.connection_url}
                onChange={e => setFormData({ ...formData, connection_url: e.target.value })}
                className="w-full bg-black border border-gray-300 rounded px-3 py-2 text-gray-900 focus:border-primary outline-none" 
                placeholder={formData.source_type === 'RTSP' ? 'rtsp://user:pass@ip:port/stream' : '0'}
              />
            </div>
          </div>
          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={() => setIsAdding(false)}>Cancel</Button>
            <Button variant="primary" onClick={handleAdd} disabled={addMutation.isPending || !formData.name || !formData.connection_url}>
              {addMutation.isPending ? 'Saving...' : 'Save Camera'}
            </Button>
          </div>
        </Card>
      )}

      {cameras && cameras.length === 0 && !isAdding ? (
        <EmptyState 
          icon={Video}
          title="No Cameras Found"
          description="Add an RTSP stream or local webcam to get started."
        />
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {cameras?.map(camera => (
            <Card key={camera.id} className={`p-4 flex items-center justify-between ${camera.is_active ? 'border-success/50 bg-success/5' : ''}`}>
              <div className="flex items-center gap-4">
                <div className={`w-12 h-12 rounded flex items-center justify-center ${camera.is_active ? 'bg-success/20 text-success' : 'bg-secondary text-gray-600'}`}>
                  <Video size={24} />
                </div>
                <div>
                  <h3 className="text-gray-900 font-medium flex items-center gap-2">
                    {camera.name}
                    {camera.is_active && <span className="text-[10px] bg-success/20 text-success px-2 py-0.5 rounded uppercase tracking-wider">Active</span>}
                  </h3>
                  <p className="text-xs text-gray-600 mt-1 font-mono">{camera.source_type} • {camera.connection_url}</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                {!camera.is_active && (
                  <Button variant="outline" size="sm" onClick={() => handleSetActive(camera.id)} disabled={setActiveMutation.isPending}>
                    <PlayCircle size={14} className="mr-2" /> Set Active
                  </Button>
                )}
                <Button variant="ghost" size="sm" onClick={() => handleDelete(camera.id)} disabled={deleteMutation.isPending} className="text-danger hover:bg-danger/10 hover:text-danger">
                  <Trash2 size={14} />
                </Button>
              </div>
            </Card>
          ))}
        </div>
      )}
      
      <div className="mt-4 p-4 bg-primary/10 border border-primary/20 rounded-md flex gap-3 text-sm text-primary">
         <AlertCircle size={20} className="shrink-0" />
         <p>Note: Changing the active camera requires the Recognition Pipeline to be restarted on the Dashboard for changes to take effect.</p>
      </div>
    </div>
  );
};
