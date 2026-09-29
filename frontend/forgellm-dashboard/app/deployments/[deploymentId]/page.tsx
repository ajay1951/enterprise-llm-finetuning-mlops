'use client';

import { useState, useEffect, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { PageHeader } from '@/components/layout/page-header';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { useParams } from 'next/navigation';
import { useWebSocket } from '@/lib/hooks/useWebSocket';

// API Wrappers
const fetchDeployment = async (id: string) => {
  const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/deployments/${id}`);
  if (!res.ok) throw new Error('Failed to fetch deployment');
  return res.json();
};

const stopDeployment = async (id: string) => {
  const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/deployments/${id}/stop`, { method: 'POST' });
  if (!res.ok) throw new Error('Failed to stop deployment');
  return res.json();
};

export default function DeploymentDetailsPage() {
  const { deploymentId } = useParams() as { deploymentId: string };
  const queryClient = useQueryClient();

  // Polling for the REST state
  const { data: deployment, isLoading } = useQuery({
    queryKey: ['deployments', deploymentId],
    queryFn: () => fetchDeployment(deploymentId),
    refetchInterval: 3000,
  });

  const stopMutation = useMutation({
    mutationFn: stopDeployment,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['deployments', deploymentId] }),
  });

  // Playground state
  const [prompt, setPrompt] = useState('Write a short story about a brave knight.');
  const [systemPrompt, setSystemPrompt] = useState('You are a helpful assistant.');
  const [response, setResponse] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [stream, setStream] = useState(true);
  const [temperature, setTemperature] = useState(0.7);

  // Live Logs state
  const [logs, setLogs] = useState<{sequence: number, event: string, timestamp: string}[]>([]);
  const logsEndRef = useRef<HTMLDivElement>(null);
  
  // Connect to Deployment events WS
  const wsUrl = process.env.NEXT_PUBLIC_API_URL?.replace('http', 'ws') || 'ws://localhost:8000';
  // We can just poll logs for simplicity since WS wasn't explicitly routed for deployments in our FastAPI yet,
  // Actually, wait, let's just fetch logs on interval
  const { data: historicalLogs } = useQuery({
    queryKey: ['deployments', deploymentId, 'logs'],
    queryFn: async () => {
        const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/deployments/${deploymentId}/logs`);
        return res.json();
    },
    refetchInterval: 2000,
  });

  useEffect(() => {
      if (historicalLogs) {
          setLogs(historicalLogs.map((l: any) => ({
              sequence: l.sequence,
              event: l.data.message || l.event_type,
              timestamp: l.timestamp
          })));
      }
  }, [historicalLogs]);

  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  const handleGenerate = async () => {
    if (!deployment) return;
    setIsGenerating(true);
    setResponse('');
    
    try {
      const messages = [];
      if (systemPrompt) messages.push({ role: 'system', content: systemPrompt });
      messages.push({ role: 'user', content: prompt });

      const apiUrl = `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/v1/chat/completions`;
      
      const reqBody = {
        model: deployment.name,
        messages,
        temperature,
        stream,
        max_tokens: 512
      };

      if (!stream) {
        const res = await fetch(apiUrl, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(reqBody)
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Generation failed');
        setResponse(data.choices[0].message.content);
      } else {
        const res = await fetch(apiUrl, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(reqBody)
        });
        
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || 'Generation failed');
        }

        const reader = res.body?.getReader();
        const decoder = new TextDecoder();
        
        if (reader) {
          while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            
            const chunk = decoder.decode(value);
            const lines = chunk.split('\n').filter(l => l.trim() !== '');
            for (const line of lines) {
              if (line === 'data: [DONE]') break;
              if (line.startsWith('data: ')) {
                try {
                  const data = JSON.parse(line.replace('data: ', ''));
                  if (data.error) {
                      setResponse(prev => prev + `\n[Error: ${data.error}]`);
                      break;
                  }
                  if (data.choices && data.choices[0].delta.content) {
                    setResponse(prev => prev + data.choices[0].delta.content);
                  }
                } catch (e) {
                  console.error('Failed to parse stream chunk', e, line);
                }
              }
            }
          }
        }
      }
    } catch (e: any) {
      setResponse(`Error: ${e.message}`);
    } finally {
      setIsGenerating(false);
    }
  };

  if (isLoading || !deployment) return <div className="p-8">Loading deployment...</div>;

  return (
    <div className="flex-1 space-y-4 p-8 pt-6">
      <PageHeader title={deployment.name} description={`Status: ${deployment.status.toUpperCase()}`}>
        <div className="flex space-x-2">
          {['ready', 'starting', 'loading', 'queued'].includes(deployment.status) && (
            <Button 
              variant="destructive" 
              onClick={() => { if(confirm('Stop deployment?')) stopMutation.mutate(deployment.id); }}
              disabled={stopMutation.isPending}
            >
              {stopMutation.isPending ? 'Stopping...' : 'Stop Deployment'}
            </Button>
          )}
        </div>
      </PageHeader>

      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle>Details</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <div className="flex justify-between border-b py-1">
              <span className="text-muted-foreground">Backend</span>
              <span className="font-medium">{deployment.serving_backend}</span>
            </div>
            <div className="flex justify-between border-b py-1">
              <span className="text-muted-foreground">Device</span>
              <span className="font-medium">{deployment.device}</span>
            </div>
            <div className="flex justify-between border-b py-1">
              <span className="text-muted-foreground">Health</span>
              <Badge variant={deployment.health_status === 'healthy' ? 'success' : 'destructive'}>{deployment.health_status.toUpperCase()}</Badge>
            </div>
            <div className="flex justify-between border-b py-1">
              <span className="text-muted-foreground">Endpoint</span>
              <span className="font-medium text-xs font-mono truncate max-w-[150px]">{deployment.endpoint || 'Pending'}</span>
            </div>
          </CardContent>
        </Card>

        <Card className="md:col-span-2">
          <CardHeader className="py-3 bg-gray-900 rounded-t-lg border-b border-gray-800">
            <CardTitle className="text-gray-300 text-sm">Deployment Lifecycle Logs</CardTitle>
          </CardHeader>
          <CardContent className="bg-black text-green-400 font-mono text-sm p-4 h-[200px] overflow-y-auto rounded-b-lg border border-gray-800">
            {logs.length === 0 ? (
              <div className="text-gray-600">Waiting for logs...</div>
            ) : (
              logs.map((log) => (
                <div key={log.sequence} className="mb-1 flex space-x-2">
                  <span className="text-gray-500 shrink-0">[{new Date(log.timestamp).toLocaleTimeString()}]</span>
                  <span className="text-gray-300">{log.event}</span>
                </div>
              ))
            )}
            <div ref={logsEndRef} />
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Model Playground</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-6 md:grid-cols-3">
            <div className="md:col-span-1 space-y-4">
              <div className="space-y-2">
                <Label>System Prompt</Label>
                <Textarea 
                  placeholder="You are a helpful assistant..." 
                  value={systemPrompt} 
                  onChange={(e) => setSystemPrompt(e.target.value)}
                  className="h-[100px]"
                />
              </div>
              <div className="space-y-2">
                <Label>Temperature ({temperature})</Label>
                <Input 
                  type="number" 
                  min="0" max="2" step="0.1" 
                  value={temperature} 
                  onChange={(e) => setTemperature(parseFloat(e.target.value))} 
                />
              </div>
              <div className="flex items-center space-x-2 pt-2">
                <Switch 
                  checked={stream} 
                  onCheckedChange={setStream} 
                  id="stream-mode"
                />
                <Label htmlFor="stream-mode">Stream output token-by-token</Label>
              </div>
              
              <Button 
                className="w-full mt-4" 
                onClick={handleGenerate} 
                disabled={isGenerating || deployment.status !== 'ready'}
              >
                {isGenerating ? 'Generating...' : 'Send Prompt'}
              </Button>
            </div>
            
            <div className="md:col-span-2 space-y-4">
              <div className="space-y-2">
                <Label>User Prompt</Label>
                <Textarea 
                  placeholder="Enter your prompt here..." 
                  value={prompt} 
                  onChange={(e) => setPrompt(e.target.value)}
                  className="h-[100px]"
                />
              </div>
              <div className="space-y-2">
                <Label>Assistant Response</Label>
                <div className="min-h-[250px] p-4 bg-muted/50 rounded-md border whitespace-pre-wrap">
                  {response || (isGenerating ? <span className="animate-pulse">Thinking...</span> : <span className="text-muted-foreground italic">Response will appear here...</span>)}
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>API Integration</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="bg-muted p-4 rounded-md font-mono text-xs overflow-x-auto">
            <code>
{`curl ${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/v1/chat/completions \\
  -H "Content-Type: application/json" \\
  -d '{
    "model": "${deployment.name}",
    "messages": [
      {
        "role": "user",
        "content": "Hello"
      }
    ]
  }'`}
            </code>
          </div>
        </CardContent>
      </Card>

    </div>
  );
}
