import { Routes, Route, Navigate } from 'react-router-dom'
import { AppLayout } from '@/components/layout/AppLayout'
import { DashboardPage }        from '@/pages/DashboardPage'
import { WorkspacesPage }       from '@/pages/WorkspacesPage'
import { WorkspaceDetailPage }  from '@/pages/WorkspaceDetailPage'
import { ConnectorsPage }       from '@/pages/ConnectorsPage'
import { ColoneesPage }         from '@/pages/ColoneesPage'
import { KnowledgeBasePage }    from '@/pages/KnowledgeBasePage'
import { PlaygroundPage }       from '@/pages/PlaygroundPage'
import { SettingsPage }         from '@/pages/SettingsPage'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<AppLayout />}>
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard"        element={<DashboardPage />} />
        <Route path="workspaces"       element={<WorkspacesPage />} />
        <Route path="workspaces/:name" element={<WorkspaceDetailPage />} />
        <Route path="connectors"       element={<ConnectorsPage />} />
        <Route path="agents"           element={<ColoneesPage />} />
        <Route path="knowledge"        element={<KnowledgeBasePage />} />
        <Route path="playground"       element={<PlaygroundPage />} />
        <Route path="settings"         element={<SettingsPage />} />
      </Route>
    </Routes>
  )
}
