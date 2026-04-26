import asyncio
import typer
import random
import webbrowser
import time
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict
from decimal import Decimal
from rich.console import Group
from rich.table import Table
from rich.panel import Panel
from rich.live import Live
from rich.align import Align
from rich.text import Text
from rich.spinner import Spinner
from pydantic import ValidationError
from httpx import HTTPStatusError, RequestError

from .services.fetcher import CryptoFetcher
from .utils.converter import CurrencyConverter
from .utils.finance import calculate_ath_percentage
from .ui.display import (
    console,
    export_ui_snap,
    get_high_density_sparkline, 
    format_currency, 
    create_crypto_table, 
    render_error_panel
)
from .models import Coin

app = typer.Typer(
    help="CryptoPulse CLI - Production-grade high-precision crypto tracker.",
    no_args_is_help=True
)

@app.callback()
def main(
    snap: bool = typer.Option(False, "--snap", "-s", help="Capture a terminal screenshot (SVG).", is_eager=True)
):
    """
    CryptoPulse CLI Callback to handle global options.
    """
    pass

ZEN_QUOTES = [
    "Focus on the signal, ignore the noise.",
    "The market is a device for transferring money from the impatient to the patient.",
    "Buy when there's blood in the streets, even if the blood is your own.",
    "In the short run, the market is a voting machine; in the long run, it is a weighing machine.", # Benjamin Graham
    "The most important quality for an investor is temperament, not intellect.",
]

async def run_list(currency: str, export: bool = False, snap: bool = False):
    fetcher = CryptoFetcher()
    converter = CurrencyConverter()
    
    with console.status(f"[bold green]Fetching data and {currency} rates...", spinner="dots"):
        coins, _ = await asyncio.gather(
            fetcher.get_latest_prices(),
            converter.get_rates()
        )

    if not coins:
        raise RuntimeError("Could not fetch coin data.")

    if fetcher.is_stale or converter.is_stale:
        console.print(Panel("[bold red]Network unreachable. Using local cache...[/bold red]", border_style="red"))

    crypto_prices = {coin.symbol: coin.current_price for coin in coins}
    crypto_prices.update({coin.id: coin.current_price for coin in coins})
    converter.set_crypto_rates(crypto_prices)

    currency_label = currency.upper()
    table = create_crypto_table(f"CryptoPulse - Top 10 Coins (vs {currency_label})", currency_label)

    for i, coin in enumerate(coins[:10], 1):
        converted_price = converter.convert(coin.current_price, currency)
        converted_cap = converter.convert(coin.market_cap, currency) if coin.market_cap else None
        
        spark = get_high_density_sparkline(coin.sparkline_7d)
        
        table.add_row(
            str(i),
            coin.symbol.upper(),
            coin.name,
            format_currency(converted_price, currency),
            format_currency(coin.current_price, "USD"),
            format_currency(converted_cap, currency) if converted_cap else "N/A",
            spark
        )

    console.print(table)
    if snap:
        export_ui_snap("list")

    if export:
        export_file = f"cryptopulse_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            with open(export_file, "w") as f:
                json.dump([coin.model_dump() for coin in coins], f, indent=4, default=str)
            console.print(f"\n[bold green]✓ Data successfully exported to {export_file}[/bold green]")
        except Exception as e:
            console.print(f"\n[bold red]✗ Export failed: {e}[/bold red]")

async def run_stat(coin_id: str, snap: bool = False):
    fetcher = CryptoFetcher()
    coin = await fetcher.get_coin_details(coin_id)
    
    if not coin:
        console.print(f"[red]Coin '{coin_id}' not found.[/red]")
        return

    ath_percent = calculate_ath_percentage(coin.current_price, coin.ath) if coin.ath else Decimal("0")
    
    grid = Table.grid(expand=True)
    grid.add_column(justify="left", style="bold cyan")
    grid.add_column(justify="right")
    
    grid.add_row("Symbol", coin.symbol.upper())
    grid.add_row("Price (USD)", format_currency(coin.current_price, "USD"))
    grid.add_row("Market Cap (USD)", format_currency(coin.market_cap, "USD") if coin.market_cap else "N/A")
    grid.add_row("24h High", format_currency(coin.high_24h, "USD") if coin.high_24h else "N/A")
    grid.add_row("24h Low", format_currency(coin.low_24h, "USD") if coin.low_24h else "N/A")
    grid.add_row("ATH", format_currency(coin.ath, "USD") if coin.ath else "N/A")
    grid.add_row("From ATH (%)", f"{ath_percent:+.2f}%")
    
    spark = get_high_density_sparkline(coin.sparkline_7d, width=40)
    
    panel_content = Group(
        Align.center(Text(coin.name, style="bold magenta fs+2")),
        "",
        grid,
        "",
        Align.center(Text("7-Day Trend")),
        Align.center(spark)
    )
    
    console.print(Panel(panel_content, title="Coin Statistics", border_style="blue", expand=False, width=50))
    if snap:
        export_ui_snap("stat")

async def run_global(snap: bool = False):
    fetcher = CryptoFetcher()
    global_data = await fetcher.get_global_data()
    
    if not global_data:
        console.print("[red]Could not fetch global market data.[/red]")
        return

    table = Table(title="Global Crypto Market Data", border_style="magenta")
    table.add_column("Metric", style="bold cyan")
    table.add_column("Value", justify="right")

    table.add_row("Active Cryptocurrencies", str(global_data.active_cryptocurrencies))
    table.add_row("Total Market Cap (USD)", format_currency(global_data.total_market_cap.get("usd", 0), "USD"))
    table.add_row("Total Volume (USD)", format_currency(global_data.total_volume.get("usd", 0), "USD"))
    table.add_row("Market Cap Change (24h)", f"{global_data.market_cap_change_percentage_24h_usd:+.2f}%")
    
    btc_dom = global_data.market_cap_percentage.get("btc", 0)
    eth_dom = global_data.market_cap_percentage.get("eth", 0)
    table.add_row("BTC Dominance", f"{btc_dom:.1f}%")
    table.add_row("ETH Dominance", f"{eth_dom:.1f}%")

    console.print(table)
    if snap:
        export_ui_snap("global")

