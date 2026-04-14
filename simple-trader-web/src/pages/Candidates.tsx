import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Search, Plus, AlertCircle, CheckCircle2 } from 'lucide-react'
import PageHeader from '@/components/shared/PageHeader'
import { Card, CardContent } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { Spinner } from '@/components/ui/Spinner'
import {
  scrapeChartink,
  getCandidates,
  addCandidateToWatchlist,
  analyzeCandidates,
  bulkAddToWatchlist
} from '@/api/endpoints'
import { formatDate } from '@/lib/utils'

export default function Candidates() {
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set())
  const queryClient = useQueryClient()

  const { data: candidates = [], isLoading } = useQuery({
    queryKey: ['candidates'],
    queryFn: getCandidates,
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

  const scrapeMutation = useMutation({
    mutationFn: scrapeChartink,
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ['candidates'] })
      if (result.success) {
        setSuccess(
          `Scan complete: ${result.total_found} stocks found, ${result.new_candidates} new candidates`
        )
      } else {
        // Show actual errors instead of generic message
        const errorDetails = result.errors.length > 0
          ? result.errors.join('; ')
          : 'Unknown error occurred'
        setError(`Scan failed: ${errorDetails}`)
      }
    },
    onError: (err: Error) => {
      setError(`Scan failed: ${err.message}`)
    },
  })

  const addToWatchlistMutation = useMutation({
    mutationFn: (symbol: string) => addCandidateToWatchlist(symbol),
    onSuccess: (result, symbol) => {
      queryClient.invalidateQueries({ queryKey: ['candidates'] })
      queryClient.invalidateQueries({ queryKey: ['watchlist'] })

      if (result.success) {
        if (result.analysis) {
          setSuccess(
            `${symbol} added → ${result.analysis.status_label} (${result.analysis.distance_from_ath.toFixed(1)}% from ATH)`
          )
        } else {
          setSuccess(`${symbol} added to watchlist`)
        }
      } else {
        setError(result.error || 'Failed to add to watchlist')
      }
    },
    onError: (err: Error) => {
      setError(err.message)
    },
  })

  const analyzeMutation = useMutation({
    mutationFn: analyzeCandidates,
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ['candidates'] })
      setSuccess(
        `Analysis complete: Phase 1: ${result.phase_1}, Phase 2: ${result.phase_2}, Phase 3: ${result.phase_3}`
      )
    },
    onError: (err: Error) => {
      setError(`Analysis failed: ${err.message}`)
    },
  })

  const bulkAddMutation = useMutation({
    mutationFn: (symbols: string[]) => bulkAddToWatchlist(symbols),
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ['candidates'] })
      queryClient.invalidateQueries({ queryKey: ['watchlist'] })
      setSelectedIds(new Set())
      setSuccess(`Added ${result.added} stocks to watchlist${result.skipped > 0 ? ` (${result.skipped} skipped)` : ''}`)
    },
    onError: (err: Error) => {
      setError(`Bulk add failed: ${err.message}`)
    },
  })

  const toggleSelection = (id: number) => {
    setSelectedIds(prev => {
      const next = new Set(prev)
      if (next.has(id)) {
        next.delete(id)
      } else {
        next.add(id)
      }
      return next
    })
  }

  const toggleSelectAll = () => {
    if (selectedIds.size === candidates.length && candidates.length > 0) {
      setSelectedIds(new Set())
    } else {
      setSelectedIds(new Set(candidates.map(c => c.id)))
    }
  }

  const handleBulkAdd = () => {
    const selectedSymbols = candidates
      .filter(c => selectedIds.has(c.id))
      .map(c => c.symbol)

    if (selectedSymbols.length === 0) {
      setError("No stocks selected")
      return
    }

    bulkAddMutation.mutate(selectedSymbols)
  }

  const getSourceBadge = (source: string) => {
    switch (source) {
      case 'within-2-52week':
        return <Badge variant="default">Within 2% of 52W High</Badge>
      case 'stage-2-trend':
        return <Badge variant="secondary">Stage 2 Trend</Badge>
      default:
        return <Badge variant="outline">{source}</Badge>
    }
  }

  const getStatusBadge = (phase: number | null, status_label: string | null) => {
    if (!phase || !status_label) {
      return <Badge variant="outline">Not Analyzed</Badge>
    }

    let variant: 'default' | 'secondary' | 'success' | 'warning' = 'default'

    if (status_label.includes('Phase 3')) {
      variant = 'success'  // Green
    } else if (status_label.includes('Approaching')) {
      variant = 'warning'  // Yellow
    } else if (status_label.includes('Phase 2')) {
      variant = 'secondary'  // Orange
    }

    return <Badge variant={variant}>{status_label}</Badge>
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Candidates"
        description="Stocks from Chartink screeners"
      />

      <Card>
        <CardContent className="p-4 space-y-2">
          <div className="flex gap-2">
            <Button
              onClick={() => scrapeMutation.mutate()}
              disabled={scrapeMutation.isPending}
              className="flex-1 sm:flex-none"
            >
              {scrapeMutation.isPending ? (
                <>
                  <Spinner size="sm" className="mr-2" />
                  Scanning... (15-30 seconds)
                </>
              ) : (
                <>
                  <Search size={16} className="mr-2" />
                  Scan Chartink
                </>
              )}
            </Button>

            <Button
              onClick={() => analyzeMutation.mutate()}
              disabled={analyzeMutation.isPending || candidates.length === 0}
              variant="outline"
              className="flex-1 sm:flex-none"
            >
              {analyzeMutation.isPending ? (
                <>
                  <Spinner size="sm" className="mr-2" />
                  Analyzing...
                </>
              ) : (
                <>
                  <Search size={16} className="mr-2" />
                  Analyze All
                </>
              )}
            </Button>
          </div>

          {selectedIds.size > 0 && (
            <div className="flex items-center gap-2 p-2 rounded-md bg-secondary">
              <span className="text-sm">{selectedIds.size} selected</span>
              <Button size="sm" onClick={handleBulkAdd} disabled={bulkAddMutation.isPending}>
                {bulkAddMutation.isPending ? (
                  <>
                    <Spinner size="sm" className="mr-1" />
                    Adding...
                  </>
                ) : (
                  <>
                    <Plus size={14} className="mr-1" />
                    Add to Watchlist
                  </>
                )}
              </Button>
              <Button size="sm" variant="outline" onClick={() => setSelectedIds(new Set())}>
                Clear
              </Button>
            </div>
          )}

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
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="flex h-32 items-center justify-center">
              <Spinner />
            </div>
          ) : candidates.length > 0 ? (
            <table className="w-full">
              <thead>
                <tr className="border-b border-border text-left text-xs font-medium uppercase text-muted-foreground">
                  <th className="px-4 py-3 w-12">
                    <input
                      type="checkbox"
                      checked={selectedIds.size === candidates.length && candidates.length > 0}
                      onChange={toggleSelectAll}
                      className="cursor-pointer"
                    />
                  </th>
                  <th className="px-4 py-3">Symbol</th>
                  <th className="px-4 py-3">Source</th>
                  <th className="px-4 py-3">Phase Status</th>
                  <th className="px-4 py-3">Distance from ATH</th>
                  <th className="px-4 py-3">Scraped</th>
                  <th className="px-4 py-3">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {candidates.map((candidate) => (
                  <tr key={`${candidate.id}-${candidate.symbol}`} className="hover:bg-secondary/50">
                    <td className="px-4 py-3">
                      <input
                        type="checkbox"
                        checked={selectedIds.has(candidate.id)}
                        onChange={() => toggleSelection(candidate.id)}
                        className="cursor-pointer"
                      />
                    </td>
                    <td className="px-4 py-3 font-medium">{candidate.symbol}</td>
                    <td className="px-4 py-3">
                      {getSourceBadge(candidate.source)}
                    </td>
                    <td className="px-4 py-3">
                      {getStatusBadge(candidate.phase, candidate.status_label)}
                    </td>
                    <td className="px-4 py-3 text-sm">
                      {candidate.distance_from_ath !== null
                        ? `${candidate.distance_from_ath.toFixed(1)}%`
                        : '—'}
                    </td>
                    <td className="px-4 py-3 text-sm text-muted-foreground">
                      {formatDate(candidate.scraped_at)}
                    </td>
                    <td className="px-4 py-3">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => addToWatchlistMutation.mutate(candidate.symbol)}
                        disabled={addToWatchlistMutation.isPending}
                      >
                        {addToWatchlistMutation.isPending ? (
                          <Spinner size="sm" className="mr-1" />
                        ) : (
                          <Plus size={14} className="mr-1" />
                        )}
                        Add
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div className="flex h-32 flex-col items-center justify-center text-muted-foreground">
              <p>No candidates found.</p>
              <p className="mt-1 text-sm">Click "Scan Chartink" above to find new stocks.</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
