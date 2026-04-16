import { apiClient } from './client'

// Types
export interface Holding {
  symbol: string
  quantity: number
  avg_price: number
  current_price: number
  pnl: number
  pnl_percent: number
  exchange: string
  product: string
}

export interface Order {
  id?: number
  symbol: string
  quantity: number
  entry_price: number
  exit_price: number
  entry_date: string
  exit_date: string
  pnl: number
  exchange: string
  order_type: string
  transaction_type: string
  status?: string
  timestamp?: string
}

export interface WatchlistItem {
  id: number
  symbol: string
  name: string | null
  type: string
  added_at: string
  notes: string | null
  phase: number | null
  status_label: string | null
  ath_value: number | null
  ath_date: string | null
  ema_200: number | null
  distance_from_ath: number | null
  last_analyzed: string | null
}

export interface Signal {
  id: number
  symbol: string
  signal_type: 'BUY' | 'SELL'
  strategy: string
  trigger_price: number | null
  triggered_at: string
  status: 'ACTIVE' | 'EXPIRED'
  metadata: Record<string, unknown> | null
}

export interface NewsItem {
  title: string
  summary?: string
  source: string
  url: string
  published_at: string
  symbols?: string[]
  sentiment?: string
}

export interface Quote {
  symbol: string
  last_price: number
  open: number
  high: number
  low: number
  volume: number
  change: number
  change_percent: number
}

export interface BacktestParams {
  symbol: string
  strategy: string
  params: Record<string, number>
  start_date: string
  end_date: string
  initial_cash: number
}

export interface BacktestTask {
  task_id: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  result?: BacktestResult
  progress: number
  error?: string | null
}

export interface BacktestResult {
  initial_cash: number
  final_value: number
  profit: number
  profit_percent: number
  metrics: {
    returns?: {
      total_return: number
      average_return: number
    }
    sharpe_ratio: number | string
    drawdown?: {
      max_drawdown: number
    }
    trades?: {
      total_trades: number
      won_trades: number
      lost_trades: number
      pnl_net_total: number
    }
  }
}

export interface LoginResponse {
  success: boolean
  session_id?: string
  message?: string
}

// Auth
export async function login(mpin: string): Promise<LoginResponse> {
  const { data } = await apiClient.post<LoginResponse>('/auth/login', { mpin })
  if (data.session_id) {
    localStorage.setItem('sessionId', data.session_id)
  }
  return data
}

export async function logout(): Promise<void> {
  await apiClient.post('/auth/logout')
  localStorage.removeItem('sessionId')
}

export async function checkAuthStatus(): Promise<{ authenticated: boolean }> {
  const { data } = await apiClient.get<{ authenticated: boolean }>('/auth/status')
  return data
}

// Nubra Broker Authentication
export interface NubraLoginRequest {
  phone: string
  mpin: string
  otp: string
}

export interface NubraLoginResponse {
  success: boolean
  session_id?: string
  message?: string
}

export interface NubraStatusResponse {
  authenticated: boolean
  message?: string
}

export async function nubraLogin(request: NubraLoginRequest): Promise<NubraLoginResponse> {
  const { data } = await apiClient.post<NubraLoginResponse>('/auth/nubra/login', request)
  if (data.session_id) {
    localStorage.setItem('sessionId', data.session_id)
    localStorage.setItem('nubraAuthenticated', 'true')
  }
  return data
}

export async function checkNubraStatus(): Promise<NubraStatusResponse> {
  const { data } = await apiClient.get<NubraStatusResponse>('/auth/nubra/status')
  return data
}

// Holdings
export async function getHoldings(): Promise<Holding[]> {
  const { data } = await apiClient.get<Holding[]>('/holdings')
  return data
}

// Orders
export async function getOrders(): Promise<Order[]> {
  const { data } = await apiClient.get<Order[]>('/orders')
  return data
}

// Quote
export async function getQuote(symbol: string): Promise<Quote> {
  const { data } = await apiClient.get<Quote>(`/quote/${symbol}`)
  return data
}

// Watchlist
export async function getWatchlist(): Promise<WatchlistItem[]> {
  const { data } = await apiClient.get<WatchlistItem[]>('/watchlist')
  return data
}

export async function addToWatchlist(symbol: string, name?: string): Promise<{ success: boolean }> {
  const { data } = await apiClient.post<{ success: boolean }>('/watchlist', { symbol, name })
  return data
}

export async function removeFromWatchlist(symbol: string): Promise<{ success: boolean }> {
  const { data } = await apiClient.delete<{ success: boolean }>(`/watchlist/${symbol}`)
  return data
}

export async function getWatchlistSymbols(): Promise<string[]> {
  const { data } = await apiClient.get<string[]>('/watchlist/symbols')
  return data
}

// Signals
export async function getSignals(): Promise<Signal[]> {
  const { data } = await apiClient.get<Signal[]>('/signals')
  return data
}

