import pytest
from decimal import Decimal
from cryptopulse.utils.converter import CurrencyConverter

def test_decimal_precision():
    converter = CurrencyConverter()
    # Mock rates for precision test
    converter.fiat_rates = {"NGN": Decimal("1354.123456789")}
    
    amount_usd = Decimal("10.50")
    expected = Decimal("10.50") * Decimal("1354.123456789")
    
    result = converter.convert(amount_usd, "NGN")
    
    assert result == expected
    assert isinstance(result, Decimal)

def test_fallback_ngn():
    converter = CurrencyConverter()
    converter.fiat_rates = {"USD": Decimal("1.0")}
    
    amount_usd = Decimal("100.00")
    # Should use fallback_ngn (1354.0)
    result = converter.convert(amount_usd, "NGN")
    
    assert result == Decimal("135400.00")

def test_crypto_to_crypto_conversion():
    converter = CurrencyConverter()
    # Mock crypto prices: BTC = $50,000, SOL = $100
    converter.set_crypto_rates({
        "BTC": Decimal("50000"),
        "SOL": Decimal("100")
    })
    
    # 1 BTC in SOL should be 500
    btc_price_usd = Decimal("50000")
    result = converter.convert(btc_price_usd, "SOL")
    
    assert result == Decimal("500")
    assert isinstance(result, Decimal)

    # 1 SOL in BTC should be 0.002
    sol_price_usd = Decimal("100")
    result = converter.convert(sol_price_usd, "BTC")
    assert result == Decimal("0.002")
