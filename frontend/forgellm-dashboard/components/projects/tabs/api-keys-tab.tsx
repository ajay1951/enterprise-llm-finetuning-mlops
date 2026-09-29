import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiKeysApi } from '@/lib/api/api-keys';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Key, Plus, Trash2, Copy, Check } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';

export function ApiKeysTab({ projectId }: { projectId: string }) {
  const queryClient = useQueryClient();
  const [isCreating, setIsCreating] = useState(false);
  const [newKeyName, setNewKeyName] = useState('');
  const [createdSecret, setCreatedSecret] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const { data: keys = [], isLoading } = useQuery({
    queryKey: ['apiKeys'], // Fetching all keys for the org for now
    queryFn: () => apiKeysApi.list(),
  });

  const createMutation = useMutation({
    mutationFn: () => apiKeysApi.create(newKeyName, projectId),
    onSuccess: (res) => {
      queryClient.invalidateQueries({ queryKey: ['apiKeys'] });
      setCreatedSecret(res.data.secret);
      setNewKeyName('');
    }
  });

  const revokeMutation = useMutation({
    mutationFn: (keyId: string) => apiKeysApi.revoke(keyId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['apiKeys'] });
    }
  });

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

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

  // Filter keys visually for this project (or show all if they are org level, but let's filter)
  const activeKeys = keys.filter(k => !k.revoked_at && (k.project_id === projectId || !k.project_id));

  return (
    <div className="space-y-6 max-w-6xl">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-xl font-semibold text-foreground">API Keys</h2>
          <p className="text-sm text-muted-foreground mt-1">Manage access tokens for your deployed models.</p>
        </div>
        <Button size="sm" onClick={() => setIsCreating(true)}>
          <Plus className="w-4 h-4 mr-2" />
          Generate New Key
        </Button>
      </div>

      {createdSecret && (
        <Card className="border-success/50 bg-success/5 shadow-sm">
          <CardContent className="p-6">
            <h3 className="text-lg font-medium text-foreground mb-2">Save your new API key</h3>
            <p className="text-sm text-muted-foreground mb-4">
              Please copy this key and store it securely. For security reasons, it will not be shown again.
            </p>
            <div className="flex items-center gap-2">
              <code className="flex-1 p-3 bg-background border border-border rounded-md text-sm font-mono break-all">
                {createdSecret}
              </code>
              <Button variant="outline" size="icon" onClick={() => handleCopy(createdSecret)}>
                {copied ? <Check className="w-4 h-4 text-success" /> : <Copy className="w-4 h-4" />}
              </Button>
            </div>
            <div className="mt-4 flex justify-end">
              <Button onClick={() => setCreatedSecret(null)}>I've saved it securely</Button>
            </div>
          </CardContent>
        </Card>
      )}

      {isCreating && !createdSecret && (
        <Card className="border-border shadow-sm">
          <CardContent className="p-6">
            <h3 className="text-lg font-medium text-foreground mb-4">Create New API Key</h3>
            <div className="space-y-4">
              <div className="space-y-2">
                <label className="text-sm font-medium text-foreground">Key Name</label>
                <input 
                  type="text" 
                  value={newKeyName}
                  onChange={(e) => setNewKeyName(e.target.value)}
                  placeholder="e.g. Production App Token"
                  className="w-full max-w-md h-10 px-3 text-sm bg-background border border-border rounded-md focus:outline-none focus:ring-1 focus:ring-ring"
                />
              </div>
              <div className="flex gap-2">
                <Button 
                  disabled={!newKeyName || createMutation.isPending}
                  onClick={() => createMutation.mutate()}
                >
                  {createMutation.isPending ? 'Generating...' : 'Generate Key'}
                </Button>
                <Button variant="outline" onClick={() => setIsCreating(false)}>Cancel</Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      <Card className="shadow-sm border-border">
        {activeKeys.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-24 text-center">
            <div className="w-16 h-16 bg-secondary/50 rounded-full flex items-center justify-center mb-6 text-muted-foreground">
              <Key size={24} />
            </div>
            <h3 className="text-lg font-medium text-foreground mb-2">No API keys found</h3>
            <p className="text-sm text-muted-foreground mb-6 max-w-sm">
              You don't have any active API keys. Create one to authenticate requests to your deployed endpoints.
            </p>
            <Button variant="outline" onClick={() => setIsCreating(true)}>
              Generate New Key
            </Button>
          </div>
        ) : (
          <div className="overflow-hidden rounded-md">
            <Table>
              <TableHeader className="bg-secondary/20">
                <TableRow>
                  <TableHead className="font-medium">Name</TableHead>
                  <TableHead className="font-medium">Key Prefix</TableHead>
                  <TableHead className="font-medium">Created</TableHead>
                  <TableHead className="text-right font-medium">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {activeKeys.map((k: any) => (
                  <TableRow key={k.id} className="hover:bg-secondary/10 transition-colors">
                    <TableCell>
                      <span className="font-medium text-foreground">{k.name}</span>
                    </TableCell>
                    <TableCell>
                      <code className="text-xs text-muted-foreground bg-secondary/50 px-2 py-1 rounded">
                        {k.key_prefix}
                      </code>
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {formatDistanceToNow(new Date(k.created_at || new Date()), { addSuffix: true })}
                    </TableCell>
                    <TableCell className="text-right">
                      <Button 
                        variant="ghost" 
                        size="icon" 
                        className="h-8 w-8 text-destructive hover:text-destructive hover:bg-destructive/10"
                        onClick={() => {
                          if (confirm('Are you sure you want to revoke this API key? This action cannot be undone.')) {
                            revokeMutation.mutate(k.id);
                          }
                        }}
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
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
