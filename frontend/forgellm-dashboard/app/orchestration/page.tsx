'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { PageHeader } from '@/components/layout/page-header';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { PlayCircle, StopCircle, RefreshCw, ArrowUpCircle } from 'lucide-react';

const fetchWorkloads = async () => {
  const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/workloads`);
  if (!res.ok) throw new Error('Failed to fetch workloads');
  return res.json();
};

const scaleWorkload = async ({id, replicas}: {id: string, replicas: number}) => {
  const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/workloads/${id}/scale`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ replicas })
  });
  if (!res.ok) throw new Error('Failed to scale');
  return res.json();
};

export default function OrchestrationPage() {
  const queryClient = useQueryClient();
  const { data: workloads, isLoading } = useQuery({
    queryKey: ['workloads'],
    queryFn: fetchWorkloads,
    refetchInterval: 3000,
  });

  const scaleMutation = useMutation({
    mutationFn: scaleWorkload,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['workloads'] }),
  });

  return (
    <div className="flex-1 space-y-4 p-8 pt-6">
      <PageHeader title="Production Orchestration" description="Manage active inference workloads, deployments, and autoscaling." />

      <Card>
        <CardHeader>
          <CardTitle>Active Workloads</CardTitle>
          <CardDescription>Zero-downtime rolling deployments across GPU pools.</CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Deployment Name</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Replicas (Active/Desired)</TableHead>
                <TableHead>Scaling</TableHead>
                <TableHead>Strategy</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                <TableRow>
                  <TableCell colSpan={6} className="text-center">Loading workloads...</TableCell>
                </TableRow>
              ) : workloads?.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} className="text-center text-muted-foreground">No workloads running.</TableCell>
                </TableRow>
              ) : (
                workloads?.map((w: any) => {
                  // Simplified display logic
                  const activeReplicas = w.replicas?.filter((r: any) => r.status === 'READY').length || 0;
                  return (
                  <TableRow key={w.id}>
                    <TableCell className="font-medium">{w.name}</TableCell>
                    <TableCell>
                      <Badge variant={w.status === 'READY' ? 'success' : 'default'}>
                        {w.status}
                      </Badge>
                    </TableCell>
                    <TableCell>
                       {activeReplicas} / {w.desired_replicas}
                    </TableCell>
                    <TableCell>
                      <div className="text-xs text-muted-foreground">
                        Min: {w.min_replicas} | Max: {w.max_replicas}
                      </div>
                    </TableCell>
                    <TableCell>{w.strategy}</TableCell>
                    <TableCell className="text-right space-x-2">
                       <Button 
                          variant="outline" size="sm"
                          onClick={() => scaleMutation.mutate({id: w.id, replicas: w.desired_replicas + 1})}
                          disabled={scaleMutation.isPending || w.desired_replicas >= w.max_replicas}
                       >
                         <ArrowUpCircle className="w-4 h-4 mr-1" /> Scale +1
                       </Button>
                       <Button 
                          variant="outline" size="sm"
                          onClick={() => scaleMutation.mutate({id: w.id, replicas: w.desired_replicas - 1})}
                          disabled={scaleMutation.isPending || w.desired_replicas <= w.min_replicas}
                       >
                         Scale -1
                       </Button>
                    </TableCell>
                  </TableRow>
                )})
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
