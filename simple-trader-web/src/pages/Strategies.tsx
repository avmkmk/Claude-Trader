import { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { Play, AlertCircle, CheckCircle2 } from 'lucide-react'
import PageHeader from '@/components/shared/PageHeader'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Spinner } from '@/components/ui/Spinner'
import SearchableSelect from '@/components/ui/SearchableSelect'
import { getAvailableSymbols, runBacktest, getBacktestStatus, type BacktestResult } from '@/api/endpoints'
import { formatCurrency, formatPercent } from '@/lib/utils'

interface StrategyParam {
  key: string
  label: string
  default: number
  type: 'int' | 'float'
  min?: number
  max?: number
}

interface StrategyConfig {
  name: string
  file: string
  class: string
  params: StrategyParam[]
}

const STRATEGIES: StrategyConfig[] = [
  {
    name: 'SMA Crossover',
    file: 'sma_crossover.py',
    class: 'SMACrossoverStrategy',
    params: [
      { key: 'fast_period', label: 'Fast Period', default: 10, type: 'int', min: 2, max: 50 },
      { key: 'slow_period', label: 'Slow Period', default: 30, type: 'int', min: 5, max: 200 },
    ],
  },
  {
    name: 'RSI Mean Reversion',
    file: 'rsi_mean_reversion_india.py',
    class: 'RSIMeanReversionIndia',
    params: [
      { key: 'rsi_period', label: 'RSI Period', default: 14, type: 'int', min: 2, max: 50 },
      { key: 'rsi_oversold', label: 'RSI Oversold Level', default: 30, type: 'int', min: 10, max: 40 },
      { key: 'rsi_exit', label: 'RSI Exit Level', default: 50, type: 'int', min: 40, max: 70 },
      { key: 'bb_period', label: 'Bollinger Bands Period', default: 20, type: 'int', min: 5, max: 50 },
      { key: 'bb_std', label: 'BB Std Deviation', default: 2.0, type: 'float', min: 1.0, max: 3.0 },
      { key: 'volume_period', label: 'Volume MA Period', default: 20, type: 'int', min: 5, max: 50 },
      { key: 'volume_threshold', label: 'Volume Threshold (%)', default: 0.8, type: 'float', min: 0.1, max: 2.0 },
      { key: 'max_hold_bars', label: 'Max Hold (bars)', default: 5, type: 'int', min: 1, max: 30 },
      { key: 'circuit_threshold', label: 'Circuit Filter (%)', default: 0.04, type: 'float', min: 0.01, max: 0.1 },
      { key: 'min_daily_volume', label: 'Min Daily Volume', default: 500000, type: 'int', min: 10000, max: 10000000 },
    ],
  },
  {
    name: 'EMA Crossover',
    file: 'ema_crossover.py',
    class: 'EMACrossoverStrategy',
    params: [
      { key: 'fast_ema_period', label: 'Fast EMA Period', default: 9, type: 'int', min: 2, max: 50 },
      { key: 'slow_ema_period', label: 'Slow EMA Period', default: 20, type: 'int', min: 5, max: 100 },
      { key: 'sma_period', label: 'Macro SMA Period', default: 200, type: 'int', min: 50, max: 300 },
      { key: 'atr_period', label: 'ATR Period', default: 14, type: 'int', min: 5, max: 50 },
      { key: 'atr_stop_mult', label: 'ATR Stop Multiplier', default: 2.0, type: 'float', min: 0.5, max: 5.0 },
      { key: 'atr_target_mult', label: 'ATR Target Multiplier', default: 3.0, type: 'float', min: 1.0, max: 10.0 },
      { key: 'max_hold_bars', label: 'Max Hold (bars)', default: 120, type: 'int', min: 10, max: 500 },
    ],
  },
]

