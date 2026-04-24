import asyncio
import typer
import random
import webbrowser
import time
from typing import List, Optional, Dict
from decimal import Decimal
from rich.console import Console, Group
from rich.table import Table
from rich.panel import Panel
from rich.live import Live
from rich.align import Align
from rich.text import Text
from pydantic import ValidationError
from httpx import HTTPError

from .services.fetcher import CryptoFetcher
from .utils.converter import CurrencyConverter
from .models import Coin

app = typer.Typer(
    help="CryptoPulse CLI - Production-grade high-precision crypto tracker.",
    no_args_is_help=True
)
console = Console()

ZEN_QUOTES = [
    "Focus on the signal, ignore the noise.",
    "The market is a device for transferring money from the impatient to the patient.",
    "Buy when there's blood in the streets, even if the blood is your own.",
    "In the short run, the market is a voting machine; in the long run, it is a weighing machine.",
    "The most important quality for an investor is temperament, not intellect.",
]

def get_sparkline(prices: Optional[List[Decimal]], width: int = 10) -> str:
    if not prices or len(prices) < 2:
        return ""
    
    # Sample to width
    step = len(prices) / width
    sampled = [prices[int(i * step)] for i in range(width)]
    
    min_p, max_p = min(sampled), max(sampled)
    if max_p == min_p:
        return "─" * width
        
    chars = " ▂▃▄▅▆▇█"
    line = ""
    for p in sampled:
        idx = int((p - min_p) / (max_p - min_p) * (len(chars) - 1))
        line += chars[idx]
    return line

def format_currency(amount: Decimal, currency: str) -> str:
    symbols = {
        "USD": "$", "EUR": "€", "GBP": "£", "JPY": "¥", 
        "NGN": "₦", "BTC": "₿", "ETH": "Ξ", "SOL": "S "
    }
    symbol = symbols.get(currency.upper(), currency.upper() + " ")
    
    # Use higher precision for crypto-to-crypto ratios
    if currency.upper() in ["BTC", "ETH", "SOL"]:
        return f"{symbol}{amount:,.4f}"
    return f"{symbol}{amount:,.2f}"

async def run_list(currency: str):
    fetcher = CryptoFetcher()
    converter = CurrencyConverter()
    
    with console.status(f"[bold green]Fetching data and {currency} rates..."):
        coins, _ = await asyncio.gather(
            fetcher.get_latest_prices(),
            converter.get_rates()
        )

    if not coins:
        raise RuntimeError("Could not fetch coin data.")

    # Populate crypto rates for conversion
    crypto_prices = {coin.symbol: coin.current_price for coin in coins}
    crypto_prices.update({coin.id: coin.current_price for coin in coins})
    converter.set_crypto_rates(crypto_prices)

    currency_label = currency.upper()
    table = Table(title=f"CryptoPulse - Top 10 Coins (vs {currency_label})")
    table.add_column("Rank", justify="right", style="dim")
    table.add_column("Symbol", style="cyan", no_wrap=True)
    table.add_column("Name", style="magenta")
    table.add_column(f"Price ({currency_label})", justify="right", style="green")
    table.add_column(f"Market Cap ({currency_label})", justify="right", style="blue")
    table.add_column("Trend (7d)", justify="center", style="yellow")

    for i, coin in enumerate(coins[:10], 1):
        converted_price = converter.convert(coin.current_price, currency)
        converted_cap = converter.convert(coin.market_cap, currency) if coin.market_cap else None
        
        spark = get_sparkline(coin.sparkline_7d)
        
        table.add_row(
            str(i),
            coin.symbol.upper(),
            coin.name,
            format_currency(converted_price, currency),
            format_currency(converted_cap, currency) if converted_cap else "N/A",
            spark
        )

    console.print(table)

async def run_zen(coin_id: str):
    fetcher = CryptoFetcher()
    coins = await fetcher.get_latest_prices()
    coin = next((c for c in coins if c.id == coin_id.lower() or c.symbol == coin_id.lower()), None)
    
    if not coin:
        console.print(f"[red]Coin '{coin_id}' not found in top 100.[/red]")
        return

    quote = random.choice(ZEN_QUOTES)
    
    panel_content = Group(
        Align.center(Text(f"{coin.name} ({coin.symbol.upper()})", style="bold cyan")),
        Align.center(Text(format_currency(coin.current_price, "USD"), style="bold green fs+2")),
        "",
        Align.center(Text(f"\"{quote}\"", style="italic yellow"))
    )
    
    console.print("\n")
    console.print(Panel(panel_content, border_style="dim", width=60))
    console.print("\n")

@app.command()
def list(
    currency: str = typer.Option("USD", "--currency", "-c", help="Currency to display prices in (e.g. EUR, NGN, SOL, ETH)."),
    debug: bool = typer.Option(False, "--debug", help="Show full traceback on error.")
):
    """List the latest prices for top cryptocurrencies."""
    try:
        asyncio.run(run_list(currency))
    except (ValidationError, HTTPError, Exception) as e:
        handle_error(e, debug)

@app.command()
def zen(
    coin: str = typer.Argument("bitcoin", help="The coin to focus on (ID or symbol)."),
    debug: bool = typer.Option(False, "--debug", help="Show full traceback on error.")
):
    """A minimalist, centered view for a single coin with a zen quote."""
    try:
        asyncio.run(run_zen(coin))
    except (ValidationError, HTTPError, Exception) as e:
        handle_error(e, debug)

@app.command(hidden=True)
def fly():
    """Trigger a hidden rocket animation and open the antigravity easter egg."""
    rocket = [
        "   ^   ",
        "  / \\  ",
        " |   | ",
        " |CP | ",
        " |   | ",
        " /_W_\\ ",
        "  vvv  "
    ]
    
    console.clear()
    for i in range(10, 0, -1):
        console.clear()
        print("\n" * i)
        for line in rocket:
            console.print(Align.center(Text(line, style="bold red")))
        time.sleep(0.1)
    
    console.print(Align.center("[bold yellow]LIFTOFF![/bold yellow]"))
    time.sleep(0.5)
    webbrowser.open("https://xkcd.com/353/")

def handle_error(e: Exception, debug: bool):
    error_type = type(e).__name__
    msg = str(e)
    
    if isinstance(e, ValidationError):
        msg = "Data validation failed. The API might have changed its format."
    elif isinstance(e, HTTPError):
        msg = "Communication error with the external API. Please check your internet or the API status."
        
    error_panel = Panel(
        Group(
            f"[bold red]Error:[/bold red] {msg}",
            "" if debug else "[dim]Use --debug to see the full technical traceback.[/dim]"
        ),
        title=f"[bold red]{error_type}",
        border_style="red",
        expand=False
    )
    console.print(error_panel)
    
    if debug:
        raise e

if __name__ == "__main__":
    app()
