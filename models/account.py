from sqlalchemy import Column, String, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from database import Base


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
    account_number_encrypted = Column(String, nullable=True)
    account_number_hash = Column(String(64), unique=True, index=True, nullable=True)
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
