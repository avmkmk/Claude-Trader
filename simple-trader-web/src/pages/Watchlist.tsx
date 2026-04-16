import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Trash2, AlertCircle, CheckCircle2, Activity, ChevronDown, ChevronUp } from 'lucide-react'
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
  checkDataFreshness,
  scrapeChartink,
  getCandidates,
  addCandidateToWatchlist,
  type WatchlistItem,
  type Candidate,
  type DataFreshnessInfo
} from '@/api/endpoints'
import { formatDate } from '@/lib/utils'

type SourceFilter = 'all' | 'manual' | 'chartink'

export default function Watchlist() {
  const [newSymbol, setNewSymbol] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [sourceFilter, setSourceFilter] = useState<SourceFilter>('all')
  const [showCandidates, setShowCandidates] = useState(false)
  const [selectedCandidates, setSelectedCandidates] = useState<Set<number>>(new Set())
  const queryClient = useQueryClient()

  const { data: watchlist = [], isLoading } = useQuery({
    queryKey: ['watchlist'],
    queryFn: getWatchlist,
  })

  const { data: validSymbols = [] } = useQuery({
    queryKey: ['watchlistSymbols'],
    queryFn: getWatchlistSymbols,
  })

  const { data: dataFreshness } = useQuery({
    queryKey: ['dataFreshness'],
    queryFn: checkDataFreshness,
    refetchInterval: 60000, // Refresh every minute
  })

  const { data: candidates = [], isLoading: candidatesLoading } = useQuery({
    queryKey: ['candidates'],
    queryFn: getCandidates,
    enabled: showCandidates,
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
      const result = await addToWatchlist(newSymbol.toUpperCase(), '', 'manual')
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
      queryClient.invalidateQueries({ queryKey: ['dataFreshness'] })
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

  const scrapeMutation = useMutation({
    mutationFn: scrapeChartink,
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ['candidates'] })
      setShowCandidates(true)
      setSuccess(
        `Scan complete: ${result.total_found} stocks found, ${result.new_candidates} new candidates`
      )
    },
    onError: (err: Error) => {
      setError(`Scan failed: ${err.message}`)
    },
  })

  const addCandidateMutation = useMutation({
    mutationFn: (candidateId: number) => {
      const candidate = candidates.find(c => c.id === candidateId)
      if (!candidate) throw new Error('Candidate not found')
      return addCandidateToWatchlist(candidate.symbol)
    },
    onSuccess: (_, candidateId) => {
      queryClient.invalidateQueries({ queryKey: ['watchlist'] })
      queryClient.invalidateQueries({ queryKey: ['candidates'] })
      setSelectedCandidates(prev => {
        const next = new Set(prev)
        next.delete(candidateId)
        return next
      })
      setSuccess('Stock added to watchlist')
    },
    onError: (err: Error) => {
      setError(`Failed to add: ${err.message}`)
    },
  })

  const handleAddSelected = async () => {
    const ids = Array.from(selectedCandidates)
    for (const id of ids) {
      await addCandidateMutation.mutateAsync(id)
    }
    setSelectedCandidates(new Set())
  }

  const toggleCandidateSelection = (id: number) => {
    setSelectedCandidates(prev => {
      const next = new Set(prev)
      if (next.has(id)) {
        next.delete(id)
      } else {
        next.add(id)
      }
      return next
    })
  }

  const getSourceBadge = (source?: string) => {
    if (!source || source === 'manual') {
      return (
        <Badge variant="secondary" className="text-xs">
          🔵 Manual
        </Badge>
      )
    }

    if (source.startsWith('chartink-within-2')) {
      return (
        <Badge className="bg-green-500/10 text-green-600 border-green-500/30 text-xs">
          🟢 Within 2% 52W
        </Badge>
      )
    }

    if (source.startsWith('chartink-stage-2')) {
      return (
        <Badge className="bg-yellow-500/10 text-yellow-600 border-yellow-500/30 text-xs">
          🟡 Stage 2 Trend
        </Badge>
      )
    }

    return (
      <Badge variant="outline" className="text-xs">
        {source}
      </Badge>
    )
  }

  const getPhaseBadge = (item: WatchlistItem | Candidate) => {
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

  // Filter watchlist by source
  const filteredWatchlist = watchlist.filter(item => {
    if (sourceFilter === 'all') return true
    if (sourceFilter === 'manual') return !item.source || item.source === 'manual'
    if (sourceFilter === 'chartink') return item.source?.startsWith('chartink')
    return true
  })

  // Sort watchlist: Phase 3 first, then by phase descending
  const sortedWatchlist = [...filteredWatchlist].sort((a, b) => {
    // Items with phase come before items without phase
    if (a.phase !== null && b.phase === null) return -1
    if (a.phase === null && b.phase !== null) return 1
    if (a.phase === null && b.phase === null) return 0

    // Sort by phase descending (3, 2, 1)
    return (b.phase || 0) - (a.phase || 0)
  })

  // Count phase distribution
  const phaseCounts = filteredWatchlist.reduce((acc, item) => {
    if (item.phase !== null) {
      acc[item.phase] = (acc[item.phase] || 0) + 1
    }
    return acc
  }, {} as Record<number, number>)

  return (
    <div className="space-y-6">
      <PageHeader
        title="Watchlist"
        description="Discover, track, and analyze stocks"
      />

      {/* Data Freshness Warning */}
      {dataFreshness && !dataFreshness.all_fresh && (
        <Card className="border-yellow-500/30 bg-yellow-500/5">
          <CardContent className="p-4">
            <div className="flex items-center gap-2 text-yellow-600">
              <AlertCircle size={16} className="shrink-0" />
              <span className="text-sm font-medium">
                ⚠️ Data as of: {dataFreshness.oldest_data_date} ({dataFreshness.oldest_days} days old) - Analysis may be outdated
              </span>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Action Bar */}
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
              onClick={() => scrapeMutation.mutate()}
              disabled={scrapeMutation.isPending}
            >
              {scrapeMutation.isPending ? (
                <>
                  <Spinner size="sm" className="mr-2" />
                  Scanning...
                </>
              ) : (
                'Scan Chartink'
              )}
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
        </CardContent>
      </Card>

      {/* Chartink Scan Results Panel (Collapsible) */}
      {showCandidates && (
        <Card>
          <CardContent className="p-0">
            <div
              className="flex items-center justify-between p-4 cursor-pointer hover:bg-secondary/50"
              onClick={() => setShowCandidates(!showCandidates)}
            >
              <h3 className="text-lg font-semibold">
                📋 Chartink Scan Results ({candidates.length} stocks)
              </h3>
              {showCandidates ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
            </div>

            {showCandidates && (
              <div className="border-t border-border">
                {candidatesLoading ? (
                  <div className="flex h-32 items-center justify-center">
                    <Spinner />
                  </div>
                ) : candidates.length > 0 ? (
                  <>
                    <table className="w-full">
                      <thead>
                        <tr className="border-b border-border text-left text-xs font-medium uppercase text-muted-foreground">
                          <th className="px-4 py-3 w-12">
                            <input
                              type="checkbox"
                              checked={selectedCandidates.size === candidates.length}
                              onChange={(e) => {
                                if (e.target.checked) {
                                  setSelectedCandidates(new Set(candidates.map(c => c.id)))
                                } else {
                                  setSelectedCandidates(new Set())
                                }
                              }}
                            />
                          </th>
                          <th className="px-4 py-3">Symbol</th>
                          <th className="px-4 py-3">Source</th>
                          <th className="px-4 py-3">Status</th>
                          <th className="px-4 py-3">Distance from ATH</th>
                          <th className="px-4 py-3">Actions</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-border">
                        {candidates.map((candidate) => (
                          <tr key={candidate.id} className="hover:bg-secondary/50">
                            <td className="px-4 py-3">
                              <input
                                type="checkbox"
                                checked={selectedCandidates.has(candidate.id)}
                                onChange={() => toggleCandidateSelection(candidate.id)}
                              />
                            </td>
                            <td className="px-4 py-3 font-medium">{candidate.symbol}</td>
                            <td className="px-4 py-3">
                              {getSourceBadge(candidate.source)}
                            </td>
                            <td className="px-4 py-3">
                              {getPhaseBadge(candidate)}
                            </td>
                            <td className="px-4 py-3 text-sm">
                              {candidate.distance_from_ath !== null ? (
                                <span className={candidate.distance_from_ath >= 0 ? 'text-profit' : 'text-muted-foreground'}>
                                  {candidate.distance_from_ath.toFixed(2)}%
                                </span>
                              ) : (
                                <span className="text-muted-foreground">—</span>
                              )}
                            </td>
                            <td className="px-4 py-3">
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => addCandidateMutation.mutate(candidate.id)}
                                disabled={addCandidateMutation.isPending}
                              >
                                Add
                              </Button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                    <div className="flex gap-2 p-4 border-t border-border">
                      <Button
                        onClick={handleAddSelected}
                        disabled={selectedCandidates.size === 0 || addCandidateMutation.isPending}
                      >
                        Add Selected ({selectedCandidates.size})
                      </Button>
                      <Button
                        variant="ghost"
                        onClick={() => setShowCandidates(false)}
                      >
                        Clear Results
                      </Button>
                    </div>
                  </>
                ) : (
                  <div className="flex h-32 items-center justify-center text-muted-foreground">
                    No candidates found. Click "Scan Chartink" to discover stocks.
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* My Watchlist Section */}
      <Card>
        <CardContent className="p-0">
          <div className="p-4 border-b border-border">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold">
                🔍 My Watchlist ({filteredWatchlist.length} stocks)
              </h3>
              <div className="flex items-center gap-3">
                <label className="text-sm text-muted-foreground">Filter:</label>
                <select
                  value={sourceFilter}
                  onChange={(e) => setSourceFilter(e.target.value as SourceFilter)}
                  className="rounded-md border border-border bg-background px-3 py-1.5 text-sm"
                >
                  <option value="all">All Sources</option>
                  <option value="manual">Manual</option>
                  <option value="chartink">Chartink</option>
                </select>
              </div>
            </div>

            {/* Phase distribution summary */}
            {Object.keys(phaseCounts).length > 0 && (
              <div className="flex gap-3 text-sm text-muted-foreground pt-2">
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
          </div>

          {isLoading ? (
            <div className="flex h-32 items-center justify-center">
              <Spinner />
            </div>
          ) : sortedWatchlist.length > 0 ? (
            <table className="w-full">
              <thead>
                <tr className="border-b border-border text-left text-xs font-medium uppercase text-muted-foreground">
                  <th className="px-4 py-3">Symbol</th>
                  <th className="px-4 py-3">Source</th>
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
                      {getSourceBadge(item.source)}
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
              {sourceFilter !== 'all'
                ? `No stocks from ${sourceFilter} source. Try "All Sources" filter.`
                : 'No stocks in watchlist. Search and add one above.'}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
