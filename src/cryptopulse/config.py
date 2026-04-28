from decimal import Decimal
from pathlib import Path

# Cache settings
CACHE_DIR = Path("~/.cryptopulse").expanduser()
PRICES_CACHE_FILE = CACHE_DIR / "prices.json"
RATES_CACHE_FILE = CACHE_DIR / "rates.json"

PRICES_TTL = 60
RATES_TTL = 24 * 60 * 60

# Financial defaults
FALLBACK_NGN_RATE = Decimal("1354.0")
DEFAULT_FIAT_CURRENCY = "USD"
