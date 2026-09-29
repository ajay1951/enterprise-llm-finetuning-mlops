'use client';

import { PageHeader } from '@/components/layout/page-header';
import { Card, CardContent } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { ShieldAlert, Search, Filter } from 'lucide-react';
import { Button } from '@/components/ui/button';

export default function AuditLogsPage() {
  // Mock demo audit logs
  const logs = [
    { id: '1', action: 'MODEL_DEPLOYED', resource: 'customer-support-v2', user: 'Ajay (Owner)', project: 'Customer Support AI', ip: '192.168.1.42', time: '12 mins ago', status: 'SUCCESS' },
    { id: '2', action: 'API_KEY_CREATED', resource: 'production-inference', user: 'Ajay (Owner)', project: 'Customer Support AI', ip: '192.168.1.42', time: '14 mins ago', status: 'SUCCESS' },
    { id: '3', action: 'ACCESS_DENIED', resource: 'deployment/delete', user: 'Viewer Account', project: 'Customer Support AI', ip: '10.0.0.15', time: '1 hour ago', status: 'FAILURE' },
    { id: '4', action: 'PROJECT_CREATED', resource: 'Internal Tools', user: 'Sarah (Admin)', project: 'Internal Tools', ip: '192.168.1.105', time: '2 days ago', status: 'SUCCESS' },
    { id: '5', action: 'DATASET_UPLOADED', resource: 'feedback_q3.csv', user: 'Sarah (Admin)', project: 'Customer Support AI', ip: '192.168.1.105', time: '2 days ago', status: 'SUCCESS' },
  ];

  return (
    <div className="flex-1 pb-8">
      <div className="px-6 py-6 border-b border-border bg-card flex justify-between items-start md:items-center">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">Audit Logs</h1>
          <p className="text-sm text-muted-foreground mt-1">Track every important action across your organization.</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" className="h-9">
            <Filter className="w-4 h-4 mr-2" />
            Filter
          </Button>
          <div className="relative w-64 hidden md:block">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <input 
              type="text"
              placeholder="Search logs..."
              className="w-full pl-9 pr-4 py-1.5 bg-background border border-border rounded-md text-sm focus:outline-none focus:ring-1 focus:ring-foreground"
            />
          </div>
        </div>
      </div>

      <div className="p-6">
        <Card className="shadow-sm">
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow className="border-border hover:bg-transparent">
                  <TableHead className="text-xs uppercase font-semibold w-12"></TableHead>
                  <TableHead className="text-xs uppercase font-semibold">Action</TableHead>
                  <TableHead className="text-xs uppercase font-semibold">Resource</TableHead>
                  <TableHead className="text-xs uppercase font-semibold">User</TableHead>
                  <TableHead className="text-xs uppercase font-semibold">Project</TableHead>
                  <TableHead className="text-xs uppercase font-semibold">IP Address</TableHead>
                  <TableHead className="text-right text-xs uppercase font-semibold">Time</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {logs.map((log) => (
                  <TableRow key={log.id} className="border-border hover:bg-secondary/30 transition-colors cursor-pointer group">
                    <TableCell>
                      <div className={`w-2 h-2 rounded-full ${log.status === 'SUCCESS' ? 'bg-foreground' : 'bg-destructive'}`} />
                    </TableCell>
                    <TableCell className="font-mono text-xs font-medium text-foreground">
                      {log.action}
                    </TableCell>
                    <TableCell className="text-sm text-foreground">{log.resource}</TableCell>
                    <TableCell className="text-sm text-muted-foreground">{log.user}</TableCell>
                    <TableCell className="text-sm text-muted-foreground">{log.project}</TableCell>
                    <TableCell className="text-xs font-mono text-muted-foreground">{log.ip}</TableCell>
                    <TableCell className="text-sm text-right text-muted-foreground whitespace-nowrap">{log.time}</TableCell>
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
