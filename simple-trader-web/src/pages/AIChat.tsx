import { useState, useRef, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Send, Bot, User, Briefcase, TrendingUp, Sparkles, Trash2 } from 'lucide-react'
import PageHeader from '@/components/shared/PageHeader'
import { Card, CardContent } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { PageLoader } from '@/components/ui/Spinner'
import { getHoldings, getOrders, chatWithAI, analyzeHoldings, analyzeTrades, suggestStocks } from '@/api/endpoints'

interface Message {
  role: 'user' | 'assistant'
  content: string
}

export default function AIChat() {
  const [messages, setMessages] = useState<Message[]>([
    { role: 'assistant', content: 'Hello! I\'m your SimpleTrader AI Assistant. I can help you with:\n\n- Analyzing stocks and trading opportunities\n- Reviewing your portfolio holdings\n- Suggesting stocks based on strategies\n- Analyzing your trade history\n\nHow can I help you today?' }
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const { data: holdings = [] } = useQuery({
    queryKey: ['holdings'],
    queryFn: getHoldings
  })

  const { data: orders = [] } = useQuery({
    queryKey: ['orders'],
    queryFn: getOrders
  })

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const sendMessage = async (content: string) => {
    if (!content.trim() || isLoading) return

    const userMessage: Message = { role: 'user', content }
    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    try {
      let context: { holdings?: string; watchlist?: string; recent_trades?: string } | undefined
      
      if (content.toLowerCase().includes('holdings') || content.toLowerCase().includes('portfolio')) {
        context = { holdings: holdings.map(h => `${h.symbol}: ${h.pnl}`).join(', ') }
      } else if (content.toLowerCase().includes('trade') || content.toLowerCase().includes('history')) {
        context = { recent_trades: orders.slice(0, 10).map(t => `${t.symbol}: ${t.pnl}`).join(', ') }
      }

      const response = await chatWithAI(content, context)
      setMessages(prev => [...prev, { role: 'assistant', content: response.response }])
    } catch (error) {
      setMessages(prev => [...prev, { role: 'assistant', content: 'Sorry, I encountered an error. Please try again.' }])
    } finally {
      setIsLoading(false)
    }
  }

  const handleAnalyzeHoldings = async () => {
    if (holdings.length === 0) {
      setMessages(prev => [...prev, { role: 'assistant', content: 'You don\'t have any holdings to analyze. Please add some positions first.' }])
      return
    }

    setMessages(prev => [...prev, { role: 'user', content: 'Analyze my holdings' }])
    setIsLoading(true)

    try {
      const response = await analyzeHoldings(holdings)
      setMessages(prev => [...prev, { role: 'assistant', content: response.response }])
    } catch (error) {
      setMessages(prev => [...prev, { role: 'assistant', content: 'Sorry, I encountered an error analyzing your holdings.' }])
    } finally {
      setIsLoading(false)
    }
  }

  const handleAnalyzeTrades = async () => {
    if (orders.length === 0) {
      setMessages(prev => [...prev, { role: 'assistant', content: 'You don\'t have any trade history to analyze.' }])
      return
    }

    setMessages(prev => [...prev, { role: 'user', content: 'Analyze my trade history' }])
    setIsLoading(true)

    try {
      const response = await analyzeTrades(orders)
      setMessages(prev => [...prev, { role: 'assistant', content: response.response }])
    } catch (error) {
      setMessages(prev => [...prev, { role: 'assistant', content: 'Sorry, I encountered an error analyzing your trades.' }])
    } finally {
      setIsLoading(false)
    }
  }

  const handleSuggestStocks = async () => {
    setMessages(prev => [...prev, { role: 'user', content: 'Suggest stocks for momentum strategy' }])
    setIsLoading(true)

    try {
      const response = await suggestStocks('momentum')
      setMessages(prev => [...prev, { role: 'assistant', content: response.response }])
    } catch (error) {
      setMessages(prev => [...prev, { role: 'assistant', content: 'Sorry, I encountered an error getting stock suggestions.' }])
    } finally {
      setIsLoading(false)
    }
  }

  const clearChat = () => {
    setMessages([
      { role: 'assistant', content: 'Chat cleared. How can I help you?' }
    ])
  }

  return (
    <div className="space-y-6">
      <PageHeader 
        title="AI Chat" 
        description="Get AI-powered insights for your trading"
      />

      <Card className="h-[600px] flex flex-col">
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map((message, index) => (
            <div
              key={index}
              className={`flex gap-3 ${message.role === 'user' ? 'flex-row-reverse' : ''}`}
            >
              <div className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${
                message.role === 'user' ? 'bg-primary text-primary-foreground' : 'bg-secondary'
              }`}>
                {message.role === 'user' ? <User size={16} /> : <Bot size={16} />}
              </div>
              <div className={`max-w-[80%] rounded-lg p-3 ${
                message.role === 'user' ? 'bg-primary/10' : 'bg-secondary'
              }`}>
                <pre className="whitespace-pre-wrap font-sans text-sm">{message.content}</pre>
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="flex gap-3">
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-secondary">
                <Bot size={16} />
              </div>
              <div className="flex items-center">
                <PageLoader />
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <div className="border-t p-4 space-y-3">
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleAnalyzeHoldings}
              disabled={isLoading}
              className="gap-2"
            >
              <Briefcase size={16} />
              Analyze Holdings
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={handleAnalyzeTrades}
              disabled={isLoading}
              className="gap-2"
            >
              <TrendingUp size={16} />
              Analyze Trades
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={handleSuggestStocks}
              disabled={isLoading}
              className="gap-2"
            >
              <Sparkles size={16} />
              Suggest Stocks
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={clearChat}
              className="ml-auto"
            >
              <Trash2 size={16} />
            </Button>
          </div>

          <form
            onSubmit={(e) => {
              e.preventDefault()
              sendMessage(input)
            }}
            className="flex gap-2"
          >
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask me anything about trading..."
              disabled={isLoading}
            />
            <Button type="submit" disabled={isLoading || !input.trim()}>
              <Send size={16} />
            </Button>
          </form>
        </div>
      </Card>
    </div>
  )
}
