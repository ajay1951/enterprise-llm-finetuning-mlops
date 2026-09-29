'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { PageHeader } from '@/components/layout/page-header';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { experimentsApi } from '@/lib/api';
import { useParams, useRouter } from 'next/navigation';

export default function CompareExperimentsPage() {
  const { projectId } = useParams() as { projectId: string };
  const router = useRouter();
  const [selectedIds, setSelectedIds] = useState<string[]>([]);

  const { data: experiments = [], isLoading } = useQuery({
    queryKey: ['experiments', projectId],
    queryFn: () => experimentsApi.list(projectId),
  });

  const toggleSelection = (id: string) => {
    setSelectedIds(prev => 
      prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
    );
  };

  const selectedExperiments = experiments.filter(e => selectedIds.includes(e.id));

  return (
    <div className="flex-1 space-y-4 pb-8">
      <PageHeader title="Compare Experiments" description="Select multiple experiments to compare side-by-side.">
        <Button variant="outline" onClick={() => router.back()}>Back to List</Button>
      </PageHeader>

      <div className="px-8 grid gap-6 grid-cols-1 md:grid-cols-3">
        {/* Selection Sidebar */}
        <div className="md:col-span-1">
          <Card>
            <CardHeader>
              <CardTitle>Select Experiments</CardTitle>
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <div className="text-sm text-muted-foreground">Loading...</div>
              ) : experiments.length === 0 ? (
                <div className="text-sm text-muted-foreground">No experiments found.</div>
              ) : (
                <div className="space-y-2">
                  {experiments.map(exp => (
                    <label key={exp.id} className="flex items-center space-x-2 p-2 hover:bg-muted rounded-md cursor-pointer">
                      <input 
                        type="checkbox" 
                        checked={selectedIds.includes(exp.id)}
                        onChange={() => toggleSelection(exp.id)}
                        className="rounded border-gray-300 text-primary focus:ring-primary"
                      />
                      <span className="text-sm font-mono">{exp.id.slice(0, 8)}</span>
                      <span className="text-xs text-muted-foreground ml-auto">
                        Loss: {exp.final_loss?.toFixed(3) || 'N/A'}
                      </span>
                    </label>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Comparison View */}
        <div className="md:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle>Comparison Matrix</CardTitle>
            </CardHeader>
            <CardContent>
              {selectedExperiments.length === 0 ? (
                <div className="h-40 flex items-center justify-center text-muted-foreground text-sm border-2 border-dashed rounded-md">
                  Select experiments from the sidebar to compare.
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Metric</TableHead>
                        {selectedExperiments.map(exp => (
                          <TableHead key={exp.id} className="font-mono">{exp.id.slice(0, 8)}</TableHead>
                        ))}
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      <TableRow>
                        <TableCell className="font-medium">Training Job ID</TableCell>
                        {selectedExperiments.map(exp => (
                          <TableCell key={exp.id} className="font-mono text-xs">{exp.training_job_id.slice(0, 8)}</TableCell>
                        ))}
                      </TableRow>
                      <TableRow>
                        <TableCell className="font-medium">Final Loss</TableCell>
                        {selectedExperiments.map(exp => (
                          <TableCell key={exp.id}>{exp.final_loss?.toFixed(4) || '-'}</TableCell>
                        ))}
                      </TableRow>
                      <TableRow>
                        <TableCell className="font-medium">Eval Loss</TableCell>
                        {selectedExperiments.map(exp => (
                          <TableCell key={exp.id}>{exp.eval_loss?.toFixed(4) || '-'}</TableCell>
                        ))}
                      </TableRow>
                      {/* Dynamic Metrics */}
                      {Array.from(new Set(selectedExperiments.flatMap(exp => Object.keys(exp.metrics || {})))).map(metricKey => (
                        <TableRow key={metricKey}>
                          <TableCell className="font-medium">{metricKey}</TableCell>
                          {selectedExperiments.map(exp => (
                            <TableCell key={exp.id}>{exp.metrics?.[metricKey] || '-'}</TableCell>
                          ))}
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
