'use client';

import { useQuery } from '@tanstack/react-query';
import { PageHeader } from '@/components/layout/page-header';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';

// For simplicity, we just fetch workers and gpus directly instead of a dedicated endpoint
const fetchWorkers = async () => {
  const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/workers`);
  if (!res.ok) throw new Error('Failed to fetch workers');
  return res.json();
};

export default function SchedulerPage() {
  const { data: workers } = useQuery({
    queryKey: ['workers'],
    queryFn: fetchWorkers,
    refetchInterval: 3000,
  });

  // Calculate aggregates
  let availableGPUs = 0;
  let busyGPUs = 0;
  let offlineGPUs = 0;

  const allGPUs: any[] = [];

  if (workers) {
    workers.forEach((w: any) => {
      w.gpus?.forEach((g: any) => {
        allGPUs.push({...g, worker: w.worker_id, worker_status: w.status});
        if (w.status !== 'ONLINE') {
          offlineGPUs++;
        } else if (g.status === 'AVAILABLE') {
          availableGPUs++;
        } else {
          busyGPUs++;
        }
      });
    });
  }

  return (
    <div className="flex-1 space-y-4 p-8 pt-6">
      <PageHeader title="Scheduler overview" description="Global view of GPU cluster availability and active jobs." />

      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Available GPUs</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-500">{availableGPUs}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Busy / Allocated GPUs</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-500">{busyGPUs}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Offline / Draining GPUs</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-500">{offlineGPUs}</div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Global GPU Fleet</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>GPU UUID</TableHead>
                <TableHead>Worker</TableHead>
                <TableHead>Model</TableHead>
                <TableHead>VRAM</TableHead>
                <TableHead>Utilization</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Current Job</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {allGPUs.map((g: any) => (
                <TableRow key={g.uuid}>
                  <TableCell className="font-mono text-xs">{g.uuid.slice(-8)}</TableCell>
                  <TableCell>{g.worker}</TableCell>
                  <TableCell>{g.name}</TableCell>
                  <TableCell>{g.memory_used ? Math.round(g.memory_used) : 0} / {Math.round(g.memory_total)} MB</TableCell>
                  <TableCell>{g.utilization || 0}%</TableCell>
                  <TableCell>
                    {g.worker_status !== 'ONLINE' ? 'OFFLINE' : g.status}
                  </TableCell>
                  <TableCell className="font-mono text-xs">
                    {g.current_job_id || '-'}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
