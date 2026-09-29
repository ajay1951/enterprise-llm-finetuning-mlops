import { useState, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { datasetsApi } from '@/lib/api';
import { X, UploadCloud, FileText } from 'lucide-react';
import { useMutation, useQueryClient } from '@tanstack/react-query';

interface UploadDatasetDialogProps {
  projectId: string;
  isOpen: boolean;
  onClose: () => void;
}

export function UploadDatasetDialog({ projectId, isOpen, onClose }: UploadDatasetDialogProps) {
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [file, setFile] = useState<File | null>(null);

  const uploadMutation = useMutation({
    mutationFn: () => datasetsApi.upload(projectId, name, description, file!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['datasets', projectId] });
      onClose();
      // Reset form
      setName('');
      setDescription('');
      setFile(null);
    },
    onError: (error: any) => {
      alert(`Upload failed: ${error.response?.data?.detail || error.message}`);
    }
  });

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm">
      <div className="w-full max-w-md bg-card border border-border shadow-lg rounded-xl overflow-hidden">
        <div className="flex items-center justify-between px-6 py-4 border-b border-border">
          <h2 className="text-lg font-semibold text-foreground">Upload Dataset</h2>
          <Button variant="ghost" size="icon" className="w-8 h-8 rounded-full" onClick={onClose}>
            <X className="w-4 h-4 text-muted-foreground" />
          </Button>
        </div>
        
        <div className="p-6 space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium text-foreground">Dataset Name</label>
            <input 
              type="text" 
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. customer-support-v1"
              className="w-full h-10 px-3 text-sm bg-background border border-border rounded-md focus:outline-none focus:ring-1 focus:ring-ring"
            />
          </div>
          
          <div className="space-y-2">
            <label className="text-sm font-medium text-foreground">Description (Optional)</label>
            <input 
              type="text" 
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Brief description of the dataset"
              className="w-full h-10 px-3 text-sm bg-background border border-border rounded-md focus:outline-none focus:ring-1 focus:ring-ring"
            />
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium text-foreground">Data File (.jsonl, .csv)</label>
            
            <div 
              onClick={() => fileInputRef.current?.click()}
              className={`border-2 border-dashed rounded-lg p-6 flex flex-col items-center justify-center cursor-pointer transition-colors ${file ? 'border-primary bg-primary/5' : 'border-border hover:border-primary/50 hover:bg-secondary/20'}`}
            >
              <input 
                type="file" 
                ref={fileInputRef}
                className="hidden" 
                accept=".jsonl,.csv,.json"
                onChange={(e) => setFile(e.target.files?.[0] || null)}
              />
              {file ? (
                <>
                  <FileText className="w-8 h-8 text-primary mb-2" />
                  <p className="text-sm font-medium text-foreground text-center">{file.name}</p>
                  <p className="text-xs text-muted-foreground mt-1">{(file.size / 1024).toFixed(1)} KB</p>
                </>
              ) : (
                <>
                  <UploadCloud className="w-8 h-8 text-muted-foreground mb-2" />
                  <p className="text-sm font-medium text-foreground text-center">Click to browse files</p>
                  <p className="text-xs text-muted-foreground mt-1">Accepts JSONL or CSV</p>
                </>
              )}
            </div>
          </div>
        </div>
        
        <div className="px-6 py-4 border-t border-border bg-secondary/20 flex justify-end gap-2">
          <Button variant="outline" onClick={onClose}>Cancel</Button>
          <Button 
            disabled={!name || !file || uploadMutation.isPending}
            onClick={() => uploadMutation.mutate()}
          >
            {uploadMutation.isPending ? 'Uploading...' : 'Upload Dataset'}
          </Button>
        </div>
      </div>
    </div>
  );
}
