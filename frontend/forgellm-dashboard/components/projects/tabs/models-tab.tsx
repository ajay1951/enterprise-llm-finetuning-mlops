import { useQuery } from '@tanstack/react-query';
import { modelsApi } from '@/lib/api/experiments';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { useState } from 'react';
import { Box, Play, Plus, MoreHorizontal } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { ImportModelDialog } from './import-model-dialog';
import { StartDeploymentDialog } from './start-deployment-dialog';

export function ModelsTab({ projectId }: { projectId: string }) {
  const [isImportOpen, setIsImportOpen] = useState(false);
  const [selectedModel, setSelectedModel] = useState<any>(null);
  const [isDeployOpen, setIsDeployOpen] = useState(false);
  
  const { data: models = [], isLoading } = useQuery({
    queryKey: ['models', projectId],
    queryFn: () => modelsApi.list(projectId),
  });

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="h-10 w-48 bg-secondary animate-pulse rounded" />
        <Card className="shadow-sm">
          <CardContent className="h-64 flex items-center justify-center">
            <div className="h-8 w-8 rounded-full border-2 border-foreground border-t-transparent animate-spin" />
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-6xl">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-xl font-semibold text-foreground">Models</h2>
          <p className="text-sm text-muted-foreground mt-1">Manage your fine-tuned models and base architectures.</p>
        </div>
        <Button size="sm" onClick={() => setIsImportOpen(true)}>
          <Plus className="w-4 h-4 mr-2" />
          Import Model
        </Button>
      </div>

      <Card className="shadow-sm border-border">
        {models.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-24 text-center">
            <div className="w-16 h-16 bg-secondary/50 rounded-full flex items-center justify-center mb-6 text-muted-foreground">
              <Box size={24} />
            </div>
            <h3 className="text-lg font-medium text-foreground mb-2">No models found</h3>
            <p className="text-sm text-muted-foreground mb-6 max-w-sm">
              You haven't trained or imported any models in this project yet. Start a new training job or import an existing model from the hub.
            </p>
            <Button variant="outline">
              Browse Model Hub
            </Button>
          </div>
        ) : (
          <div className="overflow-hidden rounded-md">
            <Table>
              <TableHeader className="bg-secondary/20">
                <TableRow>
                  <TableHead className="font-medium">Name</TableHead>
                  <TableHead className="font-medium">Base Model</TableHead>
                  <TableHead className="font-medium">Status</TableHead>
                  <TableHead className="font-medium">Created</TableHead>
                  <TableHead className="text-right font-medium">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {models.map((model: any) => {
                  const latestVersion = model.versions?.[0];
                  return (
                  <TableRow key={model.id} className="hover:bg-secondary/10 transition-colors">
                    <TableCell>
                      <div className="flex flex-col">
                        <span className="font-medium text-foreground">{model.name}</span>
                        <span className="text-xs text-muted-foreground">{model.id}</span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline" className="text-xs font-mono">{latestVersion?.base_model || 'Unknown'}</Badge>
                    </TableCell>
                    <TableCell>
                      <Badge variant="secondary" className="bg-success/10 text-success border-success/20 text-[10px]">
                        {latestVersion?.lifecycle_status || 'READY'}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {formatDistanceToNow(new Date(model.created_at || new Date()), { addSuffix: true })}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-2">
                        <Button 
                          variant="outline" 
                          size="sm" 
                          className="h-8 text-xs bg-primary text-primary-foreground hover:bg-primary/90 border-0"
                          onClick={() => {
                            setSelectedModel(model);
                            setIsDeployOpen(true);
                          }}
                        >
                          <Play className="w-3.5 h-3.5 mr-2" />
                          Deploy
                        </Button>
                        <Button variant="ghost" size="icon" className="h-8 w-8 text-muted-foreground">
                          <MoreHorizontal className="w-4 h-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </div>
        )}
      </Card>
      
      <ImportModelDialog 
        projectId={projectId} 
        isOpen={isImportOpen} 
        onClose={() => setIsImportOpen(false)} 
      />

      {selectedModel && (
        <StartDeploymentDialog
          projectId={projectId}
          modelId={selectedModel.id}
          isOpen={isDeployOpen}
          onClose={() => setIsDeployOpen(false)}
        />
      )}
    </div>
  );
}
