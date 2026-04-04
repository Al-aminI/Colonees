import { useRef, useEffect } from 'react'
import { PageHeader } from '@/components/layout/PageHeader'
import { MetricCard } from '@/components/dashboard/MetricCard'
import { StatusBanner } from '@/components/dashboard/StatusBanner'
import { ActivityChart } from '@/components/dashboard/ActivityChart'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { usePlatformStatus } from '@/hooks/usePlatformStatus'
import { useColoneesList } from '@/hooks/useColonees'
import { useMcpServers } from '@/hooks/useMcpServers'
import { Users, Bot, Server, Zap } from 'lucide-react'

interface DataPoint {
  time: string
  sessions: number
  requests: number
}

export function DashboardPage() {
  const { data: status, isLoading: statusLoading } = usePlatformStatus()
  const { data: colonees } = useColoneesList()
  const { data: mcpData } = useMcpServers()
  const chartData = useRef<DataPoint[]>([])

  useEffect(() => {
    if (!status) return
    const now = new Date()
    const label = `${now.getHours()}:${String(now.getMinutes()).padStart(2, '0')}:${String(now.getSeconds()).padStart(2, '0')}`
    chartData.current = [
      ...chartData.current.slice(-59),
      {
        time: label,
        sessions: status.active_sessions,
        requests: status.metrics.total_requests_handled,
      },
    ]
  }, [status])

  if (statusLoading) {
    return (
      <div>
        <PageHeader title="Dashboard" description="Platform overview and live metrics" />
        <div className="grid grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-24" />
          ))}
        </div>
      </div>
    )
  }

  if (!status) {
    return (
      <div>
        <PageHeader title="Dashboard" />
        <p className="text-muted-foreground text-sm">
          Could not reach the backend. Make sure the server is running at{' '}
          <code className="rounded bg-muted px-1">localhost:8080</code>.
        </p>
      </div>
    )
  }

  return (
    <div>
      <PageHeader title="Dashboard" description="Platform overview and live metrics" />

      <div className="space-y-6">
        <StatusBanner status={status} />

        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          <MetricCard
            title="Active Sessions"
            value={status.active_sessions}
            icon={Users}
            description="Currently active"
          />
          <MetricCard
            title="Total Requests"
            value={status.metrics.total_requests_handled.toLocaleString()}
            icon={Zap}
            description="Since startup"
          />
          <MetricCard
            title="Agents Spawned"
            value={status.metrics.total_agents_spawned.toLocaleString()}
            icon={Bot}
            description="Lifetime specialists"
          />
          <MetricCard
            title="Colonees"
            value={colonees?.count ?? '—'}
            icon={Server}
            description={`${mcpData?.count ?? 0} MCP servers`}
          />
        </div>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Live Activity</CardTitle>
          </CardHeader>
          <CardContent>
            <ActivityChart data={chartData.current} />
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
