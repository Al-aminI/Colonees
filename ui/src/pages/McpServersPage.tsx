import { useState } from 'react'
import { PageHeader } from '@/components/layout/PageHeader'
import { McpServerCard } from '@/components/mcp/McpServerCard'
import { McpServerForm } from '@/components/mcp/McpServerForm'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { Plus, Server } from 'lucide-react'
import { useMcpServers, useRegisterMcpServer, useRemoveMcpServer } from '@/hooks/useMcpServers'
import { useToast } from '@/components/ui/toast'
import type { CreateMcpServerPayload } from '@/types'

export function McpServersPage() {
  const { data, isLoading } = useMcpServers()
  const registerServer = useRegisterMcpServer()
  const removeServer = useRemoveMcpServer()
  const { toast } = useToast()
  const [showForm, setShowForm] = useState(false)

  const servers = data?.servers ?? []

  const handleRegister = async (values: {
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
      try { payload.headers = JSON.parse(values.headers_json) } catch {}
    }
    if (values.env_json) {
      try { payload.env = JSON.parse(values.env_json) } catch {}
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

  const handleDelete = async (name: string) => {
    if (!confirm(`Remove MCP server "${name}"?`)) return
    await removeServer.mutateAsync(name)
    toast({ title: 'Server removed', variant: 'info' })
  }

  return (
    <div>
      <PageHeader
        title="MCP Servers"
        description="Register and manage Model Context Protocol tool servers"
        actions={
          <Button onClick={() => setShowForm(true)}>
            <Plus className="h-4 w-4 mr-2" /> Register Server
          </Button>
        }
      />

      {isLoading ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-40" />)}
        </div>
      ) : servers.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 text-muted-foreground gap-3">
          <Server className="h-12 w-12 opacity-20" />
          <p className="text-sm">No MCP servers registered yet.</p>
          <Button variant="outline" onClick={() => setShowForm(true)}>Register your first server</Button>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {servers.map(s => (
            <McpServerCard
              key={s.name}
              server={s}
              onDelete={handleDelete}
              isDeleting={removeServer.isPending}
            />
          ))}
        </div>
      )}

      <McpServerForm
        open={showForm}
        onClose={() => setShowForm(false)}
        onSubmit={handleRegister}
      />
    </div>
  )
}
