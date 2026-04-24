import httpx
import json
import time
from pathlib import Path
from typing import List, Optional
from decimal import Decimal
from ..models import Coin

CACHE_FILE = Path("~/.cryptopulse/cache.json").expanduser()
TTL_60S = 60

class CryptoFetcher:
    def __init__(self, api_url: str = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=100&page=1&sparkline=true"):
        self.api_url = api_url

    async def get_latest_prices(self) -> List[Coin]:
        cached_data = self._load_cache()
        if cached_data:
            timestamp = cached_data.get("timestamp", 0)
            if time.time() - timestamp < TTL_60S:
                return [self._parse_coin(item) for item in cached_data.get("data", [])]

        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                response = await client.get(self.api_url)
                response.raise_for_status()
                data = response.json()
                self._save_cache(data)
                return [self._parse_coin(item) for item in data]
        except httpx.HTTPError:
            if cached_data:
                return [self._parse_coin(item) for item in cached_data.get("data", [])]
            return []

    def _parse_coin(self, item: dict) -> Coin:
        # Map price_usd or current_price to current_price
        price = item.get("current_price") or item.get("price_usd")
        sparkline = item.get("sparkline_in_7d", {}).get("price")
        if sparkline:
            sparkline = [Decimal(str(p)) for p in sparkline]
        
        return Coin(
            id=item["id"],
            symbol=item["symbol"],
            name=item["name"],
            current_price=Decimal(str(price)),
            market_cap=Decimal(str(item.get("market_cap"))) if item.get("market_cap") else None,
            sparkline_7d=sparkline
        )

    def _save_cache(self, data: list):
        try:
            CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
            CACHE_FILE.write_text(json.dumps({
                "data": data,
                "timestamp": time.time()
            }))
        except Exception:
            pass

    def _load_cache(self) -> Optional[dict]:
        if not CACHE_FILE.exists():
            return None
        try:
            return json.loads(CACHE_FILE.read_text())
        except Exception:
            return None
