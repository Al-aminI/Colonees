import { cn } from '@/lib/utils'

const KNOWN_TYPES: Record<string, { label: string; className: string }> = {
  researcher:     { label: 'Researcher',    className: 'bg-blue-500/20 text-blue-400 border-blue-500/20' },
  domain_expert:  { label: 'Domain Expert', className: 'bg-purple-500/20 text-purple-400 border-purple-500/20' },
  analyst:        { label: 'Analyst',       className: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/20' },
  executor:       { label: 'Executor',      className: 'bg-green-500/20 text-green-400 border-green-500/20' },
  media_producer: { label: 'Media Producer', className: 'bg-pink-500/20 text-pink-400 border-pink-500/20' },
}

const FALLBACK_COLORS = [
  'bg-indigo-500/20 text-indigo-400 border-indigo-500/20',
  'bg-teal-500/20 text-teal-400 border-teal-500/20',
  'bg-orange-500/20 text-orange-400 border-orange-500/20',
  'bg-cyan-500/20 text-cyan-400 border-cyan-500/20',
  'bg-rose-500/20 text-rose-400 border-rose-500/20',
  'bg-emerald-500/20 text-emerald-400 border-emerald-500/20',
  'bg-violet-500/20 text-violet-400 border-violet-500/20',
  'bg-amber-500/20 text-amber-400 border-amber-500/20',
]

function hashColor(str: string): string {
  let hash = 0
  for (let i = 0; i < str.length; i++) {
    hash = ((hash << 5) - hash + str.charCodeAt(i)) | 0
  }
  return FALLBACK_COLORS[Math.abs(hash) % FALLBACK_COLORS.length]
}

function formatLabel(slug: string): string {
  return slug
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase())
}

export function SpecialistTypeBadge({ type }: { type: string }) {
  const known = KNOWN_TYPES[type]
  const label = known?.label ?? formatLabel(type)
  const colorClass = known?.className ?? hashColor(type)

  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium',
        colorClass,
      )}
    >
      {label}
    </span>
  )
}
