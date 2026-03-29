"""
Backtesting Endpoints

Provides asynchronous backtesting functionality using Backtrader.
Supports running strategies on historical data and retrieving results.
"""

import os
import uuid
import threading
import importlib
from datetime import datetime
from fastapi import APIRouter, Header
from pydantic import BaseModel
from app.auth import session_manager


# Create router with /backtest prefix
router = APIRouter(prefix="/backtest", tags=["backtest"])


# Path to historical data
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
DAILY_DATA_PATH = os.environ.get(
    "DAILY_DATA_PATH",
    os.path.join(PROJECT_ROOT, "..", "historical_Indian_equity_data", "daily", "eod2")
)


# In-memory storage for backtest tasks
backtest_tasks: dict[str, dict] = {}


# Available strategies for backtesting
STRATEGIES = {
    "SMACrossoverStrategy": {
        "module": "strategies.sma_crossover",
        "class": "SMACrossoverStrategy",
    },
    "RSIMeanReversionIndia": {
        "module": "strategies.rsi_mean_reversion_india",
        "class": "RSIMeanReversionIndia",
    },
    "EMACrossoverStrategy": {
        "module": "strategies.ema_crossover",
        "class": "EMACrossoverStrategy",
    },
}


# Request Model
class BacktestRequest(BaseModel):
    """Request model for starting a backtest"""
    symbol: str
    """Stock symbol to backtest (e.g., RELIANCE)"""
    strategy: str
    """Strategy name from STRATEGIES dictionary"""
    params: dict = {}
    """Strategy parameters"""
    start_date: str | None = None
    """Start date for backtest (optional)"""
    end_date: str | None = None
    """End date for backtest (optional)"""
    initial_cash: int = 5000000
    """Initial capital for backtest (default: 50 lakhs)"""


def run_backtest_in_background(task_id: str, params: BacktestRequest):
    """
    Execute backtest in a background thread.
    
    Loads historical data, applies strategy, runs backtest,
    and stores results in the tasks dictionary.
    
    Args:
        task_id: Unique identifier for the backtest task
        params: BacktestRequest with strategy and parameters
    """
    try:
        backtest_tasks[task_id]["status"] = "running"
        backtest_tasks[task_id]["progress"] = 10

        # Validate data file exists
        csv_path = os.path.join(DAILY_DATA_PATH, f"{params.symbol}.csv")
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"Data file not found: {csv_path}")

        # Add project root to path for imports
        if PROJECT_ROOT not in os.sys.path:
            os.sys.path.insert(0, PROJECT_ROOT)

        # Validate strategy exists
        strategy_config = STRATEGIES.get(params.strategy)
        if not strategy_config:
            raise ValueError(f"Unknown strategy: {params.strategy}")

        backtest_tasks[task_id]["progress"] = 20

        # Import and run backtest
        from backtesting.backtest_runner import BacktestRunner

        strategy_module = importlib.import_module(strategy_config["module"])
        strategy_class = getattr(strategy_module, strategy_config["class"])

        runner = BacktestRunner(initial_cash=params.initial_cash)
        runner.load_data(csv_path, params.symbol)

        # Filter out None parameters
        cleaned_params = {k: v for k, v in params.params.items() if v is not None}
        runner.add_strategy(strategy_class, **cleaned_params)
        runner.add_analyzers()

        backtest_tasks[task_id]["progress"] = 50

        # Run backtest
        result = runner.run()
        metrics = runner.get_metrics(result)

        # Calculate results
        final_value = runner.cerebro.broker.getvalue()
        profit = final_value - params.initial_cash
        profit_percent = (profit / params.initial_cash) * 100

        # Store results
        backtest_result = {
            "initial_cash": params.initial_cash,
            "final_value": final_value,
            "profit": profit,
            "profit_percent": profit_percent,
            "metrics": {
                "sharpe_ratio": metrics.get("sharpe_ratio"),
                "drawdown": metrics.get("drawdown"),
                "returns": metrics.get("returns"),
                "trades": metrics.get("trades"),
            },
        }

        backtest_tasks[task_id]["status"] = "completed"
        backtest_tasks[task_id]["progress"] = 100
        backtest_tasks[task_id]["result"] = backtest_result

    except Exception as e:
        backtest_tasks[task_id]["status"] = "failed"
        backtest_tasks[task_id]["error"] = str(e)
        backtest_tasks[task_id]["progress"] = 0


