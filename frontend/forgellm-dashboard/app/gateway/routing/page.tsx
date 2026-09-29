"use client";

import { CheckCircle2, AlertTriangle, ArrowRight, Server } from "lucide-react";

export default function GatewayRoutingPage() {
  return (
    <div className="flex-1 overflow-auto bg-[#050505] p-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold tracking-tight text-white">Routing Rules</h1>
        <p className="text-sm text-neutral-400 mt-1">Configure traffic splitting, least-loaded routing, and failover fallbacks.</p>
      </div>

      <div className="space-y-6">
        <div className="rounded-xl border border-neutral-800 bg-[#0A0A0A] p-6">
          <div className="flex justify-between items-start mb-6">
            <div>
              <h2 className="text-lg font-semibold text-white flex items-center gap-2">
                customer-support
                <span className="px-2 py-0.5 rounded text-xs bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">Alias</span>
              </h2>
              <p className="text-sm text-neutral-400 mt-1">Strategy: LEAST_LOADED</p>
            </div>
            <button className="px-4 py-2 bg-neutral-800 hover:bg-neutral-700 text-white text-sm font-medium rounded-md transition-colors">
              Edit Route
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Primary */}
            <div className="border border-neutral-800 rounded-lg p-4 bg-neutral-900/50">
              <div className="flex items-center justify-between mb-4">
                <span className="text-sm font-semibold text-emerald-400">PRIMARY</span>
                <span className="text-xs font-mono bg-neutral-800 px-2 py-1 rounded">v4-production</span>
              </div>
              
              <div className="space-y-3">
                <div className="flex justify-between items-center text-sm">
                  <div className="flex items-center gap-2 text-neutral-300">
                    <Server className="w-4 h-4" /> Replica 1
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-emerald-400 text-xs flex items-center gap-1"><CheckCircle2 className="w-3 h-3"/> HEALTHY</span>
                    <span className="text-neutral-500 font-mono text-xs">Load: 31%</span>
                  </div>
                </div>
                <div className="flex justify-between items-center text-sm">
                  <div className="flex items-center gap-2 text-neutral-300">
                    <Server className="w-4 h-4" /> Replica 2
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-emerald-400 text-xs flex items-center gap-1"><CheckCircle2 className="w-3 h-3"/> HEALTHY</span>
                    <span className="text-neutral-500 font-mono text-xs">Load: 18%</span>
                  </div>
                </div>
                <div className="flex justify-between items-center text-sm">
                  <div className="flex items-center gap-2 text-neutral-300">
                    <Server className="w-4 h-4" /> Replica 3
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-amber-400 text-xs flex items-center gap-1"><AlertTriangle className="w-3 h-3"/> DEGRADED</span>
                    <span className="text-neutral-500 font-mono text-xs">Load: 87%</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Fallback */}
            <div className="border border-neutral-800 rounded-lg p-4 bg-neutral-900/20">
              <div className="flex items-center justify-between mb-4">
                <span className="text-sm font-semibold text-neutral-500">FALLBACK</span>
                <span className="text-xs font-mono bg-neutral-800/50 text-neutral-400 px-2 py-1 rounded">v3-production</span>
              </div>
              
              <div className="space-y-3 opacity-70">
                <div className="flex justify-between items-center text-sm">
                  <div className="flex items-center gap-2 text-neutral-300">
                    <Server className="w-4 h-4" /> Replica 1 (Standby)
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-emerald-400 text-xs flex items-center gap-1"><CheckCircle2 className="w-3 h-3"/> HEALTHY</span>
                    <span className="text-neutral-500 font-mono text-xs">Load: 0%</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
