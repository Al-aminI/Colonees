import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Switch } from '@/components/ui/switch'
import { SpecialistTypeBadge } from './SpecialistTypeBadge'
import { Eye, Pencil, Trash2, MoreVertical } from 'lucide-react'
import { useState } from 'react'
import { cn, truncate } from '@/lib/utils'
import type { ColoneeDefinition } from '@/types'

interface ColoneeCardProps {
  colonee: ColoneeDefinition
  onToggle: (name: string, enabled: boolean) => void
  onView: (colonee: ColoneeDefinition) => void
  onEdit: (colonee: ColoneeDefinition) => void
  onDelete: (name: string) => void
  isToggling?: boolean
}

export function ColoneeCard({ colonee, onToggle, onView, onEdit, onDelete, isToggling }: ColoneeCardProps) {
  const [menuOpen, setMenuOpen] = useState(false)

  return (
    <Card className="relative flex flex-col gap-0 overflow-visible">
      <CardContent className="p-4 flex flex-col gap-3">
        {/* Header row */}
        <div className="flex items-start justify-between gap-2">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="font-semibold truncate">{colonee.display_name}</span>
              {colonee.builtin && (
                <Badge variant="outline" className="text-[10px] px-1.5 py-0">built-in</Badge>
              )}
            </div>
            <code className="text-[11px] text-muted-foreground">{colonee.name}</code>
          </div>

          {/* Menu */}
          <div className="relative">
            <Button
              variant="ghost"
              size="icon"
              className="h-7 w-7"
              onClick={() => setMenuOpen(o => !o)}
            >
              <MoreVertical className="h-3.5 w-3.5" />
            </Button>
            {menuOpen && (
              <>
                <div className="fixed inset-0 z-10" onClick={() => setMenuOpen(false)} />
                <div className="absolute right-0 top-8 z-20 min-w-[140px] rounded-md border bg-card shadow-lg">
                  <button
                    className="flex w-full items-center gap-2 px-3 py-2 text-sm hover:bg-accent"
                    onClick={() => { setMenuOpen(false); onView(colonee) }}
                  >
                    <Eye className="h-3.5 w-3.5" /> View Detail
                  </button>
                  <button
                    className="flex w-full items-center gap-2 px-3 py-2 text-sm hover:bg-accent"
                    onClick={() => { setMenuOpen(false); onEdit(colonee) }}
                  >
                    <Pencil className="h-3.5 w-3.5" /> Edit
                  </button>
                  {!colonee.builtin && (
                    <button
                      className="flex w-full items-center gap-2 px-3 py-2 text-sm text-destructive hover:bg-accent"
                      onClick={() => { setMenuOpen(false); onDelete(colonee.name) }}
                    >
                      <Trash2 className="h-3.5 w-3.5" /> Delete
                    </button>
                  )}
                </div>
              </>
            )}
          </div>
        </div>

        {/* Type badge */}
        <SpecialistTypeBadge type={colonee.specialist_type} />

        {/* Description */}
        <p className="text-xs text-muted-foreground leading-relaxed">
          {truncate(colonee.description, 100)}
        </p>

        {/* Capabilities */}
        {colonee.capabilities.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {colonee.capabilities.slice(0, 4).map(c => (
              <span key={c} className="rounded-full bg-muted px-2 py-0.5 text-[10px] text-muted-foreground">
                {c}
              </span>
            ))}
            {colonee.capabilities.length > 4 && (
              <span className="rounded-full bg-muted px-2 py-0.5 text-[10px] text-muted-foreground">
                +{colonee.capabilities.length - 4}
              </span>
            )}
          </div>
        )}

        {/* Footer */}
        <div className="flex items-center justify-between mt-1">
          <div className="flex gap-1 flex-wrap">
            {colonee.built_in_tools.map(t => (
              <Badge key={t} variant="secondary" className="text-[10px] px-1.5 py-0">{t}</Badge>
            ))}
          </div>
          <div className={cn('flex items-center gap-2', isToggling && 'opacity-50')}>
            <span className="text-xs text-muted-foreground">
              {colonee.enabled ? 'Enabled' : 'Disabled'}
            </span>
            <Switch
              checked={colonee.enabled}
              onCheckedChange={(checked) => onToggle(colonee.name, checked)}
              disabled={isToggling}
            />
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
