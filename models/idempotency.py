from sqlalchemy import Column, String, DateTime, Integer, text
from sqlalchemy.dialects.postgresql import UUID
import uuid

from database import Base


class IdempotencyRecord(Base):
    __tablename__ = "idempotency_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    idempotency_key = Column(String(128), nullable=False, unique=True, index=True)
    endpoint = Column(String(128), nullable=False)
    request_hash = Column(String(64), nullable=False)
    response_status_code = Column(Integer, nullable=False)
    response_body = Column(String, nullable=False)
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=text("NOW()")
    )

    def __repr__(self):
        return f"<IdempotencyRecord {self.idempotency_key} {self.endpoint}>"
