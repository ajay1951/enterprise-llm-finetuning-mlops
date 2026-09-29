"use client";

import { useState } from "react";
import { Send, Terminal, Loader2 } from "lucide-react";

export default function InferencePlaygroundPage() {
  const [prompt, setPrompt] = useState("");
  const [response, setResponse] = useState("");
  const [loading, setLoading] = useState(false);
  const [metrics, setMetrics] = useState({ latency: 0, tokens: 0 });

  const handleSend = async () => {
    if (!prompt.trim()) return;
    setLoading(true);
    setResponse("");
    const startTime = Date.now();
    
    // In a real implementation this calls our /v1/chat/completions endpoint
    // We simulate the stream for the playground
    setTimeout(() => {
      const words = ["This ", "is ", "a ", "simulated ", "streaming ", "response ", "from ", "the ", "ForgeLLM ", "AI ", "Gateway."];
      let i = 0;
      const interval = setInterval(() => {
        if (i < words.length) {
          setResponse(prev => prev + words[i]);
          i++;
        } else {
          clearInterval(interval);
          setLoading(false);
          setMetrics({
            latency: Date.now() - startTime,
            tokens: 22
          });
        }
      }, 100);
    }, 500);
  };

  return (
    <div className="flex-1 overflow-auto bg-[#050505] p-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold tracking-tight text-white">Inference Playground</h1>
        <p className="text-sm text-neutral-400 mt-1">Test your deployments interactively.</p>
      </div>

      <div className="flex flex-col lg:flex-row gap-6 h-[600px]">
        {/* Left Side: Controls */}
        <div className="w-full lg:w-1/3 flex flex-col gap-6">
          <div className="rounded-xl border border-neutral-800 bg-[#0A0A0A] p-6 flex-1">
            <h3 className="text-sm font-semibold text-white mb-4">Configuration</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-neutral-400 mb-1">Model</label>
                <select className="w-full bg-neutral-900 border border-neutral-800 rounded p-2 text-sm text-white">
                  <option>customer-support (Alias)</option>
                  <option>customer-support-v4</option>
                </select>
              </div>
              
              <div>
                <label className="block text-xs font-medium text-neutral-400 mb-1">Temperature (0.7)</label>
                <input type="range" min="0" max="2" step="0.1" defaultValue="0.7" className="w-full accent-blue-500" />
              </div>

              <div>
                <label className="block text-xs font-medium text-neutral-400 mb-1">Max Tokens (256)</label>
                <input type="range" min="1" max="2048" step="1" defaultValue="256" className="w-full accent-blue-500" />
              </div>
            </div>
          </div>
        </div>

        {/* Right Side: Chat */}
        <div className="w-full lg:w-2/3 flex flex-col rounded-xl border border-neutral-800 bg-[#0A0A0A] overflow-hidden">
          {/* Chat Window */}
          <div className="flex-1 p-6 overflow-y-auto space-y-6">
            {prompt && (
              <div className="flex justify-end">
                <div className="bg-blue-600/20 border border-blue-500/30 text-white p-3 rounded-lg max-w-[80%] text-sm">
                  {prompt}
                </div>
              </div>
            )}
            
            {(response || loading) && (
              <div className="flex justify-start">
                <div className="bg-neutral-900 border border-neutral-800 text-neutral-200 p-3 rounded-lg max-w-[80%] text-sm">
                  {response}
                  {loading && <span className="animate-pulse">...</span>}
                </div>
              </div>
            )}
          </div>
          
          {/* Metrics bar */}
          {metrics.latency > 0 && (
            <div className="px-6 py-2 bg-neutral-900/50 border-t border-b border-neutral-800 flex gap-6 text-xs text-neutral-500 font-mono">
              <span>Latency: {metrics.latency}ms</span>
              <span>Tokens: {metrics.tokens}</span>
              <span>TPS: {Math.round(metrics.tokens / (metrics.latency/1000))}</span>
              <span>Req ID: req_01jxyz...</span>
            </div>
          )}

          {/* Input Area */}
          <div className="p-4 bg-neutral-900 border-t border-neutral-800">
            <div className="flex items-center gap-2">
              <input
                type="text"
                placeholder="Send a message..."
                className="flex-1 bg-neutral-800 border border-neutral-700 text-white rounded p-3 text-sm focus:outline-none focus:border-blue-500"
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSend()}
              />
              <button 
                onClick={handleSend}
                disabled={loading}
                className="p-3 bg-white text-black rounded hover:bg-neutral-200 disabled:opacity-50 transition-colors"
              >
                {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Send className="w-5 h-5" />}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
