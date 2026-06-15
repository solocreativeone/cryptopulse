# CryptoPulse

High-performance, production-grade cryptocurrency CLI utility with high-precision financial logic and global currency support.

[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://python.org)
[![Typer](https://img.shields.io/badge/Typer-CLI-green)](https://typer.tiangolo.com)
[![Rich](https://img.shields.io/badge/Rich-UI-purple)](https://rich.readthedocs.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

---
## Table of Contents

- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Quick Start — Wizard Commands](#quick-start--wizard-commands)
- [Usage](#usage)
- [Visuals](#visuals)
- [Network Resilience](#network-resilience)
- [Configuration](#configuration)
- [Technical Architecture](#technical-architecture)
- [Testing](#testing)
- [Debugging](#debugging)
- [Maintainer](#maintainer)
- [License](#license)

---


<p align="center">
  <h2 align="center">Features</h2>
</p>

- 🌍 **Real-time Global Data:** Fetch latest prices and market caps for top cryptocurrencies instantly.
- 💱 **Hybrid Conversion:** Seamless support for both fiat (EUR, NGN, JPY) and cross-crypto (SOL, ETH, BTC) valuations.
- 🎯 **High-Precision Math:** Powered by `decimal.Decimal` to eliminate floating-point errors in financial logic.
- 🛡️ **Resilient Infrastructure:** Automated retries and tiered caching (24hr TTL for rates, 60s for prices).
- 🎨 **Dynamic UI:** Beautifully formatted tables with sparklines and auto-updating headers via `Rich`.
- 🧘 **Minimalist Mode:** A focused `zen` view with curated market philosophy quotes for deep focus.
- 📸 **Auto-Doc Screenshots:** Generate high-fidelity SVG screenshots of any terminal output using the `--snap` flag.

## Requirements

- Python 3.10 or higher
- pip (for package installation)

---

## Installation

```bash
# Clone the repository
git clone https://github.com/solocreativeone/cryptopulse.git
cd cryptopulse

# Set up a virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in editable mode with test dependencies
# NOTE: Editable mode (-e) is required to activate the shorthand wizard aliases!
pip install -e ".[test]"

# Configure environment variables
cp .env.example .env
# Edit .env with your API keys for enhanced rate limits
```

---
## Quick Start — Wizard Commands

Speed is everything. CryptoPulse includes built-in 3-letter shorthands to bypass the full command prefix:

| Alias | Command     | Description              |
|-------|-------------|--------------------------|
| `cpl` | `list`      | Instant market list      |
| `cpw` | `watch`     | Live market watcher      |
| `cpz` | `zen`       | Focused zen mode         |
| `cpg` | `global`    | Global market analytics  |

> These aliases are only available after installing in editable mode (`pip install -e`).

---

## Visuals

Experience CryptoPulse in your terminal. These screenshots are **auto-generated** by the CLI's built-in `--snap` engine, ensuring they always reflect the latest UI.

### Market Overview
Experience multi-currency support with optimized layouts for high-value fiat conversions like NGN.

![List View USD](docs/screenshots/list.svg)
![List View NGN](docs/screenshots/list_ngn.svg)

### Deep Analytics
<p align="center">
  <img src="docs/screenshots/stat.svg" alt="Coin Statistics" width="400" />
  <img src="docs/screenshots/global.svg" alt="Global Data" width="400" />
</p>

### Zen Mode
<p align="center">
  <img src="docs/screenshots/zen.svg" alt="Zen Mode" width="600" />
</p>

### Live Monitoring
![Live Watcher](docs/screenshots/watch.svg)

<p align="center">
  <a href="https://typer.tiangolo.com/"><img src="https://img.shields.io/badge/Typer-4B32C3?style=for-the-badge&logo=python&logoColor=white" alt="Typer" /></a>
  <a href="https://rich.readthedocs.io/"><img src="https://img.shields.io/badge/Rich-black?style=for-the-badge&logo=python&logoColor=white" alt="Rich" /></a>
  <a href="https://www.python-httpx.org/"><img src="https://img.shields.io/badge/HTTPX-000000?style=for-the-badge&logo=python&logoColor=white" alt="HTTPX" /></a>
  <a href="https://docs.pydantic.dev/"><img src="https://img.shields.io/badge/Pydantic-E92063?style=for-the-badge&logo=pydantic&logoColor=white" alt="Pydantic" /></a>
  <a href="https://docs.python.org/3/library/decimal.html"><img src="https://img.shields.io/badge/Decimal-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Decimal" /></a>
</p>

## Installation

```bash
# Clone the repository
git clone https://github.com/solocreativeone/cryptopulse.git
cd cryptopulse

# Set up virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in editable mode with test dependencies
# NOTE: Editable mode (-e) is required to activate the shorthand wizard aliases!
pip install -e ".[test]"

# Configure environment variables
cp .env.example .env
# Edit .env with your API keys for enhanced rate limits
```

## Usage

The CLI command is `cryptopulse`. Shorthand commands are also available for instant access:
- `cpl` → `list`
- `cpw` → `watch`
- `cpz` → `zen`
- `cpg` → `global`

You can always use `cryptopulse --help` to see all available commands and options.

### List Top Coins
View the top 10 coins by market cap. You can specify any fiat or crypto currency for valuation and export data to JSON:
```bash
# Default (USD)
cpl

# Specified currency
cpl --currency eur
cpl -c sol

# Export to JSON file
cpl --export
cpl -e
```

### Coin Statistics
Get detailed information for a specific coin, including 24h highs/lows, ATH data, and a 7-day trend sparkline:
```bash
cryptopulse stat bitcoin
cryptopulse stat ethereum
```

### Global Market Data
View overall crypto market statistics:
```bash
cpg
```

### Real-time Watcher
Monitor specific coins in real-time with an auto-refreshing table:
```bash
# Watch Bitcoin and Solana every 10 seconds
cpw bitcoin sol --interval 10
```

### Zen Mode
Minimalist price view for a specific coin with curated market philosophy quotes:
```bash
cpz btc
```

## Network Resilience

CryptoPulse is built to survive outages and rate limits. If the primary API (CoinGecko) is unreachable or hits a `429` error, the system will:

1. **Switch providers** — automatically rotate to Mobula or CoinPaprika for fresh data.
2. **Local fallback** — if all providers fail, serve data from the 60-second local cache.
3. **Stale awareness** — display a `[stale]` warning panel so you always know when you're viewing cached data.

Provider chain: **CoinGecko** (primary) → **Mobula** (secondary) → **CoinPaprika** (final fallback)

## Configuration

For professional use, configure provider endpoints via your `.env` file:

| Variable | Description |
|---|---|
| `CP_COINGECKO_API_KEY` | Unlocks higher rate limits for CoinGecko |
| `CP_MOBULA_API_KEY` | Optional key for the Mobula fallback provider |
| `CP_COINGECKO_BASE_URL` | Override default endpoints (e.g. for the Pro API) |

All keys are loaded via `os.getenv` — no secrets are ever hardcoded.

### Debugging
Run any command with the `--debug` flag to see full technical tracebacks on failure:
```bash
cryptopulse list --debug
```

---

## Technical Architecture

- **Multi-provider fallback** — The provider chain (CoinGecko → Mobula → CoinPaprika) handles `429` rate limits and network failures automatically.
- **Tiered caching** — A high-speed cache in `~/.cryptopulse/` minimises API overhead (60s TTL for prices, 24hr for exchange rates).
- **Financial integrity** — All currency conversions use Python's `decimal` library for 100% mathematical accuracy.
- **Pydantic V2** — High-performance data validation and serialisation throughout.
- **Secure by design** — Zero hardcoded API keys; all configuration is managed via `.env` files.

---

## Testing
Run the comprehensive test suite to verify precision and cache logic:
```bash
pytest
```

## Maintainer

Developed and maintained by **SoloCreativeOne**.

Co-authored-by: Luckingz <luckyajidoku.com@gmail.com>

[![Follow on X](https://img.shields.io/badge/X.com-solocreativeone-000000?style=for-the-badge&logo=x&logoColor=white)](https://x.com/solocreativeone)

## License
[MIT](LICENSE)


