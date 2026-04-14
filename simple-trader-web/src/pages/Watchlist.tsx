import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Trash2, AlertCircle, CheckCircle2, Activity } from 'lucide-react'
import PageHeader from '@/components/shared/PageHeader'
import { Card, CardContent } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { Spinner } from '@/components/ui/Spinner'
import SearchableSelect from '@/components/ui/SearchableSelect'
import {
  getWatchlist,
  addToWatchlist,
  removeFromWatchlist,
  getWatchlistSymbols,
  analyzeWatchlist,
  type WatchlistItem
} from '@/api/endpoints'
import { formatDate } from '@/lib/utils'

export default function Watchlist() {
  const [newSymbol, setNewSymbol] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const queryClient = useQueryClient()

  const { data: watchlist = [], isLoading } = useQuery({
    queryKey: ['watchlist'],
    queryFn: getWatchlist,
  })

  const { data: validSymbols = [] } = useQuery({
    queryKey: ['watchlistSymbols'],
    queryFn: getWatchlistSymbols,
  })

  useEffect(() => {
    if (error) {
      const timer = setTimeout(() => setError(null), 5000)
      return () => clearTimeout(timer)
    }
  }, [error])

  useEffect(() => {
    if (success) {
      const timer = setTimeout(() => setSuccess(null), 3000)
      return () => clearTimeout(timer)
    }
  }, [success])

  const addMutation = useMutation({
    mutationFn: async () => {
      setError(null)
      setSuccess(null)
      const result = await addToWatchlist(newSymbol.toUpperCase())
      if (!result.success) {
        throw new Error((result as { error?: string }).error || 'Failed to add symbol')
      }
      return result
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['watchlist'] })
      setSuccess(`${newSymbol.toUpperCase()} added to watchlist`)
      setNewSymbol('')
    },
    onError: (err: Error) => {
      setError(err.message)
    },
  })

  const removeMutation = useMutation({
    mutationFn: (symbol: string) => removeFromWatchlist(symbol),
    onSuccess: (_, symbol) => {
      queryClient.invalidateQueries({ queryKey: ['watchlist'] })
      setSuccess(`${symbol} removed from watchlist`)
    },
  })

  const analyzeMutation = useMutation({
    mutationFn: analyzeWatchlist,
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ['watchlist'] })
      if (result.success) {
        setSuccess(
          `Analysis complete: ${result.analyzed} stocks analyzed. ` +
          `Phase 3: ${result.phase_3}, Phase 2: ${result.phase_2}, Phase 1: ${result.phase_1}`
        )
      } else {
        setError('Analysis completed with errors')
      }
    },
    onError: (err: Error) => {
      setError(`Analysis failed: ${err.message}`)
    },
  })

  const getPhaseBadge = (item: WatchlistItem) => {
    if (!item.status_label || item.phase === null) {
      return <Badge variant="outline">Not Analyzed</Badge>
    }

    // Color-coded badges based on phase
    if (item.status_label.includes('Phase 3')) {
      return <Badge className="bg-green-500/10 text-green-600 border-green-500/30">
        {item.status_label}
      </Badge>
    }

    if (item.status_label.includes('Approaching Phase 3')) {
      return <Badge className="bg-yellow-500/10 text-yellow-600 border-yellow-500/30">
        {item.status_label}
      </Badge>
    }

    if (item.status_label.includes('Phase 2')) {
      return <Badge className="bg-orange-500/10 text-orange-600 border-orange-500/30">
        {item.status_label}
      </Badge>
    }

    if (item.status_label.includes('Phase 1')) {
      return <Badge variant="secondary">
        {item.status_label}
      </Badge>
    }

    return <Badge variant="outline">{item.status_label}</Badge>
  }

  // Sort watchlist: Phase 3 first, then by phase descending
  const sortedWatchlist = [...watchlist].sort((a, b) => {
    // Items with phase come before items without phase
    if (a.phase !== null && b.phase === null) return -1
    if (a.phase === null && b.phase !== null) return 1
    if (a.phase === null && b.phase === null) return 0

    // Sort by phase descending (3, 2, 1)
    return (b.phase || 0) - (a.phase || 0)
  })

  // Count phase distribution
  const phaseCounts = watchlist.reduce((acc, item) => {
    if (item.phase !== null) {
      acc[item.phase] = (acc[item.phase] || 0) + 1
    }
    return acc
  }, {} as Record<number, number>)

  return (
    <div className="space-y-6">
      <PageHeader
        title="Watchlist"
        description="Stocks you're tracking"
      />

      <Card>
        <CardContent className="p-4 space-y-2">
          <div className="flex gap-2">
            <div className="flex-1">
              <SearchableSelect
                options={validSymbols}
                value={newSymbol}
                onChange={setNewSymbol}
                placeholder={`Type symbol... (${validSymbols.length} available)`}
                className="w-full"
                error={!!error}
              />
            </div>
            <Button
              onClick={() => addMutation.mutate()}
              disabled={!newSymbol.trim() || addMutation.isPending}
            >
              {addMutation.isPending ? (
                <Spinner size="sm" className="mr-2" />
              ) : (
                <Plus size={16} className="mr-2" />
              )}
              Add
            </Button>
            <Button
              variant="outline"
              onClick={() => analyzeMutation.mutate()}
              disabled={analyzeMutation.isPending || watchlist.length === 0}
            >
              {analyzeMutation.isPending ? (
                <>
                  <Spinner size="sm" className="mr-2" />
                  Analyzing...
                </>
              ) : (
                <>
                  <Activity size={16} className="mr-2" />
                  Run ATH Analysis
                </>
              )}
            </Button>
          </div>

          {error && (
            <div className="flex items-center gap-2 rounded-md border border-loss/30 bg-loss/10 p-2.5 text-sm text-loss animate-in fade-in">
              <AlertCircle size={14} className="shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {success && (
            <div className="flex items-center gap-2 rounded-md border border-profit/30 bg-profit/10 p-2.5 text-sm text-profit animate-in fade-in">
              <CheckCircle2 size={14} className="shrink-0" />
              <span>{success}</span>
            </div>
          )}

          {/* Phase distribution summary */}
          {Object.keys(phaseCounts).length > 0 && (
            <div className="flex gap-3 text-sm text-muted-foreground pt-1">
              <span>Distribution:</span>
              {phaseCounts[3] > 0 && (
                <span className="text-green-600">Phase 3: {phaseCounts[3]}</span>
              )}
              {phaseCounts[2] > 0 && (
                <span className="text-orange-600">Phase 2: {phaseCounts[2]}</span>
              )}
              {phaseCounts[1] > 0 && (
                <span>Phase 1: {phaseCounts[1]}</span>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="flex h-32 items-center justify-center">
              <Spinner />
            </div>
          ) : sortedWatchlist.length > 0 ? (
            <table className="w-full">
              <thead>
                <tr className="border-b border-border text-left text-xs font-medium uppercase text-muted-foreground">
                  <th className="px-4 py-3">Symbol</th>
                  <th className="px-4 py-3">Type</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Distance from ATH</th>
                  <th className="px-4 py-3">Added</th>
                  <th className="px-4 py-3">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {sortedWatchlist.map((item) => (
                  <tr key={item.id} className="hover:bg-secondary/50">
                    <td className="px-4 py-3 font-medium">{item.symbol}</td>
                    <td className="px-4 py-3">
                      <Badge variant="secondary">{item.type}</Badge>
                    </td>
                    <td className="px-4 py-3">
                      {getPhaseBadge(item)}
                    </td>
                    <td className="px-4 py-3 text-sm">
                      {item.distance_from_ath !== null ? (
                        <span className={item.distance_from_ath >= 0 ? 'text-profit' : 'text-muted-foreground'}>
                          {item.distance_from_ath.toFixed(2)}%
                        </span>
                      ) : (
                        <span className="text-muted-foreground">—</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-sm text-muted-foreground">
                      {formatDate(item.added_at)}
                    </td>
                    <td className="px-4 py-3">
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => removeMutation.mutate(item.symbol)}
                      >
                        <Trash2 size={16} className="text-loss" />
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div className="flex h-32 items-center justify-center text-muted-foreground">
              No stocks in watchlist. Search and add one above.
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
