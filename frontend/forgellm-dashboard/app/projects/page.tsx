'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Button } from '@/components/ui/button';
import { projectsApi } from '@/lib/api';
import Link from 'next/link';
import { Search, Plus, FolderKanban, Activity, Box, Play, Clock, MoreVertical } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

export default function ProjectsPage() {
  const queryClient = useQueryClient();
  const [isCreating, setIsCreating] = useState(false);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [searchQuery, setSearchQuery] = useState('');

  const { data: projects = [], isLoading } = useQuery({
    queryKey: ['projects'],
    queryFn: projectsApi.list,
  });

  const createMutation = useMutation({
    mutationFn: (data: { name: string; description?: string }) => projectsApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      setIsCreating(false);
      setName('');
      setDescription('');
    },
  });

  const handleCreate = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    createMutation.mutate({ name: name.trim(), description: description.trim() });
  };

  const filteredProjects = projects.filter(p => 
    p.name.toLowerCase().includes(searchQuery.toLowerCase()) || 
    (p.description && p.description.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  return (
    <div className="flex-1 pb-8">
      {/* Header */}
      <div className="px-6 py-6 border-b border-border bg-card flex justify-between items-start md:items-center flex-col md:flex-row gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">Projects</h1>
          <p className="text-sm text-muted-foreground mt-1">Manage your workspaces, models, and fine-tuning experiments.</p>
        </div>
        <div className="flex items-center gap-3 w-full md:w-auto">
          <div className="relative flex-1 md:w-64">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <input 
              type="text"
              placeholder="Search projects..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-4 py-2 bg-background border border-border rounded-md text-sm focus:outline-none focus:ring-1 focus:ring-foreground transition-all"
            />
          </div>
          <Button onClick={() => setIsCreating(!isCreating)} className="shrink-0 h-9">
            <Plus className="w-4 h-4 mr-2" />
            New Project
          </Button>
        </div>
      </div>
      
      {/* Create Form */}
      {isCreating && (
        <div className="px-6 mt-6">
          <div className="bg-card border border-border rounded-lg p-5 shadow-sm max-w-2xl">
            <h2 className="text-sm font-semibold mb-4 uppercase tracking-wider text-muted-foreground">Create New Project</h2>
            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="block text-xs font-medium mb-1.5 text-foreground">Project Name</label>
                <input 
                  type="text" 
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-foreground transition-all" 
                  placeholder="e.g. customer-support-v1" 
                  required 
                />
              </div>
              <div>
                <label className="block text-xs font-medium mb-1.5 text-foreground">Description</label>
                <textarea 
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-foreground transition-all" 
                  rows={2} 
                  placeholder="Brief description of this project's purpose" 
                />
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <Button variant="outline" type="button" size="sm" onClick={() => setIsCreating(false)}>Cancel</Button>
                <Button type="submit" size="sm" disabled={createMutation.isPending}>
                  {createMutation.isPending ? 'Creating...' : 'Create Project'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Grid */}
      <div className="px-6 mt-6">
        {isLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {[1, 2, 3].map(i => (
              <div key={i} className="h-[200px] rounded-lg border border-border bg-card animate-pulse" />
            ))}
          </div>
        ) : filteredProjects.length === 0 ? (
          <div className="border border-dashed border-border rounded-lg bg-secondary/10 p-12 text-center max-w-xl mx-auto mt-12">
            <FolderKanban className="w-10 h-10 text-muted-foreground mx-auto mb-4 opacity-50" />
            <h3 className="text-lg font-medium text-foreground mb-1">No projects found</h3>
            <p className="text-sm text-muted-foreground mb-6">
              {searchQuery ? "No projects match your search criteria." : "Create your first AI workspace to get started."}
            </p>
            {!searchQuery && (
              <Button onClick={() => setIsCreating(true)}>
                <Plus className="w-4 h-4 mr-2" />
                Create Project
              </Button>
            )}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {filteredProjects.map((project) => (
              <Link key={project.id} href={`/projects/${project.id}`}>
                <div className="group h-full bg-card border border-border rounded-lg p-5 hover:border-foreground/30 hover:shadow-sm transition-all flex flex-col cursor-pointer relative overflow-hidden">
                  
                  {/* Decorative Gradient Line */}
                  <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-foreground/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />

                  <div className="flex justify-between items-start mb-3">
                    <div>
                      <h3 className="font-semibold text-foreground group-hover:text-primary transition-colors">{project.name}</h3>
                      <p className="text-sm text-muted-foreground mt-1 line-clamp-2 min-h-[40px]">
                        {project.description || 'No description provided.'}
                      </p>
                    </div>
                    <button className="text-muted-foreground hover:text-foreground p-1 transition-colors z-10" onClick={(e) => e.preventDefault()}>
                      <MoreVertical size={16} />
                    </button>
                  </div>

                  {/* Mock Metrics for Data Density */}
                  <div className="grid grid-cols-3 gap-2 py-4 border-y border-border/50 mt-auto">
                    <div>
                      <div className="flex items-center gap-1.5 text-xs text-muted-foreground mb-1">
                        <Box size={12} /> Models
                      </div>
                      <div className="text-sm font-medium font-mono text-foreground">{Math.floor(Math.random() * 10)}</div>
                    </div>
                    <div>
                      <div className="flex items-center gap-1.5 text-xs text-muted-foreground mb-1">
                        <Activity size={12} /> Training
                      </div>
                      <div className="text-sm font-medium font-mono text-foreground">{Math.floor(Math.random() * 5)}</div>
                    </div>
                    <div>
                      <div className="flex items-center gap-1.5 text-xs text-muted-foreground mb-1">
                        <Play size={12} /> Deploys
                      </div>
                      <div className="text-sm font-medium font-mono text-foreground">{Math.floor(Math.random() * 3)}</div>
                    </div>
                  </div>

                  <div className="flex items-center justify-between mt-4 text-xs text-muted-foreground">
                    <div className="flex items-center gap-1.5">
                      <Clock size={12} />
                      Updated {Math.floor(Math.random() * 59) + 1} min ago
                    </div>
                    <Badge variant="secondary" className="text-[10px] bg-secondary/50 font-mono text-muted-foreground px-1.5 py-0">
                      {project.id.split('-')[0]}
                    </Badge>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
