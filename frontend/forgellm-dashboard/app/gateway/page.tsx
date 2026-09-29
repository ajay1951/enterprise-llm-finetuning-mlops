"use client";

import { Activity, Zap, ShieldAlert, SplitSquareHorizontal, LineChart, Globe } from "lucide-react";

export default function GatewayOverviewPage() {
  return (
    <div className="flex-1 overflow-auto bg-[#050505] p-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold tracking-tight text-white">AI Gateway</h1>
        <p className="text-sm text-neutral-400 mt-1">Production inference routing, fallbacks, and metrics.</p>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {/* Metric Cards */}
        <div className="rounded-xl border border-neutral-800 bg-[#0A0A0A] p-6 shadow-sm">
          <div className="flex items-center gap-4 text-neutral-400">
            <Globe className="h-5 w-5 text-blue-500" />
            <span className="text-sm font-medium">TOTAL REQUESTS</span>
          </div>
          <p className="mt-4 text-3xl font-bold tracking-tight text-white">1.42M</p>
        </div>

        <div className="rounded-xl border border-neutral-800 bg-[#0A0A0A] p-6 shadow-sm">
          <div className="flex items-center gap-4 text-neutral-400">
            <Activity className="h-5 w-5 text-emerald-500" />
            <span className="text-sm font-medium">SUCCESS RATE</span>
          </div>
          <p className="mt-4 text-3xl font-bold tracking-tight text-emerald-500">99.4%</p>
        </div>

        <div className="rounded-xl border border-neutral-800 bg-[#0A0A0A] p-6 shadow-sm">
          <div className="flex items-center gap-4 text-neutral-400">
            <Zap className="h-5 w-5 text-amber-500" />
            <span className="text-sm font-medium">P95 LATENCY</span>
          </div>
          <p className="mt-4 text-3xl font-bold tracking-tight text-white">1.8s</p>
        </div>
        
        <div className="rounded-xl border border-neutral-800 bg-[#0A0A0A] p-6 shadow-sm">
          <div className="flex items-center gap-4 text-neutral-400">
            <LineChart className="h-5 w-5 text-purple-500" />
            <span className="text-sm font-medium">TOKENS / SEC</span>
          </div>
          <p className="mt-4 text-3xl font-bold tracking-tight text-white">48</p>
        </div>

        <div className="rounded-xl border border-neutral-800 bg-[#0A0A0A] p-6 shadow-sm">
          <div className="flex items-center gap-4 text-neutral-400">
            <SplitSquareHorizontal className="h-5 w-5 text-indigo-500" />
            <span className="text-sm font-medium">ACTIVE MODELS</span>
          </div>
          <p className="mt-4 text-3xl font-bold tracking-tight text-white">8</p>
        </div>

        <div className="rounded-xl border border-neutral-800 bg-[#0A0A0A] p-6 shadow-sm">
          <div className="flex items-center gap-4 text-neutral-400">
            <ShieldAlert className="h-5 w-5 text-rose-500" />
            <span className="text-sm font-medium">FALLBACKS TRIGGERED</span>
          </div>
          <p className="mt-4 text-3xl font-bold tracking-tight text-white">32</p>
        </div>
      </div>
      
      {/* Visual Flow diagram placeholder */}
      <div className="mt-8 rounded-xl border border-neutral-800 bg-[#0A0A0A] p-6">
        <h2 className="text-lg font-semibold text-white mb-6">Request Flow Topology</h2>
        <div className="flex flex-col md:flex-row items-center justify-between text-neutral-300 font-mono text-sm opacity-80 gap-4">
           <div className="px-4 py-2 border border-neutral-700 rounded bg-neutral-900">Client</div>
           <span className="hidden md:block">→</span>
           <div className="px-4 py-2 border border-emerald-900/50 rounded bg-emerald-950/20 text-emerald-400">Auth & Rate Limit</div>
           <span className="hidden md:block">→</span>
           <div className="px-4 py-2 border border-indigo-900/50 rounded bg-indigo-950/20 text-indigo-400">Model Router (Least Loaded)</div>
           <span className="hidden md:block">→</span>
           <div className="px-4 py-2 border border-blue-900/50 rounded bg-blue-950/20 text-blue-400">vLLM GPU Replica</div>
        </div>
      </div>
    </div>
  );
}
