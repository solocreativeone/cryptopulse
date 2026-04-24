import pytest
import respx
import json
import time
from httpx import Response
from decimal import Decimal
from pathlib import Path
from cryptopulse.services.fetcher import CryptoFetcher, CACHE_FILE

@pytest.mark.asyncio
async def test_fetcher_fallback_on_500():
    # Setup cache
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
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
        "timestamp": time.time() - 100 # Expired (>60s)
    }))

    fetcher = CryptoFetcher()
    
    with respx.mock:
        # Mock 500 error
        respx.get(fetcher.api_url).mock(return_value=Response(500))
        
        coins = await fetcher.get_latest_prices()
        
        assert len(coins) == 1
        assert coins[0].id == "bitcoin"
        assert coins[0].current_price == Decimal("50000")

@pytest.mark.asyncio
async def test_fetcher_success_updates_cache():
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
    
    with respx.mock:
        respx.get(fetcher.api_url).mock(return_value=Response(200, json=mock_data))
        
        coins = await fetcher.get_latest_prices()
        
        assert len(coins) == 1
        assert coins[0].id == "ethereum"
        
        # Verify cache was updated
        cached = json.loads(CACHE_FILE.read_text())
        assert cached["data"][0]["id"] == "ethereum"
