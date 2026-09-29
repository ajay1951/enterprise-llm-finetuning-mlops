'use client';

import { TrainingTab } from '@/components/projects/tabs/training-tab';
import { useParams } from 'next/navigation';

export default function TrainingPage() {
  const { projectId } = useParams() as { projectId: string };
  return <TrainingTab projectId={projectId} />;
}
