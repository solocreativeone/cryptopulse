from typing import List, Optional
from decimal import Decimal
from rich.table import Table
from rich.text import Text
from rich.console import Group
from rich.panel import Panel
from rich.align import Align

def get_high_density_sparkline(prices: Optional[List[Decimal]], width: int = 15) -> Text:
    if not prices or len(prices) < 2:
        return Text("─" * width, style="dim")
    
    # Sample to width
    step = len(prices) / width
    sampled = [prices[int(i * step)] for i in range(width)]
    
    min_p, max_p = min(sampled), max(sampled)
    
    # Sentiment coloring: Green if last >= first, Red otherwise
    color = "green" if sampled[-1] >= sampled[0] else "red"
    
    if max_p == min_p:
        return Text("─" * width, style=color)
        
    chars = " ▂▃▄▅▆▇█"
    line = ""
    for p in sampled:
        idx = int((p - min_p) / (max_p - min_p) * (len(chars) - 1))
        line += chars[idx]
    
    return Text(line, style=color)

def format_currency(amount: Decimal, currency: str, precision: Optional[int] = None) -> str:
    symbols = {
        "USD": "$", "EUR": "€", "GBP": "£", "JPY": "¥", 
        "NGN": "₦", "BTC": "₿", "ETH": "Ξ", "SOL": "S "
    }
    currency_upper = currency.upper()
    symbol = symbols.get(currency_upper, currency_upper + " ")
    
    if precision is None:
        # Use higher precision for crypto-to-crypto ratios or small prices
        if currency_upper in ["BTC", "ETH", "SOL"] or (amount < 1 and amount > 0):
            precision = 4
        else:
            precision = 2
            
    return f"{symbol}{amount:,.{precision}f}"

def create_crypto_table(title: str, currency_label: str) -> Table:
    table = Table(title=title)
    table.add_column("Rank", justify="right", style="dim")
    table.add_column("Symbol", style="cyan", no_wrap=True)
    table.add_column("Name", style="magenta")
    table.add_column(f"Price ({currency_label})", justify="right", style="green")
    table.add_column("Price (USD)", justify="right", style="dim green")
    table.add_column(f"Market Cap ({currency_label})", justify="right", style="blue")
    table.add_column("Trend (7d)", justify="center")
    return table

def render_error_panel(msg: str, error_type: str, debug: bool = False) -> Panel:
    return Panel(
        Group(
            f"[bold red]Error:[/bold red] {msg}",
            "" if debug else "[dim]Use --debug to see the full technical traceback.[/dim]"
        ),
        title=f"[bold red]{error_type}",
        border_style="red",
        expand=False
    )
