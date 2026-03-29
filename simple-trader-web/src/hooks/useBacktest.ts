import { useState, useCallback } from 'react'
import { useQuery } from '@tanstack/react-query'
import { runBacktest, getBacktestStatus, type BacktestParams, type BacktestTask } from '@/api/endpoints'

export function useBacktest() {
  const [taskId, setTaskId] = useState<string | null>(null)

  const startBacktest = useCallback(async (params: BacktestParams) => {
    const result = await runBacktest(params)
    setTaskId(result.task_id)
    return result.task_id
  }, [])

  const { data: status, isLoading } = useQuery<BacktestTask>({
    queryKey: ['backtest', taskId],
    queryFn: async () => {
      if (!taskId) throw new Error('No task ID')
      return getBacktestStatus(taskId)
    },
    enabled: !!taskId,
    refetchInterval: (query) => {
      const data = query.state.data
      if (!data || data.status === 'pending' || data.status === 'running') {
        return 2000
      }
      return false
    },
  })

  return {
    taskId,
    status,
    isRunning: isLoading && !!taskId,
    startBacktest,
    reset: () => setTaskId(null),
  }
}
