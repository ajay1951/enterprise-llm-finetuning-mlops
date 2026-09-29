import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { deploymentsApi } from '@/lib/api';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Play, Plus, Server, Pause, Trash2, RefreshCw, Terminal } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { useState } from 'react';
import { StartDeploymentDialog } from './start-deployment-dialog';
import { DeploymentLogsDialog } from './deployment-logs-dialog';

export function DeploymentsTab({ projectId }: { projectId: string }) {
  const queryClient = useQueryClient();
  const [isStartOpen, setIsStartOpen] = useState(false);
  const [logsDeploymentId, setLogsDeploymentId] = useState<string | null>(null);

  const { data: deployments = [], isLoading } = useQuery({
    queryKey: ['deployments', projectId],
    queryFn: () => deploymentsApi.list(projectId),
    refetchInterval: 5000,
  });

  const startMutation = useMutation({
    mutationFn: (id: string) => deploymentsApi.start(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['deployments', projectId] })
  });

  const stopMutation = useMutation({
    mutationFn: (id: string) => deploymentsApi.stop(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['deployments', projectId] })
  });

  const restartMutation = useMutation({
    mutationFn: (id: string) => deploymentsApi.restart(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['deployments', projectId] })
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => deploymentsApi.delete(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['deployments', projectId] })
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

  const getStatusBadge = (status: string) => {
    switch (status?.toUpperCase()) {
      case 'RUNNING':
        return <Badge className="bg-success/10 text-success border-success/20 text-[10px] animate-pulse">RUNNING</Badge>;
      case 'STOPPED':
        return <Badge className="bg-secondary/20 text-muted-foreground border-border text-[10px]">STOPPED</Badge>;
      case 'FAILED':
        return <Badge className="bg-destructive/10 text-destructive border-destructive/20 text-[10px]">FAILED</Badge>;
      default:
        return <Badge variant="outline" className="text-[10px]">{status || 'UNKNOWN'}</Badge>;
    }
  };

  return (
    <div className="space-y-6 max-w-6xl">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-xl font-semibold text-foreground">Deployments</h2>
          <p className="text-sm text-muted-foreground mt-1">Manage active model API endpoints.</p>
        </div>
        <Button size="sm" onClick={() => setIsStartOpen(true)}>
          <Plus className="w-4 h-4 mr-2" />
          New Deployment
        </Button>
      </div>

      <Card className="shadow-sm border-border">
        {deployments.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-24 text-center">
            <div className="w-16 h-16 bg-secondary/50 rounded-full flex items-center justify-center mb-6 text-muted-foreground">
              <Play size={24} />
            </div>
            <h3 className="text-lg font-medium text-foreground mb-2">No active deployments</h3>
            <p className="text-sm text-muted-foreground mb-6 max-w-sm">
              You haven't deployed any models yet. Start a new deployment to query your model.
            </p>
            <Button variant="outline" onClick={() => setIsStartOpen(true)}>
              New Deployment
            </Button>
          </div>
        ) : (
          <div className="overflow-hidden rounded-md">
            <Table>
              <TableHeader className="bg-secondary/20">
                <TableRow>
                  <TableHead className="font-medium">Deployment Name</TableHead>
                  <TableHead className="font-medium">Model ID</TableHead>
                  <TableHead className="font-medium">Status</TableHead>
                  <TableHead className="font-medium">Endpoint</TableHead>
                  <TableHead className="text-right font-medium">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {deployments.map((dep: any) => (
                  <TableRow key={dep.id} className="hover:bg-secondary/10 transition-colors">
                    <TableCell>
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-md bg-secondary flex items-center justify-center text-muted-foreground">
                          <Server size={16} />
                        </div>
                        <div className="flex flex-col">
                          <span className="font-medium text-foreground">{dep.name || 'Unnamed Deployment'}</span>
                          <span className="text-xs text-muted-foreground">
                            {formatDistanceToNow(new Date(dep.created_at || new Date()), { addSuffix: true })}
                          </span>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell className="text-sm font-mono text-muted-foreground">
                      {dep.model_id?.substring(0,8) || '-'}
                    </TableCell>
                    <TableCell>
                      {getStatusBadge(dep.status)}
                    </TableCell>
                    <TableCell className="text-sm font-mono text-muted-foreground">
                      {dep.port ? `localhost:${dep.port}` : '-'}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-1">
                        {dep.status !== 'RUNNING' && (
                          <Button 
                            variant="ghost" 
                            size="icon" 
                            className="h-8 w-8 text-success hover:text-success/80 hover:bg-success/10"
                            onClick={() => startMutation.mutate(dep.id)}
                            title="Start Deployment"
                          >
                            <Play className="w-4 h-4" />
                          </Button>
                        )}
                        {dep.status === 'RUNNING' && (
                          <Button 
                            variant="ghost" 
                            size="icon" 
                            className="h-8 w-8 text-warning hover:text-warning/80 hover:bg-warning/10"
                            onClick={() => stopMutation.mutate(dep.id)}
                            title="Stop Deployment"
                          >
                            <Pause className="w-4 h-4" />
                          </Button>
                        )}
                        {dep.status === 'RUNNING' && (
                          <Button 
                            variant="ghost" 
                            size="icon" 
                            className="h-8 w-8 text-primary hover:text-primary/80 hover:bg-primary/10"
                            onClick={() => restartMutation.mutate(dep.id)}
                            title="Restart Deployment"
                          >
                            <RefreshCw className="w-4 h-4" />
                          </Button>
                        )}
                        <Button 
                          variant="ghost" 
                          size="icon" 
                          className="h-8 w-8 text-muted-foreground hover:text-foreground hover:bg-secondary/50"
                          onClick={() => setLogsDeploymentId(dep.id)}
                          title="View Logs"
                        >
                          <Terminal className="w-4 h-4" />
                        </Button>
                        <Button 
                          variant="ghost" 
                          size="icon" 
                          className="h-8 w-8 text-destructive hover:text-destructive/80 hover:bg-destructive/10"
                          onClick={() => {
                            if (confirm('Delete this deployment?')) deleteMutation.mutate(dep.id);
                          }}
                          title="Delete Deployment"
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </Card>
      
      <StartDeploymentDialog
        projectId={projectId}
        isOpen={isStartOpen}
        onClose={() => setIsStartOpen(false)}
      />
      
      <DeploymentLogsDialog
        deploymentId={logsDeploymentId}
        isOpen={!!logsDeploymentId}
        onClose={() => setLogsDeploymentId(null)}
      />
    </div>
  );
}
