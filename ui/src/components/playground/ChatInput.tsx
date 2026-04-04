import { Textarea } from '@/components/ui/textarea'
import { Button } from '@/components/ui/button'
import { Send } from 'lucide-react'
import { KeyboardEvent, useRef } from 'react'

interface ChatInputProps {
  onSend: (message: string) => void
  disabled?: boolean
  placeholder?: string
}

export function ChatInput({ onSend, disabled, placeholder }: ChatInputProps) {
  const ref = useRef<HTMLTextAreaElement>(null)

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      submit()
    }
  }

  const submit = () => {
    const val = ref.current?.value.trim()
    if (!val || disabled) return
    onSend(val)
    if (ref.current) ref.current.value = ''
  }

  return (
    <div className="flex gap-2 items-end">
      <Textarea
        ref={ref}
        placeholder={placeholder ?? 'Describe a goal for the agent swarm… (Enter to send, Shift+Enter for newline)'}
        className="flex-1 resize-none min-h-[60px] max-h-40"
        onKeyDown={handleKeyDown}
        disabled={disabled}
        rows={2}
      />
      <Button onClick={submit} disabled={disabled} size="icon" className="h-10 w-10 shrink-0">
        <Send className="h-4 w-4" />
      </Button>
    </div>
  )
}
