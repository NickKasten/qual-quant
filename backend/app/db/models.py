from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class Trade(BaseModel):
    """Model for trade records."""
    id: Optional[int] = None
    order_id: str  # Now required, matches DB schema
    symbol: str
    side: str  # 'buy' or 'sell'
    quantity: float
    price: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    strategy: str
    profit_loss: Optional[float] = None
    status: str = 'completed'  # 'pending', 'completed', 'failed'

class Position(BaseModel):
    """Model for current positions."""
    id: Optional[int] = None
    symbol: str
    quantity: float
    average_entry_price: float
    current_price: float
    unrealized_pnl: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class Equity(BaseModel):
    """Model for equity curve data."""
    id: Optional[int] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    equity: float
    cash: float

class Signal(BaseModel):
    """Model for trading signals."""
    id: Optional[int] = None
    symbol: str
    signal_type: str  # 'buy', 'sell', 'hold'
    strength: float  # 0 to 1
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    strategy: str
    price: float 
