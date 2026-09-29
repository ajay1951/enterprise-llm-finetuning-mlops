'use client';
import { ExperimentsTab } from '@/components/projects/tabs/experiments-tab';
import { useParams } from 'next/navigation';

export default function ExperimentsPage() {
  const params = useParams();
  const projectId = params.projectId as string;
  
  return (
    <ExperimentsTab projectId={projectId} />
  );
}
