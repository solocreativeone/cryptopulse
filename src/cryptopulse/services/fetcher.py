import httpx
import json
import time
from pathlib import Path
from typing import List, Optional, Dict, Any
from decimal import Decimal
from ..models import Coin, GlobalData
from ..api.client import CryptoAPIClient, NetworkError

# Local file system cache for API results
CACHE_FILE = Path("~/.cryptopulse/cache.json").expanduser()
# 60 seconds time-to-live for price data cache
TTL_60S = 60

class CryptoFetcher:
    """
    Service responsible for fetching and caching cryptocurrency market data.
    
    Implements a transparent caching layer and handles graceful fallback to stale
    data when the network or API is unavailable.
    """
    
    def __init__(self):
        self.client = CryptoAPIClient()
        self.is_stale = False

    @property
    def api_url(self) -> str:
        """Returns the markets endpoint URL from the client."""
        return f"{self.client.base_url}/coins/markets"

    async def get_latest_prices(self, per_page: int = 100) -> List[Coin]:
        """
        Retrieves the latest market prices for the top N coins.
        
        Tries the cache first. If cache is missing or expired, fetches fresh data 
        from the API. If the API fetch fails, falls back to stale cache.
        """
        self.is_stale = False
        cached_data = self._load_cache()
        if cached_data:
            timestamp = cached_data.get("timestamp", 0)
            if time.time() - timestamp < TTL_60S:
                return [self._parse_coin(item) for item in cached_data.get("data", [])]

        try:
            data = await self.client.get_markets(per_page=per_page)
            self._save_cache(data)
            return [self._parse_coin(item) for item in data]
        except (NetworkError, Exception):
            self.is_stale = True
            # Graceful degradation: return stale cache if available
            if cached_data:
                return [self._parse_coin(item) for item in cached_data.get("data", [])]
            return []

    async def get_coin_details(self, coin_id: str) -> Optional[Coin]:
        """Fetches granular details for a specific coin by its ID."""
        try:
            data = await self.client.get_coin_details(coin_id)
            return self._parse_coin_details(data)
        except Exception:
            return None

    async def get_global_data(self) -> Optional[GlobalData]:
        """Fetches high-level global crypto market statistics."""
        try:
            data = await self.client.get_global_data()
            raw_data = data.get("data", {})
            return GlobalData(
                total_market_cap=raw_data.get("total_market_cap", {}),
                total_volume=raw_data.get("total_volume", {}),
                market_cap_percentage=raw_data.get("market_cap_percentage", {}),
                market_cap_change_percentage_24h_usd=Decimal(str(raw_data.get("market_cap_change_percentage_24h_usd", 0))),
                active_cryptocurrencies=raw_data.get("active_cryptocurrencies", 0),
                upcoming_icos=raw_data.get("upcoming_icos", 0),
                ongoing_icos=raw_data.get("ongoing_icos", 0),
                ended_icos=raw_data.get("ended_icos", 0),
                markets=raw_data.get("markets", 0)
            )
        except Exception:
            return None

    def _parse_coin(self, item: dict) -> Coin:
        """Parses raw market list item into a Coin model."""
        sparkline = item.get("sparkline_in_7d", {}).get("price")
        if sparkline:
            sparkline = [Decimal(str(p)) for p in sparkline]
        
        return Coin(
            id=item["id"],
            symbol=item["symbol"],
            name=item["name"],
            current_price=Decimal(str(item.get("current_price", 0))),
            market_cap=Decimal(str(item.get("market_cap"))) if item.get("market_cap") else None,
            total_volume=Decimal(str(item.get("total_volume"))) if item.get("total_volume") else None,
            high_24h=Decimal(str(item.get("high_24h"))) if item.get("high_24h") else None,
            low_24h=Decimal(str(item.get("low_24h"))) if item.get("low_24h") else None,
            ath=Decimal(str(item.get("ath"))) if item.get("ath") else None,
            ath_date=item.get("ath_date"),
            sparkline_7d=sparkline
        )

    def _parse_coin_details(self, data: dict) -> Coin:
        """Parses raw detailed coin data into a Coin model."""
        market_data = data.get("market_data", {})
        sparkline = market_data.get("sparkline_7d", {}).get("price")
        if sparkline:
            sparkline = [Decimal(str(p)) for p in sparkline]

        return Coin(
            id=data["id"],
            symbol=data["symbol"],
            name=data["name"],
            current_price=Decimal(str(market_data.get("current_price", {}).get("usd", 0))),
            market_cap=Decimal(str(market_data.get("market_cap", {}).get("usd", 0))),
            total_volume=Decimal(str(market_data.get("total_volume", {}).get("usd", 0))),
            high_24h=Decimal(str(market_data.get("high_24h", {}).get("usd", 0))),
            low_24h=Decimal(str(market_data.get("low_24h", {}).get("usd", 0))),
            ath=Decimal(str(market_data.get("ath", {}).get("usd", 0))),
            ath_date=market_data.get("ath_date", {}).get("usd"),
            sparkline_7d=sparkline
        )

    def _save_cache(self, data: list):
        """Serializes and saves API response to local disk."""
        try:
            CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
            CACHE_FILE.write_text(json.dumps({
                "data": data,
                "timestamp": time.time()
            }))
        except Exception:
            pass

    def _load_cache(self) -> Optional[dict]:
        """Loads cached API response from local disk."""
        if not CACHE_FILE.exists():
            return None
        try:
            return json.loads(CACHE_FILE.read_text())
        except Exception:
            return None
