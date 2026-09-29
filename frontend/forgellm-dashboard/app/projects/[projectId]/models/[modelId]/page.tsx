'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { PageHeader } from '@/components/layout/page-header';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { modelsApi, evaluationsApi, datasetsApi } from '@/lib/api';
import { useParams } from 'next/navigation';
import Link from 'next/link';

export default function ModelDetailsPage() {
  const { projectId, modelId } = useParams() as { projectId: string, modelId: string };
  const queryClient = useQueryClient();
  const [isEvaluating, setIsEvaluating] = useState(false);
  const [isDeploying, setIsDeploying] = useState(false);
  const [selectedDataset, setSelectedDataset] = useState('');
  
  // Deployment state
  const [deployName, setDeployName] = useState('');
  const [deployDevice, setDeployDevice] = useState('cuda');
  const [deployBackend, setDeployBackend] = useState('transformers');
  const [deployMaxContext, setDeployMaxContext] = useState(4096);
  const [deployMaxTokens, setDeployMaxTokens] = useState(512);

  const { data: model, isLoading } = useQuery({
    queryKey: ['models', modelId],
    queryFn: () => modelsApi.get(modelId),
  });

  const { data: datasets = [] } = useQuery({
    queryKey: ['datasets', projectId],
    queryFn: () => datasetsApi.list(projectId),
  });

  const { data: allEvaluations = [] } = useQuery({
    queryKey: ['evaluations', projectId],
    queryFn: () => evaluationsApi.list(projectId),
  });

  const evaluateMutation = useMutation({
    mutationFn: () => evaluationsApi.create(modelId, selectedDataset),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['evaluations', projectId] });
      setIsEvaluating(false);
      setSelectedDataset('');
    },
  });

  const deployMutation = useMutation({
    mutationFn: async () => {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/projects/${projectId}/deployments`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model_version_id: modelId,
          name: deployName || `${model?.name}-prod`,
          backend: deployBackend,
          device: deployDevice,
          configuration: {
            max_model_len: deployMaxContext,
            max_new_tokens: deployMaxTokens,
            temperature: 0.7
          }
        })
      });
      if (!res.ok) throw new Error(await res.text());
      return res.json();
    },
    onSuccess: () => {
      setIsDeploying(false);
      alert('Deployment created successfully! Go to the Deployments tab to start it.');
    },
    onError: (err: any) => {
      alert(`Failed to deploy: ${err.message}`);
    }
  });

  const modelEvaluations = allEvaluations.filter(e => e.model_id === modelId);

  if (isLoading) return <div className="p-8">Loading model...</div>;
  if (!model) return <div className="p-8 text-destructive">Model not found</div>;

  return (
    <div className="flex-1 space-y-4 pb-8">
      <PageHeader title={model.name} description={`Version: ${model.version}`}>
        <div className="flex space-x-2">
          <Button onClick={() => setIsDeploying(true)} variant="default">Deploy Model</Button>
          <Link href={`/projects/${projectId}/models/${model.id}/playground`}>
            <Button variant="outline">Local Playground</Button>
          </Link>
        </div>
      </PageHeader>

      <div className="px-8 grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Status</CardTitle>
          </CardHeader>
          <CardContent>
            <Badge variant={model.status === 'ready' ? 'success' : 'default'}>
              {model.status.toUpperCase()}
            </Badge>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Path</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-sm font-mono truncate" title={model.path}>{model.path}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Created</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-sm">{new Date(model.created_at).toLocaleString()}</div>
          </CardContent>
        </Card>
      </div>

      {isEvaluating && (
        <div className="px-8 mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Run Evaluation</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4 max-w-md">
                <div>
                  <label className="block text-sm font-medium mb-1">Select Validation Dataset</label>
                  <select 
                    className="w-full rounded-md border bg-background px-3 py-2 text-sm"
                    value={selectedDataset}
                    onChange={(e) => setSelectedDataset(e.target.value)}
                  >
                    <option value="">Select a dataset version...</option>
                    {datasets.map(d => 
                      d.versions.map(v => (
                        <option key={v.id} value={v.id}>{d.name} ({v.version_tag})</option>
                      ))
                    )}
                  </select>
                </div>
                <div className="flex space-x-2">
                  <Button variant="outline" onClick={() => setIsEvaluating(false)}>Cancel</Button>
                  <Button 
                    onClick={() => evaluateMutation.mutate()} 
                    disabled={!selectedDataset || evaluateMutation.isPending}
                  >
                    {evaluateMutation.isPending ? 'Starting...' : 'Start Evaluation'}
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {isDeploying && (
        <div className="px-8 mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Deploy Model</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <label className="text-sm font-medium">Deployment Name</label>
                  <input 
                    type="text" 
                    className="w-full rounded-md border bg-background px-3 py-2 text-sm"
                    placeholder={`${model.name}-prod`}
                    value={deployName}
                    onChange={(e) => setDeployName(e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Hardware / Device</label>
                  <select 
                    className="w-full rounded-md border bg-background px-3 py-2 text-sm"
                    value={deployDevice}
                    onChange={(e) => setDeployDevice(e.target.value)}
                  >
                    <option value="cuda">GPU (cuda)</option>
                    <option value="cpu">CPU (slower)</option>
                  </select>
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Serving Backend</label>
                  <select 
                    className="w-full rounded-md border bg-background px-3 py-2 text-sm"
                    value={deployBackend}
                    onChange={(e) => setDeployBackend(e.target.value)}
                  >
                    <option value="transformers">Transformers (Compatible)</option>
                    <option value="vllm" disabled>vLLM (Coming soon)</option>
                  </select>
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Max Context Length</label>
                  <input 
                    type="number" 
                    className="w-full rounded-md border bg-background px-3 py-2 text-sm"
                    value={deployMaxContext}
                    onChange={(e) => setDeployMaxContext(parseInt(e.target.value))}
                  />
                </div>
              </div>
              <div className="flex space-x-2 mt-6">
                <Button variant="outline" onClick={() => setIsDeploying(false)}>Cancel</Button>
                <Button onClick={() => deployMutation.mutate()} disabled={deployMutation.isPending}>
                  {deployMutation.isPending ? 'Deploying...' : 'Create Deployment'}
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      <div className="px-8 mt-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>Evaluation Results</CardTitle>
            {!isEvaluating && (
              <Button variant="outline" size="sm" onClick={() => setIsEvaluating(true)}>
                Run Evaluation
              </Button>
            )}
          </CardHeader>
          <CardContent>
            {modelEvaluations.length === 0 ? (
              <div className="text-sm text-muted-foreground py-4 text-center">
                No evaluation results yet. Run an evaluation to benchmark this model.
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Eval ID</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Metrics</TableHead>
                    <TableHead>Created At</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {modelEvaluations.map(evalRun => (
                    <TableRow key={evalRun.id}>
                      <TableCell className="font-mono text-xs">{evalRun.id.slice(0, 8)}</TableCell>
                      <TableCell>
                        <Badge variant={evalRun.status === 'completed' ? 'success' : 'default'}>
                          {evalRun.status}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <div className="flex flex-col gap-1 text-xs font-mono">
                          {Object.entries(evalRun.metrics || {}).map(([k, v]) => (
                            <span key={k}>{k}: {String(v)}</span>
                          ))}
                          {Object.keys(evalRun.metrics || {}).length === 0 && <span className="text-muted-foreground">Pending</span>}
                        </div>
                      </TableCell>
                      <TableCell>{new Date(evalRun.created_at).toLocaleString()}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
