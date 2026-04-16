from sqlalchemy import (
    Column,
    String,
    DateTime,
    Numeric,
    Integer,
    Boolean,
    ForeignKey,
    text,
    CheckConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from database import Base


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        CheckConstraint(
            "status IN ('BOOKED', 'PENDING', 'REJECTED')",
            name="ck_transactions_status_iso",
        ),
    )

    transaction_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(
        UUID(as_uuid=True),
        ForeignKey("accounts.account_id", ondelete="CASCADE"),
        nullable=False,
    )
    date = Column(DateTime(timezone=True), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), nullable=False)
    type = Column(String(10), nullable=False)
    status = Column(String(15), nullable=False, server_default=text("'BOOKED'"))
    category_purpose_code = Column(
        String(4), nullable=False, server_default=text("'OTHR'")
    )
    mcc = Column(Integer, nullable=False, server_default=text("5999"))
    proprietary_bank_code = Column(
        String(20), nullable=False, server_default=text("'GIBL-FT-01'")
    )
    description = Column(String, nullable=True)
    merchant = Column(String, nullable=True)
    merchant_logo_url = Column(String, nullable=True)
    merchant_verified_status = Column(
        Boolean, nullable=False, server_default=text("false")
    )
    category = Column(String, nullable=True)

    account = relationship("Account", back_populates="transactions")

    def __repr__(self):
        return f"<Transaction {self.amount} {self.currency} - {self.type}>"
