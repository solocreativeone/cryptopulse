import json
import time
from pathlib import Path
from decimal import Decimal
from typing import Dict, Optional
from ..api.client import FiatAPIClient, NetworkError
from .finance import FinancialCalculator

RATES_CACHE = Path("~/.cryptopulse/rates.json").expanduser()
TTL_24H = 24 * 60 * 60

class CurrencyConverter:
    def __init__(self):
        self.client = FiatAPIClient()
        self.calculator = FinancialCalculator()
        self.fallback_ngn = Decimal("1354.0")
        self.is_stale = False

    @property
    def fiat_rates(self) -> Dict[str, Decimal]:
        return self.calculator.fiat_rates

    @fiat_rates.setter
    def fiat_rates(self, rates: Dict[str, Decimal]):
        self.calculator.set_fiat_rates(rates)

    async def get_rates(self) -> Dict[str, Decimal]:
        self.is_stale = False
        cached_data = self._load_cache()
        if cached_data:
            rates = {k: Decimal(str(v)) for k, v in cached_data.get("rates", {}).items()}
            timestamp = cached_data.get("timestamp", 0)
            if time.time() - timestamp < TTL_24H:
                self.calculator.set_fiat_rates(rates)
                return rates

        try:
            data = await self.client.get_rates(base="USD")
            new_rates = {k: Decimal(str(v)) for k, v in data.get("rates", {}).items()}
            new_rates["USD"] = Decimal("1.0")
            self._save_cache(new_rates)
            self.calculator.set_fiat_rates(new_rates)
        except (NetworkError, Exception):
            self.is_stale = True
            if cached_data:
                rates = {k: Decimal(str(v)) for k, v in cached_data.get("rates", {}).items()}
                self.calculator.set_fiat_rates(rates)
            else:
                rates = {"USD": Decimal("1.0"), "NGN": self.fallback_ngn}
                self.calculator.set_fiat_rates(rates)
        
        return self.calculator.fiat_rates

    def set_crypto_rates(self, prices: Dict[str, Decimal]):
        self.calculator.set_crypto_rates(prices)

    def convert(self, amount: Decimal, to_currency: str) -> Decimal:
        return self.calculator.convert(amount, "USD", to_currency)

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
