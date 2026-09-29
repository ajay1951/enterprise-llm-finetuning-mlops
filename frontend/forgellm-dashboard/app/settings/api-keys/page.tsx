'use client';

import { useState } from 'react';
import { PageHeader } from '@/components/layout/page-header';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Key, Plus, ShieldAlert, Copy, Check, Trash2 } from 'lucide-react';

export default function ApiKeysPage() {
  const [isCreating, setIsCreating] = useState(false);
  const [newKey, setNewKey] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  // Mock demo keys
  const keys = [
    { id: '1', name: 'Production Inference', project: 'Customer Support AI', scopes: ['models:read', 'models:inference'], created: 'Oct 12, 2026', expires: 'Never', status: 'Active' },
    { id: '2', name: 'CI/CD Pipeline', project: 'All Projects', scopes: ['models:deploy', 'deployments:read'], created: 'Sep 05, 2026', expires: 'Dec 31, 2026', status: 'Active' },
    { id: '3', name: 'Dev Testing', project: 'Internal Tools', scopes: ['*'], created: 'Aug 20, 2026', expires: 'Sep 20, 2026', status: 'Expired' },
  ];

  const handleCreate = (e: React.FormEvent) => {
    e.preventDefault();
    // Simulate generation
    setNewKey('fl_live_9h2j98h3u02jd092j3d0923jd029j');
  };

  const copyToClipboard = () => {
    if (newKey) {
      navigator.clipboard.writeText(newKey);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="flex-1 pb-8">
      <div className="px-6 py-6 border-b border-border bg-card flex justify-between items-start md:items-center">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">API Keys</h1>
          <p className="text-sm text-muted-foreground mt-1">Manage secure access credentials for ForgeLLM APIs.</p>
        </div>
        <Button onClick={() => setIsCreating(true)} className="shrink-0">
          <Plus className="w-4 h-4 mr-2" />
          Create API Key
        </Button>
      </div>

      <div className="p-6">
        {/* Secure Key Generation Modal */}
        {isCreating && (
          <div className="fixed inset-0 bg-background/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="bg-card border border-border shadow-lg rounded-xl max-w-lg w-full overflow-hidden">
              <div className="px-6 py-4 border-b border-border">
                <h2 className="text-lg font-semibold text-foreground">Generate New API Key</h2>
              </div>
              
              {!newKey ? (
                <form onSubmit={handleCreate} className="p-6 space-y-5">
                  <div>
                    <label className="block text-sm font-medium mb-1.5 text-foreground">Key Name</label>
                    <input type="text" className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-foreground" placeholder="e.g. Production Client" required />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1.5 text-foreground">Project Scope</label>
                    <select className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-foreground">
                      <option>All Projects (Organization Wide)</option>
                      <option>Customer Support AI</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1.5 text-foreground">Permissions</label>
                    <div className="space-y-2 border border-border rounded-md p-3 bg-secondary/20">
                      <label className="flex items-center gap-2"><input type="checkbox" defaultChecked className="rounded border-border" /> <span className="text-sm">Inference (models:inference)</span></label>
                      <label className="flex items-center gap-2"><input type="checkbox" defaultChecked className="rounded border-border" /> <span className="text-sm">Read Models (models:read)</span></label>
                      <label className="flex items-center gap-2"><input type="checkbox" className="rounded border-border" /> <span className="text-sm">Manage Deployments (deployments:write)</span></label>
                    </div>
                  </div>
                  <div className="flex justify-end gap-3 pt-2">
                    <Button type="button" variant="outline" onClick={() => setIsCreating(false)}>Cancel</Button>
                    <Button type="submit">Generate Key</Button>
                  </div>
                </form>
              ) : (
                <div className="p-6 space-y-6">
                  <div className="bg-destructive/10 text-destructive border border-destructive/20 rounded-lg p-4 flex gap-3">
                    <ShieldAlert className="shrink-0 w-5 h-5 mt-0.5" />
                    <div className="text-sm">
                      <p className="font-semibold mb-1">Please copy this key now.</p>
                      <p>For security reasons, you won't be able to view it again after closing this window.</p>
                    </div>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium mb-1.5 text-foreground">Your Secret Key</label>
                    <div className="flex gap-2">
                      <div className="flex-1 bg-secondary border border-border rounded-md px-3 py-2 text-sm font-mono break-all text-foreground">
                        {newKey}
                      </div>
                      <Button variant="outline" className="shrink-0" onClick={copyToClipboard}>
                        {copied ? <Check className="w-4 h-4 text-success" /> : <Copy className="w-4 h-4" />}
                      </Button>
                    </div>
                  </div>
                  
                  <div className="flex justify-end pt-2">
                    <Button onClick={() => { setIsCreating(false); setNewKey(null); }}>Done, I've copied it</Button>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        <Card className="shadow-sm">
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow className="border-border hover:bg-transparent">
                  <TableHead className="text-xs uppercase font-semibold">Name</TableHead>
                  <TableHead className="text-xs uppercase font-semibold">Project</TableHead>
                  <TableHead className="text-xs uppercase font-semibold">Scopes</TableHead>
                  <TableHead className="text-xs uppercase font-semibold">Created</TableHead>
                  <TableHead className="text-xs uppercase font-semibold">Status</TableHead>
                  <TableHead className="text-right text-xs uppercase font-semibold">Action</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {keys.map((k) => (
                  <TableRow key={k.id} className="border-border hover:bg-secondary/30 transition-colors">
                    <TableCell className="font-medium text-foreground">
                      <div className="flex items-center gap-2">
                        <Key size={14} className="text-muted-foreground" />
                        {k.name}
                      </div>
                    </TableCell>
                    <TableCell className="text-muted-foreground">{k.project}</TableCell>
                    <TableCell>
                      <div className="flex gap-1 flex-wrap">
                        {k.scopes.map(s => (
                          <Badge key={s} variant="secondary" className="text-[10px] font-mono bg-secondary/50">{s}</Badge>
                        ))}
                      </div>
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">{k.created}</TableCell>
                    <TableCell>
                      <Badge variant={k.status === 'Active' ? 'success' : 'secondary'} className="text-[10px] uppercase">
                        {k.status}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      <Button variant="ghost" size="icon" className="h-8 w-8 text-destructive hover:text-destructive hover:bg-destructive/10">
                        <Trash2 size={14} />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
