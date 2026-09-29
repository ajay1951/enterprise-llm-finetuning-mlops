"use client";

import { Play, Pause, CheckSquare } from "lucide-react";

export default function ExperimentsPage() {
  return (
    <div className="flex-1 overflow-auto bg-[#050505] p-8">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white">A/B Experiments</h1>
          <p className="text-sm text-neutral-400 mt-1">Safely route traffic to evaluate new model iterations.</p>
        </div>
        <button className="px-4 py-2 bg-white text-black font-medium text-sm rounded-md hover:bg-neutral-200 transition-colors">
          New Experiment
        </button>
      </div>

      <div className="rounded-xl border border-neutral-800 bg-[#0A0A0A] p-6 mb-6">
        <div className="flex justify-between items-start mb-6">
          <div>
            <div className="flex items-center gap-3">
              <h2 className="text-lg font-semibold text-white">Customer Support v4 Validation</h2>
              <span className="px-2 py-0.5 rounded text-xs bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-medium">RUNNING</span>
            </div>
            <p className="text-sm text-neutral-400 mt-1">Comparing v4 (fine-tuned on Q3 data) against current production v3.</p>
          </div>
          <div className="flex gap-2">
            <button className="p-2 bg-neutral-800 hover:bg-neutral-700 text-neutral-300 rounded-md transition-colors" title="Pause">
              <Pause className="w-4 h-4" />
            </button>
            <button className="px-4 py-2 bg-neutral-800 hover:bg-neutral-700 text-white text-sm font-medium rounded-md transition-colors">
              Complete
            </button>
          </div>
        </div>

        <div className="grid md:grid-cols-2 gap-8">
          {/* Variant A */}
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <h3 className="text-md font-semibold text-white">v3 (Control)</h3>
              <span className="px-3 py-1 bg-neutral-800 rounded font-mono text-sm text-neutral-300">90% Traffic</span>
            </div>
            <div className="h-2 w-full bg-neutral-800 rounded-full overflow-hidden">
              <div className="h-full bg-blue-500" style={{ width: '90%' }}></div>
            </div>
            
            <div className="grid grid-cols-2 gap-4 mt-4">
              <div className="p-3 bg-neutral-900/50 rounded border border-neutral-800">
                <div className="text-xs text-neutral-500 mb-1">Requests</div>
                <div className="text-lg text-white font-mono">900</div>
              </div>
              <div className="p-3 bg-neutral-900/50 rounded border border-neutral-800">
                <div className="text-xs text-neutral-500 mb-1">Latency</div>
                <div className="text-lg text-white font-mono">1.8s</div>
              </div>
              <div className="p-3 bg-neutral-900/50 rounded border border-neutral-800">
                <div className="text-xs text-neutral-500 mb-1">Success Rate</div>
                <div className="text-lg text-white font-mono">99.1%</div>
              </div>
              <div className="p-3 bg-neutral-900/50 rounded border border-neutral-800">
                <div className="text-xs text-neutral-500 mb-1">Errors</div>
                <div className="text-lg text-white font-mono">8</div>
              </div>
            </div>
          </div>

          {/* Variant B */}
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <h3 className="text-md font-semibold text-white">v4 (Experiment)</h3>
              <span className="px-3 py-1 bg-neutral-800 rounded font-mono text-sm text-neutral-300">10% Traffic</span>
            </div>
            <div className="h-2 w-full bg-neutral-800 rounded-full overflow-hidden">
              <div className="h-full bg-emerald-500" style={{ width: '10%' }}></div>
            </div>
            
            <div className="grid grid-cols-2 gap-4 mt-4">
              <div className="p-3 bg-neutral-900/50 rounded border border-emerald-900/30">
                <div className="text-xs text-neutral-500 mb-1">Requests</div>
                <div className="text-lg text-white font-mono">100</div>
              </div>
              <div className="p-3 bg-neutral-900/50 rounded border border-emerald-900/30">
                <div className="text-xs text-neutral-500 mb-1">Latency</div>
                <div className="text-lg text-emerald-400 font-mono">1.5s</div>
              </div>
              <div className="p-3 bg-neutral-900/50 rounded border border-emerald-900/30">
                <div className="text-xs text-neutral-500 mb-1">Success Rate</div>
                <div className="text-lg text-emerald-400 font-mono">99.0%</div>
              </div>
              <div className="p-3 bg-neutral-900/50 rounded border border-emerald-900/30">
                <div className="text-xs text-neutral-500 mb-1">Errors</div>
                <div className="text-lg text-white font-mono">1</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
