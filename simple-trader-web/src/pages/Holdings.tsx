import { useQuery } from '@tanstack/react-query'
import PageHeader from '@/components/shared/PageHeader'
import MetricCard from '@/components/shared/MetricCard'
import StockTable, { PnLCell, PnLBadge } from '@/components/shared/StockTable'
import { PageLoader } from '@/components/ui/Spinner'
import { Button } from '@/components/ui/Button'
import { getHoldings, type Holding } from '@/api/endpoints'
import { formatCurrency, formatCompactNumber } from '@/lib/utils'

export default function Holdings() {
  const { data: holdings = [], isLoading, refetch } = useQuery({
    queryKey: ['holdings'],
    queryFn: getHoldings,
    refetchInterval: 30000,
  })

  const stats = holdings.length > 0
    ? {
        totalValue: holdings.reduce((sum, h) => sum + h.current_price * h.quantity, 0),
        totalPnL: holdings.reduce((sum, h) => sum + h.pnl, 0),
        positions: holdings.length,
        winRate: (holdings.filter(h => h.pnl > 0).length / holdings.length) * 100,
      }
    : { totalValue: 0, totalPnL: 0, positions: 0, winRate: 0 }

  const columns = [
    { key: 'symbol', header: 'Symbol', className: 'font-medium' },
    { key: 'exchange', header: 'Exchange' },
    { 
      key: 'quantity', 
      header: 'Qty', 
      render: (h: Holding) => h.quantity 
    },
    { 
      key: 'avg_price', 
      header: 'Avg Price', 
      render: (h: Holding) => formatCurrency(h.avg_price) 
    },
    { 
      key: 'current_price', 
      header: 'Current', 
      render: (h: Holding) => formatCurrency(h.current_price) 
    },
    { 
      key: 'pnl', 
      header: 'P&L', 
      render: (h: Holding) => <PnLCell value={h.pnl} /> 
    },
    { 
      key: 'pnl_percent', 
      header: 'Change %', 
      render: (h: Holding) => <PnLBadge value={h.pnl_percent} /> 
    },
    { key: 'product', header: 'Product' },
  ]

  return (
    <div className="space-y-6">
      <PageHeader 
        title="Holdings" 
        description="Your current open positions from Nubra broker"
        actions={
          <Button variant="outline" size="sm" onClick={() => refetch()}>
            Refresh
          </Button>
        }
      />

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          title="Total Value"
          value={formatCompactNumber(stats.totalValue)}
        />
        <MetricCard
          title="Total P&L"
          value={formatCurrency(stats.totalPnL)}
          change={`${((stats.totalPnL / stats.totalValue) * 100).toFixed(2)}%`}
          changeType={stats.totalPnL >= 0 ? 'positive' : 'negative'}
        />
        <MetricCard
          title="Positions"
          value={stats.positions.toString()}
        />
        <MetricCard
          title="Win Rate"
          value={`${stats.winRate.toFixed(0)}%`}
        />
      </div>

      <div className="rounded-lg border border-border bg-card">
        {isLoading ? (
          <PageLoader />
        ) : holdings && holdings.length > 0 ? (
          <StockTable
            data={holdings}
            columns={columns}
          />
        ) : (
          <div className="flex h-32 items-center justify-center text-muted-foreground">
            No open positions found
          </div>
        )}
      </div>
    </div>
  )
}
