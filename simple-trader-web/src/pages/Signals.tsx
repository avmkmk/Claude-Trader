import { useQuery } from '@tanstack/react-query'
import { TrendingUp, TrendingDown } from 'lucide-react'
import PageHeader from '@/components/shared/PageHeader'
import { Card, CardContent } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { PageLoader } from '@/components/ui/Spinner'
import { getSignals } from '@/api/endpoints'
import { formatCurrency, formatDateTime } from '@/lib/utils'

export default function Signals() {
  const { data: signals = [], isLoading } = useQuery({
    queryKey: ['signals'],
    queryFn: getSignals,
    refetchInterval: 60000,
  })

  const activeSignals = signals.filter(s => s.status === 'ACTIVE')
  const buySignals = activeSignals.filter(s => s.signal_type === 'BUY')
  const sellSignals = activeSignals.filter(s => s.signal_type === 'SELL')

  return (
    <div className="space-y-6">
      <PageHeader 
        title="Signals" 
        description="Trading signals from your strategies"
      />

      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="rounded-full bg-profit/20 p-2">
                <TrendingUp className="h-5 w-5 text-profit" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Buy Signals</p>
                <p className="text-2xl font-bold">{buySignals.length}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="rounded-full bg-loss/20 p-2">
                <TrendingDown className="h-5 w-5 text-loss" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Sell Signals</p>
                <p className="text-2xl font-bold">{sellSignals.length}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="rounded-full bg-warning/20 p-2">
                <TrendingUp className="h-5 w-5 text-warning" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Total Active</p>
                <p className="text-2xl font-bold">{activeSignals.length}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <PageLoader />
          ) : signals.length > 0 ? (
            <table className="w-full">
              <thead>
                <tr className="border-b border-border text-left text-xs font-medium uppercase text-muted-foreground">
                  <th className="px-4 py-3">Symbol</th>
                  <th className="px-4 py-3">Signal</th>
                  <th className="px-4 py-3">Strategy</th>
                  <th className="px-4 py-3">Trigger Price</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Time</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {signals.map((signal) => (
                  <tr key={signal.id} className="hover:bg-secondary/50">
                    <td className="px-4 py-3 font-medium">{signal.symbol}</td>
                    <td className="px-4 py-3">
                      <Badge variant={signal.signal_type === 'BUY' ? 'success' : 'error'}>
                        {signal.signal_type}
                      </Badge>
                    </td>
                    <td className="px-4 py-3 text-sm text-muted-foreground">
                      {signal.strategy}
                    </td>
                    <td className="px-4 py-3 font-mono">
                      {signal.trigger_price ? formatCurrency(signal.trigger_price) : '-'}
                    </td>
                    <td className="px-4 py-3">
                      <Badge variant={signal.status === 'ACTIVE' ? 'success' : 'secondary'}>
                        {signal.status}
                      </Badge>
                    </td>
                    <td className="px-4 py-3 text-sm text-muted-foreground">
                      {formatDateTime(signal.triggered_at)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div className="flex h-32 items-center justify-center text-muted-foreground">
              No signals generated yet
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
