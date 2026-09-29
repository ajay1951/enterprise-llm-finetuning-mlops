import { useState, useEffect, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { trainingApi } from '@/lib/api';
import { X } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';

interface LogsDialogProps {
  jobId: string | null;
  isOpen: boolean;
  onClose: () => void;
}

export function LogsDialog({ jobId, isOpen, onClose }: LogsDialogProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  const { data: logs = [], isLoading } = useQuery({
    queryKey: ['trainingLogs', jobId],
    queryFn: () => jobId ? trainingApi.getLogs(jobId) : Promise.resolve({ data: [] }),
    enabled: isOpen && !!jobId,
    refetchInterval: 3000, // Poll every 3 seconds for new logs
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
          <h2 className="text-lg font-semibold text-foreground font-mono">Job Logs: {jobId?.substring(0,8)}...</h2>
          <Button variant="ghost" size="icon" className="w-8 h-8 rounded-full" onClick={onClose}>
            <X className="w-4 h-4 text-muted-foreground" />
          </Button>
        </div>
        
        <div 
          ref={scrollRef}
          className="flex-1 p-4 bg-[#0c0c0c] overflow-y-auto font-mono text-sm"
        >
          {isLoading ? (
            <div className="text-muted-foreground animate-pulse">Loading logs...</div>
          ) : logs.length === 0 ? (
            <div className="text-muted-foreground">No logs available yet.</div>
          ) : (
            <div className="space-y-1">
              {logs.map((log: any) => (
                <div key={log.id} className="text-gray-300">
                  <span className="text-gray-500 mr-4">
                    {new Date(log.timestamp).toISOString().split('T')[1].split('.')[0]}
                  </span>
                  <span className={
                    log.level?.toLowerCase() === 'error' ? 'text-red-400' : 
                    log.level?.toLowerCase() === 'warning' ? 'text-yellow-400' : 
                    'text-gray-300'
                  }>
                    [{log.level}] 
                  </span>
                  <span className="ml-2">
                    {log.message}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
