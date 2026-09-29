import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { trainingApi, datasetsApi } from '@/lib/api';
import { X, Play } from 'lucide-react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

interface StartTrainingDialogProps {
  projectId: string;
  isOpen: boolean;
  onClose: () => void;
}

export function StartTrainingDialog({ projectId, isOpen, onClose }: StartTrainingDialogProps) {
  const queryClient = useQueryClient();
  
  const [modelName, setModelName] = useState('');
  const [datasetVersionId, setDatasetVersionId] = useState('');
  const [method, setMethod] = useState('qlora');
  const [epochs, setEpochs] = useState('1');
  const [learningRate, setLearningRate] = useState('0.0002');

  const { data: datasets = [] } = useQuery({
    queryKey: ['datasets', projectId],
    queryFn: () => datasetsApi.list(projectId),
    enabled: isOpen,
  });

  const startMutation = useMutation({
    mutationFn: () => trainingApi.create(projectId, { 
      model_name: modelName, 
      dataset_version_id: datasetVersionId,
      method,
      epochs: parseFloat(epochs),
      learning_rate: parseFloat(learningRate)
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['trainingJobs', projectId] });
      onClose();
      // Reset form
      setModelName('');
      setDatasetVersionId('');
      setMethod('qlora');
      setEpochs('1');
      setLearningRate('0.0002');
    },
    onError: (error: any) => {
      alert(`Failed to start job: ${error.response?.data?.detail || error.message}`);
    }
  });

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm">
      <div className="w-full max-w-md bg-card border border-border shadow-lg rounded-xl overflow-hidden">
        <div className="flex items-center justify-between px-6 py-4 border-b border-border">
          <h2 className="text-lg font-semibold text-foreground">Start Fine-Tuning Job</h2>
          <Button variant="ghost" size="icon" className="w-8 h-8 rounded-full" onClick={onClose}>
            <X className="w-4 h-4 text-muted-foreground" />
          </Button>
        </div>
        
        <div className="p-6 space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium text-foreground">Target Model Name</label>
            <input 
              type="text" 
              value={modelName}
              onChange={(e) => setModelName(e.target.value)}
              placeholder="e.g. my-finetuned-llama"
              className="w-full h-10 px-3 text-sm bg-background border border-border rounded-md focus:outline-none focus:ring-1 focus:ring-ring"
            />
          </div>
          
          <div className="space-y-2">
            <label className="text-sm font-medium text-foreground">Dataset</label>
            <select 
              value={datasetVersionId}
              onChange={(e) => setDatasetVersionId(e.target.value)}
              className="w-full h-10 px-3 text-sm bg-background border border-border rounded-md focus:outline-none focus:ring-1 focus:ring-ring"
            >
              <option value="">Select a dataset...</option>
              {datasets.map((ds: any) => {
                const latestVersion = ds.versions?.[0];
                if (!latestVersion) return null;
                return (
                  <option key={latestVersion.id} value={latestVersion.id}>
                    {ds.name} (v{latestVersion.version_tag})
                  </option>
                );
              })}
            </select>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium text-foreground">Fine-Tuning Method</label>
            <select 
              value={method}
              onChange={(e) => setMethod(e.target.value)}
              className="w-full h-10 px-3 text-sm bg-background border border-border rounded-md focus:outline-none focus:ring-1 focus:ring-ring"
            >
              <option value="qlora">QLoRA (Recommended for local)</option>
              <option value="lora">LoRA</option>
              <option value="full">Full Fine-tuning</option>
            </select>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="text-sm font-medium text-foreground">Epochs</label>
              <input 
                type="number" 
                min="0.1"
                step="0.1"
                value={epochs}
                onChange={(e) => setEpochs(e.target.value)}
                className="w-full h-10 px-3 text-sm bg-background border border-border rounded-md focus:outline-none focus:ring-1 focus:ring-ring"
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium text-foreground">Learning Rate</label>
              <input 
                type="number" 
                step="0.0001"
                value={learningRate}
                onChange={(e) => setLearningRate(e.target.value)}
                className="w-full h-10 px-3 text-sm bg-background border border-border rounded-md focus:outline-none focus:ring-1 focus:ring-ring"
              />
            </div>
          </div>
        </div>
        
        <div className="px-6 py-4 border-t border-border bg-secondary/20 flex justify-end gap-2">
          <Button variant="outline" onClick={onClose}>Cancel</Button>
          <Button 
            disabled={!modelName || !datasetVersionId || startMutation.isPending}
            onClick={() => startMutation.mutate()}
          >
            {startMutation.isPending ? 'Starting...' : (
              <span className="flex items-center">
                <Play className="w-4 h-4 mr-2" /> Start Job
              </span>
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}
