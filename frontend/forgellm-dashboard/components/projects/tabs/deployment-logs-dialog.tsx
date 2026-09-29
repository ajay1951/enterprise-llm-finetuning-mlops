import { useQuery } from '@tanstack/react-query';
import { deploymentsApi } from '@/lib/api';
import { Loader2, X } from 'lucide-react';
import { format } from 'date-fns';
import { Button } from '@/components/ui/button';
import { useEffect, useRef } from 'react';

interface DeploymentLogsDialogProps {
  deploymentId: string | null;
  isOpen: boolean;
  onClose: () => void;
}

export function DeploymentLogsDialog({ deploymentId, isOpen, onClose }: DeploymentLogsDialogProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  const { data: logs = [], isLoading } = useQuery({
    queryKey: ['deployments', deploymentId, 'logs'],
    queryFn: () => deploymentId ? deploymentsApi.getLogs(deploymentId) : Promise.resolve([]),
    enabled: !!deploymentId && isOpen,
    refetchInterval: 3000, // refresh logs every 3s
  });

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm p-4">
      <div className="w-full max-w-4xl h-[80vh] flex flex-col bg-card border border-border shadow-lg rounded-xl overflow-hidden">
        <div className="flex items-center justify-between px-6 py-4 border-b border-border">
          <h2 className="font-mono text-sm flex items-center gap-2 text-foreground">
            <span className="w-2 h-2 rounded-full bg-success animate-pulse" />
            Deployment Logs: {deploymentId?.substring(0, 8)}...
          </h2>
          <Button variant="ghost" size="icon" className="w-8 h-8 rounded-full" onClick={onClose}>
            <X className="w-4 h-4 text-muted-foreground" />
          </Button>
        </div>
        
        <div className="flex-1 bg-black/90 overflow-hidden relative font-mono text-xs">
          {isLoading ? (
            <div className="absolute inset-0 flex items-center justify-center text-muted-foreground">
              <Loader2 className="w-5 h-5 animate-spin mr-2" /> Loading logs...
            </div>
          ) : logs.length === 0 ? (
            <div className="absolute inset-0 flex items-center justify-center text-muted-foreground">
              No logs available yet.
            </div>
          ) : (
            <div ref={scrollRef} className="h-full w-full p-4 overflow-y-auto">
              <div className="space-y-1">
                {logs.map((log: any, i: number) => (
                  <div key={i} className="flex gap-4 hover:bg-white/5 py-0.5 rounded px-1 transition-colors group">
                    <span className="text-muted-foreground/50 w-24 shrink-0">
                      {log.timestamp ? format(new Date(log.timestamp), 'HH:mm:ss') : ''}
                    </span>
                    <span className="text-primary/70 shrink-0 w-32 overflow-hidden text-ellipsis whitespace-nowrap">
                      [{log.event_type}]
                    </span>
                    <span className="text-foreground/90 whitespace-pre-wrap break-all">
                      {log.data?.message || JSON.stringify(log.data)}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
