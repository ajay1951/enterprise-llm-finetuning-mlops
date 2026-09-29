'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { PageHeader } from '@/components/layout/page-header';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { datasetsApi, trainingApi } from '@/lib/api';
import { useParams, useRouter } from 'next/navigation';

export default function NewTrainingJobPage() {
  const { projectId } = useParams() as { projectId: string };
  const router = useRouter();
  const queryClient = useQueryClient();

  const [datasetVersionId, setDatasetVersionId] = useState('');
  const [modelName, setModelName] = useState('Qwen/Qwen2.5-0.5B');
  const [method, setMethod] = useState('qlora');
  const [epochs, setEpochs] = useState(3);
  const [learningRate, setLearningRate] = useState(0.0002);
  const [loraRank, setLoraRank] = useState(8);

  const { data: datasets = [], isLoading: loadingDatasets } = useQuery({
    queryKey: ['datasets', projectId],
    queryFn: () => datasetsApi.list(projectId),
  });

  const createMutation = useMutation({
    mutationFn: () => trainingApi.create(projectId, {
      dataset_version_id: datasetVersionId,
      model_name: modelName,
      method,
      epochs,
      learning_rate: learningRate,
      lora_rank: loraRank,
    }),
    onSuccess: (job) => {
      queryClient.invalidateQueries({ queryKey: ['trainingJobs', projectId] });
      router.push(`/projects/${projectId}/training/${job.id}`);
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!datasetVersionId || !modelName || !method) return;
    createMutation.mutate();
  };

  return (
    <div className="flex-1 space-y-4 pb-8">
      <PageHeader title="New Training Job" description="Configure and start a new fine-tuning job." />

      <div className="px-8 max-w-3xl">
        <Card>
          <CardHeader>
            <CardTitle>Configuration Wizard</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-6">
              
              <div className="space-y-4 border-b pb-4">
                <h3 className="font-medium text-lg">1. Dataset</h3>
                {loadingDatasets ? (
                  <p className="text-sm text-muted-foreground">Loading datasets...</p>
                ) : (
                  <div>
                    <label className="block text-sm font-medium mb-1">Select Dataset Version</label>
                    <select 
                      className="w-full rounded-md border bg-background px-3 py-2 text-sm"
                      value={datasetVersionId}
                      onChange={(e) => setDatasetVersionId(e.target.value)}
                      required
                    >
                      <option value="">Select a dataset version...</option>
                      {datasets.map(d => 
                        d.versions.map(v => (
                          <option key={v.id} value={v.id}>{d.name} ({v.version_tag})</option>
                        ))
                      )}
                    </select>
                  </div>
                )}
              </div>

              <div className="space-y-4 border-b pb-4">
                <h3 className="font-medium text-lg">2. Base Model</h3>
                <div>
                  <label className="block text-sm font-medium mb-1">Model Name</label>
                  <select 
                    className="w-full rounded-md border bg-background px-3 py-2 text-sm"
                    value={modelName}
                    onChange={(e) => setModelName(e.target.value)}
                  >
                    <option value="Qwen/Qwen2.5-0.5B">Qwen/Qwen2.5-0.5B</option>
                    <option value="Qwen/Qwen-1_8B">Qwen/Qwen-1_8B</option>
                    <option value="meta-llama/Llama-2-7b-hf">meta-llama/Llama-2-7b-hf (Requires HF Token)</option>
                  </select>
                </div>
              </div>

              <div className="space-y-4 border-b pb-4">
                <h3 className="font-medium text-lg">3. Method</h3>
                <div>
                  <label className="block text-sm font-medium mb-1">Fine-Tuning Method</label>
                  <select 
                    className="w-full rounded-md border bg-background px-3 py-2 text-sm"
                    value={method}
                    onChange={(e) => setMethod(e.target.value)}
                  >
                    <option value="qlora">QLoRA (Quantized LoRA)</option>
                    <option value="lora">LoRA</option>
                    <option value="full" disabled>Full Fine-Tuning (Unsupported)</option>
                  </select>
                </div>
              </div>

              <div className="space-y-4 border-b pb-4">
                <h3 className="font-medium text-lg">4. Hyperparameters</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-1">Epochs</label>
                    <input 
                      type="number" 
                      min="1" max="10" step="1"
                      className="w-full rounded-md border bg-background px-3 py-2 text-sm"
                      value={epochs}
                      onChange={(e) => setEpochs(Number(e.target.value))}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Learning Rate</label>
                    <input 
                      type="number" 
                      min="0.00001" max="0.1" step="0.00001"
                      className="w-full rounded-md border bg-background px-3 py-2 text-sm"
                      value={learningRate}
                      onChange={(e) => setLearningRate(Number(e.target.value))}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">LoRA Rank</label>
                    <select 
                      className="w-full rounded-md border bg-background px-3 py-2 text-sm"
                      value={loraRank}
                      onChange={(e) => setLoraRank(Number(e.target.value))}
                    >
                      <option value="4">4</option>
                      <option value="8">8</option>
                      <option value="16">16</option>
                      <option value="32">32</option>
                    </select>
                  </div>
                </div>
              </div>

              <div className="flex justify-end space-x-2 pt-4">
                <Button variant="outline" type="button" onClick={() => router.back()}>Cancel</Button>
                <Button type="submit" disabled={createMutation.isPending || !datasetVersionId}>
                  {createMutation.isPending ? 'Starting...' : 'Start Training'}
                </Button>
              </div>

            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
