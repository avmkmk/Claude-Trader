"""
SimpleTrader API - FastAPI Backend

Main entry point for the SimpleTrader REST API.
Provides endpoints for portfolio management, trading signals, backtesting, and AI chat.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import news, backtest, ai, scanner


# Initialize FastAPI application with metadata
app = FastAPI(
    title="SimpleTrader API",
    version="1.0.0",
    description="REST API for algorithmic trading with Indian equity markets"
)


# Configure CORS to allow requests from the React frontend
# Only allows localhost:5173 (development) - update for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Register all API routers
# Each router handles a specific domain of functionality
app.include_router(news.router)       # Market news
app.include_router(backtest.router)    # Strategy backtesting
app.include_router(ai.router)         # AI chat and analysis
app.include_router(scanner.router)    # Chartink scraping and ATH analysis


@app.get("/api/health")
async def health():
    """
    Health check endpoint.
    
    Returns:
        dict: Simple status response indicating the API is running
    """
    return {"status": "ok"}


# Run the application directly when executed as a script
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
