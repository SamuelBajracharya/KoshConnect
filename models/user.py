from sqlalchemy import Column, String, DateTime, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from database import Base


class User(Base):
    __tablename__ = "users"

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String, unique=True, index=True, nullable=False)
    phonenumber = Column(String, unique=True, index=True, nullable=True)
    phonenumber_encrypted = Column(String, nullable=True)
    phonenumber_hash = Column(String(64), unique=True, index=True, nullable=True)
    email_encrypted = Column(String, nullable=True)
    email_hash = Column(String(64), unique=True, index=True, nullable=True)
    full_name = Column(String, nullable=False)
    role = Column(String(30), nullable=False, server_default=text("'customer'"))
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
