import { RegistryTab } from '@/components/projects/tabs/registry-tab';

export default function RegistryPage({ params }: { params: { projectId: string } }) {
  return (
    <div className="max-w-6xl mx-auto">
      <RegistryTab projectId={params.projectId} />
    </div>
  );
}
