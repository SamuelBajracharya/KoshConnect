from sqlalchemy import Column, String, DateTime, Numeric, text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
import uuid

from database import Base


class StockInstrument(Base):
    __tablename__ = "stock_instruments"
    __table_args__ = (
        UniqueConstraint("user_id", "id", name="uq_stock_instruments_user_id_id"),
        UniqueConstraint(
            "user_id", "symbol", name="uq_stock_instruments_user_id_symbol"
        ),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(64), nullable=False, index=True)
    symbol = Column(String(20), nullable=False)
    name = Column(String(255), nullable=True)
    quantity = Column(Numeric(18, 6), nullable=False, server_default=text("0"))
    average_buy_price = Column(Numeric(18, 6), nullable=True)
    current_price = Column(Numeric(18, 6), nullable=True)
    currency = Column(String(10), nullable=True)
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
        onupdate=text("NOW()"),
    )
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=text("NOW()")
    )

    def __repr__(self):
        return f"<StockInstrument {self.symbol} ({self.quantity})>"
