'use client';
import { ApiKeysTab } from '@/components/projects/tabs/api-keys-tab';
import { useParams } from 'next/navigation';

export default function ApiKeysPage() {
  const params = useParams();
  const projectId = params.projectId as string;
  
  return (
    <ApiKeysTab projectId={projectId} />
  );
}
