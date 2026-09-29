'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { modelsApi } from '@/lib/api/experiments';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { useState } from 'react';
import { ShieldCheck, Database, History, ArrowRight, ShieldAlert } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog';

export function RegistryTab({ projectId }: { projectId: string }) {
  const queryClient = useQueryClient();
  const [promoteDialogOpen, setPromoteDialogOpen] = useState(false);
  const [selectedVersion, setSelectedVersion] = useState<any>(null);
  
  const { data: models = [], isLoading } = useQuery({
    queryKey: ['models', projectId],
    queryFn: () => modelsApi.list(projectId),
  });

  const promoteMutation = useMutation({
    mutationFn: async ({ modelId, versionId, target }: { modelId: string, versionId: string, target: string }) => {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/models/${modelId}/versions/${versionId}/promote`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ new_status: target, reason: 'Promoted via Registry UI' })
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Failed to promote');
      }
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['models', projectId] });
      setPromoteDialogOpen(false);
      setSelectedVersion(null);
    }
  });

  const archiveMutation = useMutation({
    mutationFn: async ({ modelId, versionId }: { modelId: string, versionId: string }) => {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/models/${modelId}/versions/${versionId}/archive`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reason: 'Archived via Registry UI' })
      });
      if (!res.ok) throw new Error('Failed to archive');
      return res.json();
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['models', projectId] })
  });

  const rollbackMutation = useMutation({
    mutationFn: async ({ modelId, versionId }: { modelId: string, versionId: string }) => {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/models/${modelId}/rollback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ target_version_id: versionId, reason: 'Rollback via Registry UI' })
      });
      if (!res.ok) throw new Error('Failed to rollback');
      return res.json();
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['models', projectId] })
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

  // Flatten versions
  const allVersions = models.flatMap((m: any) => 
    (m.versions || []).map((v: any) => ({ ...v, modelName: m.name }))
  ).sort((a: any, b: any) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());

  const getStatusColor = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'production': return 'bg-success/10 text-success border-success/20';
      case 'staging': return 'bg-blue-500/10 text-blue-500 border-blue-500/20';
      case 'archived': return 'bg-neutral-500/10 text-neutral-500 border-neutral-500/20';
      case 'rejected': return 'bg-destructive/10 text-destructive border-destructive/20';
      default: return 'bg-secondary/50 text-foreground border-border';
    }
  };

  const handlePromoteClick = (version: any) => {
    setSelectedVersion(version);
    setPromoteDialogOpen(true);
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-xl font-semibold text-foreground">Model Registry</h2>
          <p className="text-sm text-muted-foreground mt-1">Manage model lifecycles, quality gates, and deployments.</p>
        </div>
      </div>

      <Card className="shadow-sm border-border">
        {allVersions.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-24 text-center">
            <div className="w-16 h-16 bg-secondary/50 rounded-full flex items-center justify-center mb-6 text-muted-foreground">
              <Database size={24} />
            </div>
            <h3 className="text-lg font-medium text-foreground mb-2">Registry is empty</h3>
            <p className="text-sm text-muted-foreground mb-6 max-w-sm">
              No models have been trained and registered to the catalog yet.
            </p>
          </div>
        ) : (
          <div className="overflow-hidden rounded-md">
            <Table>
              <TableHeader className="bg-secondary/20">
                <TableRow>
                  <TableHead className="font-medium">Model & Version</TableHead>
                  <TableHead className="font-medium">Lifecycle</TableHead>
                  <TableHead className="font-medium">Quality Gate</TableHead>
                  <TableHead className="font-medium">Metrics</TableHead>
                  <TableHead className="font-medium">Created</TableHead>
                  <TableHead className="text-right font-medium">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {allVersions.map((v: any) => {
                  let qScore = null;
                  try {
                    if (v.quality_score) qScore = JSON.parse(v.quality_score);
                  } catch (e) {}

                  return (
                  <TableRow key={v.id} className="hover:bg-secondary/10 transition-colors">
                    <TableCell>
                      <div className="flex flex-col">
                        <span className="font-medium text-foreground">{v.modelName}</span>
                        <span className="text-xs text-muted-foreground font-mono">{v.version_tag}</span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline" className={`text-xs ${getStatusColor(v.lifecycle_status)}`}>
                        {v.lifecycle_status?.toUpperCase() || 'DEVELOPMENT'}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      {qScore ? (
                        qScore.passed ? 
                          <span className="flex items-center text-xs text-success"><ShieldCheck className="w-3.5 h-3.5 mr-1"/> Passed</span> :
                          <span className="flex items-center text-xs text-destructive"><ShieldAlert className="w-3.5 h-3.5 mr-1"/> Failed</span>
                      ) : (
                        <span className="text-xs text-muted-foreground">Pending</span>
                      )}
                    </TableCell>
                    <TableCell>
                       <div className="text-xs text-muted-foreground font-mono">
                          {v.training_run_id ? `Run: ${v.training_run_id.substring(0,8)}` : 'No run data'}
                       </div>
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {formatDistanceToNow(new Date(v.created_at || new Date()), { addSuffix: true })}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-2">
                        {v.lifecycle_status !== 'production' && (
                          <Button variant="outline" size="sm" className="h-8 text-xs" onClick={() => handlePromoteClick(v)}>
                            Promote <ArrowRight className="w-3 h-3 ml-1" />
                          </Button>
                        )}
                        {v.lifecycle_status === 'archived' && (
                          <Button variant="outline" size="sm" className="h-8 text-xs" onClick={() => rollbackMutation.mutate({ modelId: v.model_id, versionId: v.id })}>
                            Rollback
                          </Button>
                        )}
                        {v.lifecycle_status !== 'archived' && v.lifecycle_status !== 'production' && (
                          <Button variant="ghost" size="sm" className="h-8 text-xs text-destructive" onClick={() => archiveMutation.mutate({ modelId: v.model_id, versionId: v.id })}>
                            Archive
                          </Button>
                        )}
                      </div>
                    </TableCell>
                  </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </div>
        )}
      </Card>

      <Dialog open={promoteDialogOpen} onOpenChange={setPromoteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Promote Model Version</DialogTitle>
            <DialogDescription>
              Move {selectedVersion?.modelName} ({selectedVersion?.version_tag}) to the next lifecycle stage.
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
             <p className="text-sm">Current Status: <strong>{selectedVersion?.lifecycle_status || 'development'}</strong></p>
          </div>
          <DialogFooter className="flex gap-2">
            <Button variant="outline" onClick={() => setPromoteDialogOpen(false)}>Cancel</Button>
            {selectedVersion?.lifecycle_status === 'development' && (
              <Button 
                onClick={() => promoteMutation.mutate({ modelId: selectedVersion.model_id, versionId: selectedVersion.id, target: 'staging' })}
                disabled={promoteMutation.isPending}
              >
                Promote to Staging
              </Button>
            )}
            {selectedVersion?.lifecycle_status === 'staging' && (
              <Button 
                onClick={() => promoteMutation.mutate({ modelId: selectedVersion.model_id, versionId: selectedVersion.id, target: 'production' })}
                disabled={promoteMutation.isPending}
              >
                Promote to Production
              </Button>
            )}
            {promoteMutation.isError && (
               <p className="text-destructive text-sm mt-2">{promoteMutation.error.message}</p>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
