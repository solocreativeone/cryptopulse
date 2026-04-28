from decimal import Decimal
from typing import Dict, Optional
from ..config import FALLBACK_NGN_RATE

def calculate_ath_percentage(current_price: Decimal, ath_price: Decimal) -> Decimal:
    if not ath_price or ath_price == 0:
        return Decimal("0")
    return (current_price - ath_price) / ath_price * 100

class FinancialCalculator:
    def __init__(self):
        self.fiat_rates: Dict[str, Decimal] = {"USD": Decimal("1.0")}
        self.crypto_rates: Dict[str, Decimal] = {}
        self.fallback_ngn = FALLBACK_NGN_RATE

    def set_fiat_rates(self, rates: Dict[str, Decimal]):
        self.fiat_rates = rates

    def set_crypto_rates(self, rates: Dict[str, Decimal]):
        self.crypto_rates = {k.upper(): v for k, v in rates.items()}

    def convert(self, amount: Decimal, from_currency: str, to_currency: str) -> Decimal:
        """
        Multi-hop conversion: from_currency -> USD -> to_currency
        """
        from_currency = from_currency.upper()
        to_currency = to_currency.upper()

        if from_currency == to_currency:
            return amount

        # Convert from_currency to USD
        usd_amount = amount
        if from_currency != "USD":
            if from_currency in self.crypto_rates:
                usd_amount = amount * self.crypto_rates[from_currency]
            elif from_currency in self.fiat_rates:
                usd_amount = amount / self.fiat_rates[from_currency]
            elif from_currency == "NGN":
                usd_amount = amount / self.fallback_ngn
            else:
                pass

        # Convert USD to to_currency
        if to_currency == "USD":
            return usd_amount
        
        if to_currency in self.crypto_rates:
            target_price_usd = self.crypto_rates[to_currency]
            if target_price_usd == 0:
                return Decimal("0")
            return usd_amount / target_price_usd
        
        if to_currency in self.fiat_rates:
            return usd_amount * self.fiat_rates[to_currency]
        
        if to_currency == "NGN":
            return usd_amount * self.fallback_ngn
        
        return usd_amount # Fallback
