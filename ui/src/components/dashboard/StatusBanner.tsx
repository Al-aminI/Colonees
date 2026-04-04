import { Badge } from '@/components/ui/badge'
import { CheckCircle, XCircle } from 'lucide-react'
import type { PlatformStatus } from '@/types'

interface StatusBannerProps {
  status: PlatformStatus
}

export function StatusBanner({ status }: StatusBannerProps) {
  const { platform_initialized, config_summary } = status

  return (
    <div className="flex flex-wrap items-center gap-3 rounded-lg border bg-card p-4 text-sm">
      <div className="flex items-center gap-2">
        {platform_initialized ? (
          <CheckCircle className="h-4 w-4 text-green-400" />
        ) : (
          <XCircle className="h-4 w-4 text-red-400" />
        )}
        <span className="font-medium">
          {platform_initialized ? 'Platform Ready' : 'Platform Initializing'}
        </span>
      </div>
      <Badge variant={config_summary.environment === 'production' ? 'success' : 'secondary'}>
        {config_summary.environment}
      </Badge>
      <span className="text-muted-foreground">
        Capacity: {config_summary.max_concurrent_users.toLocaleString()} users ·{' '}
        {config_summary.max_active_sessions.toLocaleString()} sessions
      </span>
    </div>
  )
}
