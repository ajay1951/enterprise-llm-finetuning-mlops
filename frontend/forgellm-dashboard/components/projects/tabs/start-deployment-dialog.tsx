import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { deploymentsApi, modelsApi } from '@/lib/api';
import { X } from 'lucide-react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

interface StartDeploymentDialogProps {
  projectId: string;
  isOpen: boolean;
  onClose: () => void;
}

export function StartDeploymentDialog({ projectId, isOpen, onClose }: StartDeploymentDialogProps) {
  const queryClient = useQueryClient();
  
  const [name, setName] = useState('');
  const [modelId, setModelId] = useState('');
  const [modelVersionId, setModelVersionId] = useState('');

  const { data: models = [] } = useQuery({
    queryKey: ['models', projectId],
    queryFn: () => modelsApi.list(projectId),
    enabled: isOpen,
  });

  const createMutation = useMutation({
    mutationFn: () => deploymentsApi.create(projectId, { 
      name,
      model_version_id: modelVersionId,
      backend: "transformers",
      device: "cuda"
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['deployments', projectId] });
      onClose();
      setName('');
      setModelId('');
      setModelVersionId('');
    },
    onError: (error: any) => {
      alert(`Failed to create deployment: ${error.response?.data?.detail?.[0]?.msg || error.response?.data?.detail || error.message}`);
    }
  });

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm">
      <div className="w-full max-w-md bg-card border border-border shadow-lg rounded-xl overflow-hidden">
        <div className="flex items-center justify-between px-6 py-4 border-b border-border">
          <h2 className="text-lg font-semibold text-foreground">New API Deployment</h2>
          <Button variant="ghost" size="icon" className="w-8 h-8 rounded-full" onClick={onClose}>
            <X className="w-4 h-4 text-muted-foreground" />
          </Button>
        </div>
        
        <div className="p-6 space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium text-foreground">Deployment Name</label>
            <input 
              type="text" 
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Production API"
              className="w-full h-10 px-3 text-sm bg-background border border-border rounded-md focus:outline-none focus:ring-1 focus:ring-ring"
            />
          </div>
          
          <div className="space-y-2">
            <label className="text-sm font-medium text-foreground">Select Model</label>
            <select 
              value={modelId}
              onChange={(e) => {
                setModelId(e.target.value);
                setModelVersionId('');
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
            <label className="text-sm font-medium text-foreground">Select Version</label>
            <select 
              value={modelVersionId}
              onChange={(e) => setModelVersionId(e.target.value)}
              disabled={!modelId}
              className="w-full h-10 px-3 text-sm bg-background border border-border rounded-md focus:outline-none focus:ring-1 focus:ring-ring disabled:opacity-50"
            >
              <option value="">Select a version...</option>
              {models.find((m: any) => m.id === modelId)?.versions?.map((v: any) => (
                <option key={v.id} value={v.id}>{v.version_tag} ({v.lifecycle_status})</option>
              ))}
            </select>
          </div>
        </div>
        
        <div className="px-6 py-4 border-t border-border bg-secondary/20 flex justify-end gap-2">
          <Button variant="outline" onClick={onClose}>Cancel</Button>
          <Button 
            disabled={!name || !modelVersionId || createMutation.isPending}
            onClick={() => createMutation.mutate()}
          >
            {createMutation.isPending ? 'Deploying...' : 'Launch Deployment'}
          </Button>
        </div>
      </div>
    </div>
  );
}
