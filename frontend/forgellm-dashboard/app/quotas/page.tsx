'use client';

import { PageHeader } from '@/components/layout/page-header';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';

export default function QuotasPage() {
  return (
    <div className="flex-1 space-y-4 p-8 pt-6">
      <PageHeader title="Resource Quotas & Capacity" description="Manage project limits and monitor global cluster capacity." />

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">GPU Quota</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">2 / 4</div>
            <Progress value={50} className="mt-2" />
            <p className="text-xs text-muted-foreground mt-2">50% of allocated limit used</p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Replicas Quota</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">3 / 10</div>
            <Progress value={30} className="mt-2" />
            <p className="text-xs text-muted-foreground mt-2">30% of allocated limit used</p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Global GPU Capacity</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">8 / 12</div>
            <Progress value={66} className="mt-2" />
            <p className="text-xs text-muted-foreground mt-2">66% of cluster capacity active</p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Offline GPUs</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-destructive">1</div>
            <p className="text-xs text-muted-foreground mt-2">Maintenance required</p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
