'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { PageHeader } from '@/components/layout/page-header';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';

// API fetchers
const fetchWorkers = async () => {
  const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/workers`);
  if (!res.ok) throw new Error('Failed to fetch workers');
  return res.json();
};

const actionWorker = async ({id, action}: {id: string, action: string}) => {
  const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/workers/${id}/${action}`, { method: 'POST' });
  if (!res.ok) throw new Error(`Failed to ${action} worker`);
  return res.json();
};

export default function WorkersPage() {
  const queryClient = useQueryClient();
  const { data: workers, isLoading } = useQuery({
    queryKey: ['workers'],
    queryFn: fetchWorkers,
    refetchInterval: 5000,
  });

  const workerAction = useMutation({
    mutationFn: actionWorker,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['workers'] }),
  });

  return (
    <div className="flex-1 space-y-4 p-8 pt-6">
      <PageHeader title="Worker Fleet" description="Manage your distributed compute cluster." />

      <Card>
        <CardHeader>
          <CardTitle>Registered Workers</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>ID</TableHead>
                <TableHead>Hostname</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Hardware (CPU / RAM)</TableHead>
                <TableHead>GPUs</TableHead>
                <TableHead>Last Heartbeat</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                <TableRow>
                  <TableCell colSpan={8} className="text-center">Loading workers...</TableCell>
                </TableRow>
              ) : workers?.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={8} className="text-center text-muted-foreground">No workers registered.</TableCell>
                </TableRow>
              ) : (
                workers?.map((worker: any) => (
                  <TableRow key={worker.worker_id}>
                    <TableCell className="font-mono text-xs">{worker.worker_id}</TableCell>
                    <TableCell>{worker.hostname}</TableCell>
                    <TableCell>
                      <Badge variant={
                        worker.status === 'ONLINE' ? 'success' : 
                        worker.status === 'OFFLINE' ? 'destructive' : 
                        worker.status === 'DRAINING' ? 'secondary' : 'default'
                      }>
                        {worker.status}
                      </Badge>
                    </TableCell>
                    <TableCell>{worker.worker_type}</TableCell>
                    <TableCell>{worker.cpu_count} vCPUs / {Math.round(worker.ram_total)} GB</TableCell>
                    <TableCell>
                      {worker.gpus && worker.gpus.length > 0 ? (
                        <div className="flex flex-col gap-1 text-xs">
                           {worker.gpus.map((gpu: any, i: int) => (
                             <span key={i}>{gpu.name} ({Math.round(gpu.memory_total / 1024)}GB)</span>
                           ))}
                        </div>
                      ) : "CPU Only"}
                    </TableCell>
                    <TableCell>
                       {worker.last_heartbeat ? new Date(worker.last_heartbeat).toLocaleTimeString() : 'Never'}
                    </TableCell>
                    <TableCell className="space-x-2">
                      {worker.status === 'ONLINE' && (
                        <Button 
                          variant="outline" size="sm"
                          onClick={() => workerAction.mutate({id: worker.worker_id, action: 'drain'})}
                          disabled={workerAction.isPending}
                        >Drain</Button>
                      )}
                      {worker.status === 'DRAINING' && (
                        <Button 
                          variant="outline" size="sm"
                          onClick={() => workerAction.mutate({id: worker.worker_id, action: 'enable'})}
                          disabled={workerAction.isPending}
                        >Enable</Button>
                      )}
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