// News
export async function getNews(): Promise<NewsItem[]> {
  const { data } = await apiClient.get<NewsItem[]>('/news')
  return data
}

// Backtest
export async function runBacktest(params: BacktestParams): Promise<{ task_id: string }> {
  const { data } = await apiClient.post<{ task_id: string }>('/backtest/run', params)
  return data
}

export async function getBacktestStatus(taskId: string): Promise<BacktestTask> {
  const { data } = await apiClient.get<BacktestTask>(`/backtest/status/${taskId}`)
  return data
}

export async function cancelBacktest(taskId: string): Promise<{ success: boolean }> {
  const { data } = await apiClient.post<{ success: boolean }>(`/backtest/cancel/${taskId}`)
  return data
}

// Available symbols for backtest
export async function getAvailableSymbols(): Promise<string[]> {
  const { data } = await apiClient.get<string[]>('/backtest/symbols')
  return data
}

// AI Chat
export interface AIChatResponse {
  response: string
}

export interface ChatContext {
  holdings?: string
  watchlist?: string
  recent_trades?: string
}

export async function chatWithAI(message: string, context?: ChatContext): Promise<AIChatResponse> {
  const { data } = await apiClient.post<AIChatResponse>('/ai/chat', { message, context })
  return data
}

export async function analyzeStock(symbol: string): Promise<AIChatResponse> {
  const { data } = await apiClient.post<AIChatResponse>('/ai/analyze-stock', { symbol })
  return data
}

export async function suggestStocks(criteria?: string, watchlist?: string[]): Promise<AIChatResponse> {
  const { data } = await apiClient.post<AIChatResponse>('/ai/suggest-stocks', { criteria, watchlist })
  return data
}

export async function analyzeHoldings(holdings: Holding[]): Promise<AIChatResponse> {
  const holdingsData = holdings.map(h => ({
    symbol: h.symbol,
    quantity: h.quantity,
    avg_price: h.avg_price,
    current_price: h.current_price,
    pnl: h.pnl
  }))
  const { data } = await apiClient.post<AIChatResponse>('/ai/analyze-holdings', { holdings: holdingsData })
  return data
}

export async function analyzeTrades(trades: Order[]): Promise<AIChatResponse> {
  const tradesData = trades.map(t => ({
    symbol: t.symbol,
    pnl: t.pnl
  }))
  const { data } = await apiClient.post<AIChatResponse>('/ai/analyze-trades', { trades: tradesData })
  return data
}

// Scanner - Chartink scraping and ATH analysis
export interface Candidate {
  id: number
  symbol: string
  source: string
  current_price: number | null
  week_52_high: number | null
  distance_from_high: number | null
  scraped_at: string
  // Phase analysis fields
  phase: number | null
  status_label: string | null
  ath_value: number | null
  ath_date: string | null
  ema_200: number | null
  distance_from_ath: number | null
  last_analyzed: string | null
}

export interface ScrapeResponse {
  success: boolean
  total_found: number
  unique_stocks: number
  overlap_removed: number
  new_candidates: number
  duplicates_skipped: number
  errors: string[]
}

export interface AddToWatchlistResponse {
  success: boolean
  error?: string
  analysis?: {
    symbol: string
    phase: number
    status_label: string
    distance_from_ath: number
  }
}

export async function scrapeChartink(): Promise<ScrapeResponse> {
  const { data } = await apiClient.post<ScrapeResponse>('/scanner/scrape-chartink')
  return data
}

export async function getCandidates(): Promise<Candidate[]> {
  const { data } = await apiClient.get<Candidate[]>('/scanner/candidates')
  return data
}

export async function addCandidateToWatchlist(symbol: string): Promise<AddToWatchlistResponse> {
  const { data } = await apiClient.post<AddToWatchlistResponse>(`/scanner/candidates/${symbol}/add-to-watchlist`)
  return data
}

export interface AnalyzeWatchlistResponse {
  success: boolean
  analyzed: number
  phase_1: number
  phase_2: number
  phase_3: number
  errors: string[]
}

export interface AnalyzeCandidatesResponse {
  success: boolean
  analyzed: number
  phase_1: number
  phase_2: number
  phase_3: number
  errors: string[]
}

export interface BulkAddResponse {
  success: boolean
  added: number
  skipped: number
  errors: string[]
}

export async function analyzeWatchlist(): Promise<AnalyzeWatchlistResponse> {
  const { data } = await apiClient.post<AnalyzeWatchlistResponse>('/scanner/analyze-watchlist')
  return data
}

export async function analyzeCandidates(): Promise<AnalyzeCandidatesResponse> {
  const { data } = await apiClient.post<AnalyzeCandidatesResponse>('/scanner/analyze-candidates')
  return data
}

export async function bulkAddToWatchlist(symbols: string[]): Promise<BulkAddResponse> {
  const { data } = await apiClient.post<BulkAddResponse>('/scanner/candidates/bulk-add-to-watchlist', { symbols })
  return data
}
