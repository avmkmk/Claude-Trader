import { cn } from '@/lib/utils'
import { Card } from '@/components/ui/Card'

interface MetricCardProps {
  title: string
  value: string
  change?: string
  changeType?: 'positive' | 'negative' | 'neutral'
  className?: string
}

export default function MetricCard({
  title,
  value,
  change,
  changeType = 'neutral',
  className,
}: MetricCardProps) {
  return (
    <Card className={cn('p-4', className)}>
      <p className="text-sm text-muted-foreground">{title}</p>
      <p className="mt-1 text-2xl font-bold font-mono">{value}</p>
      {change && (
        <p
          className={cn(
            'mt-1 text-sm font-medium',
            changeType === 'positive' && 'text-profit',
            changeType === 'negative' && 'text-loss',
            changeType === 'neutral' && 'text-muted-foreground'
          )}
        >
          {change}
        </p>
      )}
    </Card>
  )
}
