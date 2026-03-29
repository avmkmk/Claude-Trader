import { useQuery } from '@tanstack/react-query'
import PageHeader from '@/components/shared/PageHeader'
import StockTable, { PnLCell } from '@/components/shared/StockTable'
import { PageLoader } from '@/components/ui/Spinner'
import { Badge } from '@/components/ui/Badge'
import { getOrders, type Order } from '@/api/endpoints'
import { formatCurrency, formatDate } from '@/lib/utils'

export default function Orders() {
  const { data: orders = [], isLoading } = useQuery({
    queryKey: ['orders'],
    queryFn: getOrders,
    refetchInterval: 30000,
  })

  const columns = [
    { key: 'symbol', header: 'Symbol', className: 'font-medium' },
    { key: 'exchange', header: 'Exchange' },
    { key: 'transaction_type', header: 'Type', 
      render: (o: Order) => (
        <Badge variant={o.transaction_type === 'BUY' ? 'success' : 'error'}>
          {o.transaction_type}
        </Badge>
      )
    },
    { key: 'quantity', header: 'Qty', render: (o: Order) => o.quantity },
    { 
      key: 'entry_price', 
      header: 'Entry', 
      render: (o: Order) => formatCurrency(o.entry_price) 
    },
    { 
      key: 'exit_price', 
      header: 'Exit', 
      render: (o: Order) => formatCurrency(o.exit_price) 
    },
    { 
      key: 'pnl', 
      header: 'P&L', 
      render: (o: Order) => <PnLCell value={o.pnl} /> 
    },
    { 
      key: 'timestamp', 
      header: 'Date', 
      render: (o: Order) => formatDate(o.timestamp || o.exit_date) 
    },
  ]

  const totalPnL = orders.reduce((sum, o) => sum + o.pnl, 0)

  return (
    <div className="space-y-6">
      <PageHeader 
        title="Orders" 
        description="Your closed/filled orders and trade history"
      />

      <div className="grid gap-4 md:grid-cols-3">
        <div className="rounded-lg border border-border bg-card p-4">
          <p className="text-sm text-muted-foreground">Total Trades</p>
          <p className="text-2xl font-bold">{orders.length}</p>
        </div>
        <div className="rounded-lg border border-border bg-card p-4">
          <p className="text-sm text-muted-foreground">Total P&L</p>
          <p className={`text-2xl font-bold font-mono ${totalPnL >= 0 ? 'text-profit' : 'text-loss'}`}>
            {formatCurrency(totalPnL)}
          </p>
        </div>
        <div className="rounded-lg border border-border bg-card p-4">
          <p className="text-sm text-muted-foreground">Win Rate</p>
          <p className="text-2xl font-bold">
            {orders.length > 0
              ? `${((orders.filter(o => o.pnl > 0).length / orders.length) * 100).toFixed(0)}%`
              : '0%'}
          </p>
        </div>
      </div>

      <div className="rounded-lg border border-border bg-card">
        {isLoading ? (
          <PageLoader />
        ) : orders.length > 0 ? (
          <StockTable
            data={orders}
            columns={columns}
          />
        ) : (
          <div className="flex h-32 items-center justify-center text-muted-foreground">
            No order history available
          </div>
        )}
      </div>
    </div>
  )
}
