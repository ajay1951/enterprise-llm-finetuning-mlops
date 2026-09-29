'use client';

import { useState, useEffect, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { PageHeader } from '@/components/layout/page-header';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { trainingApi } from '@/lib/api';
import { useParams } from 'next/navigation';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { useWebSocket } from '@/lib/hooks/useWebSocket';

type LogEntry = { sequence: number; level: string; message: string; timestamp: string };

export default function TrainingJobDetailsPage() {
  const { projectId, jobId } = useParams() as { projectId: string, jobId: string };
  const queryClient = useQueryClient();

  const [liveState, setLiveState] = useState<any>(null);
  const [metrics, setMetrics] = useState<any[]>([]);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const logsEndRef = useRef<HTMLDivElement>(null);
  const [autoScroll, setAutoScroll] = useState(true);

  // Initial fetch for REST state
  const { data: initialJob, isLoading } = useQuery({
    queryKey: ['trainingJobs', jobId],
    queryFn: () => trainingApi.get(jobId),
    staleTime: Infinity,
  });

  const wsUrl = process.env.NEXT_PUBLIC_API_URL?.replace('http', 'ws') || 'ws://localhost:8000';
  const { status: wsStatus, lastMessage } = useWebSocket(`${wsUrl}/api/v1/ws/training/${jobId}`);

  useEffect(() => {
    if (initialJob && !liveState) {
      setLiveState(initialJob);
    }
  }, [initialJob, liveState]);

  useEffect(() => {
    if (lastMessage) {
      const { event_type, data, sequence, timestamp } = lastMessage;
      if (event_type === 'training.progress' || event_type === 'training.started' || event_type === 'training.completed' || event_type === 'training.failed') {
        setLiveState((prev: any) => ({ ...prev, ...data }));
        if (event_type === 'training.completed' || event_type === 'training.failed') {
          queryClient.invalidateQueries({ queryKey: ['trainingJobs'] });
        }
      }
      if (event_type === 'training.metric') {
        setMetrics(prev => [...prev.slice(-100), data]);
      }
      if (event_type === 'training.log') {
        setLogs(prev => [...prev.slice(-500), { sequence, level: data.level, message: data.message, timestamp }]);
      }
    }
  }, [lastMessage, queryClient]);

  // Auto-scroll logs
  useEffect(() => {
    if (autoScroll && logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs, autoScroll]);

  const cancelMutation = useMutation({
    mutationFn: () => trainingApi.cancel(jobId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['trainingJobs', jobId] });
    },
  });

  if (isLoading || !liveState) return <div className="p-8">Loading training job...</div>;

  const progress = liveState.status === 'completed' ? 100 : liveState.total_steps > 0 ? Math.round((liveState.current_step / liveState.total_steps) * 100) : 0;
  const isCancellable = liveState.status === 'queued' || liveState.status === 'running';

  const wsBadgeVariant = wsStatus === 'LIVE' ? 'success' : wsStatus === 'RECONNECTING' ? 'warning' : 'destructive';

  return (
    <div className="flex-1 space-y-4 pb-8">
      <PageHeader title={`Training Job`} description={`ID: ${jobId}`}>
        <div className="flex items-center space-x-4">
          <Badge variant={wsBadgeVariant}>{wsStatus}</Badge>
          {isCancellable && (
            <Button 
              variant="destructive" 
              onClick={() => { if(confirm('Cancel this training job?')) cancelMutation.mutate(); }}
              disabled={cancelMutation.isPending}
            >
              {cancelMutation.isPending ? 'Cancelling...' : 'Cancel Job'}
            </Button>
          )}
        </div>
      </PageHeader>

      <div className="px-8 grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Status</CardTitle>
          </CardHeader>
          <CardContent>
            <Badge variant={liveState.status === 'completed' ? 'success' : liveState.status === 'failed' ? 'destructive' : liveState.status === 'running' ? 'default' : 'secondary'}>
              {liveState.status.toUpperCase()}
            </Badge>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Progress</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{progress}%</div>
            <p className="text-xs text-muted-foreground">Step {liveState.current_step || 0} of {liveState.total_steps || '?'}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Speed</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics.length > 0 ? metrics[metrics.length-1].samples_per_second?.toFixed(1) || '-' : '-'}</div>
            <p className="text-xs text-muted-foreground">Samples / sec</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Current Loss</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{liveState.current_loss?.toFixed(4) || '-'}</div>
          </CardContent>
        </Card>
      </div>

      <div className="px-8 grid gap-4 grid-cols-1 md:grid-cols-3">
        <Card className="md:col-span-2">
          <CardHeader>
            <CardTitle>Live Loss Chart</CardTitle>
          </CardHeader>
          <CardContent>
            {metrics.length > 0 ? (
              <div className="h-[250px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={metrics}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} />
                    <XAxis dataKey="step" tickLine={false} axisLine={false} />
                    <YAxis tickLine={false} axisLine={false} domain={['auto', 'auto']} />
                    <Tooltip 
                      contentStyle={{ backgroundColor: 'hsl(var(--card))', borderColor: 'hsl(var(--border))', color: 'hsl(var(--foreground))' }} 
                    />
                    <Line type="monotone" dataKey="loss" stroke="var(--color-primary)" strokeWidth={2} dot={false} isAnimationActive={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="h-[250px] flex items-center justify-center text-muted-foreground text-sm">
                Waiting for metrics...
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Configuration</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <div className="flex justify-between py-1 border-b"><span className="text-muted-foreground">Base Model</span> <span className="font-medium">{liveState.model_name}</span></div>
            <div className="flex justify-between py-1 border-b"><span className="text-muted-foreground">Method</span> <span className="font-medium">{liveState.method}</span></div>
            <div className="flex justify-between py-1 border-b"><span className="text-muted-foreground">Learning Rate</span> <span className="font-medium">{liveState.learning_rate}</span></div>
            <div className="flex justify-between py-1"><span className="text-muted-foreground">LoRA Rank</span> <span className="font-medium">{liveState.lora_rank}</span></div>
          </CardContent>
        </Card>
      </div>

      <div className="px-8">
        <Card className="bg-black text-green-400 font-mono text-sm border-gray-800">
          <CardHeader className="flex flex-row items-center justify-between py-2 bg-gray-900 border-b border-gray-800">
            <CardTitle className="text-gray-300 text-xs">Training Logs</CardTitle>
            <Button variant="ghost" size="sm" className="h-6 text-gray-400 hover:text-white" onClick={() => setAutoScroll(!autoScroll)}>
              {autoScroll ? 'Pause Scroll' : 'Auto Scroll'}
            </Button>
          </CardHeader>
          <CardContent className="p-4 h-[300px] overflow-y-auto">
            {logs.length === 0 ? (
              <div className="text-gray-600">Waiting for logs...</div>
            ) : (
              logs.map((log) => (
                <div key={log.sequence} className="mb-1 flex space-x-2">
                  <span className="text-gray-500 shrink-0">[{new Date(log.timestamp).toLocaleTimeString()}]</span>
                  <span className={`shrink-0 ${log.level === 'ERROR' ? 'text-red-400' : log.level === 'WARNING' ? 'text-yellow-400' : 'text-blue-400'}`}>
                    {log.level}
                  </span>
                  <span className="text-gray-300">{log.message}</span>
                </div>
              ))
            )}
            <div ref={logsEndRef} />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
