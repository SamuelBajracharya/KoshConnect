import json
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Security
from sqlalchemy.orm import Session

from database import get_db
import models
import schemas
from security import get_current_user, hash_idempotency_payload, require_signed_request
from services.common import (
    build_transaction_response,
    get_today_utc_end,
    get_visible_transactions_query,
)

router = APIRouter(tags=["Transactions"])


@router.get("/transactions/{transaction_id}", response_model=schemas.Transaction)
def get_transaction(
    transaction_id: UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Security(get_current_user, scopes=["transaction:read"]),
):
    db_transaction = (
        get_visible_transactions_query(db)
        .filter(models.Transaction.transaction_id == transaction_id)
        .first()
    )
    if db_transaction is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    if db_transaction.account.user_id != current_user.user_id:
        raise HTTPException(
            status_code=403, detail="Not authorized to access this transaction"
        )
    return build_transaction_response(db_transaction, datetime.now(timezone.utc).date())


@router.post("/transactions/", response_model=schemas.Transaction)
def add_transaction(
    transaction: schemas.TransactionCreate,
    request: Request,
    _: None = Depends(require_signed_request),
    db: Session = Depends(get_db),
    current_user: models.User = Security(
        get_current_user, scopes=["transaction:write"]
    ),
):
    idempotency_key = request.headers.get("X-Idempotency-Key")
    if not idempotency_key:
        raise HTTPException(status_code=400, detail="Missing X-Idempotency-Key header")

    request_hash = hash_idempotency_payload(transaction.dict())
    existing_record = (
        db.query(models.IdempotencyRecord)
        .filter(
            models.IdempotencyRecord.idempotency_key == idempotency_key,
            models.IdempotencyRecord.endpoint == "/transactions/",
        )
        .first()
    )
    if existing_record:
        if existing_record.request_hash != request_hash:
            raise HTTPException(
                status_code=409,
                detail="Idempotency key already used with a different payload",
            )
        return schemas.Transaction(**json.loads(existing_record.response_body))

    db_account = (
        db.query(models.Account)
        .filter(models.Account.account_id == transaction.account_id)
        .first()
    )
    if db_account is None:
        raise HTTPException(status_code=404, detail="Account not found")
    if db_account.user_id != current_user.user_id:
        raise HTTPException(
            status_code=403, detail="Not authorized to add transaction to this account"
        )

    if transaction.date > get_today_utc_end():
        raise HTTPException(
            status_code=400,
            detail="Transactions after today's date are not available via this API",
        )

    db_transaction = models.Transaction(**transaction.dict())
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    response = build_transaction_response(
        db_transaction, datetime.now(timezone.utc).date()
    )

    response_payload = response.dict()
    response_payload["date"] = response_payload["date"].isoformat()
    db.add(
        models.IdempotencyRecord(
            idempotency_key=idempotency_key,
            endpoint="/transactions/",
            request_hash=request_hash,
            response_status_code=200,
            response_body=json.dumps(response_payload, separators=(",", ":")),
        )
    )
    db.commit()

    return response
