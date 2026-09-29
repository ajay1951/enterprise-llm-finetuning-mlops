'use client';

import { useQuery } from '@tanstack/react-query';
import { PageHeader } from '@/components/layout/page-header';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { projectsApi, trainingApi } from '@/lib/api';
import { FolderKanban, Activity, Database, Box, Key, ActivitySquare } from 'lucide-react';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Area, AreaChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

const mockChartData = [
  { time: '00:00', requests: 120 },
  { time: '04:00', requests: 400 },
  { time: '08:00', requests: 850 },
  { time: '12:00', requests: 2300 },
  { time: '16:00', requests: 1800 },
  { time: '20:00', requests: 900 },
  { time: '24:00', requests: 300 },
];

export default function DashboardPage() {
  const { data: projects = [], isLoading: loadingProjects } = useQuery({
    queryKey: ['projects'],
    queryFn: projectsApi.list,
  });

  const { data: jobs = [], isLoading: loadingJobs } = useQuery({
    queryKey: ['trainingJobs'],
    queryFn: () => trainingApi.list(),
  });

  // Mock demo data
  const isDemo = true;
  const metrics = [
    { name: 'PROJECTS', value: isDemo ? '08' : (loadingProjects ? '-' : projects.length.toString().padStart(2, '0')) },
    { name: 'MODELS', value: isDemo ? '24' : '-' },
    { name: 'DEPLOYMENTS', value: isDemo ? '12' : '-' },
    { name: 'API REQUESTS', value: isDemo ? '1.42M' : '-' },
    { name: 'ACTIVE KEYS', value: isDemo ? '17' : '-' },
  ];

  return (
    <div className="flex-1 pb-8">
      <div className="px-6 py-6 border-b border-border bg-card flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">ForgeLLM Overview</h1>
          <p className="text-sm text-muted-foreground mt-1">Your AI infrastructure, secure and under control.</p>
        </div>
        {isDemo && (
          <Badge variant="outline" className="text-[10px] tracking-widest bg-secondary/50">DEMO ENVIRONMENT</Badge>
        )}
      </div>
      
      <div className="p-6">
        {/* KPI Metric Blocks */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-px bg-border rounded-lg overflow-hidden border border-border">
          {metrics.map((m) => (
            <div key={m.name} className="bg-card p-5 hover:bg-secondary/20 transition-colors">
              <div className="text-caption mb-1">{m.name}</div>
              <div className="text-3xl text-metric text-foreground">{m.value}</div>
            </div>
          ))}
        </div>

        {/* Charts and Tables Area */}
        <div className="grid gap-6 md:grid-cols-3 mt-6">
          <Card className="md:col-span-2 shadow-sm">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground uppercase tracking-wider">API Requests (24h)</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-[250px] w-full mt-4">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={mockChartData} margin={{ top: 5, right: 0, left: -20, bottom: 0 }}>
                    <defs>
                      <linearGradient id="colorRequests" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="hsl(var(--foreground))" stopOpacity={0.1}/>
                        <stop offset="95%" stopColor="hsl(var(--foreground))" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <XAxis 
                      dataKey="time" 
                      stroke="hsl(var(--muted-foreground))" 
                      fontSize={11}
                      tickLine={false}
                      axisLine={false}
                    />
                    <YAxis 
                      stroke="hsl(var(--muted-foreground))" 
                      fontSize={11}
                      tickLine={false}
                      axisLine={false}
                      tickFormatter={(value) => `${value}`}
                    />
                    <Tooltip 
                      contentStyle={{ backgroundColor: 'hsl(var(--card))', borderColor: 'hsl(var(--border))', borderRadius: '6px' }}
                      itemStyle={{ color: 'hsl(var(--foreground))' }}
                      labelStyle={{ color: 'hsl(var(--muted-foreground))', marginBottom: '4px' }}
                    />
                    <Area 
                      type="monotone" 
                      dataKey="requests" 
                      stroke="hsl(var(--foreground))" 
                      strokeWidth={2}
                      fillOpacity={1} 
                      fill="url(#colorRequests)" 
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>

          <Card className="shadow-sm flex flex-col">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground uppercase tracking-wider">Recent Security Events</CardTitle>
            </CardHeader>
            <CardContent className="flex-1 flex flex-col justify-between">
              <div className="space-y-4 mt-2">
                {[
                  { action: 'API_KEY_CREATED', user: 'Ajay', time: '14 mins ago', status: 'success' },
                  { action: 'ACCESS_DENIED', user: 'Viewer', time: '1 hour ago', status: 'destructive' },
                  { action: 'MODEL_DEPLOYED', user: 'Ajay', time: '2 hours ago', status: 'success' }
                ].map((event, i) => (
                  <div key={i} className="flex justify-between items-start">
                    <div className="flex gap-3">
                      <div className={`mt-0.5 w-2 h-2 rounded-full ${event.status === 'success' ? 'bg-foreground' : 'bg-destructive'}`} />
                      <div>
                        <div className="text-xs font-mono font-medium text-foreground">{event.action}</div>
                        <div className="text-xs text-muted-foreground mt-0.5">{event.user}</div>
                      </div>
                    </div>
                    <div className="text-xs text-muted-foreground">{event.time}</div>
                  </div>
                ))}
              </div>
              <Button variant="outline" className="w-full mt-6 text-xs h-8" asChild>
                <Link href="/settings/audit-logs">View All Audit Logs</Link>
              </Button>
            </CardContent>
          </Card>
        </div>

        <div className="mt-6">
          <Card className="shadow-sm">
            <CardHeader className="pb-4">
              <CardTitle className="text-sm font-medium text-muted-foreground uppercase tracking-wider">Active Training Jobs</CardTitle>
            </CardHeader>
            <CardContent>
              {jobs.length === 0 ? (
                <div className="text-sm text-muted-foreground py-8 text-center border border-dashed border-border rounded-lg bg-secondary/20">
                  No training jobs running.
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow className="border-border hover:bg-transparent">
                      <TableHead className="text-xs uppercase font-semibold">Model</TableHead>
                      <TableHead className="text-xs uppercase font-semibold">Method</TableHead>
                      <TableHead className="text-xs uppercase font-semibold">Status</TableHead>
                      <TableHead className="text-xs uppercase font-semibold">Progress</TableHead>
                      <TableHead className="text-right text-xs uppercase font-semibold">Action</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {jobs.slice(0, 5).map((job) => (
                      <TableRow key={job.id} className="border-border border-b hover:bg-secondary/30 transition-colors">
                        <TableCell className="font-medium text-foreground">{job.model_name}</TableCell>
                        <TableCell className="text-muted-foreground">{job.method}</TableCell>
                        <TableCell>
                          <Badge variant={job.status === 'completed' ? 'success' : job.status === 'failed' ? 'destructive' : job.status === 'running' ? 'default' : 'secondary'} className="rounded-sm font-mono text-[10px]">
                            {job.status}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-metric">
                          {job.total_steps > 0 ? Math.round((job.current_step / job.total_steps) * 100) + '%' : '-'}
                        </TableCell>
                        <TableCell className="text-right">
                          <Link href={`/projects/${job.project_id}/training/${job.id}`}>
                            <Button variant="ghost" size="sm" className="h-7 text-xs">View</Button>
                          </Link>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
