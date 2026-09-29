import { useQuery } from '@tanstack/react-query';
import { activityApi } from '@/lib/api/activity';
import { Card, CardContent } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { ActivitySquare, Fingerprint, MapPin, Monitor } from 'lucide-react';
import { formatDistanceToNow, format } from 'date-fns';
import { Badge } from '@/components/ui/badge';

export function ActivityTab({ projectId }: { projectId: string }) {
  const { data: logs = [], isLoading } = useQuery({
    queryKey: ['activity', projectId],
    queryFn: () => activityApi.list(projectId),
  });

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="h-10 w-48 bg-secondary animate-pulse rounded" />
        <Card className="shadow-sm">
          <CardContent className="h-64 flex items-center justify-center">
            <div className="h-8 w-8 rounded-full border-2 border-foreground border-t-transparent animate-spin" />
          </CardContent>
        </Card>
      </div>
    );
  }

  const formatAction = (action: string) => {
    return action.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
  };

  const getActionColor = (action: string) => {
    if (action.includes('create') || action.includes('import')) return 'bg-success/10 text-success border-success/20';
    if (action.includes('delete') || action.includes('revoke')) return 'bg-destructive/10 text-destructive border-destructive/20';
    if (action.includes('update')) return 'bg-primary/10 text-primary border-primary/20';
    return 'bg-secondary/20 text-foreground border-border';
  };

  return (
    <div className="space-y-6 max-w-6xl">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-xl font-semibold text-foreground">Activity Log</h2>
          <p className="text-sm text-muted-foreground mt-1">Audit trail of actions performed in this project.</p>
        </div>
      </div>

      <Card className="shadow-sm border-border">
        {logs.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-24 text-center">
            <div className="w-16 h-16 bg-secondary/50 rounded-full flex items-center justify-center mb-6 text-muted-foreground">
              <ActivitySquare size={24} />
            </div>
            <h3 className="text-lg font-medium text-foreground mb-2">No recent activity</h3>
            <p className="text-sm text-muted-foreground max-w-sm">
              There are no audit logs recorded for this project yet.
            </p>
          </div>
        ) : (
          <div className="overflow-hidden rounded-md">
            <Table>
              <TableHeader className="bg-secondary/20">
                <TableRow>
                  <TableHead className="font-medium">Action</TableHead>
                  <TableHead className="font-medium">User ID</TableHead>
                  <TableHead className="font-medium">Context</TableHead>
                  <TableHead className="font-medium">Timestamp</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {logs.map((log: any) => (
                  <TableRow key={log.id} className="hover:bg-secondary/10 transition-colors">
                    <TableCell>
                      <div className="flex items-center gap-3">
                        <div className={`px-2.5 py-1 rounded-md border text-xs font-medium ${getActionColor(log.action)}`}>
                          {formatAction(log.action)}
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2 text-sm text-muted-foreground">
                        <Fingerprint className="w-4 h-4" />
                        <span className="font-mono truncate max-w-[120px]">{log.user_id.substring(0, 8)}...</span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex flex-col gap-1 text-xs text-muted-foreground">
                        {log.target_type && log.target_id && (
                          <div className="flex items-center gap-1.5">
                            <Badge variant="outline" className="text-[9px] px-1 py-0 h-4 rounded-sm">{log.target_type}</Badge>
                            <span className="font-mono">{log.target_id.substring(0, 8)}...</span>
                          </div>
                        )}
                        {log.ip_address && (
                          <div className="flex items-center gap-1.5 opacity-60">
                            <MapPin className="w-3 h-3" />
                            {log.ip_address}
                          </div>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex flex-col text-sm">
                        <span className="text-foreground">
                          {formatDistanceToNow(new Date(log.created_at), { addSuffix: true })}
                        </span>
                        <span className="text-xs text-muted-foreground">
                          {format(new Date(log.created_at), 'MMM d, yyyy HH:mm')}
                        </span>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </Card>
    </div>
  );
}
