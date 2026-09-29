"use client";

import { Activity, Play } from "lucide-react";

export default function BenchmarksPage() {
  return (
    <div className="flex-1 overflow-auto bg-[#050505] p-8">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white">Model Benchmarks</h1>
          <p className="text-sm text-neutral-400 mt-1">Compare inference performance across model versions.</p>
        </div>
        <button className="px-4 py-2 bg-white text-black font-medium text-sm rounded-md hover:bg-neutral-200 transition-colors flex items-center gap-2">
          <Play className="w-4 h-4" /> Run Benchmark
        </button>
      </div>

      <div className="rounded-xl border border-neutral-800 bg-[#0A0A0A] overflow-hidden">
        <div className="p-6 border-b border-neutral-800 flex justify-between items-center">
          <h2 className="text-lg font-semibold text-white">Latest Run: v3 vs v4</h2>
          <span className="text-sm text-neutral-500">Completed 2 hours ago</span>
        </div>
        
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-neutral-400">
            <thead className="bg-neutral-900/50 text-neutral-300">
              <tr>
                <th className="px-6 py-4 font-medium">Model Version</th>
                <th className="px-6 py-4 font-medium">Avg Latency</th>
                <th className="px-6 py-4 font-medium">P95 Latency</th>
                <th className="px-6 py-4 font-medium">P99 Latency</th>
                <th className="px-6 py-4 font-medium">TTFT</th>
                <th className="px-6 py-4 font-medium">Tokens / Sec</th>
                <th className="px-6 py-4 font-medium">Error Rate</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-neutral-800">
              <tr className="hover:bg-neutral-900/30">
                <td className="px-6 py-4 font-medium text-white">v3-production</td>
                <td className="px-6 py-4 font-mono">1.4s</td>
                <td className="px-6 py-4 font-mono">2.3s</td>
                <td className="px-6 py-4 font-mono">3.1s</td>
                <td className="px-6 py-4 font-mono">240ms</td>
                <td className="px-6 py-4 font-mono">48</td>
                <td className="px-6 py-4 font-mono">0.1%</td>
              </tr>
              <tr className="hover:bg-neutral-900/30">
                <td className="px-6 py-4 font-medium text-emerald-400">v4-production</td>
                <td className="px-6 py-4 font-mono text-emerald-400">1.1s</td>
                <td className="px-6 py-4 font-mono text-emerald-400">1.9s</td>
                <td className="px-6 py-4 font-mono text-emerald-400">2.6s</td>
                <td className="px-6 py-4 font-mono text-emerald-400">180ms</td>
                <td className="px-6 py-4 font-mono text-emerald-400">55</td>
                <td className="px-6 py-4 font-mono">0.05%</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
