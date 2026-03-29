import { useQuery } from '@tanstack/react-query'
import { ExternalLink } from 'lucide-react'
import PageHeader from '@/components/shared/PageHeader'
import { Card, CardContent } from '@/components/ui/Card'
import { PageLoader } from '@/components/ui/Spinner'
import { getNews } from '@/api/endpoints'
import { formatDateTime } from '@/lib/utils'

export default function News() {
  const { data: news = [], isLoading } = useQuery({
    queryKey: ['news'],
    queryFn: getNews,
    refetchInterval: 300000, // 5 minutes
  })

  return (
    <div className="space-y-6">
      <PageHeader 
        title="News" 
        description="Latest market news and updates"
      />

      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <PageLoader />
          ) : news.length > 0 ? (
            <div className="divide-y divide-border">
              {news.map((item, idx) => (
                <a
                  key={idx}
                  href={item.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-start justify-between gap-4 p-4 transition-colors hover:bg-secondary/50"
                >
                  <div className="flex-1">
                    <h3 className="font-medium">{item.title}</h3>
                    <div className="mt-1 flex items-center gap-3 text-xs text-muted-foreground">
                      <span>{item.source}</span>
                      <span>•</span>
                      <span>{formatDateTime(item.published_at)}</span>
                    </div>
                  </div>
                  <ExternalLink size={16} className="text-muted-foreground" />
                </a>
              ))}
            </div>
          ) : (
            <div className="flex h-32 items-center justify-center text-muted-foreground">
              No news available
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
