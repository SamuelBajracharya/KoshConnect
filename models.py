from sqlalchemy import (
    Column,
    String,
    DateTime,
    Numeric,
    ForeignKey,
    text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from database import Base


class User(Base):
    __tablename__ = "users"

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String, unique=True, index=True, nullable=False)
    phonenumber = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=text("NOW()")
    )

    accounts = relationship(
        "Account",
        back_populates="owner",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self):
        return f"<User {self.username}>"


class Account(Base):
    __tablename__ = "accounts"

    account_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
    )
    bank_name = Column(String, nullable=False)
    account_number_masked = Column(String, nullable=False)
    account_type = Column(String, nullable=False)
    balance = Column(Numeric(12, 2), nullable=False)

    owner = relationship("User", back_populates="accounts")

    transactions = relationship(
        "Transaction",
        back_populates="account",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self):
        return f"<Account {self.bank_name} • {self.account_number_masked}>"


class Transaction(Base):
    __tablename__ = "transactions"

    transaction_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(
        UUID(as_uuid=True),
        ForeignKey("accounts.account_id", ondelete="CASCADE"),
        nullable=False,
    )
    date = Column(DateTime(timezone=True), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), nullable=False)
    type = Column(String(10), nullable=False)  # "DEBIT" or "CREDIT"
    status = Column(String(15), nullable=False)  # "COMPLETED" or "PENDING"
    description = Column(String, nullable=True)

    # Optional fields
    merchant = Column(String, nullable=True)
    category = Column(String, nullable=True)

    account = relationship("Account", back_populates="transactions")

    def __repr__(self):
        return f"<Transaction {self.amount} {self.currency} - {self.type}>"


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
