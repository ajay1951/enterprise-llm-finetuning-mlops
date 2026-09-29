import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { modelsApi } from '@/lib/api';
import { X, FolderSearch } from 'lucide-react';
import { useMutation, useQueryClient } from '@tanstack/react-query';

interface ImportModelDialogProps {
  projectId: string;
  isOpen: boolean;
  onClose: () => void;
}

export function ImportModelDialog({ projectId, isOpen, onClose }: ImportModelDialogProps) {
  const queryClient = useQueryClient();
  const [name, setName] = useState('');
  const [baseModel, setBaseModel] = useState('');
  const [localPath, setLocalPath] = useState('');

  const importMutation = useMutation({
    mutationFn: () => modelsApi.importLocal(projectId, { name, base_model: baseModel, local_path: localPath }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['models', projectId] });
      onClose();
      // Reset form
      setName('');
      setBaseModel('');
      setLocalPath('');
    },
    onError: (error: any) => {
      alert(`Import failed: ${error.response?.data?.detail || error.message}`);
    }
  });

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm">
      <div className="w-full max-w-md bg-card border border-border shadow-lg rounded-xl overflow-hidden">
        <div className="flex items-center justify-between px-6 py-4 border-b border-border">
          <h2 className="text-lg font-semibold text-foreground">Import Local Model</h2>
          <Button variant="ghost" size="icon" className="w-8 h-8 rounded-full" onClick={onClose}>
            <X className="w-4 h-4 text-muted-foreground" />
          </Button>
        </div>
        
        <div className="p-6 space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium text-foreground">Model Name</label>
            <input 
              type="text" 
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. llama-3-customer-support"
              className="w-full h-10 px-3 text-sm bg-background border border-border rounded-md focus:outline-none focus:ring-1 focus:ring-ring"
            />
          </div>
          
          <div className="space-y-2">
            <label className="text-sm font-medium text-foreground">Base Model Architecture</label>
            <input 
              type="text" 
              value={baseModel}
              onChange={(e) => setBaseModel(e.target.value)}
              placeholder="e.g. meta-llama/Llama-3-8b"
              className="w-full h-10 px-3 text-sm bg-background border border-border rounded-md focus:outline-none focus:ring-1 focus:ring-ring"
            />
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium text-foreground">Local Folder Path</label>
            <div className="relative">
              <FolderSearch className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <input 
                type="text" 
                value={localPath}
                onChange={(e) => setLocalPath(e.target.value)}
                placeholder="e.g. C:\models\my-finetuned-model"
                className="w-full h-10 pl-9 pr-3 text-sm bg-background border border-border rounded-md focus:outline-none focus:ring-1 focus:ring-ring"
              />
            </div>
            <p className="text-xs text-muted-foreground mt-1">Provide the absolute path to the directory containing your model weights.</p>
          </div>
        </div>
        
        <div className="px-6 py-4 border-t border-border bg-secondary/20 flex justify-end gap-2">
          <Button variant="outline" onClick={onClose}>Cancel</Button>
          <Button 
            disabled={!name || !baseModel || !localPath || importMutation.isPending}
            onClick={() => importMutation.mutate()}
          >
            {importMutation.isPending ? 'Importing...' : 'Import Model'}
          </Button>
        </div>
      </div>
    </div>
  );
}
