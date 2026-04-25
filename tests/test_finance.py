import pytest
from decimal import Decimal
from cryptopulse.utils.finance import FinancialCalculator, calculate_ath_percentage

def test_ath_percentage():
    assert calculate_ath_percentage(Decimal("50000"), Decimal("100000")) == Decimal("-50")
    assert calculate_ath_percentage(Decimal("120"), Decimal("100")) == Decimal("20")
    assert calculate_ath_percentage(Decimal("50"), Decimal("0")) == Decimal("0")

def test_financial_calculator_convert():
    calc = FinancialCalculator()
    calc.set_fiat_rates({"EUR": Decimal("0.9")})
    calc.set_crypto_rates({"BTC": Decimal("50000")})
    
    # 100 USD to EUR
    assert calc.convert(Decimal("100"), "USD", "EUR") == Decimal("90")
    
    # 90 EUR to USD
    assert calc.convert(Decimal("90"), "EUR", "USD") == Decimal("100")
    
    # 1 BTC to USD
    assert calc.convert(Decimal("1"), "BTC", "USD") == Decimal("50000")
    
    # 50000 USD to BTC
    assert calc.convert(Decimal("50000"), "USD", "BTC") == Decimal("1")
    
    # 1 BTC to EUR
    # 1 BTC = 50000 USD, 50000 USD = 50000 * 0.9 = 45000 EUR
    assert calc.convert(Decimal("1"), "BTC", "EUR") == Decimal("45000")
    
    # 45000 EUR to BTC
    # 45000 EUR = 45000 / 0.9 = 50000 USD, 50000 USD = 1 BTC
    assert calc.convert(Decimal("45000"), "EUR", "BTC") == Decimal("1")
