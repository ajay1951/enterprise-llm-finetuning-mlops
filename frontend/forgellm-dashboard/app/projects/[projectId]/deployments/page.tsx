'use client';
import { DeploymentsTab } from '@/components/projects/tabs/deployments-tab';
import { useParams } from 'next/navigation';

export default function DeploymentsPage() {
  const params = useParams();
  const projectId = params.projectId as string;
  
  return (
    <DeploymentsTab projectId={projectId} />
  );
}
