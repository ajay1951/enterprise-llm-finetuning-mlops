'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';

export default function Home() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setTimeout(() => {
      router.push('/dashboard');
    }, 600);
  };

  return (
    <div className="min-h-screen w-full flex bg-background text-foreground font-sans">
      {/* Left Panel: Enterprise Branding & System Telemetry Info */}
      <div className="hidden lg:flex flex-1 flex-col justify-between p-12 bg-card border-r border-border">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-primary text-primary-foreground flex items-center justify-center font-bold text-sm font-mono rounded-[var(--radius)]">
            F
          </div>
          <span className="text-xl font-bold tracking-tight">ForgeLLM Control Plane</span>
        </div>

        <div className="w-full max-w-lg space-y-6 my-auto">
          <div className="inline-block px-2.5 py-1 rounded-[var(--radius)] border border-border text-caption bg-background">
            AI Infrastructure & SFT Platform
          </div>
          <h1 className="text-3xl font-semibold tracking-tight leading-tight">
            Enterprise LLM Fine-Tuning & Model Management
          </h1>
          <p className="text-sm text-muted-foreground leading-relaxed">
            Unified workspace for dataset preparation, QLoRA fine-tuning, automated evaluation quality gates, and model registry lifecycle operations.
          </p>
          <div className="grid grid-cols-2 gap-4 pt-4 border-t border-border font-mono text-xs">
            <div>
              <div className="text-muted-foreground uppercase text-[10px] tracking-wider mb-1">Architecture</div>
              <div className="font-medium text-foreground">Multi-Tenant / Async</div>
            </div>
            <div>
              <div className="text-muted-foreground uppercase text-[10px] tracking-wider mb-1">Registry Stage</div>
              <div className="font-medium text-foreground">MLflow Production Alias</div>
            </div>
          </div>
        </div>

        <div className="flex justify-between text-xs font-mono text-muted-foreground uppercase tracking-wider">
          <span>v9.0.0-production</span>
          <span>System Status: Normal</span>
        </div>
      </div>

      {/* Right Panel: Clean Authentication Form */}
      <div className="flex-1 flex flex-col justify-center items-center p-8 lg:p-12 bg-background">
        <div className="w-full max-w-sm space-y-8">
          <div>
            <h2 className="text-2xl font-semibold tracking-tight">Sign In</h2>
            <p className="text-sm text-muted-foreground mt-2">Enter credentials to access your workspace</p>
          </div>

          <form onSubmit={handleLogin} className="space-y-5">
            <div className="space-y-4">
              <div className="space-y-1.5">
                <label className="block text-sm font-medium">Email Address</label>
                <input 
                  type="email" 
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full rounded-[var(--radius)] border border-border bg-card px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-primary transition-all shadow-none" 
                  placeholder="name@company.com" 
                  required 
                />
              </div>
              <div className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <label className="block text-sm font-medium">Password</label>
                  <Link href="/forgot-password" className="text-xs text-muted-foreground hover:text-foreground transition-colors">
                    Forgot password?
                  </Link>
                </div>
                <input 
                  type="password" 
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full rounded-[var(--radius)] border border-border bg-card px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-primary transition-all shadow-none" 
                  placeholder="••••••••" 
                  required 
                />
              </div>
            </div>

            <Button type="submit" className="w-full" disabled={isLoading}>
              {isLoading ? 'Authenticating...' : 'Sign In'}
            </Button>
          </form>

          <p className="text-center text-sm text-muted-foreground">
            Need access?{' '}
            <Link href="/register" className="font-medium text-foreground hover:underline">
              Request workspace credentials
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
