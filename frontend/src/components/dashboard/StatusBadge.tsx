import type { ApplicationStatus } from '@/lib/types';

const labels: Record<ApplicationStatus, string> = {
  pending: 'Pending',
  processing: 'Processing',
  ready: 'Ready',
  evaluating: 'Evaluating',
  complete: 'Complete',
  failed: 'Failed',
};

const styles: Record<ApplicationStatus, string> = {
  pending: 'bg-[#1a1814]/8 text-[#3a342c]',
  processing: 'bg-[#a35f1f]/12 text-[#a35f1f]',
  ready: 'bg-[#2b4f3a]/10 text-[#2b4f3a]',
  evaluating: 'bg-[#a35f1f]/12 text-[#a35f1f]',
  complete: 'bg-[#2b4f3a]/15 text-[#1f3a2a]',
  failed: 'bg-[#9b2226]/12 text-[#9b2226]',
};

export function StatusBadge({ status }: { status: ApplicationStatus }) {
  const cls = styles[status] || styles.pending;
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[10px] uppercase tracking-[0.15em] ${cls}`}
    >
      <span className="h-1.5 w-1.5 rounded-full bg-current" />
      {labels[status] || status}
    </span>
  );
}
