import json
import time
from pathlib import Path
from decimal import Decimal
from typing import Dict, Optional
from ..api.client import FiatAPIClient, NetworkError
from ..config import RATES_CACHE_FILE as RATES_CACHE, RATES_TTL as TTL_24H, FALLBACK_NGN_RATE
from .finance import FinancialCalculator

class CurrencyConverter:
    """
    Handles conversion between different fiat and cryptocurrency assets.
    
    Uses a FinancialCalculator for precise math and maintains a local cache
     of fiat exchange rates to minimize API calls.
    """
    
    def __init__(self):
        self.client = FiatAPIClient()
        self.calculator = FinancialCalculator()
        self.fallback_ngn = FALLBACK_NGN_RATE
        self.is_stale = False

    @property
    def fiat_rates(self) -> Dict[str, Decimal]:
        """Returns the current fiat exchange rates from the calculator."""
        return self.calculator.fiat_rates

    @fiat_rates.setter
    def fiat_rates(self, rates: Dict[str, Decimal]):
        """Updates the fiat exchange rates in the calculator."""
        self.calculator.set_fiat_rates(rates)

    async def get_rates(self) -> Dict[str, Decimal]:
        """
        Retrieves and caches the latest fiat exchange rates.
        
        Prioritizes the local cache within the TTL. Fetches from the API
        if necessary and falls back to stale data or hardcoded defaults on failure.
        """
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
            # Graceful fallback to stale cache or hardcoded NGN default
            if cached_data:
                rates = {k: Decimal(str(v)) for k, v in cached_data.get("rates", {}).items()}
                self.calculator.set_fiat_rates(rates)
            else:
                rates = {"USD": Decimal("1.0"), "NGN": self.fallback_ngn}
                self.calculator.set_fiat_rates(rates)
        
        return self.calculator.fiat_rates

    def set_crypto_rates(self, prices: Dict[str, Decimal]):
        """Injects current crypto prices (vs USD) into the calculator for conversions."""
        self.calculator.set_crypto_rates(prices)

    def convert(self, amount: Decimal, to_currency: str) -> Decimal:
        """
        Performs asset conversion from USD to the target currency.
        
        Supported targets include fiat (EUR, NGN, etc.) and crypto (BTC, SOL, etc.).
        """
        return self.calculator.convert(amount, "USD", to_currency)

    def _save_cache(self, rates: Dict[str, Decimal]):
        """Persists fiat rates to local disk as strings to maintain precision."""
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
        """Loads cached fiat rates from local disk."""
        if not RATES_CACHE.exists():
            return None
        try:
            return json.loads(RATES_CACHE.read_text())
        except Exception:
            return None
