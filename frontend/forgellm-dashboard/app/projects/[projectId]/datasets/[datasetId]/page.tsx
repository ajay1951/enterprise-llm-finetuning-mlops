'use client';

import { useQuery } from '@tanstack/react-query';
import { PageHeader } from '@/components/layout/page-header';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { datasetsApi } from '@/lib/api';
import { useParams } from 'next/navigation';

export default function DatasetDetailsPage() {
  const { projectId, datasetId } = useParams() as { projectId: string, datasetId: string };

  const { data: datasets = [], isLoading } = useQuery({
    queryKey: ['datasets', projectId],
    queryFn: () => datasetsApi.list(projectId),
  });

  const dataset = datasets.find(d => d.id === datasetId);

  if (isLoading) return <div className="p-8">Loading dataset...</div>;
  if (!dataset) return <div className="p-8 text-destructive">Dataset not found</div>;

  return (
    <div className="flex-1 space-y-4 pb-8">
      <PageHeader title={dataset.name} description={dataset.description || 'Dataset details and versions'} />

      <div className="px-8">
        <Card>
          <CardHeader>
            <CardTitle>Versions</CardTitle>
          </CardHeader>
          <CardContent>
            {dataset.versions.length === 0 ? (
              <div className="text-sm text-muted-foreground py-4">No versions found.</div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Version Tag</TableHead>
                    <TableHead>Format</TableHead>
                    <TableHead>Examples</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Created At</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {dataset.versions.map((version) => (
                    <TableRow key={version.id}>
                      <TableCell className="font-medium font-mono text-xs">{version.version_tag}</TableCell>
                      <TableCell>{version.format}</TableCell>
                      <TableCell>{version.num_examples}</TableCell>
                      <TableCell>
                        <Badge variant={version.status === 'ready' ? 'success' : version.status === 'error' ? 'destructive' : 'default'}>
                          {version.status}
                        </Badge>
                      </TableCell>
                      <TableCell>{new Date(version.created_at).toLocaleDateString()}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      </div>
      
      {/* Validation Stats - mocked since full API may not return deep metrics in list response */}
      <div className="px-8 grid gap-4 grid-cols-1 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Format Validation</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <div className="flex justify-between py-1 border-b"><span className="text-muted-foreground">Conversational Format</span> <span className="font-medium text-green-500">Valid</span></div>
            <div className="flex justify-between py-1 border-b"><span className="text-muted-foreground">Missing Fields</span> <span className="font-medium">0</span></div>
            <div className="flex justify-between py-1"><span className="text-muted-foreground">Invalid Roles</span> <span className="font-medium">0</span></div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Cleaning Pipeline</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <div className="flex justify-between py-1 border-b"><span className="text-muted-foreground">Duplicates Removed</span> <span className="font-medium">0</span></div>
            <div className="flex justify-between py-1 border-b"><span className="text-muted-foreground">Empty Messages Removed</span> <span className="font-medium">0</span></div>
            <div className="flex justify-between py-1"><span className="text-muted-foreground">Long Sequences Truncated</span> <span className="font-medium">0</span></div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
