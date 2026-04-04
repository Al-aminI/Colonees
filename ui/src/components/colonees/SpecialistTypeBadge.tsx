import { Badge } from '@/components/ui/badge'
import type { SpecialistType } from '@/types'
import { cn } from '@/lib/utils'

const typeConfig: Record<SpecialistType, { label: string; className: string }> = {
  researcher: { label: 'Researcher', className: 'bg-blue-500/20 text-blue-400 border-blue-500/20' },
  domain_expert: { label: 'Domain Expert', className: 'bg-purple-500/20 text-purple-400 border-purple-500/20' },
  analyst: { label: 'Analyst', className: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/20' },
  executor: { label: 'Executor', className: 'bg-green-500/20 text-green-400 border-green-500/20' },
  media_producer: { label: 'Media Producer', className: 'bg-pink-500/20 text-pink-400 border-pink-500/20' },
}

export function SpecialistTypeBadge({ type }: { type: SpecialistType }) {
  const config = typeConfig[type] ?? { label: type, className: '' }
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium',
        config.className,
      )}
    >
      {config.label}
    </span>
  )
}
