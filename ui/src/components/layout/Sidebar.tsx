import { NavLink } from 'react-router-dom'
import { cn } from '@/lib/utils'
import { usePlatformHealth } from '@/hooks/usePlatformStatus'
import {
  LayoutDashboard,
  FolderOpen,
  Plug,
  Bot,
  Database,
  Play,
  Settings,
  Zap,
} from 'lucide-react'

const navItems = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/workspaces', icon: FolderOpen, label: 'Workspaces' },
  { to: '/agents', icon: Bot, label: 'Agents' },
  { to: '/connectors', icon: Plug, label: 'Connectors' },
  { to: '/knowledge', icon: Database, label: 'Knowledge' },
  { to: '/playground', icon: Play, label: 'Playground' },
  { to: '/settings', icon: Settings, label: 'Settings' },
]

export function Sidebar() {
  const { data: health } = usePlatformHealth()
  const isHealthy = health?.status === 'healthy'

  return (
    <aside className="w-56 shrink-0 flex flex-col border-r border-border bg-card">
      {/* Logo */}
      <div className="flex items-center gap-2 px-4 py-5 border-b border-border">
        <Zap className="h-6 w-6 text-primary" />
        <span className="font-bold text-base tracking-tight">Colonees</span>
        <span
          className={cn(
            'ml-auto h-2 w-2 rounded-full',
            isHealthy ? 'bg-green-400' : 'bg-red-400',
          )}
          title={isHealthy ? 'Backend healthy' : 'Backend unreachable'}
        />
      </div>

      {/* Nav */}
      <nav className="flex-1 px-2 py-4 space-y-1">
        {navItems.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              cn(
                'flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors',
                isActive
                  ? 'bg-primary/10 text-primary'
                  : 'text-muted-foreground hover:bg-accent hover:text-foreground',
              )
            }
          >
            <Icon className="h-4 w-4 shrink-0" />
            {label}
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      <div className="px-4 py-3 border-t border-border">
        <p className="text-xs text-muted-foreground">v0.1.0 · Agent Swarm Platform</p>
      </div>
    </aside>
  )
}
