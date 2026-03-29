import { TrendingUp, TrendingDown, Activity } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import PageHeader from '@/components/shared/PageHeader'
import MetricCard from '@/components/shared/MetricCard'
import StockTable, { PnLCell, PnLBadge } from '@/components/shared/StockTable'
import { PageLoader } from '@/components/ui/Spinner'
import { getHoldings, type Holding } from '@/api/endpoints'
import { formatCurrency, formatPercent, formatCompactNumber } from '@/lib/utils'

export default function Dashboard() {
  const { data: holdings = [], isLoading } = useQuery({
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
    { key: 'quantity', header: 'Qty', render: (h: Holding) => h.quantity },
    { 
      key: 'avg_price', 
      header: 'Avg', 
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
      header: '%', 
      render: (h: Holding) => <PnLBadge value={h.pnl_percent} /> 
    },
  ]

  return (
    <div className="space-y-6">
      <PageHeader 
        title="Dashboard" 
        description="Overview of your portfolio performance"
      />

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          title="Portfolio Value"
          value={formatCompactNumber(stats.totalValue)}
          change={formatCurrency(stats.totalValue)}
          changeType="neutral"
        />
        <MetricCard
          title="Total P&L"
          value={formatCurrency(stats.totalPnL)}
          change={formatPercent(stats.totalPnL / stats.totalValue * 100)}
          changeType={stats.totalPnL >= 0 ? 'positive' : 'negative'}
        />
        <MetricCard
          title="Open Positions"
          value={stats.positions.toString()}
        />
        <MetricCard
          title="Win Rate"
          value={`${stats.winRate.toFixed(0)}%`}
        />
      </div>

      <div className="rounded-lg border border-border bg-card">
        <div className="border-b border-border p-4">
          <h2 className="font-semibold">Holdings</h2>
        </div>
        {isLoading ? (
          <PageLoader />
        ) : (
          <StockTable
            data={holdings || []}
            columns={columns}
            emptyMessage="No holdings found. Authenticate to view positions."
          />
        )}
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <div className="rounded-lg border border-border bg-card p-4">
          <div className="flex items-center gap-3">
            <div className="rounded-full bg-primary/20 p-2">
              <TrendingUp className="h-5 w-5 text-primary" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Today's Gainers</p>
              <p className="text-lg font-semibold">3</p>
            </div>
          </div>
        </div>
        <div className="rounded-lg border border-border bg-card p-4">
          <div className="flex items-center gap-3">
            <div className="rounded-full bg-loss/20 p-2">
              <TrendingDown className="h-5 w-5 text-loss" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Today's Losers</p>
              <p className="text-lg font-semibold">2</p>
            </div>
          </div>
        </div>
        <div className="rounded-lg border border-border bg-card p-4">
          <div className="flex items-center gap-3">
            <div className="rounded-full bg-warning/20 p-2">
              <Activity className="h-5 w-5 text-warning" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Active Signals</p>
              <p className="text-lg font-semibold">5</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
