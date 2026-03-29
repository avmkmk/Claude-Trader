import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Trash2, AlertCircle, CheckCircle2 } from 'lucide-react'
import PageHeader from '@/components/shared/PageHeader'
import { Card, CardContent } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { Spinner } from '@/components/ui/Spinner'
import SearchableSelect from '@/components/ui/SearchableSelect'
import { getWatchlist, addToWatchlist, removeFromWatchlist, getWatchlistSymbols } from '@/api/endpoints'
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

      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="flex h-32 items-center justify-center">
              <Spinner />
            </div>
          ) : watchlist.length > 0 ? (
            <table className="w-full">
              <thead>
                <tr className="border-b border-border text-left text-xs font-medium uppercase text-muted-foreground">
                  <th className="px-4 py-3">Symbol</th>
                  <th className="px-4 py-3">Type</th>
                  <th className="px-4 py-3">Added</th>
                  <th className="px-4 py-3">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {watchlist.map((item) => (
                  <tr key={item.id} className="hover:bg-secondary/50">
                    <td className="px-4 py-3 font-medium">{item.symbol}</td>
                    <td className="px-4 py-3">
                      <Badge variant="secondary">{item.type}</Badge>
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
