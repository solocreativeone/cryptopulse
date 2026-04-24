from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal

class Coin(BaseModel):
    id: str
    symbol: str
    name: str
    current_price: Decimal = Field(..., alias="current_price")
    market_cap: Optional[Decimal] = None
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    sparkline_7d: Optional[List[Decimal]] = None

    class Config:
        populate_by_name = True
        json_encoders = {
            Decimal: lambda v: str(v)
        }
