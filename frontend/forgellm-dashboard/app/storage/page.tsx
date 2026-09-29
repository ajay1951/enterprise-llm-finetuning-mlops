'use client';

import { useQuery } from '@tanstack/react-query';
import { PageHeader } from '@/components/layout/page-header';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';

// For simplicity, we just fetch projects, then their artifacts
const fetchProjects = async () => {
  const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/projects/`);
  if (!res.ok) throw new Error('Failed to fetch projects');
  return res.json();
};

const fetchArtifacts = async (projectId: string) => {
  const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/projects/${projectId}/artifacts`);
  if (!res.ok) throw new Error('Failed to fetch artifacts');
  return res.json();
};

export default function StoragePage() {
  const { data: projects } = useQuery({
    queryKey: ['projects'],
    queryFn: fetchProjects,
  });

  // Simple sequential fetch for demonstration
  const allArtifacts: any[] = []; // In a real app we'd use useQueries or a backend aggregation

  return (
    <div className="flex-1 space-y-4 p-8 pt-6">
      <PageHeader title="Artifact Storage" description="Manage datasets, model weights, and checkpoints in S3/MinIO." />

      <Card>
        <CardHeader>
          <CardTitle>Global Artifact Registry</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>URI</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Project</TableHead>
                <TableHead>Size</TableHead>
                <TableHead>Provider</TableHead>
                <TableHead>Created</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
                <TableRow>
                  <TableCell colSpan={6} className="text-center text-muted-foreground">Select a project to view its artifacts</TableCell>
                </TableRow>
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
