import { useQuery } from '@tanstack/react-query';
import { datasetsApi } from '@/lib/api/datasets';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { useState } from 'react';
import { Database, Plus, MoreHorizontal, FileText } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { UploadDatasetDialog } from './upload-dataset-dialog';

export function DatasetsTab({ projectId }: { projectId: string }) {
  const [isUploadOpen, setIsUploadOpen] = useState(false);

  const { data: datasets = [], isLoading } = useQuery({
    queryKey: ['datasets', projectId],
    queryFn: () => datasetsApi.list(projectId),
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

  return (
    <div className="space-y-6 max-w-6xl">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-xl font-semibold text-foreground">Datasets</h2>
          <p className="text-sm text-muted-foreground mt-1">Manage data for fine-tuning and evaluation.</p>
        </div>
        <Button size="sm" onClick={() => setIsUploadOpen(true)}>
          <Plus className="w-4 h-4 mr-2" />
          Upload Dataset
        </Button>
      </div>

      <Card className="shadow-sm border-border">
        {datasets.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-24 text-center">
            <div className="w-16 h-16 bg-secondary/50 rounded-full flex items-center justify-center mb-6 text-muted-foreground">
              <Database size={24} />
            </div>
            <h3 className="text-lg font-medium text-foreground mb-2">No datasets found</h3>
            <p className="text-sm text-muted-foreground mb-6 max-w-sm">
              You haven't uploaded any training or evaluation datasets. Upload a CSV or JSONL file to get started.
            </p>
            <Button variant="outline" onClick={() => setIsUploadOpen(true)}>
              Upload Data
            </Button>
          </div>
        ) : (
          <div className="overflow-hidden rounded-md">
            <Table>
              <TableHeader className="bg-secondary/20">
                <TableRow>
                  <TableHead className="font-medium">Name</TableHead>
                  <TableHead className="font-medium">Description</TableHead>
                  <TableHead className="font-medium">Created</TableHead>
                  <TableHead className="text-right font-medium">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {datasets.map((ds: any) => (
                  <TableRow key={ds.id} className="hover:bg-secondary/10 transition-colors">
                    <TableCell>
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-md bg-secondary flex items-center justify-center text-muted-foreground">
                          <FileText size={16} />
                        </div>
                        <div className="flex flex-col">
                          <span className="font-medium text-foreground">{ds.name}</span>
                          <span className="text-xs text-muted-foreground">{ds.id}</span>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground max-w-xs truncate">
                      {ds.description || 'No description provided'}
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {formatDistanceToNow(new Date(ds.created_at || new Date()), { addSuffix: true })}
                    </TableCell>
                    <TableCell className="text-right">
                      <Button variant="ghost" size="icon" className="h-8 w-8 text-muted-foreground">
                        <MoreHorizontal className="w-4 h-4" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </Card>

      <UploadDatasetDialog 
        projectId={projectId} 
        isOpen={isUploadOpen} 
        onClose={() => setIsUploadOpen(false)} 
      />
    </div>
  );
}
