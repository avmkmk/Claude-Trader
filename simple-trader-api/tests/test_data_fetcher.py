"""Tests for DataFetcher class"""

import pytest
import pandas as pd
import os
import tempfile
import shutil
from datetime import datetime
from unittest.mock import Mock, MagicMock

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from lib.data_fetcher import DataFetcher


@pytest.fixture
def mock_nubra_handler():
    """Create mock Nubra API handler"""
    handler = Mock()
    handler.get_historical_data = MagicMock()
    return handler


@pytest.fixture
def test_csv_dir():
    """Create temporary directory for test CSV files"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_valid_data():
    """Create sample valid OHLCV data"""
    dates = pd.date_range(start='2024-01-01', end='2024-01-05', freq='D')
    data = {
        'open': [100.0, 102.0, 101.0, 103.0, 105.0],
        'high': [105.0, 106.0, 104.0, 107.0, 108.0],
        'low': [99.0, 101.0, 100.0, 102.0, 104.0],
        'close': [102.0, 103.0, 101.5, 105.0, 107.0],
        'volume': [1000000, 1200000, 1100000, 1300000, 1250000]
    }
    df = pd.DataFrame(data, index=dates)
    return df


def test_fetch_and_append_success(mock_nubra_handler, test_csv_dir, sample_valid_data):
    """Test successful data fetch and append to CSV"""
    # Setup
    symbol = 'RELIANCE'
    from_date = '2024-01-01'
    to_date = '2024-01-05'
    csv_path = os.path.join(test_csv_dir, f'{symbol}.csv')

    # Mock Nubra API to return valid data
    mock_nubra_handler.get_historical_data.return_value = sample_valid_data

    # Create DataFetcher instance
    fetcher = DataFetcher(mock_nubra_handler, test_csv_dir)

    # Execute
    result = fetcher.fetch_and_append(symbol, from_date, to_date)

    # Verify
    assert result['status'] == 'success'
    assert result['rows_added'] == 5
    assert result['error'] is None

    # Verify CSV file was created and contains correct data
    assert os.path.exists(csv_path)
    df = pd.read_csv(csv_path)
    assert len(df) == 5
    assert list(df.columns) == ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
    assert df['Close'].iloc[0] == 102.0

    # Verify Nubra API was called correctly
    mock_nubra_handler.get_historical_data.assert_called_once_with(
        symbol, from_date, to_date, '1d'
    )


def test_fetch_and_append_validation_failure(mock_nubra_handler, test_csv_dir):
    """Test that data with negative prices is rejected"""
    # Setup
    symbol = 'TESTSTOCK'
    from_date = '2024-01-01'
    to_date = '2024-01-03'

    # Create invalid data with negative price
    dates = pd.date_range(start='2024-01-01', end='2024-01-03', freq='D')
    invalid_data = {
        'open': [100.0, -5.0, 101.0],  # Negative open price
        'high': [105.0, 106.0, 104.0],
        'low': [99.0, 101.0, 100.0],
        'close': [102.0, 103.0, 101.5],
        'volume': [1000000, 1200000, 1100000]
    }
    df = pd.DataFrame(invalid_data, index=dates)

    # Mock Nubra API to return invalid data
    mock_nubra_handler.get_historical_data.return_value = df

    # Create DataFetcher instance
    fetcher = DataFetcher(mock_nubra_handler, test_csv_dir)

    # Execute
    result = fetcher.fetch_and_append(symbol, from_date, to_date)

    # Verify
    assert result['status'] == 'failed'
    assert result['rows_added'] == 0
    assert 'negative' in result['error'].lower() or 'invalid' in result['error'].lower()
