import httpx
import json
import time
from pathlib import Path
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Optional

RATES_CACHE = Path("~/.cryptopulse/rates.json").expanduser()
TTL_24H = 24 * 60 * 60

class CurrencyConverter:
    def __init__(self):
        self.fiat_rates: Dict[str, Decimal] = {"USD": Decimal("1.0")}
        self.crypto_rates: Dict[str, Decimal] = {}
        self.last_fetched = 0.0
        self.fallback_ngn = Decimal("1354.0")

    async def get_rates(self) -> Dict[str, Decimal]:
        # Try to load from cache first
        cached_data = self._load_cache()
        if cached_data:
            rates = {k: Decimal(str(v)) for k, v in cached_data.get("rates", {}).items()}
            timestamp = cached_data.get("timestamp", 0)
            if time.time() - timestamp < TTL_24H:
                self.fiat_rates = rates
                return self.fiat_rates

        # Fetch new rates
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get("https://api.frankfurter.dev/v1/latest?from=USD")
                response.raise_for_status()
                data = response.json()
                new_rates = {k: Decimal(str(v)) for k, v in data.get("rates", {}).items()}
                new_rates["USD"] = Decimal("1.0")
                self._save_cache(new_rates)
                self.fiat_rates = new_rates
        except Exception:
            # If offline and cache expired, use last cached rates or fallback
            if cached_data:
                self.fiat_rates = {k: Decimal(str(v)) for k, v in cached_data.get("rates", {}).items()}
            else:
                self.fiat_rates["NGN"] = self.fallback_ngn
        
        return self.fiat_rates

    def set_crypto_rates(self, prices: Dict[str, Decimal]):
        """
        Store crypto prices (symbol/id -> USD price) for cross-asset conversion.
        """
        self.crypto_rates = {k.upper(): v for k, v in prices.items()}

    def convert(self, amount: Decimal, to_currency: str) -> Decimal:
        to_currency = to_currency.upper()
        
        # 1. Handle Crypto-to-Crypto
        if to_currency in self.crypto_rates:
            target_price_usd = self.crypto_rates[to_currency]
            if target_price_usd == 0:
                return Decimal("0")
            return (amount / target_price_usd)

        # 2. Handle Fiat
        if to_currency in self.fiat_rates:
            return amount * self.fiat_rates[to_currency]
            
        # 3. Handle Fallbacks
        if to_currency == "NGN" and "NGN" not in self.fiat_rates:
             return amount * self.fallback_ngn
             
        return amount # Fallback to USD if currency unknown

    def _save_cache(self, rates: Dict[str, Decimal]):
        try:
            RATES_CACHE.parent.mkdir(parents=True, exist_ok=True)
            serializable_rates = {k: str(v) for k, v in rates.items()}
            RATES_CACHE.write_text(json.dumps({
                "rates": serializable_rates,
                "timestamp": time.time()
            }))
        except Exception:
            pass

    def _load_cache(self) -> Optional[Dict]:
        if not RATES_CACHE.exists():
            return None
        try:
            return json.loads(RATES_CACHE.read_text())
        except Exception:
            return None
