import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { experimentsApi, modelsApi } from '@/lib/api';
import { X } from 'lucide-react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

interface StartExperimentDialogProps {
  projectId: string;
  isOpen: boolean;
  onClose: () => void;
}

export function StartExperimentDialog({ projectId, isOpen, onClose }: StartExperimentDialogProps) {
  const queryClient = useQueryClient();
  
  const [name, setName] = useState('');
  const [modelId, setModelId] = useState('');
  const [modelAVersionId, setModelAVersionId] = useState('');
  const [modelBVersionId, setModelBVersionId] = useState('');
  const [weightA, setWeightA] = useState('50');
  const [weightB, setWeightB] = useState('50');

  const { data: models = [] } = useQuery({
    queryKey: ['models', projectId],
    queryFn: () => modelsApi.list(projectId),
    enabled: isOpen,
  });

  const startMutation = useMutation({
    mutationFn: () => experimentsApi.create({ 
      project_id: projectId,
      model_id: modelId,
      name,
      model_a_version_id: modelAVersionId,
      model_b_version_id: modelBVersionId,
      weight_a: parseInt(weightA),
      weight_b: parseInt(weightB),
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['experiments', projectId] });
      onClose();
      setName('');
      setModelId('');
      setModelAVersionId('');
      setModelBVersionId('');
      setWeightA('50');
      setWeightB('50');
    },
    onError: (error: any) => {
      alert(`Failed to start experiment: ${error.response?.data?.detail || error.message}`);
    }
  });

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm">
      <div className="w-full max-w-md bg-card border border-border shadow-lg rounded-xl overflow-hidden">
        <div className="flex items-center justify-between px-6 py-4 border-b border-border">
          <h2 className="text-lg font-semibold text-foreground">New A/B Experiment</h2>
          <Button variant="ghost" size="icon" className="w-8 h-8 rounded-full" onClick={onClose}>
            <X className="w-4 h-4 text-muted-foreground" />
          </Button>
        </div>
        
        <div className="p-6 space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium text-foreground">Experiment Name</label>
            <input 
              type="text" 
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Qwen vs Llama for Support"
              className="w-full h-10 px-3 text-sm bg-background border border-border rounded-md focus:outline-none focus:ring-1 focus:ring-ring"
            />
          </div>
          
          <div className="space-y-2">
            <label className="text-sm font-medium text-foreground">Base API Model</label>
            <select 
              value={modelId}
              onChange={(e) => {
                setModelId(e.target.value);
                setModelAVersionId('');
                setModelBVersionId('');
              }}
              className="w-full h-10 px-3 text-sm bg-background border border-border rounded-md focus:outline-none focus:ring-1 focus:ring-ring"
            >
              <option value="">Select a model...</option>
              {models.map((m: any) => (
                <option key={m.id} value={m.id}>{m.name}</option>
              ))}
            </select>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium text-foreground">Variant A (Model Version)</label>
            <select 
              value={modelAVersionId}
              onChange={(e) => setModelAVersionId(e.target.value)}
              disabled={!modelId}
              className="w-full h-10 px-3 text-sm bg-background border border-border rounded-md focus:outline-none focus:ring-1 focus:ring-ring disabled:opacity-50"
            >
              <option value="">Select version for A...</option>
              {models.find((m: any) => m.id === modelId)?.versions?.map((v: any) => (
                <option key={v.id} value={v.id}>{v.version_tag} ({v.lifecycle_status})</option>
              ))}
            </select>
          </div>
          
          <div className="space-y-2">
            <label className="text-sm font-medium text-foreground">Variant B (Model Version)</label>
            <select 
              value={modelBVersionId}
              onChange={(e) => setModelBVersionId(e.target.value)}
              disabled={!modelId}
              className="w-full h-10 px-3 text-sm bg-background border border-border rounded-md focus:outline-none focus:ring-1 focus:ring-ring disabled:opacity-50"
            >
              <option value="">Select version for B...</option>
              {models.find((m: any) => m.id === modelId)?.versions?.map((v: any) => (
                <option key={v.id} value={v.id}>{v.version_tag} ({v.lifecycle_status})</option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="text-sm font-medium text-foreground">Traffic Weight A (%)</label>
              <input 
                type="number" 
                value={weightA}
                onChange={(e) => {
                  setWeightA(e.target.value);
                  setWeightB((100 - parseInt(e.target.value || '0')).toString());
                }}
                className="w-full h-10 px-3 text-sm bg-background border border-border rounded-md focus:outline-none focus:ring-1 focus:ring-ring"
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium text-foreground">Traffic Weight B (%)</label>
              <input 
                type="number" 
                value={weightB}
                onChange={(e) => {
                  setWeightB(e.target.value);
                  setWeightA((100 - parseInt(e.target.value || '0')).toString());
                }}
                className="w-full h-10 px-3 text-sm bg-background border border-border rounded-md focus:outline-none focus:ring-1 focus:ring-ring"
              />
            </div>
          </div>
        </div>
        
        <div className="px-6 py-4 border-t border-border bg-secondary/20 flex justify-end gap-2">
          <Button variant="outline" onClick={onClose}>Cancel</Button>
          <Button 
            disabled={!name || !modelId || !modelAVersionId || !modelBVersionId || startMutation.isPending}
            onClick={() => startMutation.mutate()}
          >
            {startMutation.isPending ? 'Creating...' : 'Create Experiment'}
          </Button>
        </div>
      </div>
    </div>
  );
}
