# CryptoPulse

High-performance, production-grade cryptocurrency CLI utility with high-precision financial logic and global currency support.

## Features
- **Real-time Global Data:** Fetch latest prices and market caps for top cryptocurrencies.
- **Hybrid Conversion:** Support for both fiat (EUR, NGN, JPY, etc.) and cross-crypto (SOL, ETH, BTC) price valuations.
- **High-Precision Math:** Uses `decimal.Decimal` to eliminate floating-point errors in financial calculations.
- **Resilient Infrastructure:** Automated retries and tiered caching (`rates.json` 24hr TTL, `cache.json` 60s TTL) for offline reliability.
- **Dynamic UI:** Beautifully formatted tables with sparklines and auto-updating headers powered by `Rich`.
- **Minimalist Mode:** `zen` command for a focused view with curated market philosophy quotes.

## Tech Stack
- **CLI Framework:** [Typer](https://typer.tiangolo.com/)
- **UI/Formatting:** [Rich](https://rich.readthedocs.io/)
- **HTTP Client:** [HTTPX](https://www.python-httpx.org/)
- **Data Validation:** [Pydantic](https://docs.pydantic.dev/)
- **Precision:** [Decimal](https://docs.python.org/3/library/decimal.html)

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/cryptopulse.git
cd cryptopulse

# Install in editable mode with test dependencies
pip install -e ".[test]"
```

## Usage

### List Top Coins
View the top 10 coins in any fiat or crypto currency:
```bash
cryptopulse list --currency eur
cryptopulse list --currency sol
```

### Zen Mode
Minimalist price view for a specific coin with a random quote:
```bash
cryptopulse zen btc
```

### Debugging
Run any command with the `--debug` flag to see full technical tracebacks on failure.

## Testing
Run the comprehensive test suite to verify precision and cache logic:
```bash
pytest
```

## License
MIT
