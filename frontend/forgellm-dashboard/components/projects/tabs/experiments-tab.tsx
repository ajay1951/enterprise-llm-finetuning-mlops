import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { experimentsApi } from '@/lib/api/experiments';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Beaker, Plus, ActivitySquare, Play, Pause, Trash2 } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { useState } from 'react';
import { StartExperimentDialog } from './start-experiment-dialog';

export function ExperimentsTab({ projectId }: { projectId: string }) {
  const queryClient = useQueryClient();
  const [isStartOpen, setIsStartOpen] = useState(false);

  const { data: experiments = [], isLoading } = useQuery({
    queryKey: ['experiments', projectId],
    queryFn: () => experimentsApi.list(projectId),
    refetchInterval: 5000,
  });

  const startMutation = useMutation({
    mutationFn: (id: string) => experimentsApi.start(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['experiments', projectId] })
  });

  const pauseMutation = useMutation({
    mutationFn: (id: string) => experimentsApi.pause(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['experiments', projectId] })
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => experimentsApi.delete(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['experiments', projectId] })
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
      case 'COMPLETED':
        return <Badge className="bg-success/10 text-success border-success/20 text-[10px]">COMPLETED</Badge>;
      case 'RUNNING':
        return <Badge className="bg-primary/10 text-primary border-primary/20 text-[10px] animate-pulse">RUNNING</Badge>;
      case 'FAILED':
        return <Badge className="bg-destructive/10 text-destructive border-destructive/20 text-[10px]">FAILED</Badge>;
      case 'PAUSED':
        return <Badge className="bg-warning/10 text-warning border-warning/20 text-[10px]">PAUSED</Badge>;
      default:
        return <Badge variant="outline" className="text-[10px]">{status || 'PENDING'}</Badge>;
    }
  };

  return (
    <div className="space-y-6 max-w-6xl">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-xl font-semibold text-foreground">Experiments</h2>
          <p className="text-sm text-muted-foreground mt-1">Compare model evaluations and benchmark scores.</p>
        </div>
        <Button size="sm" onClick={() => setIsStartOpen(true)}>
          <Plus className="w-4 h-4 mr-2" />
          New Experiment
        </Button>
      </div>

      <Card className="shadow-sm border-border">
        {experiments.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-24 text-center">
            <div className="w-16 h-16 bg-secondary/50 rounded-full flex items-center justify-center mb-6 text-muted-foreground">
              <Beaker size={24} />
            </div>
            <h3 className="text-lg font-medium text-foreground mb-2">No experiments found</h3>
            <p className="text-sm text-muted-foreground mb-6 max-w-sm">
              You haven't run any evaluations yet. Start an experiment to compare your fine-tuned models against baselines.
            </p>
            <Button variant="outline" onClick={() => setIsStartOpen(true)}>
              New Experiment
            </Button>
          </div>
        ) : (
          <div className="overflow-hidden rounded-md">
            <Table>
              <TableHeader className="bg-secondary/20">
                <TableRow>
                  <TableHead className="font-medium">Experiment Name</TableHead>
                  <TableHead className="font-medium">Status</TableHead>
                  <TableHead className="text-right font-medium">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {/* @ts-ignore */}
                {experiments.map((exp: any) => (
                  <TableRow key={exp.id} className="hover:bg-secondary/10 transition-colors">
                    <TableCell>
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-md bg-secondary flex items-center justify-center text-muted-foreground">
                          <ActivitySquare size={16} />
                        </div>
                        <div className="flex flex-col">
                          <span className="font-medium text-foreground">{exp.name || 'Unnamed Eval'}</span>
                          <span className="text-xs text-muted-foreground font-mono mt-1">
                            {exp.id}
                          </span>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      {getStatusBadge(exp.status)}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-1">
                        {exp.status !== 'RUNNING' && (
                          <Button 
                            variant="ghost" 
                            size="icon" 
                            className="h-8 w-8 text-success hover:text-success/80 hover:bg-success/10"
                            onClick={() => startMutation.mutate(exp.id)}
                            title="Start Experiment"
                          >
                            <Play className="w-4 h-4" />
                          </Button>
                        )}
                        {exp.status === 'RUNNING' && (
                          <Button 
                            variant="ghost" 
                            size="icon" 
                            className="h-8 w-8 text-warning hover:text-warning/80 hover:bg-warning/10"
                            onClick={() => pauseMutation.mutate(exp.id)}
                            title="Pause Experiment"
                          >
                            <Pause className="w-4 h-4" />
                          </Button>
                        )}
                        <Button 
                          variant="ghost" 
                          size="icon" 
                          className="h-8 w-8 text-destructive hover:text-destructive/80 hover:bg-destructive/10"
                          onClick={() => {
                            if (confirm('Delete this experiment?')) deleteMutation.mutate(exp.id);
                          }}
                          title="Delete Experiment"
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

      <StartExperimentDialog 
        projectId={projectId} 
        isOpen={isStartOpen} 
        onClose={() => setIsStartOpen(false)} 
      />
    </div>
  );
}
