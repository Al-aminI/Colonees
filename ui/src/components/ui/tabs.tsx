import { cn } from '@/lib/utils'
import { createContext, useContext, useState, ReactNode } from 'react'

interface TabsContextValue {
  value: string
  onValueChange: (v: string) => void
}

const TabsContext = createContext<TabsContextValue>({ value: '', onValueChange: () => {} })

interface TabsProps {
  defaultValue?: string
  value?: string
  onValueChange?: (v: string) => void
  children: ReactNode
  className?: string
}

export function Tabs({ defaultValue = '', value, onValueChange, children, className }: TabsProps) {
  const [internal, setInternal] = useState(defaultValue)
  const current = value ?? internal
  const handleChange = onValueChange ?? setInternal
  return (
    <TabsContext.Provider value={{ value: current, onValueChange: handleChange }}>
      <div className={cn('', className)}>{children}</div>
    </TabsContext.Provider>
  )
}

export function TabsList({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <div className={cn('inline-flex h-9 items-center justify-center rounded-lg bg-muted p-1 text-muted-foreground', className)}>
      {children}
    </div>
  )
}

export function TabsTrigger({ value, children, className }: { value: string; children: ReactNode; className?: string }) {
  const { value: current, onValueChange } = useContext(TabsContext)
  return (
    <button
      className={cn(
        'inline-flex items-center justify-center whitespace-nowrap rounded-md px-3 py-1 text-sm font-medium transition-all',
        current === value ? 'bg-background text-foreground shadow' : 'hover:text-foreground',
        className,
      )}
      onClick={() => onValueChange(value)}
    >
      {children}
    </button>
  )
}

export function TabsContent({ value, children, className }: { value: string; children: ReactNode; className?: string }) {
  const { value: current } = useContext(TabsContext)
  if (current !== value) return null
  return <div className={cn('mt-2', className)}>{children}</div>
}
