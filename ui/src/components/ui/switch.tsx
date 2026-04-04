import { cn } from '@/lib/utils'
import { InputHTMLAttributes, forwardRef } from 'react'

interface SwitchProps extends Omit<InputHTMLAttributes<HTMLInputElement>, 'type'> {
  checked?: boolean
  onCheckedChange?: (checked: boolean) => void
}

export const Switch = forwardRef<HTMLInputElement, SwitchProps>(
  ({ className, checked, onCheckedChange, onChange, ...props }, ref) => (
    <label className={cn('relative inline-flex cursor-pointer items-center', className)}>
      <input
        type="checkbox"
        className="sr-only peer"
        ref={ref}
        checked={checked}
        onChange={(e) => {
          onChange?.(e)
          onCheckedChange?.(e.target.checked)
        }}
        {...props}
      />
      <div className="peer h-5 w-9 rounded-full border border-input bg-secondary transition-colors peer-checked:bg-primary peer-checked:border-primary peer-focus-visible:ring-1 peer-focus-visible:ring-ring after:absolute after:left-0.5 after:top-0.5 after:h-4 after:w-4 after:rounded-full after:bg-background after:transition-transform peer-checked:after:translate-x-4" />
    </label>
  ),
)
Switch.displayName = 'Switch'
