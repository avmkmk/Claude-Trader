import { User } from 'lucide-react'

export default function Header() {
  return (
    <header className="flex h-14 items-center justify-between border-b border-border bg-card px-6">
      <div />
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <User size={16} />
          <span>Demo User</span>
        </div>
        <div className="h-8 w-8 rounded-full bg-primary/20 flex items-center justify-center">
          <User size={16} className="text-primary" />
        </div>
      </div>
    </header>
  )
}
