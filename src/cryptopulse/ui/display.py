from typing import List, Optional
from decimal import Decimal
from rich.table import Table
from rich.text import Text
from rich.console import Group, Console
from rich.panel import Panel
from rich.align import Align
import time
from pathlib import Path

# Initializing a global console with recording enabled for auto-doc screenshots.
# standarizing width to 100 ensures consistent SVG documentation layouts.
console = Console(record=True, width=100)

def export_ui_snap(filename: str):
    """
    Captures the current console state and saves it as an SVG screenshot.
    
    This function is used for automated documentation generation. It ensures
    the screenshot directory exists, adds a small stability delay for the 
    terminal buffer, and saves the SVG with a standardized title.
    
    Args:
        filename: The base name for the generated .svg file (e.g., 'list').
    """
    # Small sleep to ensure terminal buffer is stable before capturing
    time.sleep(0.2)
    
    screenshot_dir = Path("docs/screenshots")
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    
    path = screenshot_dir / f"{filename}.svg"
    console.save_svg(str(path), title="CryptoPulse Terminal")
    console.print(f"\n[italic cyan]📸 Screenshot saved to {screenshot_dir}/[/italic cyan]")

def get_high_density_sparkline(prices: Optional[List[Decimal]], width: int = 15) -> Text:
    """
    Generates a Unicode sparkline (e.g., ▂▃▅▇) to represent price trends.
    
    Args:
        prices: A list of Decimal price points.
        width: The horizontal resolution of the sparkline.
        
    Returns:
        A rich.text.Text object containing the colored sparkline.
    """
    if not prices or len(prices) < 2:
        return Text("─" * width, style="dim")
    
    # Sample the price list to match the requested width
    step = len(prices) / width
    sampled = [prices[int(i * step)] for i in range(width)]
    
    min_p, max_p = min(sampled), max(sampled)
    
    # Sentiment coloring: Green if the trend ended higher than it started, else Red.
    color = "green" if sampled[-1] >= sampled[0] else "red"
    
    if max_p == min_p:
        return Text("─" * width, style=color)
        
    # Unicode block characters sorted by density
    chars = " ▂▃▄▅▆▇█"
    line = ""
    for p in sampled:
        # Calculate height index based on relative position between min and max
        idx = int((p - min_p) / (max_p - min_p) * (len(chars) - 1))
        line += chars[idx]
    
    return Text(line, style=color)

def format_currency(amount: Decimal, currency: str, precision: Optional[int] = None) -> str:
    """
    Standardizes currency formatting with support for fiat and crypto symbols.
    
    Includes human-readable suffixing for large values (B for Billions, T for Trillions)
    and handles variable precision based on the asset type.
    
    Args:
        amount: The decimal value to format.
        currency: The currency code (USD, BTC, etc.)
        precision: Optional override for decimal places.
        
    Returns:
        A formatted string (e.g., "$1.23T" or "₿0.0045").
    """
    symbols = {
        "USD": "$", "EUR": "€", "GBP": "£", "JPY": "¥", 
        "NGN": "₦", "BTC": "₿", "ETH": "Ξ", "SOL": "S "
    }
    currency_upper = currency.upper()
    symbol = symbols.get(currency_upper, currency_upper + " ")
    
    # Human-readable formatting for large values (B/T)
    suffix = ""
    val = amount
    if amount >= 1_000_000_000_000:
        val = amount / 1_000_000_000_000
        suffix = "T"
    elif amount >= 1_000_000_000:
        val = amount / 1_000_000_000
        suffix = "B"

    # Determine optimal precision if not provided
    if precision is None:
        if suffix:
            precision = 2
        elif currency_upper in ["BTC", "ETH", "SOL"] or (0 < amount < 1):
            precision = 4
        else:
            precision = 2
            
    return f"{symbol}{val:,.{precision}f}{suffix}"

def create_crypto_table(title: str, currency_label: str) -> Table:
    """
    Configures a Rich table for displaying cryptocurrency data.
    
    The table layout is responsive: it hides 'Rank' and 'Name' columns
    if the terminal width is too narrow to ensure core data remains readable.
    """
    width = console.width
    show_extra = width > 70

    table = Table(title=title, expand=True, min_width=80)
    if show_extra:
        table.add_column("Rank", justify="right", style="dim", no_wrap=True)
    
    table.add_column("Symbol", style="cyan")
    
    if show_extra:
        table.add_column("Name", style="magenta", overflow="ellipsis")
        
    table.add_column(f"Price ({currency_label})", justify="right", style="green", no_wrap=True)
    table.add_column("Price (USD)", justify="right", style="dim green", no_wrap=True)
    table.add_column(f"Market Cap ({currency_label})", justify="right", style="blue", no_wrap=True)
    table.add_column("Trend (7d)", justify="center", min_width=12)
    return table

def render_error_panel(msg: str, error_type: str, debug: bool = False) -> Panel:
    """
    Returns a consistent error panel for display in the terminal.
    """
    return Panel(
        Group(
            f"[bold red]Error:[/bold red] {msg}",
            "" if debug else "[dim]Use --debug to see the full technical traceback.[/dim]"
        ),
        title=f"[bold red]{error_type}",
        border_style="red",
        expand=False
    )
