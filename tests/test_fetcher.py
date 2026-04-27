import pytest
import respx
import json
import time
import os
from httpx import Response
from decimal import Decimal
from pathlib import Path
from cryptopulse.services.fetcher import CryptoFetcher, CACHE_FILE

# Default URLs from providers
COINGECKO_URL = "https://api.coingecko.com/api/v3/coins/markets"
MOBULA_URL = "https://api.mobula.io/api/1/market/data"
COINPAPRIKA_URL = "https://api.coinpaprika.com/v1/tickers"

@pytest.mark.asyncio
async def test_fetcher_fallback_on_api_failure():
    """
    Test that if CoinGecko fails, it falls back to Mobula.
    """
    # Setup expired cache
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    CACHE_FILE.write_text(json.dumps({
        "data": [],
        "timestamp": time.time() - 100 
    }))

    fetcher = CryptoFetcher()
    
    mobula_mock_data = {
        "data": [
            {
                "symbol": "BTC",
                "name": "Bitcoin",
                "price": 60000,
                "market_cap": 1200000000000
            }
        ]
    }

    with respx.mock:
        # Mock CoinGecko failure (429)
        respx.get(COINGECKO_URL).mock(return_value=Response(429))
        # Mock Mobula success
        respx.get(MOBULA_URL).mock(return_value=Response(200, json=mobula_mock_data))
        
        coins = await fetcher.get_latest_prices()
        
        assert len(coins) == 1
        assert coins[0].name == "Bitcoin"
        assert coins[0].current_price == Decimal("60000")

@pytest.mark.asyncio
async def test_fetcher_stale_cache_fallback():
    """
    Test that if all providers fail, it returns stale cache.
    """
    cache_data = [
        {
            "id": "bitcoin",
            "symbol": "btc",
            "name": "Bitcoin",
            "current_price": 50000,
            "market_cap": 1000000,
            "sparkline_in_7d": {"price": [49000, 50000]}
        }
    ]
    CACHE_FILE.write_text(json.dumps({
        "data": cache_data,
        "timestamp": time.time() - 100 
    }))

    fetcher = CryptoFetcher()
    
    with respx.mock:
        respx.get(COINGECKO_URL).mock(return_value=Response(500))
        respx.get(MOBULA_URL).mock(return_value=Response(500))
        respx.get(COINPAPRIKA_URL).mock(return_value=Response(500))
        
        coins = await fetcher.get_latest_prices()
        
        assert len(coins) == 1
        assert coins[0].current_price == Decimal("50000")
        assert fetcher.is_stale is True

@pytest.mark.asyncio
async def test_fetcher_success_updates_cache():
    """
    Test that a successful fetch updates the local cache file.
    """
    fetcher = CryptoFetcher()
    mock_data = [
        {
            "id": "ethereum",
            "symbol": "eth",
            "name": "Ethereum",
            "current_price": 3000,
            "market_cap": 300000,
            "sparkline_in_7d": {"price": [2900, 3000]}
        }
    ]
    
    # Ensure cache is expired or non-existent
    if CACHE_FILE.exists():
        CACHE_FILE.unlink()

    with respx.mock:
        respx.get(COINGECKO_URL).mock(return_value=Response(200, json=mock_data))
        
        await fetcher.get_latest_prices()
        
        # Verify cache was updated
        assert CACHE_FILE.exists()
        cached = json.loads(CACHE_FILE.read_text())
        assert cached["data"][0]["id"] == "ethereum"
