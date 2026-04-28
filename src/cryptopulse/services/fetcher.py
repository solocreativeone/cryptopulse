import json
import time
import os
from pathlib import Path
from typing import List, Optional, Dict, Any
from decimal import Decimal
from ..config import PRICES_CACHE_FILE as CACHE_FILE, PRICES_TTL as TTL_60S
from ..models import Coin, GlobalData
from ..api.client import (
    CoinGeckoProvider, 
    MobulaProvider, 
    CoinPaprikaProvider, 
    NetworkError, 
    RateLimitError
)

class CryptoFetcher:
    """
    Resilient Fetcher using the Service Provider pattern.
    Fallback Chain: CoinGecko -> Mobula -> CoinPaprika.
    Includes a 60-second local JSON cache.
    """
    
    def __init__(self):
        self.providers = [
            CoinGeckoProvider(),
            MobulaProvider(),
            CoinPaprikaProvider()
        ]
        self.is_stale = False

    async def get_latest_prices(self, per_page: int = 100) -> List[Coin]:
        """
        Tries to fetch fresh data through the provider chain.
        Prioritizes the local cache within TTL.
        """
        self.is_stale = False
        
        # 1. Check Local Cache
        cached = self._load_cache()
        if cached and (time.time() - cached.get("timestamp", 0) < TTL_60S):
            return [self._normalize_coin(item, "coingecko") for item in cached.get("data", [])]

        # 2. Try Provider Chain
        for provider in self.providers:
            try:
                data = await provider.get_markets(per_page=per_page)
                self._save_cache(data)
                provider_type = provider.__class__.__name__.lower().replace("provider", "")
                return [self._normalize_coin(item, provider_type) for item in data]
            except (RateLimitError, NetworkError):
                continue
            except Exception:
                continue

        # 3. Final Fallback: Stale Cache
        self.is_stale = True
        if cached:
            return [self._normalize_coin(item, "coingecko") for item in cached.get("data", [])]
        
        return []

    async def get_coin_details(self, coin_id: str) -> Optional[Coin]:
        """Fetches granular details for a specific coin by its ID."""
        for provider in self.providers:
            if isinstance(provider, CoinGeckoProvider):
                try:
                    data = await provider.get_coin_details(coin_id)
                    return self._normalize_coin_details(data)
                except:
                    continue
        return None

    async def get_global_data(self) -> Optional[GlobalData]:
        """Fetches high-level global crypto market statistics."""
        for provider in self.providers:
            if isinstance(provider, CoinGeckoProvider):
                try:
                    data = await provider.get_global_data()
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
                except:
                    continue
        return None

    def _normalize_coin(self, item: dict, source: str) -> Coin:
        """
        Maps different API responses to the unified Coin model.
        """
        if source == "coingecko":
            sparkline = item.get("sparkline_in_7d", {}).get("price")
            if sparkline:
                sparkline = [Decimal(str(p)) for p in sparkline]
            
            return Coin(
                id=item.get("id", ""),
                symbol=item.get("symbol", ""),
                name=item.get("name", ""),
                current_price=Decimal(str(item.get("current_price", 0))),
                market_cap=Decimal(str(item.get("market_cap"))) if item.get("market_cap") else None,
                sparkline_7d=sparkline
            )
        elif source == "mobula":
            return Coin(
                id=item.get("name", "").lower(),
                symbol=item.get("symbol", ""),
                name=item.get("name", ""),
                current_price=Decimal(str(item.get("price", 0))),
                market_cap=Decimal(str(item.get("market_cap", 0)))
            )
        return Coin(id="unknown", symbol="?", name="Unknown", current_price=Decimal("0"))

    def _normalize_coin_details(self, data: dict) -> Coin:
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

    def _save_cache(self, data: Any):
        try:
            CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
            CACHE_FILE.write_text(json.dumps({
                "data": data,
                "timestamp": time.time()
            }))
        except Exception:
            pass

    def _load_cache(self) -> Optional[Dict]:
        if not CACHE_FILE.exists():
            return None
        try:
            return json.loads(CACHE_FILE.read_text())
        except Exception:
            return None
