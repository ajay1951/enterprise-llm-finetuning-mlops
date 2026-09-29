'use client';

import { DatasetsTab } from '@/components/projects/tabs/datasets-tab';
import { useParams } from 'next/navigation';

export default function DatasetsPage() {
  const { projectId } = useParams() as { projectId: string };
  return <DatasetsTab projectId={projectId} />;
}
