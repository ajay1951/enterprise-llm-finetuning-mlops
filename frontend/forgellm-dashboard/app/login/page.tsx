'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    // Mock login for demo
    setTimeout(() => {
      router.push('/dashboard');
    }, 800);
  };

  return (
    <div className="min-h-screen w-full flex bg-background">
      {/* Left side: Premium Branding */}
      <div className="hidden lg:flex flex-1 flex-col justify-between p-12 bg-card border-r border-border relative overflow-hidden">
        {/* Subtle decorative grid/glow */}
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_left,_var(--tw-gradient-stops))] from-foreground/5 via-background to-background pointer-events-none" />
        
        <div className="relative z-10 flex items-center gap-3">
          <div className="w-8 h-8 rounded bg-foreground text-background flex items-center justify-center font-bold text-sm">F</div>
          <span className="text-xl font-bold tracking-tight text-foreground">ForgeLLM</span>
        </div>

        <div className="relative z-10 max-w-lg">
          <h1 className="text-4xl font-semibold tracking-tight text-foreground mb-4">
            Build. Fine-tune.<br/>Deploy. Scale.
          </h1>
          <p className="text-lg text-muted-foreground leading-relaxed">
            The enterprise AI infrastructure control plane. Secure, multi-tenant, and built for production performance.
          </p>
        </div>

        <div className="relative z-10 text-sm font-mono text-muted-foreground">
          v9.0.0-production
        </div>
      </div>

      {/* Right side: Login Form */}
      <div className="flex-1 flex flex-col justify-center items-center p-8 lg:p-12 relative">
        <div className="w-full max-w-sm space-y-8">
          <div className="text-center lg:text-left">
            <h2 className="text-2xl font-semibold tracking-tight text-foreground">Welcome back</h2>
            <p className="text-sm text-muted-foreground mt-2">Enter your credentials to access your workspace</p>
          </div>

          <form onSubmit={handleLogin} className="space-y-6">
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1.5 text-foreground">Email</label>
                <input 
                  type="email" 
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-foreground transition-all" 
                  placeholder="name@company.com" 
                  required 
                />
              </div>
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <label className="block text-sm font-medium text-foreground">Password</label>
                  <Link href="/forgot-password" className="text-xs text-muted-foreground hover:text-foreground transition-colors">
                    Forgot password?
                  </Link>
                </div>
                <input 
                  type="password" 
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-foreground transition-all" 
                  placeholder="••••••••" 
                  required 
                />
              </div>
            </div>

            <Button type="submit" className="w-full h-10" disabled={isLoading}>
              {isLoading ? 'Authenticating...' : 'Sign In'}
            </Button>
          </form>

          <p className="text-center text-sm text-muted-foreground">
            Don't have an account?{' '}
            <Link href="/register" className="font-medium text-foreground hover:underline">
              Request access
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
