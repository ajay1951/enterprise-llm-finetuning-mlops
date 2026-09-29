import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { trainingApi } from '@/lib/api/training';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { useState } from 'react';
import { Activity, Plus, TerminalSquare, XCircle, Trash2 } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { StartTrainingDialog } from './start-training-dialog';
import { LogsDialog } from './logs-dialog';

export function TrainingTab({ projectId }: { projectId: string }) {
  const queryClient = useQueryClient();
  const [isStartOpen, setIsStartOpen] = useState(false);
  const [logsJobId, setLogsJobId] = useState<string | null>(null);

  const { data: jobs = [], isLoading } = useQuery({
    queryKey: ['trainingJobs', projectId],
    queryFn: () => trainingApi.list(projectId),
    refetchInterval: 5000,
  });

  const cancelMutation = useMutation({
    mutationFn: (jobId: string) => trainingApi.cancel(jobId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['trainingJobs', projectId] });
    }
  });

  const deleteMutation = useMutation({
    mutationFn: (jobId: string) => trainingApi.delete(jobId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['trainingJobs', projectId] });
    }
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
    switch (status) {
      case 'COMPLETED':
        return <Badge className="bg-success/10 text-success border-success/20 text-[10px]">COMPLETED</Badge>;
      case 'RUNNING':
        return <Badge className="bg-primary/10 text-primary border-primary/20 text-[10px] animate-pulse">RUNNING</Badge>;
      case 'FAILED':
        return <Badge className="bg-destructive/10 text-destructive border-destructive/20 text-[10px]">FAILED</Badge>;
      case 'CANCEL_REQUESTED':
        return <Badge className="bg-warning/10 text-warning border-warning/20 text-[10px] animate-pulse">CANCELLING</Badge>;
      default:
        return <Badge variant="outline" className="text-[10px]">{status}</Badge>;
    }
  };

  return (
    <div className="space-y-6 max-w-6xl">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-xl font-semibold text-foreground">Training Jobs</h2>
          <p className="text-sm text-muted-foreground mt-1">Monitor and manage fine-tuning workloads.</p>
        </div>
        <Button size="sm" onClick={() => setIsStartOpen(true)}>
          <Plus className="w-4 h-4 mr-2" />
          Start Fine-Tuning
        </Button>
      </div>

      <Card className="shadow-sm border-border">
        {jobs.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-24 text-center">
            <div className="w-16 h-16 bg-secondary/50 rounded-full flex items-center justify-center mb-6 text-muted-foreground">
              <Activity size={24} />
            </div>
            <h3 className="text-lg font-medium text-foreground mb-2">No training jobs</h3>
            <p className="text-sm text-muted-foreground mb-6 max-w-sm">
              You haven't started any fine-tuning jobs yet. Select a base model and a dataset to begin training.
            </p>
            <Button variant="outline" onClick={() => setIsStartOpen(true)}>
              Start a Job
            </Button>
          </div>
        ) : (
          <div className="overflow-hidden rounded-md">
            <Table>
              <TableHeader className="bg-secondary/20">
                <TableRow>
                  <TableHead className="font-medium">Model Name</TableHead>
                  <TableHead className="font-medium">Method</TableHead>
                  <TableHead className="font-medium">Status</TableHead>
                  <TableHead className="font-medium">Progress</TableHead>
                  <TableHead className="text-right font-medium">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {/* @ts-ignore */}
                {jobs.map((job: any) => (
                  <TableRow key={job.id} className="hover:bg-secondary/10 transition-colors">
                    <TableCell>
                      <div className="flex flex-col">
                        <span className="font-medium text-foreground">{job.model_name}</span>
                        <span className="text-xs text-muted-foreground">{formatDistanceToNow(new Date(job.created_at || new Date()), { addSuffix: true })}</span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline" className="text-xs font-mono">{job.method || 'LORA'}</Badge>
                    </TableCell>
                    <TableCell>
                      {getStatusBadge(job.status?.toUpperCase() || 'PENDING')}
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <div className="w-24 h-1.5 rounded-full bg-secondary overflow-hidden">
                          <div 
                            className="h-full bg-primary" 
                            style={{ width: `${job.total_steps ? Math.min(100, (job.current_step / job.total_steps) * 100) : 0}%` }}
                          />
                        </div>
                        <span className="text-xs font-mono text-muted-foreground">
                          {job.current_step || 0}/{job.total_steps || '-'}
                        </span>
                      </div>
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-1">
                        <Button 
                          variant="ghost" 
                          size="icon" 
                          className="h-8 w-8 text-muted-foreground hover:text-foreground"
                          onClick={() => setLogsJobId(job.id)}
                          title="View Logs"
                        >
                          <TerminalSquare className="w-4 h-4" />
                        </Button>
                        
                        {['queued', 'running'].includes(job.status) && (
                          <Button 
                            variant="ghost" 
                            size="icon" 
                            className="h-8 w-8 text-warning hover:text-warning/80 hover:bg-warning/10"
                            onClick={() => {
                              if (confirm('Cancel this training job?')) cancelMutation.mutate(job.id);
                            }}
                            title="Cancel Job"
                          >
                            <XCircle className="w-4 h-4" />
                          </Button>
                        )}

                        {!['running', 'cancel_requested'].includes(job.status) && (
                          <Button 
                            variant="ghost" 
                            size="icon" 
                            className="h-8 w-8 text-destructive hover:text-destructive/80 hover:bg-destructive/10"
                            onClick={() => {
                              if (confirm('Delete this job record permanently?')) deleteMutation.mutate(job.id);
                            }}
                            title="Delete Job"
                          >
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        )}
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </Card>
      
      <StartTrainingDialog 
        projectId={projectId} 
        isOpen={isStartOpen} 
        onClose={() => setIsStartOpen(false)} 
      />

      <LogsDialog 
        jobId={logsJobId} 
        isOpen={!!logsJobId} 
        onClose={() => setLogsJobId(null)} 
      />
    </div>
  );
}
