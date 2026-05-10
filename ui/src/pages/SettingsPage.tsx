import { PageHeader } from '@/components/layout/PageHeader'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { ExternalLink, RefreshCw } from 'lucide-react'
import { usePlatformStatus } from '@/hooks/usePlatformStatus'

export function SettingsPage() {
  const { data: status, isLoading, refetch } = usePlatformStatus()

  return (
    <div>
      <PageHeader
        title="Settings"
        description="Platform configuration and API access"
        actions={
          <Button variant="outline" size="sm" onClick={() => refetch()}>
            <RefreshCw className="h-3.5 w-3.5 mr-1" /> Refresh
          </Button>
        }
      />

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Platform Config */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Platform Configuration</CardTitle>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="space-y-2">
                {Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-8" />)}
              </div>
            ) : status ? (
              <dl className="space-y-3 text-sm">
                <div className="flex justify-between items-center py-2 border-b border-border">
                  <dt className="text-muted-foreground">Environment</dt>
                  <dd>
                    <Badge variant={status.config_summary.environment === 'production' ? 'success' : 'secondary'}>
                      {status.config_summary.environment}
                    </Badge>
                  </dd>
                </div>
                <div className="flex justify-between items-center py-2 border-b border-border">
                  <dt className="text-muted-foreground">Platform Status</dt>
                  <dd>
                    <Badge variant={status.platform_initialized ? 'success' : 'warning'}>
                      {status.platform_initialized ? 'Initialized' : 'Pending'}
                    </Badge>
                  </dd>
                </div>
                <div className="flex justify-between py-2 border-b border-border">
                  <dt className="text-muted-foreground">Max Concurrent Users</dt>
                  <dd className="font-mono">{status.config_summary.max_concurrent_users.toLocaleString()}</dd>
                </div>
                <div className="flex justify-between py-2 border-b border-border">
                  <dt className="text-muted-foreground">Max Active Sessions</dt>
                  <dd className="font-mono">{status.config_summary.max_active_sessions.toLocaleString()}</dd>
                </div>
                <div className="flex justify-between py-2 border-b border-border">
                  <dt className="text-muted-foreground">Active Sessions Now</dt>
                  <dd className="font-mono">{status.active_sessions}</dd>
                </div>
                <div className="flex justify-between py-2">
                  <dt className="text-muted-foreground">Total Requests Handled</dt>
                  <dd className="font-mono">{status.metrics.total_requests_handled.toLocaleString()}</dd>
                </div>
              </dl>
            ) : (
              <p className="text-sm text-muted-foreground">Backend unreachable.</p>
            )}
          </CardContent>
        </Card>

        {/* API Access */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">API Access</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-muted-foreground">
              The Colonees backend exposes a full REST API. Use the links below to explore the
              auto-generated documentation.
            </p>
            <div className="space-y-2">
              {[
                { label: 'Swagger UI', url: '/api/docs', desc: 'Interactive API explorer' },
                { label: 'ReDoc', url: '/api/redoc', desc: 'Full API reference' },
                { label: 'OpenAPI JSON', url: '/api/openapi.json', desc: 'Machine-readable schema' },
              ].map(({ label, url, desc }) => (
                <a
                  key={url}
                  href={url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center justify-between rounded-md border border-border p-3 text-sm hover:bg-accent transition-colors group"
                >
                  <div>
                    <p className="font-medium">{label}</p>
                    <p className="text-xs text-muted-foreground">{desc}</p>
                  </div>
                  <ExternalLink className="h-4 w-4 text-muted-foreground group-hover:text-foreground" />
                </a>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Resource Stats */}
        {status && Object.keys(status.resource_stats).length > 0 && (
          <Card className="lg:col-span-2">
            <CardHeader>
              <CardTitle className="text-base">Resource Stats</CardTitle>
            </CardHeader>
            <CardContent>
              <pre className="text-xs rounded bg-muted p-3 overflow-x-auto">
                {JSON.stringify(status.resource_stats, null, 2)}
              </pre>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}
