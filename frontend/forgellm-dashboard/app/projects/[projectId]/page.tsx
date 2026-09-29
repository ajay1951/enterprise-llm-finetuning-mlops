'use client';

import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { datasetsApi, trainingApi, modelsApi, deploymentsApi } from '@/lib/api';
import { Database, Activity, Box, Play, Key, Users } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useParams, useRouter } from 'next/navigation';
import { Badge } from '@/components/ui/badge';

export default function ProjectOverviewPage() {
  const { projectId } = useParams() as { projectId: string };
  const router = useRouter();

  const { data: datasets = [] } = useQuery({
    queryKey: ['datasets', projectId],
    queryFn: () => datasetsApi.list(projectId),
  });

  const { data: jobs = [] } = useQuery({
    queryKey: ['trainingJobs', projectId],
    queryFn: () => trainingApi.list(projectId),
  });

  const { data: models = [] } = useQuery({
    queryKey: ['models', projectId],
    queryFn: () => modelsApi.list(projectId),
  });

  const { data: deployments = [] } = useQuery({
    queryKey: ['deployments', projectId],
    queryFn: () => deploymentsApi.list(projectId),
  });

  return (
    <div className="space-y-6 max-w-6xl">
      
      {/* Metrics Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: 'Models', value: models.length.toString(), icon: Box },
          { label: 'Deployments', value: deployments.length.toString(), icon: Play },
          { label: 'Datasets', value: datasets.length.toString(), icon: Database },
          { label: 'Training Jobs', value: jobs.length.toString(), icon: Activity },
        ].map((m, i) => (
          <Card key={i} className="shadow-sm">
            <CardContent className="p-4 flex items-center justify-between">
              <div>
                <p className="text-caption mb-1">{m.label}</p>
                <p className="text-2xl text-metric text-foreground">{m.value}</p>
              </div>
              <div className="w-10 h-10 rounded-md bg-secondary flex items-center justify-center text-muted-foreground">
                <m.icon size={18} />
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Quick Actions & Recent Activity */}
      <div className="grid md:grid-cols-3 gap-6">
        
        <div className="md:col-span-2 space-y-6">
          <Card className="shadow-sm">
            <CardHeader className="pb-3 border-b border-border">
              <CardTitle className="text-sm font-medium">Recent Activity</CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <div className="divide-y divide-border">
                {[
                  { text: 'Deployed customer-support-v2 to production', time: '12 min ago', icon: Play },
                  { text: 'Completed fine-tuning job FT-892', time: '2 hours ago', icon: Activity },
                  { text: 'Uploaded dataset feedback_q3.csv', time: '1 day ago', icon: Database },
                ].map((activity, i) => (
                  <div key={i} className="p-4 flex items-start gap-4 hover:bg-secondary/20 transition-colors">
                    <div className="mt-0.5 text-muted-foreground"><activity.icon size={16} /></div>
                    <div>
                      <p className="text-sm text-foreground">{activity.text}</p>
                      <p className="text-xs text-muted-foreground mt-1">{activity.time}</p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="space-y-6">
          <Card className="shadow-sm">
            <CardHeader className="pb-3 border-b border-border">
              <CardTitle className="text-sm font-medium">Project Members</CardTitle>
            </CardHeader>
            <CardContent className="p-4">
              <div className="space-y-4">
                {[
                  { name: 'Ajay (You)', role: 'OWNER' },
                  { name: 'Sarah Developer', role: 'DEVELOPER' },
                  { name: 'Service Account', role: 'API' },
                ].map((member, i) => (
                  <div key={i} className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className="w-6 h-6 rounded-full bg-secondary flex items-center justify-center text-[10px] font-bold">{member.name[0]}</div>
                      <span className="text-sm text-foreground">{member.name}</span>
                    </div>
                    <Badge variant="secondary" className="text-[10px] font-mono">{member.role}</Badge>
                  </div>
                ))}
              </div>
              <Button variant="outline" className="w-full mt-4 text-xs h-8">
                <Users size={14} className="mr-2" />
                Manage Access
              </Button>
            </CardContent>
          </Card>

          <Card className="shadow-sm">
            <CardHeader className="pb-3 border-b border-border">
              <CardTitle className="text-sm font-medium">API Access</CardTitle>
            </CardHeader>
            <CardContent className="p-4">
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm text-muted-foreground">Active Keys</span>
                <span className="text-sm font-mono text-foreground">3</span>
              </div>
              <div className="flex justify-between items-center mb-4">
                <span className="text-sm text-muted-foreground">Requests (24h)</span>
                <span className="text-sm font-mono text-foreground">12.4k</span>
              </div>
              <Button 
                variant="outline" 
                className="w-full text-xs h-8" 
                onClick={() => router.push(`/projects/${projectId}/api-keys`)}
              >
                <Key size={14} className="mr-2" />
                Manage API Keys
              </Button>
            </CardContent>
          </Card>
        </div>

      </div>
    </div>
  );
}
