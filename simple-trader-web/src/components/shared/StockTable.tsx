import { cn } from '@/lib/utils'
import { Badge } from '@/components/ui/Badge'

interface Column<T> {
  key: string
  header: string
  render?: (item: T) => React.ReactNode
  className?: string
}

interface StockTableProps<T> {
  data: T[]
  columns: Column<T>[]
  emptyMessage?: string
  onRowClick?: (item: T) => void
}

export default function StockTable<T extends { symbol: string }>({
  data,
  columns,
  emptyMessage = 'No data available',
  onRowClick,
}: StockTableProps<T>) {
  // Ensure data is actually an array before proceeding
  if (!data || !Array.isArray(data) || data.length === 0) {
    return (
      <div className="flex h-32 items-center justify-center text-muted-foreground">
        {emptyMessage}
      </div>
    )
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead>
          <tr className="border-b border-border">
            {columns.map((col) => (
              <th
                key={col.key}
                className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground"
              >
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-border">
          {data.map((item, idx) => (
            <tr
              key={item.symbol + idx}
              onClick={() => onRowClick?.(item)}
              className={cn(
                'transition-colors',
                onRowClick && 'cursor-pointer hover:bg-secondary/50'
              )}
            >
              {columns.map((col) => (
                <td key={col.key} className={cn('px-4 py-3 text-sm', col.className)}>
                  {col.render ? col.render(item) : (item as Record<string, unknown>)[col.key] as React.ReactNode}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export function PnLBadge({ value }: { value: number }) {
  return (
    <Badge variant={value >= 0 ? 'success' : 'error'}>
      {value >= 0 ? '+' : ''}
      {value.toFixed(2)}%
    </Badge>
  )
}

export function PnLCell({ value, prefix = '₹' }: { value: number; prefix?: string }) {
  return (
    <span className={cn('font-mono', value >= 0 ? 'text-profit' : 'text-loss')}>
      {prefix}
      {value.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
    </span>
  )
}