@router.get("/symbols")
async def get_symbols(x_session_id: str = Header(alias="X-Session-ID")):
    """
    Get list of available symbols for backtesting.
    
    Returns stock symbols that have historical data available.
    
    Args:
        x_session_id: Session ID from header for authentication
        
    Returns:
        List of stock symbols sorted alphabetically
    """
    if not session_manager.validate_session(x_session_id):
        return []

    try:
        if not os.path.exists(DAILY_DATA_PATH):
            return []

        files = [f.replace(".csv", "").upper() for f in os.listdir(DAILY_DATA_PATH) if f.endswith(".csv")]
        files.sort()
        return files
    except Exception:
        return []


@router.post("/run")
async def start_backtest(
    request: BacktestRequest,
    x_session_id: str = Header(alias="X-Session-ID")
):
    """
    Start a new backtest task.
    
    Runs the backtest asynchronously in a background thread.
    Use the returned task_id to poll for status and results.
    
    Args:
        request: BacktestRequest with strategy and parameters
        x_session_id: Session ID from header for authentication
        
    Returns:
        task_id for polling backtest status
    """
    if not session_manager.validate_session(x_session_id):
        return {"error": "Not authenticated"}

    # Validate symbol has data
    csv_path = os.path.join(DAILY_DATA_PATH, f"{request.symbol}.csv")
    if not os.path.exists(csv_path):
        return {"error": f"Data not found for symbol: {request.symbol}"}

    # Validate strategy exists
    if request.strategy not in STRATEGIES:
        return {"error": f"Unknown strategy: {request.strategy}"}

    # Create task
    task_id = str(uuid.uuid4())
    backtest_tasks[task_id] = {
        "status": "pending",
        "progress": 0,
        "result": None,
        "error": None,
    }

    # Run in background thread
    thread = threading.Thread(
        target=run_backtest_in_background,
        args=(task_id, request),
        daemon=True
    )
    thread.start()

    return {"task_id": task_id}


@router.get("/status/{task_id}")
async def get_backtest_status(
    task_id: str,
    x_session_id: str = Header(alias="X-Session-ID")
):
    """
    Get status of a backtest task.
    
    Poll this endpoint to check progress and retrieve results.
    
    Args:
        task_id: The task ID returned from /backtest/run
        x_session_id: Session ID from header for authentication
        
    Returns:
        Task status, progress percentage, and results if completed
    """
    if not session_manager.validate_session(x_session_id):
        return {"error": "Not authenticated"}

    if task_id not in backtest_tasks:
        return {"error": "Task not found"}

    task = backtest_tasks[task_id]
    return {
        "task_id": task_id,
        "status": task["status"],
        "progress": task["progress"],
        "result": task.get("result"),
        "error": task.get("error"),
    }


@router.post("/cancel/{task_id}")
async def cancel_backtest(
    task_id: str,
    x_session_id: str = Header(alias="X-Session-ID")
):
    """
    Cancel a running backtest task.
    
    Note: This only marks the task as cancelled;
    the background thread may continue running.
    
    Args:
        task_id: The task ID to cancel
        x_session_id: Session ID from header for authentication
        
    Returns:
        Success status
    """
    if not session_manager.validate_session(x_session_id):
        return {"error": "Not authenticated"}

    if task_id in backtest_tasks:
        backtest_tasks[task_id]["status"] = "cancelled"
        return {"success": True}

    return {"success": False, "error": "Task not found"}
