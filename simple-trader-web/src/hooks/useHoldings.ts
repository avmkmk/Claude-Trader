import { useQuery } from '@tanstack/react-query'
import { getHoldings } from '@/api/endpoints'

export function useHoldings(refetchInterval = 30000) {
  return useQuery({
    queryKey: ['holdings'],
    queryFn: getHoldings,
    refetchInterval,
  })
}
