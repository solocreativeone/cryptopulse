from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
from decimal import Decimal

class Coin(BaseModel):
    id: str
    symbol: str
    name: str
    current_price: Decimal = Field(..., alias="current_price")
    market_cap: Optional[Decimal] = None
    total_volume: Optional[Decimal] = None
    high_24h: Optional[Decimal] = None
    low_24h: Optional[Decimal] = None
    ath: Optional[Decimal] = None
    ath_date: Optional[datetime] = None
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    sparkline_7d: Optional[List[Decimal]] = None

    class Config:
        populate_by_name = True
        json_encoders = {
            Decimal: lambda v: str(v)
        }

class GlobalData(BaseModel):
    total_market_cap: Dict[str, Decimal]
    total_volume: Dict[str, Decimal]
    market_cap_percentage: Dict[str, Decimal]
    market_cap_change_percentage_24h_usd: Decimal
    active_cryptocurrencies: int
    upcoming_icos: int
    ongoing_icos: int
    ended_icos: int
    markets: int
