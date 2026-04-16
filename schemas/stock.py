from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime


class StockInstrumentBase(BaseModel):
    user_id: str
    symbol: str
    name: Optional[str] = None
    quantity: float = 0
    average_buy_price: Optional[float] = None
    current_price: Optional[float] = None
    currency: Optional[str] = None


class StockInstrumentCreate(StockInstrumentBase):
    pass


class StockInstrument(StockInstrumentBase):
    id: UUID
    updated_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True
