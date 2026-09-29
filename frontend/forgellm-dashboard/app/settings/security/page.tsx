'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ShieldCheck, Key, Activity, Users, Plus } from 'lucide-react';

export default function SecurityCenterPage() {
  const members = [
    { name: 'Ajay (You)', email: 'ajay@forgellm.com', role: 'OWNER', lastActive: 'Just now' },
    { name: 'Sarah Developer', email: 'sarah@forgellm.com', role: 'DEVELOPER', lastActive: '2 hrs ago' },
    { name: 'David Analyst', email: 'david@forgellm.com', role: 'VIEWER', lastActive: '1 day ago' },
  ];

  return (
    <div className="flex-1 pb-8">
      <div className="px-6 py-6 border-b border-border bg-card">
        <h1 className="text-2xl font-semibold tracking-tight text-foreground">Security Center</h1>
        <p className="text-sm text-muted-foreground mt-1">Manage authentication, roles, and monitor platform health.</p>
      </div>

      <div className="p-6 space-y-6">
        
        {/* Security Status Cards */}
        <h2 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">Platform Status</h2>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[
            { label: 'Authentication', value: 'Healthy', icon: ShieldCheck, status: 'success' },
            { label: 'API Keys', value: '3 Active', icon: Key, status: 'success' },
            { label: 'Rate Limiting', value: 'Operational', icon: Activity, status: 'success' },
            { label: 'Audit Logging', value: 'Operational', icon: Activity, status: 'success' },
          ].map((s, i) => (
            <Card key={i} className="shadow-sm">
              <CardContent className="p-5 flex items-center justify-between">
                <div>
                  <p className="text-caption mb-1">{s.label}</p>
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-foreground" />
                    <p className="text-sm font-medium text-foreground">{s.value}</p>
                  </div>
                </div>
                <div className="text-muted-foreground"><s.icon size={20} /></div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* RBAC Table */}
        <div className="mt-8 flex justify-between items-end mb-4">
          <h2 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">Members & Roles</h2>
          <Button size="sm" className="h-8">
            <Plus className="w-4 h-4 mr-2" />
            Invite Member
          </Button>
        </div>
        <Card className="shadow-sm">
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow className="border-border hover:bg-transparent">
                  <TableHead className="text-xs uppercase font-semibold">User</TableHead>
                  <TableHead className="text-xs uppercase font-semibold">Role</TableHead>
                  <TableHead className="text-xs uppercase font-semibold">Last Active</TableHead>
                  <TableHead className="text-right text-xs uppercase font-semibold">Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {members.map((m) => (
                  <TableRow key={m.email} className="border-border hover:bg-secondary/30 transition-colors">
                    <TableCell>
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded bg-secondary flex items-center justify-center text-xs font-bold">{m.name[0]}</div>
                        <div>
                          <div className="font-medium text-foreground text-sm">{m.name}</div>
                          <div className="text-xs text-muted-foreground">{m.email}</div>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="secondary" className="text-[10px] font-mono bg-secondary/50">{m.role}</Badge>
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">{m.lastActive}</TableCell>
                    <TableCell className="text-right">
                      <Badge variant="outline" className="text-[10px] bg-success/10 text-success border-success/20 uppercase">Active</Badge>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
        
        {/* Role Explanations */}
        <div className="grid md:grid-cols-2 gap-4 mt-4">
          <div className="border border-border rounded-lg bg-secondary/10 p-4">
            <h3 className="text-sm font-semibold text-foreground mb-3 flex items-center gap-2"><Badge variant="secondary" className="font-mono text-[10px]">DEVELOPER</Badge></h3>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <div className="text-muted-foreground mb-2 text-xs uppercase">Can</div>
                <ul className="space-y-1 text-foreground">
                  <li className="flex items-center gap-2"><span className="text-success">✓</span> Run training</li>
                  <li className="flex items-center gap-2"><span className="text-success">✓</span> Deploy models</li>
                  <li className="flex items-center gap-2"><span className="text-success">✓</span> Run inference</li>
                </ul>
              </div>
              <div>
                <div className="text-muted-foreground mb-2 text-xs uppercase">Cannot</div>
                <ul className="space-y-1 text-muted-foreground">
                  <li className="flex items-center gap-2"><span>✕</span> Manage organization</li>
                  <li className="flex items-center gap-2"><span>✕</span> Manage users</li>
                </ul>
              </div>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
