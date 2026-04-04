import { Routes, Route, Navigate } from 'react-router-dom'
import { AppLayout } from '@/components/layout/AppLayout'
import { DashboardPage }    from '@/pages/DashboardPage'
import { WorkspacesPage }   from '@/pages/WorkspacesPage'
import { ColoneesPage }     from '@/pages/ColoneesPage'
import { McpServersPage }   from '@/pages/McpServersPage'
import { KnowledgeBasePage } from '@/pages/KnowledgeBasePage'
import { ConnectorsPage }   from '@/pages/ConnectorsPage'
import { TemplatesPage }    from '@/pages/TemplatesPage'
import { SessionsPage }     from '@/pages/SessionsPage'
import { PlaygroundPage }   from '@/pages/PlaygroundPage'
import { SettingsPage }     from '@/pages/SettingsPage'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<AppLayout />}>
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard"      element={<DashboardPage />} />
        <Route path="workspaces"     element={<WorkspacesPage />} />
        <Route path="colonees"       element={<ColoneesPage />} />
        <Route path="mcp"            element={<McpServersPage />} />
        <Route path="knowledge-base" element={<KnowledgeBasePage />} />
        <Route path="connectors"     element={<ConnectorsPage />} />
        <Route path="templates"      element={<TemplatesPage />} />
        <Route path="sessions"       element={<SessionsPage />} />
        <Route path="playground"     element={<PlaygroundPage />} />
        <Route path="settings"       element={<SettingsPage />} />
      </Route>
    </Routes>
  )
}
