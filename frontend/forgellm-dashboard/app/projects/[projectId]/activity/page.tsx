'use client';
import { ActivityTab } from '@/components/projects/tabs/activity-tab';
import { useParams } from 'next/navigation';

export default function ActivityPage() {
  const params = useParams();
  const projectId = params.projectId as string;
  
  return (
    <ActivityTab projectId={projectId} />
  );
}
