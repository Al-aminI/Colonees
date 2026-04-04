import { useState } from 'react'
import { PageHeader } from '@/components/layout/PageHeader'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { Separator } from '@/components/ui/separator'
import { ExternalLink, RefreshCw, Plus, Server } from 'lucide-react'
import { usePlatformStatus } from '@/hooks/usePlatformStatus'
import { useMcpServers, useRegisterMcpServer, useRemoveMcpServer } from '@/hooks/useMcpServers'
import { McpServerCard } from '@/components/mcp/McpServerCard'
import { McpServerForm } from '@/components/mcp/McpServerForm'
import { useToast } from '@/components/ui/toast'
import type { CreateMcpServerPayload } from '@/types'

export function SettingsPage() {
  const { data: status, isLoading, refetch } = usePlatformStatus()
  const { data: mcpData, isLoading: mcpLoading } = useMcpServers()
  const registerServer = useRegisterMcpServer()
  const removeServer = useRemoveMcpServer()
  const { toast } = useToast()
  const [showMcpForm, setShowMcpForm] = useState(false)

  const servers = mcpData?.servers ?? []

  const handleRegisterMcp = async (values: {
    name: string
    transport: string
    url?: string
    headers_json?: string
    command?: string
    args_str?: string
    env_json?: string
    specialist_types_str?: string
  }) => {
    const payload: CreateMcpServerPayload = {
      name: values.name,
      transport: values.transport as CreateMcpServerPayload['transport'],
    }
    if (values.url) payload.url = values.url
    if (values.command) payload.command = values.command
    if (values.args_str) payload.args = values.args_str.split(/\s+/).filter(Boolean)
    if (values.headers_json) {
      try { payload.headers = JSON.parse(values.headers_json) } catch { /* ignore */ }
    }
    if (values.env_json) {
      try { payload.env = JSON.parse(values.env_json) } catch { /* ignore */ }
    }
    if (values.specialist_types_str) {
      payload.specialist_types = values.specialist_types_str
        .split(',')
        .map(s => s.trim())
        .filter(Boolean)
    }
    await registerServer.mutateAsync(payload)
    toast({ title: 'MCP server registered', variant: 'success' })
  }

  const handleDeleteMcp = async (name: string) => {
    if (!confirm(`Remove MCP server "${name}"?`)) return
    await removeServer.mutateAsync(name)
    toast({ title: 'Server removed', variant: 'info' })
  }

  return (
    <div>
      <PageHeader
        title="Settings"
        description="Platform configuration, API access, and global MCP servers"
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
                { label: 'Swagger UI', url: 'http://localhost:8080/docs', desc: 'Interactive API explorer' },
                { label: 'ReDoc', url: 'http://localhost:8080/redoc', desc: 'Full API reference' },
                { label: 'OpenAPI JSON', url: 'http://localhost:8080/openapi.json', desc: 'Machine-readable schema' },
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

      <Separator className="my-8" />

      {/* MCP Servers Section */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-lg font-semibold">MCP Servers</h2>
            <p className="text-sm text-muted-foreground">
              Register and manage global Model Context Protocol tool servers
            </p>
          </div>
          <Button onClick={() => setShowMcpForm(true)}>
            <Plus className="h-4 w-4 mr-2" /> Register Server
          </Button>
        </div>

        {mcpLoading ? (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-40" />)}
          </div>
        ) : servers.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 text-muted-foreground gap-3">
            <Server className="h-10 w-10 opacity-20" />
            <p className="text-sm">No MCP servers registered yet.</p>
            <Button variant="outline" onClick={() => setShowMcpForm(true)}>Register your first server</Button>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {servers.map(s => (
              <McpServerCard
                key={s.name}
                server={s}
                onDelete={handleDeleteMcp}
                isDeleting={removeServer.isPending}
              />
            ))}
          </div>
        )}
      </div>

      <McpServerForm
        open={showMcpForm}
        onClose={() => setShowMcpForm(false)}
        onSubmit={handleRegisterMcp}
      />
    </div>
  )
}
