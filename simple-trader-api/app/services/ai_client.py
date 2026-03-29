"""
AI Client Service

Provides AI-powered chat and analysis using Google Gemini.
Handles configuration, prompt building, and API interactions.
"""

import os
from typing import List, Dict, Optional
from app.config import settings


class AIClient:
    """
    Client for Google Gemini AI integration.
    
    Provides methods for chat, stock analysis, portfolio analysis,
    and trading insights using Gemini models.
    """
    
    def __init__(self):
        """Initialize the AI client with Gemini API configuration."""
        self.api_key = settings.GEMINI_API_KEY
        self.model = None
        
        # Configure Gemini if API key is available
        if self.api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                # Use Gemini 2.0 Flash for fastest responses
                self.model = genai.GenerativeModel("gemini-2.0-flash")
            except ImportError:
                pass
    
    
    def is_configured(self) -> bool:
        """
        Check if the AI client is properly configured.
        
        Returns:
            bool: True if API key is set and model is initialized
        """
        return self.api_key is not None and self.model is not None
    
    
    def chat(self, message: str, context: Optional[Dict] = None) -> str:
        """
        Send a chat message to the AI assistant.
        
        Args:
            message: User's message
            context: Optional context (holdings, watchlist, trades)
            
        Returns:
            str: AI response or error message
        """
        if not self.is_configured():
            return self._dummy_response()
        
        # Build prompt with context
        prompt = self._build_prompt(message, context)
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error: {str(e)}"
    
    
    def analyze_stock(self, symbol: str, context: Optional[Dict] = None) -> str:
        """
        Analyze a specific stock for trading opportunities.
        
        Args:
            symbol: Stock symbol to analyze (e.g., RELIANCE)
            context: Optional additional context
            
        Returns:
            str: Stock analysis including technical outlook and strategy suggestions
        """
        prompt = f"""You are a trading assistant. Analyze {symbol} for potential trading opportunities.

Context: {context or 'No additional context'}

Provide:
1. Brief technical outlook
2. Key support/resistance levels
3. Any news or catalysts
4. Suggested strategy type (momentum/mean reversion/breakout)
"""
        return self.chat(prompt)
    
    
    def suggest_stocks(self, criteria: str = "momentum", 
                       watchlist: Optional[List[str]] = None) -> str:
        """
        Get AI-suggested stocks for a trading strategy.
        
        Args:
            criteria: Trading strategy type (momentum, mean_reversion, breakout)
            watchlist: Optional user's watchlist for context
            
        Returns:
            str: 5 stock suggestions with symbols, names, and rationale
        """
        watchlist_info = f"Current watchlist: {', '.join(watchlist) if watchlist else 'Empty'}"
        
        prompt = f"""As a trading assistant, suggest 5 Indian stocks for {criteria} strategy.

{watchlist_info}

For each suggestion provide:
- Symbol (NSE)
- Company name
- Brief rationale
- Suggested timeframe

Consider: Nifty 50 stocks, high liquidity, recent momentum."""
        return self.chat(prompt)
    
    
    def analyze_holdings(self, holdings: List[Dict]) -> str:
        """
        Analyze user's portfolio holdings.
        
        Args:
            holdings: List of holdings with symbol, quantity, prices, and P&L
            
        Returns:
            str: Portfolio analysis with health assessment and recommendations
        """
        if not holdings:
            return "No holdings to analyze."
        
        # Build holdings summary
        holdings_summary = "\n".join([
            f"- {h.get('symbol')}: Qty {h.get('quantity')}, Avg ₹{h.get('avg_price')}, "
            f"Current ₹{h.get('current_price')}, P&L ₹{h.get('pnl')}"
            for h in holdings
        ])
        
        prompt = f"""Analyze my current portfolio:

{holdings_summary}

Provide:
1. Overall portfolio health assessment
2. Any overweight positions to consider
3. Stocks showing losses that may need attention
4. Diversification suggestions
"""
        return self.chat(prompt)
    
    
    def analyze_trade_history(self, trades: List[Dict]) -> str:
        """
        Analyze user's trade history for performance insights.
        
        Args:
            trades: List of completed trades with P&L
            
        Returns:
            str: Trade analysis with performance metrics and recommendations
        """
        if not trades:
            return "No trade history to analyze."
        
        # Calculate summary statistics
        total_pnl = sum(t.get('pnl', 0) for t in trades)
        wins = [t for t in trades if t.get('pnl', 0) > 0]
        losses = [t for t in trades if t.get('pnl', 0) < 0]
        
        summary = f"""Total Trades: {len(trades)}
Wins: {len(wins)} | Losses: {len(losses)}
Win Rate: {len(wins)/len(trades)*100:.1f}%
Total P&L: ₹{total_pnl:,.2f}

Recent Trades:"""
        for t in trades[:10]:
            summary += f"\n- {t.get('symbol')}: ₹{t.get('pnl', 0):,.2f}"
        
        prompt = f"""Analyze my trading performance:

{summary}

Provide:
1. Performance assessment
2. Any patterns in wins/losses
3. Areas for improvement
4. Suggested strategy adjustments
"""
        return self.chat(prompt)
    
    
    def _build_prompt(self, message: str, context: Optional[Dict] = None) -> str:
        """
        Build a prompt with system instructions and optional context.
        
        Args:
            message: User's message
            context: Optional context dictionary
            
        Returns:
            str: Formatted prompt for Gemini
        """
        base_prompt = """You are SimpleTrader AI Assistant, a helpful trading assistant.

You can help with:
- Analyzing stocks and trading opportunities
- Reviewing portfolio holdings
- Explaining trading strategies
- Answering questions about the market

"""
        
        # Add context if provided
        if context:
            context_str = "Context:\n"
            if "holdings" in context:
                context_str += f"- Holdings: {context['holdings']}\n"
            if "watchlist" in context:
                context_str += f"- Watchlist: {context['watchlist']}\n"
            if "recent_trades" in context:
                context_str += f"- Recent trades: {context['recent_trades']}\n"
            base_prompt += context_str + "\n"
        
        base_prompt += f"User: {message}\n\nAssistant:"
        return base_prompt
    
    
    def _dummy_response(self) -> str:
        """
        Get a response when API key is not configured.
        
        Returns:
            str: Instructions for configuring the API
        """
        return """⚠️ Gemini API not configured.

To enable AI features:
1. Get a free API key from https://aistudio.google.com/app/apikey
2. Add to .env file:
   GEMINI_API_KEY=your-api-key

Once configured, I can help with:
- Stock analysis and suggestions
- Portfolio insights
- Trading strategy recommendations
"""


# Global AI client instance
ai_client = AIClient()
