import { Sun, Moon } from 'lucide-react'
import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'

export function Topbar() {
  const [dark, setDark] = useState(() => {
    const stored = localStorage.getItem('colonees:theme')
    if (stored !== null) return stored === 'dark'
    return document.documentElement.classList.contains('dark')
  })

  useEffect(() => {
    if (dark) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
    localStorage.setItem('colonees:theme', dark ? 'dark' : 'light')
  }, [dark])

  return (
    <header className="flex h-12 items-center justify-end gap-2 border-b border-border px-6">
      <Button
        variant="ghost"
        size="icon"
        onClick={() => setDark(d => !d)}
        title="Toggle theme"
      >
        {dark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
      </Button>
    </header>
  )
}
