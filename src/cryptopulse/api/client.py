import httpx
from typing import List, Dict, Optional, Any
from decimal import Decimal
import time
import json
from pathlib import Path

CACHE_DIR = Path("~/.cryptopulse").expanduser()
COINGECKO_CACHE = CACHE_DIR / "cache.json"
FRANKFURTER_CACHE = CACHE_DIR / "rates.json"

class NetworkError(Exception):
    """Custom exception for network-related failures."""
    pass

class CryptoAPIClient:
    def __init__(self, base_url: str = "https://api.coingecko.com/api/v3"):
        self.base_url = base_url

    async def get_markets(self, vs_currency: str = "usd", per_page: int = 100) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/coins/markets"
        params = {
            "vs_currency": vs_currency,
            "order": "market_cap_desc",
            "per_page": per_page,
            "page": 1,
            "sparkline": "true"
        }
        
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                return response.json()
        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            raise NetworkError(f"Coingecko API unreachable: {e}")

    async def get_coin_details(self, coin_id: str) -> Dict[str, Any]:
        url = f"{self.base_url}/coins/{coin_id}"
        params = {
            "localization": "false",
            "tickers": "false",
            "market_data": "true",
            "community_data": "false",
            "developer_data": "false",
            "sparkline": "true"
        }
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                return response.json()
        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            raise NetworkError(f"Coingecko API unreachable: {e}")

    async def get_global_data(self) -> Dict[str, Any]:
        url = f"{self.base_url}/global"
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.json()
        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            raise NetworkError(f"Coingecko API unreachable: {e}")

class FiatAPIClient:
    def __init__(self, base_url: str = "https://api.frankfurter.dev/v1"):
        self.base_url = base_url

    async def get_rates(self, base: str = "USD") -> Dict[str, Any]:
        url = f"{self.base_url}/latest"
        params = {"from": base}
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                return response.json()
        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            raise NetworkError(f"Fiat Rates API unreachable: {e}")
