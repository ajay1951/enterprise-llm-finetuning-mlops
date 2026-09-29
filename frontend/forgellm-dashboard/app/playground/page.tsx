'use client';

import { useState } from 'react';
import { DashboardLayout } from '@/components/layout/dashboard-layout';
import { Button } from '@/components/ui/button';
import { Sparkles, Send, RefreshCw, Zap } from 'lucide-react';

export default function PlaygroundPage() {
  const [prompt, setPrompt] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [baseResponse, setBaseResponse] = useState('');
  const [fineTunedResponse, setFineTunedResponse] = useState('');

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim()) return;

    setIsGenerating(true);
    setBaseResponse('');
    setFineTunedResponse('');

    // Simulate side-by-side completion comparison
    setTimeout(() => {
      setBaseResponse("Thank you for reaching out. Please check your account settings or contact support for further assistance.");
      setFineTunedResponse("I understand how frustrating loading issues can be. I've inspected your account status and verified your active plan. Please clear your cache and restart your app!");
      setIsGenerating(false);
    }, 1200);
  };

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between border-b border-border pb-4">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">Model Playground</h1>
            <p className="text-sm text-muted-foreground mt-1">
              Test and compare base model responses against fine-tuned model checkpoints side-by-side in real time.
            </p>
          </div>
          <div className="flex items-center gap-2 font-mono text-xs text-caption">
            <span className="w-2 h-2 rounded-full bg-[#00ff00]" />
            Inference Engine Active
          </div>
        </div>

        {/* Input Form */}
        <form onSubmit={handleGenerate} className="space-y-3">
          <div className="space-y-1.5">
            <label className="block text-sm font-medium text-foreground">Test Prompt</label>
            <textarea
              rows={3}
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="e.g. My dashboard is not loading properly, can you help?"
              className="w-full rounded-[var(--radius)] border border-border bg-card p-3 text-sm focus:outline-none focus:ring-1 focus:ring-primary shadow-none font-sans"
            />
          </div>
          <div className="flex justify-end gap-3">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => { setPrompt(''); setBaseResponse(''); setFineTunedResponse(''); }}
            >
              Clear
            </Button>
            <Button type="submit" size="sm" disabled={isGenerating || !prompt.trim()}>
              {isGenerating ? (
                <>
                  <RefreshCw className="w-4 h-4 mr-2 animate-spin" /> Generating...
                </>
              ) : (
                <>
                  <Send className="w-4 h-4 mr-2" /> Run Comparison
                </>
              )}
            </Button>
          </div>
        </form>

        {/* Side-by-Side Comparison Panels */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-4">
          {/* Base Model Panel */}
          <div className="border border-border rounded-[var(--radius)] bg-card p-5 space-y-3">
            <div className="flex items-center justify-between border-b border-border pb-3">
              <div className="flex items-center gap-2">
                <Zap className="w-4 h-4 text-muted-foreground" />
                <span className="font-semibold text-sm">Base Model (Qwen2.5-0.5B)</span>
              </div>
              <span className="px-2 py-0.5 text-[10px] font-mono uppercase bg-secondary text-muted-foreground rounded-[var(--radius)]">
                Baseline
              </span>
            </div>
            <div className="min-h-[160px] text-sm text-foreground leading-relaxed font-sans pt-1">
              {isGenerating ? (
                <div className="flex items-center gap-2 text-muted-foreground font-mono text-xs animate-pulse">
                  <span>Generating response...</span>
                </div>
              ) : baseResponse ? (
                baseResponse
              ) : (
                <span className="text-muted-foreground text-xs font-mono">Submit a prompt above to generate baseline completion.</span>
              )}
            </div>
          </div>

          {/* Fine-Tuned Model Panel */}
          <div className="border border-primary/40 rounded-[var(--radius)] bg-card p-5 space-y-3 relative overflow-hidden">
            <div className="absolute top-0 right-0 w-24 h-24 bg-primary/5 rounded-full blur-2xl pointer-events-none" />
            <div className="flex items-center justify-between border-b border-border pb-3">
              <div className="flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-primary" />
                <span className="font-semibold text-sm text-foreground">Fine-Tuned Adapter (customer-support:v7)</span>
              </div>
              <span className="px-2 py-0.5 text-[10px] font-mono uppercase bg-primary text-primary-foreground font-bold rounded-[var(--radius)]">
                Active Adapter
              </span>
            </div>
            <div className="min-h-[160px] text-sm text-foreground leading-relaxed font-sans pt-1">
              {isGenerating ? (
                <div className="flex items-center gap-2 text-primary font-mono text-xs animate-pulse">
                  <span>Generating tuned response...</span>
                </div>
              ) : fineTunedResponse ? (
                fineTunedResponse
              ) : (
                <span className="text-muted-foreground text-xs font-mono">Submit a prompt above to generate fine-tuned completion.</span>
              )}
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
