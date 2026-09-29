'use client';

import { useQuery } from '@tanstack/react-query';
import { projectsApi } from '@/lib/api';
import { Settings, Play, ShieldAlert } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useParams, usePathname } from 'next/navigation';
import { Badge } from '@/components/ui/badge';
import Link from 'next/link';

const TABS = [
  { name: 'Overview', href: '' },
  { name: 'Models', href: '/models' },
  { name: 'Registry', href: '/registry' },
  { name: 'Datasets', href: '/datasets' },
  { name: 'Training', href: '/training' },
  { name: 'Experiments', href: '/experiments' },
  { name: 'Deployments', href: '/deployments' },
  { name: 'API Keys', href: '/api-keys' },
  { name: 'Activity', href: '/activity' }
];

export default function ProjectLayout({ children }: { children: React.ReactNode }) {
  const { projectId } = useParams() as { projectId: string };
  const pathname = usePathname();

  const { data: project, isLoading: loadingProject } = useQuery({
    queryKey: ['projects', projectId],
    queryFn: () => projectsApi.get(projectId),
  });

  if (loadingProject) return (
    <div className="flex-1 p-8">
      <div className="h-8 w-64 bg-secondary animate-pulse rounded mb-4" />
      <div className="h-4 w-96 bg-secondary/50 animate-pulse rounded" />
    </div>
  );
  
  if (!project) return (
    <div className="flex-1 p-12 flex flex-col items-center justify-center text-center">
      <div className="w-12 h-12 rounded-full bg-destructive/10 text-destructive flex items-center justify-center mb-4">
        <ShieldAlert />
      </div>
      <h2 className="text-xl font-semibold mb-2">Project not found</h2>
      <p className="text-muted-foreground text-sm">The project you're looking for doesn't exist or you don't have access.</p>
    </div>
  );

  return (
    <div className="flex-1 flex flex-col h-full bg-background overflow-hidden">
      {/* Header Area */}
      <div className="px-6 pt-6 bg-card border-b border-border shrink-0">
        <div className="flex justify-between items-start mb-6">
          <div>
            <div className="flex items-center gap-3 mb-1">
              <h1 className="text-2xl font-semibold tracking-tight text-foreground">{project.name}</h1>
              <Badge variant="outline" className="bg-success/10 text-success border-success/20 text-[10px] uppercase">Active</Badge>
            </div>
            <p className="text-sm text-muted-foreground">{project.description || 'No description provided.'}</p>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" className="h-8 text-xs">
              <Settings className="w-3.5 h-3.5 mr-2" />
              Settings
            </Button>
            <Button size="sm" className="h-8 text-xs" asChild>
              <Link href={`/projects/${projectId}/models`}>
                <Play className="w-3.5 h-3.5 mr-2" />
                Deploy
              </Link>
            </Button>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex space-x-1 overflow-x-auto no-scrollbar">
          {TABS.map(tab => {
            const tabPath = `/projects/${projectId}${tab.href}`;
            const isActive = tab.href === '' 
              ? pathname === `/projects/${projectId}` 
              : pathname.startsWith(tabPath);
              
            return (
              <Link
                key={tab.name}
                href={tabPath}
                className={`px-4 py-2 text-sm font-medium border-b-2 whitespace-nowrap transition-colors ${
                  isActive
                    ? 'border-foreground text-foreground'
                    : 'border-transparent text-muted-foreground hover:text-foreground hover:border-border'
                }`}
              >
                {tab.name}
              </Link>
            );
          })}
        </div>
      </div>
      
      {/* Scrollable Content Area */}
      <div className="flex-1 overflow-y-auto p-6">
        {children}
      </div>
    </div>
  );
}
