'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { PageHeader } from '@/components/layout/page-header';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import Link from 'next/link';

// Simple API wrapper
const fetchDeployments = async () => {
  const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/deployments`);
  if (!res.ok) throw new Error('Failed to fetch deployments');
  return res.json();
};

const stopDeployment = async (id: string) => {
  const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/deployments/${id}/stop`, { method: 'POST' });
  if (!res.ok) throw new Error('Failed to stop deployment');
  return res.json();
};

export default function DeploymentsPage() {
  const queryClient = useQueryClient();
  const { data: deployments, isLoading } = useQuery({
    queryKey: ['deployments'],
    queryFn: fetchDeployments,
    refetchInterval: 3000,
  });

  const stopMutation = useMutation({
    mutationFn: stopDeployment,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['deployments'] }),
  });

  return (
    <div className="flex-1 space-y-4 p-8 pt-6">
      <PageHeader title="Deployments" description="Manage your active model inference endpoints." />

      <Card>
        <CardHeader>
          <CardTitle>Active Deployments</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Deployment Name</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Health</TableHead>
                <TableHead>Backend</TableHead>
                <TableHead>Device</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                <TableRow>
                  <TableCell colSpan={6} className="text-center">Loading deployments...</TableCell>
                </TableRow>
              ) : deployments?.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} className="text-center text-muted-foreground">No deployments found.</TableCell>
                </TableRow>
              ) : (
                deployments?.map((deployment: any) => (
                  <TableRow key={deployment.id}>
                    <TableCell className="font-medium">
                      <Link href={`/deployments/${deployment.id}`} className="hover:underline text-primary">
                        {deployment.name}
                      </Link>
                    </TableCell>
                    <TableCell>
                      <Badge variant={
                        deployment.status === 'ready' ? 'success' : 
                        deployment.status === 'failed' ? 'destructive' : 
                        deployment.status === 'stopped' ? 'secondary' : 'default'
                      }>
                        {deployment.status.toUpperCase()}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge variant={deployment.health_status === 'healthy' ? 'success' : deployment.health_status === 'unhealthy' ? 'destructive' : 'secondary'}>
                        {deployment.health_status.toUpperCase()}
                      </Badge>
                    </TableCell>
                    <TableCell>{deployment.serving_backend}</TableCell>
                    <TableCell>{deployment.device}</TableCell>
                    <TableCell className="space-x-2">
                      <Link href={`/deployments/${deployment.id}`}>
                        <Button variant="outline" size="sm">View</Button>
                      </Link>
                      {['ready', 'starting', 'loading', 'queued'].includes(deployment.status) && (
                        <Button 
                          variant="destructive" 
                          size="sm"
                          onClick={() => {
                            if(confirm('Stop this deployment?')) stopMutation.mutate(deployment.id);
                          }}
                          disabled={stopMutation.isPending}
                        >
                          Stop
                        </Button>
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
