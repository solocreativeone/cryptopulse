from pydantic import BaseModel, Field, ConfigDict, field_serializer
from typing import Optional, List, Dict
from datetime import datetime, timezone
from decimal import Decimal

class Coin(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

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
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    sparkline_7d: Optional[List[Decimal]] = None

    @field_serializer("current_price", "market_cap", "total_volume", "high_24h", "low_24h", "ath", "sparkline_7d")
    def serialize_decimal(self, v: Optional[Decimal | List[Decimal]], _info):
        if v is None:
            return None
        if isinstance(v, list):
            return [str(item) for item in v]
        return str(v)

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
