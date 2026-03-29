# SimpleTrader Dashboard - UX Improvement Specifications

This document outlines all planned UX improvements across every page of the SimpleTrader React dashboard.

---

## Table of Contents

1. [Global Components](#1-global-components)
2. [Auth Page](#2-auth-page)
3. [Dashboard Page](#3-dashboard-page)
4. [Holdings Page](#4-holdings-page)
5. [Orders Page](#5-orders-page)
6. [Strategies Page](#6-strategies-page)
7. [Watchlist Page](#7-watchlist-page)
8. [Signals Page](#8-signals-page)
9. [News Page](#9-news-page)
10. [Sidebar](#10-sidebar)

---

## 1. Global Components

### 1.1 Sidebar

| Issue | Priority | Specification |
|-------|----------|---------------|
| Collapse state not persisted | Medium | Save collapsed state to localStorage, restore on mount |
| No tooltips when collapsed | Medium | On hover, show tooltip with page name |
| No notification badge | Low | Show red badge on Signals icon when active signals > 0 |
| No mobile responsive | Medium | On screens < 768px, sidebar should overlay (not shrink content), auto-collapse on nav click |

### 1.2 MetricCard

| Issue | Priority | Specification |
|-------|----------|---------------|
| No icon support | Low | Accept optional `icon: ReactNode` prop, render before title |
| No loading state | Medium | Show skeleton shimmer animation when `loading: true` prop set |
| No tooltip | Low | Accept optional `tooltip: string` prop, show on hover with "?" icon |

### 1.3 StockTable

| Issue | Priority | Specification |
|-------|----------|---------------|
| No sorting | Medium | Add `sortable: boolean` to Column interface. Click header to sort asc/desc. Show sort indicator |
| No pagination | Medium | Add `pageSize` prop (default 20). Show pagination controls at bottom |
| No sticky header | Low | Add `sticky` class to thead when table container has overflow |
| No row selection | Low | Add optional `selectable: boolean` prop with checkbox column |
| No empty state icon | Low | Show illustration/icon above empty message |

### 1.4 SearchableSelect

| Issue | Priority | Specification |
|-------|----------|---------------|
| No loading state | Medium | Show spinner inside dropdown while options load |
| No "no results" action | Low | Show "Add new" suggestion when no match found |

---

## 2. Auth Page

### File: `src/pages/Auth.tsx`

| Issue | Priority | Specification |
|-------|----------|---------------|
| No MPIN length hint | Medium | Add text below input: "Enter 4-6 digit MPIN" |
| Generic error messages | Medium | Show specific messages: "Invalid MPIN" vs "MPIN not configured in environment" |
| No auto-focus | Low | Add `autoFocus` to MPIN input, focus on mount |
| No loading text | Low | Change button text to "Authenticating..." while loading |
| No keyboard hint | Low | Show "Press Enter to login" below button |

### Implementation Notes

```tsx
// Error differentiation
if (!settings.NUBRA_MPIN) {
  return { success: false, message: "MPIN not configured. Set NUBRA_MPIN or MPIN environment variable." }
}
if (mpin !== settings.NUBRA_MPIN) {
  return { success: false, message: "Invalid MPIN. Please try again." }
}
```

---

## 3. Dashboard Page

### File: `src/pages/Dashboard.tsx`

| Issue | Priority | Specification |
|-------|----------|---------------|
| Hardcoded stats | 🔴 High | Replace hardcoded "Gainers: 3", "Losers: 2", "Signals: 5" with real data from API |
| No market status | Medium | Add API endpoint `/api/market/status` returning `{"open": bool, "time": str}` |
| No timestamp | Low | Show "Last updated: HH:MM IST" below page header |
| No portfolio chart | Low | Add sparkline showing portfolio value trend (requires historical data) |
| No quick actions | Medium | Add "Quick Trade" button linking to broker terminal, "View All" link to Holdings |
| No refresh button | Low | Add refresh button in page header |
| Holdings table duplicate | Low | Holdings table here is duplicate of Holdings page. Either remove or make it a compact view |

### New Data Required

```typescript
interface MarketStatus {
  open: boolean
  time: string  // "09:30 IST"
  session: 'pre-market' | 'regular' | 'post-market' | 'closed'
}
```

---

## 4. Holdings Page

### File: `src/pages/Holdings.tsx`

| Issue | Priority | Specification |
|-------|----------|---------------|
| No sorting | Medium | Add sortable columns: Symbol, Qty, Avg Price, Current, P&L, P&L % |
| No filtering | Medium | Add filter dropdown: All, Profit Only, Loss Only |
| No search | Medium | Add search input to filter by symbol |
| No day change | Medium | Add "Day Change" column showing today's P&L (need new API field) |
| No total row | Low | Add summary row at bottom: Total Qty, Total Value, Total P&L |
| No export | Low | Add "Export CSV" button in page header actions |
| No last updated | Low | Show "Data refreshed at HH:MM" next to Refresh button |

### New API Fields Required

```typescript
interface Holding {
  // existing fields...
  day_change: number       // Today's P&L
  day_change_percent: number
  market_value: number     // current_price * quantity
}
```

---

## 5. Orders Page

### File: `src/pages/Orders.tsx`

| Issue | Priority | Specification |
|-------|----------|---------------|
| No date filtering | 🔴 High | Add date range picker: Last 7 days, Last 30 days, Custom range |
| No symbol filter | Medium | Add dropdown to filter by specific symbol |
| No sorting | Medium | Sortable columns: Date, Symbol, P&L |
| No pagination | Medium | Paginate if > 20 orders |
| No holding period | Low | Add "Duration" column: entry_date → exit_date in days |
| No profit breakdown | Medium | Show summary: "X winning trades, Y losing trades, Avg win: ₹Z, Avg loss: ₹W" |
| No export | Low | Add "Export CSV" button |

### UI Structure

```
┌─────────────────────────────────────────────────┐
│ [Last 7d ▾] [All Symbols ▾] [Search...] [Export] │
├─────────────────────────────────────────────────┤
│ Summary: 3 trades | 2 won (₹5,000) | 1 lost (-₹3,000) │
├─────────────────────────────────────────────────┤
│ Symbol | Type | Qty | Entry | Exit | P&L | Date │
│ ...                                               │
├─────────────────────────────────────────────────┤
│ [< 1 2 3 >]                                       │
└─────────────────────────────────────────────────┘
```

---

## 6. Strategies Page

### File: `src/pages/Strategies.tsx`

| Issue | Priority | Specification |
|-------|----------|---------------|
| No backtest history | 🔴 High | Store results in localStorage. Show "Recent Backtests" panel with last 5 runs |
| No compare mode | Medium | Add "Compare" button to run multiple strategies side-by-side |
| No preset date ranges | Low | Quick buttons: "1Y", "2Y", "3Y", "Max" |
| No param validation | Medium | Show red border + error text if value outside min/max |
| Results lost on refresh | Medium | Save last result to localStorage, restore on mount |
| No strategy description | Low | Show brief description below strategy name in dropdown |
| No reset button | Low | Add "Reset to Defaults" button below params |
| No equity curve | Low | Add mini chart showing portfolio value over time (requires backend support) |

### Backtest History Structure

```typescript
interface BacktestHistory {
  id: string
  timestamp: string
  symbol: string
  strategy: string
  params: Record<string, number>
  result: {
    profit_percent: number
    total_trades: number
    win_rate: number
    sharpe_ratio: number | null
  }
}
```

### Storage

```typescript
// localStorage key: 'backtest_history'
// Store last 10 runs
// Show in collapsible panel on left side
```

---

## 7. Watchlist Page

### File: `src/pages/Watchlist.tsx`

| Issue | Priority | Specification |
|-------|----------|---------------|
| No live prices | 🔴 High | Show current price, day change, day change % next to each symbol |
| No sorting | Medium | Sortable by: Symbol, Added Date, Price |
| No duplicate prevention UI | Low | Disable Add button + show message if symbol already in list |
| No refresh | Low | Add refresh button |
| Full timestamp shown | Low | Show relative time: "Added 2 hours ago" |
| No click to view | Medium | Click symbol row to see quote details or link to broker |

### New API Required

```typescript
// GET /api/watchlist/quotes
// Returns:
[
  {
    "symbol": "RELIANCE",
    "last_price": 2650.00,
    "day_change": 15.00,
    "day_change_percent": 0.57
  }
]
```

### Table Structure

```
┌────────────────────────────────────────────────────────────┐
│ Symbol    │ Type  │ Price      │ Day Change    │ Added    │
├───────────┼───────┼────────────┼───────────────┼──────────┤
│ RELIANCE  │ EQUITY│ ₹2,650.00  │ +₹15.00 (0.57%)│ 2 days ago│
│ TCS       │ EQUITY│ ₹3,950.00  │ -₹30.00 (0.75%)│ 1 week ago│
└────────────────────────────────────────────────────────────┘
```

---

## 8. Signals Page

### File: `src/pages/Signals.tsx`

| Issue | Priority | Specification |
|-------|----------|---------------|
| No filtering | 🔴 High | Add filter bar: Status (Active/All), Type (Buy/Sell/All), Strategy (dropdown) |
| No sorting | Medium | Sortable columns: Time, Symbol, Status |
| No action buttons | Medium | Add "Trade" button per row linking to broker or Holdings |
| No expandable details | Low | Click row to expand and show signal metadata |
| No sidebar badge | Medium | Show notification badge on Signals icon in sidebar for active signals |

### Filter UI

```
┌─────────────────────────────────────────────────────────┐
│ [Status: Active ▾] [Type: All ▾] [Strategy: All ▾]      │
├─────────────────────────────────────────────────────────┤
│ Symbol │ Signal │ Strategy │ Price │ Status │ Time       │
└─────────────────────────────────────────────────────────┘
```

---

## 9. News Page

### File: `src/pages/News.tsx`

| Issue | Priority | Specification |
|-------|----------|---------------|
| No real news source | 🔴 High | Integrate real news API (e.g., NewsAPI, Marketaux, or custom scraper) |
| No categories | Medium | Add filter: All, Market, Stock-specific, Economic |
| No sentiment | Low | Show sentiment badge: Bullish / Bearish / Neutral |
| No bookmark | Low | Add bookmark icon to save news |
| No infinite scroll | Low | Add "Load More" button or infinite scroll |
| Placeholder URLs | 🔴 High | News URLs point to example.com - need real URLs |

### News Source Options

1. **Marketaux API** (already have API key in env) - Stock-specific news
2. **NewsAPI** - General market news
3. **RSS Feeds** - Economic Times, Moneycontrol, LiveMint
4. **Custom scraper** - Scrape specific sites

---

## 10. Cross-Cutting Concerns

### 10.1 Loading States

| Component | Current | Proposed |
|-----------|---------|----------|
| Tables | Full page spinner | Skeleton rows (3-5 gray animated rows) |
| Metric cards | Show "0" immediately | Show skeleton until data loads |
| Dropdowns | No loading | Show spinner inside dropdown |

### 10.2 Error States

| Component | Current | Proposed |
|-----------|---------|----------|
| API errors | Silent fail | Show toast notification with error message |
| Network errors | No retry | Show "Connection lost" banner with "Retry" button |
| Auth expired | Redirect to login | Show "Session expired" message before redirect |

### 10.3 Empty States

| Component | Current | Proposed |
|-----------|---------|----------|
| Holdings | "No open positions found" | Add icon + "Your holdings will appear here" |
| Orders | "No order history available" | Add icon + "Completed orders will appear here" |
| Watchlist | "No stocks in watchlist" | Add icon + "Search and add stocks to track" |
| Signals | "No signals generated yet" | Add icon + "Signals will appear when strategies detect opportunities" |

### 10.4 Responsive Design

| Breakpoint | Current | Proposed |
|------------|---------|----------|
| Desktop (>1024px) | Works | OK |
| Tablet (768-1024px) | Partial | Fix grid layouts |
| Mobile (<768px) | Broken | Add hamburger menu, stack cards vertically |

---

## Implementation Priority Order

### Phase 1 (Critical UX)
1. Dashboard - remove hardcoded values
2. Orders - add date filtering
3. Signals - add filtering
4. Watchlist - add live prices
5. Strategies - backtest history

### Phase 2 (Enhanced UX)
1. All pages - sorting
2. All pages - filtering
3. Holdings - day change column
4. Watchlist - relative time
5. Loading states - skeletons

### Phase 3 (Polish)
1. News - real news source
2. Export CSV functionality
3. Mobile responsive
4. Empty states with icons
5. Keyboard shortcuts

---

## API Endpoints Needed

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/market/status` | GET | Market open/closed status |
| `/api/watchlist/quotes` | GET | Live prices for watchlist symbols |
| `/api/holdings` | GET | Add `day_change`, `day_change_percent`, `market_value` fields |
| `/api/news` | GET | Integrate real news source |
| `/api/signals?status=ACTIVE&type=BUY&strategy=X` | GET | Add filter query params |

---

## Notes

- All sorting should be client-side for now (data sets are small)
- Pagination should be client-side for < 100 items, server-side for larger
- localStorage for: sidebar state, backtest history, last used strategy params
- Toast notifications for: success messages, errors, info alerts
- All timestamps should display in IST (Indian Standard Time)

---

*Document created: 2025-03-28*
*Last updated: 2025-03-28*
