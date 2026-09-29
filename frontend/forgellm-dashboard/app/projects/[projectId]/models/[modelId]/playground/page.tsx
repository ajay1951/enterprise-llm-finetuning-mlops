'use client';

import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { PageHeader } from '@/components/layout/page-header';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { modelsApi, inferenceApi } from '@/lib/api';
import { useParams, useRouter } from 'next/navigation';
import { Loader2 } from 'lucide-react';

export default function ModelPlaygroundPage() {
  const { projectId, modelId } = useParams() as { projectId: string, modelId: string };
  const router = useRouter();
  const [prompt, setPrompt] = useState('');
  const [history, setHistory] = useState<{ role: 'user' | 'model'; content: string }[]>([]);

  const { data: model, isLoading } = useQuery({
    queryKey: ['models', modelId],
    queryFn: () => modelsApi.get(modelId),
  });

  const generateMutation = useMutation({
    mutationFn: (text: string) => inferenceApi.generate(modelId, { prompt: text, max_new_tokens: 256 }),
    onSuccess: (res, reqText) => {
      setHistory(prev => [
        ...prev, 
        { role: 'user', content: reqText }, 
        { role: 'model', content: res.generated_text }
      ]);
      setPrompt('');
    },
  });

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim()) return;
    generateMutation.mutate(prompt.trim());
  };

  if (isLoading) return <div className="p-8">Loading playground...</div>;
  if (!model) return <div className="p-8 text-destructive">Model not found</div>;

  return (
    <div className="flex-1 flex flex-col h-[calc(100vh-theme(spacing.16))] pb-8">
      <PageHeader title="Playground" description={`Testing Model: ${model.name} (${model.version})`}>
        <Button variant="outline" onClick={() => router.back()}>Back to Model</Button>
      </PageHeader>

      <div className="px-8 flex-1 flex flex-col min-h-0">
        <Card className="flex-1 flex flex-col min-h-0 overflow-hidden">
          <CardHeader className="border-b shrink-0 bg-muted/20">
            <CardTitle className="text-sm font-medium flex items-center justify-between">
              <span>Chat Interface</span>
              <span className="text-xs font-normal text-muted-foreground font-mono">{model.id}</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="flex-1 flex flex-col p-0 min-h-0">
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {history.length === 0 ? (
                <div className="h-full flex flex-col items-center justify-center text-muted-foreground text-sm opacity-50">
                  Send a message to start generating with this LoRA model.
                </div>
              ) : (
                history.map((msg, i) => (
                  <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                    <div className={`max-w-[80%] rounded-lg p-3 text-sm ${msg.role === 'user' ? 'bg-primary text-primary-foreground' : 'bg-muted text-foreground'}`}>
                      {msg.content}
                    </div>
                  </div>
                ))
              )}
              {generateMutation.isPending && (
                <div className="flex justify-start">
                  <div className="max-w-[80%] rounded-lg p-3 text-sm bg-muted text-foreground flex items-center gap-2">
                    <Loader2 className="h-4 w-4 animate-spin" /> Generating...
                  </div>
                </div>
              )}
            </div>
            <div className="border-t p-4 shrink-0 bg-background">
              <form onSubmit={handleSend} className="flex gap-2">
                <input
                  type="text"
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  placeholder="Type a message..."
                  className="flex-1 rounded-md border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                  disabled={generateMutation.isPending}
                />
                <Button type="submit" disabled={!prompt.trim() || generateMutation.isPending}>
                  Send
                </Button>
              </form>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