async def run_watch(coin_ids: List[str], interval: int, snap: bool = False):
    fetcher = CryptoFetcher()
    snapped = False
    
    with Live(auto_refresh=True, console=console) as live:
        while True:
            coins = await fetcher.get_latest_prices()
            
            if fetcher.is_stale:
                sync_signal = Align.right(Text.from_markup("[blink red]![/blink red] [stale]"))
            else:
                sync_signal = Align.right(Text.from_markup("[blink green]●[/blink green]"))
            
            filtered_coins = [c for c in coins if c.id in coin_ids or c.symbol.lower() in coin_ids]
            
            now = datetime.now().strftime("%H:%M:%S")
            
            if not filtered_coins:
                live.update(Panel("[red]No watched coins found in top 100.[/red]", title="Watcher"))
            else:
                table = Table(title="CryptoPulse Live Watcher")
                table.add_column("Symbol", style="cyan")
                table.add_column("Price (USD)", justify="right", style="green")
                
                for coin in filtered_coins:
                    table.add_row(coin.symbol.upper(), format_currency(coin.current_price, "USD"))
                
                footer = Group(
                    Align.right(Text(f"Last Updated: {now}", style="dim")),
                    Align.center(Spinner("dots", text="Monitoring..."))
                )
                
                live.update(Group(sync_signal, table, footer))
                
                if snap and not snapped:
                    # Small sleep to let the live display render before snapping
                    await asyncio.sleep(0.5)
                    export_ui_snap("watch")
                    snapped = True
            
            await asyncio.sleep(interval)

async def run_zen(coin_id: str, snap: bool = False):
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
    if snap:
        export_ui_snap("zen")

@app.command()
def list(
    currency: str = typer.Option("USD", "--currency", "-c", help="Currency to display prices in."),
    export: bool = typer.Option(False, "--export", "-e", help="Export current data to a .json file."),
    snap: bool = typer.Option(False, "--snap", "-s", help="Capture a terminal screenshot (SVG)."),
    debug: bool = typer.Option(False, "--debug", help="Show full traceback on error.")
):
    """List the latest prices for top cryptocurrencies."""
    try:
        asyncio.run(run_list(currency, export, snap))
    except Exception as e:
        handle_error(e, debug)

@app.command()
def stat(
    coin: str = typer.Argument(..., help="The coin ID to get details for (e.g. bitcoin, ethereum)."),
    snap: bool = typer.Option(False, "--snap", "-s", help="Capture a terminal screenshot (SVG)."),
    debug: bool = typer.Option(False, "--debug", help="Show full traceback on error.")
):
    """Get detailed statistics for a specific coin."""
    try:
        asyncio.run(run_stat(coin, snap))
    except Exception as e:
        handle_error(e, debug)

@app.command(name="global")
def global_cmd(
    snap: bool = typer.Option(False, "--snap", "-s", help="Capture a terminal screenshot (SVG)."),
    debug: bool = typer.Option(False, "--debug", help="Show full traceback on error.")
):
    """Show global cryptocurrency market data."""
    try:
        asyncio.run(run_global(snap))
    except Exception as e:
        handle_error(e, debug)

@app.command()
def watch(
    coins: List[str] = typer.Argument(..., help="List of coin IDs or symbols to watch."),
    interval: int = typer.Option(30, "--interval", "-i", help="Refresh interval in seconds."),
    snap: bool = typer.Option(False, "--snap", "-s", help="Capture a terminal screenshot (SVG)."),
    debug: bool = typer.Option(False, "--debug", help="Show full traceback on error.")
):
    """Watch specific coins in real-time."""
    try:
        asyncio.run(run_watch([c.lower() for c in coins], interval, snap))
    except KeyboardInterrupt:
        pass
    except Exception as e:
        handle_error(e, debug)

@app.command()
def zen(
    coin: str = typer.Argument("bitcoin", help="The coin to focus on."),
    snap: bool = typer.Option(False, "--snap", "-s", help="Capture a terminal screenshot (SVG)."),
    debug: bool = typer.Option(False, "--debug", help="Show full traceback on error.")
):
    """A minimalist, centered view for a single coin with a zen quote."""
    try:
        asyncio.run(run_zen(coin, snap))
    except Exception as e:
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
    msg = str(e)
    error_type = type(e).__name__
    
    if isinstance(e, ValidationError):
        msg = "Data validation failed. The API might have changed its format."
    elif isinstance(e, (HTTPStatusError, RequestError)):
        if hasattr(e, "response") and e.response is not None and e.response.status_code == 429:
            msg = "Rate limit exceeded. Please wait a few minutes before trying again."
        else:
            msg = "Communication error with the external API. Please check your internet or the API status."
        
    console.print(render_error_panel(msg, error_type, debug))
    
    if debug:
        raise e

def cpl():
    app(["list"] + sys.argv[1:])

def cpw():
    app(["watch"] + sys.argv[1:])

def cpz():
    app(["zen"] + sys.argv[1:])

def cpg():
    app(["global"] + sys.argv[1:])

if __name__ == "__main__":
    app()
