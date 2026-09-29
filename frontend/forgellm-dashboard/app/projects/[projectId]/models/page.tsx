'use client';

import { ModelsTab } from '@/components/projects/tabs/models-tab';
import { useParams } from 'next/navigation';

export default function ModelsPage() {
  const { projectId } = useParams() as { projectId: string };
  return <ModelsTab projectId={projectId} />;
}
