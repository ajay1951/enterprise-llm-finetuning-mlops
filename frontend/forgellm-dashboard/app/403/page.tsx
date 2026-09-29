'use client';

import { ShieldAlert, ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';
import Link from 'next/link';

export default function ForbiddenPage() {
  return (
    <div className="flex-1 flex flex-col h-full bg-background items-center justify-center p-6">
      <div className="max-w-md w-full bg-card border border-border rounded-xl p-8 shadow-sm text-center">
        <div className="w-16 h-16 bg-destructive/10 rounded-full flex items-center justify-center mx-auto mb-6 text-destructive">
          <ShieldAlert size={32} />
        </div>
        
        <h1 className="text-2xl font-semibold tracking-tight text-foreground mb-2">Access restricted</h1>
        <p className="text-muted-foreground text-sm mb-8">
          You don't have permission to perform this action.
        </p>

        <div className="bg-secondary/20 border border-border rounded-lg p-4 text-left space-y-4 mb-8">
          <div className="flex justify-between items-center">
            <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Required Permission</span>
            <span className="text-sm font-mono text-foreground font-medium">models:deploy</span>
          </div>
          <div className="h-px bg-border w-full" />
          <div className="flex justify-between items-center">
            <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Your Role</span>
            <span className="text-xs font-mono bg-secondary px-2 py-1 rounded text-foreground">VIEWER</span>
          </div>
        </div>

        <div className="flex gap-3 justify-center">
          <Button variant="outline" onClick={() => window.history.back()}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Go Back
          </Button>
          <Button asChild>
            <Link href="/dashboard">Return to Dashboard</Link>
          </Button>
        </div>
      </div>
    </div>
  );
}
