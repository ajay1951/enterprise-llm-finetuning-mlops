'use client';

import { useQuery } from '@tanstack/react-query';
import { PageHeader } from '@/components/layout/page-header';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';

// Simplified fetch for autoscaling policies (we don't have a dedicated endpoint yet, we'll just mock or reuse workloads)
const fetchWorkloads = async () => {
  const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/workloads`);
  if (!res.ok) throw new Error('Failed to fetch workloads');
  return res.json();
};

export default function AutoscalingPage() {
  const { data: workloads, isLoading } = useQuery({
    queryKey: ['workloads'],
    queryFn: fetchWorkloads,
    refetchInterval: 3000,
  });

  return (
    <div className="flex-1 space-y-4 p-8 pt-6">
      <PageHeader title="Autoscaling Configuration" description="Manage traffic-based scaling policies and monitor scaling events." />

      <Card>
        <CardHeader>
          <CardTitle>Scaling Policies</CardTitle>
          <CardDescription>Policies attached to active workloads.</CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Workload</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Target Utilization</TableHead>
                <TableHead>Target Traffic</TableHead>
                <TableHead>Cooldown (Up/Down)</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                <TableRow>
                  <TableCell colSpan={5} className="text-center">Loading policies...</TableCell>
                </TableRow>
              ) : workloads?.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} className="text-center text-muted-foreground">No workloads configured.</TableCell>
                </TableRow>
              ) : (
                workloads?.map((w: any) => (
                  <TableRow key={w.id}>
                    <TableCell className="font-medium">{w.name}</TableCell>
                    <TableCell>Active</TableCell>
                    <TableCell>70% GPU</TableCell>
                    <TableCell>10 req/sec</TableCell>
                    <TableCell>60s / 300s</TableCell>
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