export default function Strategies() {
  const [selectedSymbol, setSelectedSymbol] = useState('')
  const [selectedStrategy, setSelectedStrategy] = useState<StrategyConfig>(STRATEGIES[0])
  const [params, setParams] = useState<Record<string, number>>(() => {
    const p: Record<string, number> = {}
    STRATEGIES[0].params.forEach(param => { p[param.key] = param.default })
    return p
  })
  const [startDate, setStartDate] = useState(() => {
    const d = new Date()
    d.setFullYear(d.getFullYear() - 1)
    return d.toISOString().split('T')[0]
  })
  const [endDate, setEndDate] = useState(() => new Date().toISOString().split('T')[0])
  const [initialCash, setInitialCash] = useState(5000000)
  const [taskId, setTaskId] = useState<string | null>(null)
  const [result, setResult] = useState<BacktestResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [statusMessage, setStatusMessage] = useState<string | null>(null)

  const { data: symbols = [] } = useQuery({
    queryKey: ['symbols'],
    queryFn: getAvailableSymbols,
  })

  const backtestMutation = useMutation({
    mutationFn: async () => {
      setError(null)
      setResult(null)
      setStatusMessage('Starting backtest...')
      const res = await runBacktest({
        symbol: selectedSymbol,
        strategy: selectedStrategy.class,
        params,
        start_date: startDate,
        end_date: endDate,
        initial_cash: initialCash,
      })
      if ((res as { error?: string }).error) {
        throw new Error((res as { error?: string }).error)
      }
      return res.task_id
    },
    onError: (err: Error) => {
      setError(err.message || 'Failed to start backtest')
      setStatusMessage(null)
    },
  })

  const pollQuery = useQuery({
    queryKey: ['backtest', taskId],
    queryFn: async () => {
      if (!taskId) return null
      const status = await getBacktestStatus(taskId)
      if (status.status === 'completed' && status.result) {
        setResult(status.result)
        setStatusMessage('Backtest completed!')
      } else if (status.status === 'failed') {
        setError(status.error || 'Backtest failed')
        setStatusMessage(null)
      } else if (status.status === 'running') {
        setStatusMessage(`Running backtest... ${status.progress}%`)
      }
      return status
    },
    enabled: !!taskId,
    refetchInterval: (query) => {
      const data = query.state.data
      if (!data || data.status === 'pending' || data.status === 'running') {
        return 1500
      }
      return false
    },
  })

  const isRunning = backtestMutation.isPending || pollQuery.data?.status === 'pending' || pollQuery.data?.status === 'running'

  const handleStrategyChange = (strategyName: string) => {
    const strategy = STRATEGIES.find(s => s.name === strategyName) || STRATEGIES[0]
    setSelectedStrategy(strategy)
    const p: Record<string, number> = {}
    strategy.params.forEach(param => { p[param.key] = param.default })
    setParams(p)
  }

  const handleParamChange = (key: string, value: string) => {
    const num = parseFloat(value)
    setParams(prev => ({ ...prev, [key]: isNaN(num) ? 0 : num }))
  }

  const handleRun = async () => {
    setResult(null)
    setError(null)
    setStatusMessage(null)
    const id = await backtestMutation.mutateAsync()
    setTaskId(id)
    setStatusMessage(`Running backtest for ${selectedSymbol} with ${selectedStrategy.name}...`)
  }

  const isValid = selectedSymbol && initialCash >= 10000 && !isRunning

  return (
    <div className="space-y-6">
      <PageHeader 
        title="Strategies" 
        description="Run backtests on historical data"
      />

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="space-y-4">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle>Configuration</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="text-sm font-medium">Symbol ({symbols.length} available)</label>
                <SearchableSelect
                  options={symbols}
                  value={selectedSymbol}
                  onChange={setSelectedSymbol}
                  placeholder="Type to search symbols..."
                  className="mt-1"
                />
              </div>

              <div>
                <label className="text-sm font-medium">Strategy</label>
                <select
                  className="mt-1 flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm outline-none"
                  value={selectedStrategy.name}
                  onChange={(e) => handleStrategyChange(e.target.value)}
                >
                  {STRATEGIES.map((s) => (
                    <option key={s.name} value={s.name}>{s.name}</option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium">Start Date</label>
                  <Input
                    type="date"
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                    className="mt-1"
                  />
                </div>
                <div>
                  <label className="text-sm font-medium">End Date</label>
                  <Input
                    type="date"
                    value={endDate}
                    onChange={(e) => setEndDate(e.target.value)}
                    className="mt-1"
                  />
                </div>
              </div>

              <div>
                <label className="text-sm font-medium">Initial Cash (₹)</label>
                <Input
                  type="number"
                  value={initialCash}
                  onChange={(e) => setInitialCash(Number(e.target.value))}
                  placeholder="Min ₹10,000"
                  className="mt-1"
                />
                <p className="mt-1 text-xs text-muted-foreground">
                  ₹{initialCash.toLocaleString('en-IN')}
                </p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle>Strategy Parameters</CardTitle>
              <p className="text-xs text-muted-foreground">{selectedStrategy.name}</p>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-3">
                {selectedStrategy.params.map((param) => (
                  <div key={param.key}>
                    <label className="text-xs font-medium text-muted-foreground">{param.label}</label>
                    <Input
                      type="number"
                      value={params[param.key] ?? param.default}
                      onChange={(e) => handleParamChange(param.key, e.target.value)}
                      step={param.type === 'float' ? '0.1' : '1'}
                      min={param.min}
                      max={param.max}
                      className="mt-1 h-8 text-sm"
                    />
                    <p className="mt-0.5 text-[10px] text-muted-foreground">
                      Default: {param.default}
                    </p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <Button 
            onClick={handleRun} 
            disabled={!isValid}
            className="w-full"
            size="lg"
          >
            {isRunning ? (
              <Spinner size="sm" className="mr-2" />
            ) : (
              <Play size={16} className="mr-2" />
            )}
            {isRunning ? 'Running...' : 'Run Backtest'}
          </Button>

          {!selectedSymbol && (
            <p className="text-xs text-center text-muted-foreground">Select a symbol to run backtest</p>
          )}
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Results</CardTitle>
          </CardHeader>
          <CardContent>
            {statusMessage && !error && (
              <div className="mb-4 flex items-center gap-2 rounded-md border border-primary/30 bg-primary/10 p-3 text-sm text-primary">
                <Spinner size="sm" />
                <div>
                  <p className="font-medium">{statusMessage}</p>
                  {pollQuery.data?.progress !== undefined && pollQuery.data.progress > 0 && (
                    <div className="mt-2 h-1.5 w-full rounded-full bg-primary/20">
                      <div 
                        className="h-1.5 rounded-full bg-primary transition-all duration-500" 
                        style={{ width: `${pollQuery.data.progress}%` }}
                      />
                    </div>
                  )}
                </div>
              </div>
            )}

            {statusMessage && result && (
              <div className="mb-4 flex items-center gap-2 rounded-md border border-profit/30 bg-profit/10 p-3 text-sm text-profit">
                <CheckCircle2 size={16} />
                <p className="font-medium">{statusMessage}</p>
              </div>
            )}

            {error && (
              <div className="mb-4 flex items-start gap-2 rounded-md border border-loss/30 bg-loss/10 p-3 text-sm text-loss">
                <AlertCircle size={16} className="mt-0.5 shrink-0" />
                <div>
                  <p className="font-medium">Backtest Failed</p>
                  <p className="mt-1 font-mono text-xs break-all">{error}</p>
                </div>
              </div>
            )}

            {result ? (
              <div className="space-y-4">
                <div className="grid grid-cols-3 gap-4">
                  <div className="rounded-lg bg-secondary p-3">
                    <p className="text-xs text-muted-foreground">Initial</p>
                    <p className="font-mono font-semibold">{formatCurrency(result.initial_cash)}</p>
                  </div>
                  <div className="rounded-lg bg-secondary p-3">
                    <p className="text-xs text-muted-foreground">Final</p>
                    <p className="font-mono font-semibold">{formatCurrency(result.final_value)}</p>
                  </div>
                  <div className="rounded-lg bg-secondary p-3">
                    <p className="text-xs text-muted-foreground">Return</p>
                    <p className={`font-mono font-semibold ${result.profit >= 0 ? 'text-profit' : 'text-loss'}`}>
                      {formatPercent(result.profit_percent)}
                    </p>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div className="rounded-md bg-secondary/50 p-3">
                    <p className="text-xs text-muted-foreground">Sharpe Ratio</p>
                    <p className="font-mono font-semibold">
                      {result.metrics.sharpe_ratio !== null && result.metrics.sharpe_ratio !== undefined
                        ? typeof result.metrics.sharpe_ratio === 'number'
                          ? result.metrics.sharpe_ratio.toFixed(2)
                          : String(result.metrics.sharpe_ratio)
                        : 'N/A'}
                    </p>
                  </div>
                  {result.metrics.drawdown && (
                    <div className="rounded-md bg-secondary/50 p-3">
                      <p className="text-xs text-muted-foreground">Max Drawdown</p>
                      <p className="font-mono font-semibold text-loss">
                        {result.metrics.drawdown.max_drawdown !== null
                          ? `${result.metrics.drawdown.max_drawdown.toFixed(2)}%`
                          : 'N/A'}
                      </p>
                    </div>
                  )}
                  {result.metrics.trades && (
                    <>
                      <div className="rounded-md bg-secondary/50 p-3">
                        <p className="text-xs text-muted-foreground">Total Trades</p>
                        <p className="font-mono font-semibold">{result.metrics.trades.total_trades}</p>
                      </div>
                      <div className="rounded-md bg-secondary/50 p-3">
                        <p className="text-xs text-muted-foreground">Win Rate</p>
                        <p className="font-mono font-semibold">
                          {result.metrics.trades.total_trades > 0
                            ? `${((result.metrics.trades.won_trades / result.metrics.trades.total_trades) * 100).toFixed(0)}%`
                            : 'N/A'}
                        </p>
                      </div>
                      <div className="rounded-md bg-secondary/50 p-3">
                        <p className="text-xs text-muted-foreground">Won</p>
                        <p className="font-mono font-semibold text-profit">{result.metrics.trades.won_trades}</p>
                      </div>
                      <div className="rounded-md bg-secondary/50 p-3">
                        <p className="text-xs text-muted-foreground">Lost</p>
                        <p className="font-mono font-semibold text-loss">{result.metrics.trades.lost_trades}</p>
                      </div>
                    </>
                  )}
                </div>
              </div>
            ) : (
              !isRunning && !error && (
                <div className="flex h-64 items-center justify-center text-muted-foreground text-sm">
                  Select symbol, strategy and click "Run Backtest"
                </div>
              )
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
