from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Security
from sqlalchemy.orm import Session

from database import get_db
import models
import schemas
from security import get_current_user
from services.common import (
    build_transaction_list_response,
    get_masked_account_number,
    get_visible_transactions_query,
)

router = APIRouter(tags=["Accounts"])


@router.get("/accounts/{account_id}", response_model=schemas.AccountWithTransactions)
def get_account(
    account_id: UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Security(get_current_user, scopes=["account:read"]),
):
    db_account = (
        db.query(models.Account).filter(models.Account.account_id == account_id).first()
    )
    if db_account is None:
        raise HTTPException(status_code=404, detail="Account not found")
    if db_account.user_id != current_user.user_id:
        raise HTTPException(
            status_code=403, detail="Not authorized to access this account"
        )

    visible_transactions = (
        get_visible_transactions_query(db)
        .filter(models.Transaction.account_id == db_account.account_id)
        .order_by(models.Transaction.date.desc())
        .all()
    )

    return schemas.AccountWithTransactions(
        account_id=db_account.account_id,
        user_id=db_account.user_id,
        bank_name=db_account.bank_name,
        account_number_masked=get_masked_account_number(db_account),
        account_type=db_account.account_type,
        balance=float(db_account.balance),
        transactions=build_transaction_list_response(visible_transactions),
    )


@router.get(
    "/accounts/{account_id}/transactions", response_model=list[schemas.Transaction]
)
def get_account_transactions(
    account_id: UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Security(get_current_user, scopes=["transaction:read"]),
):
    db_account = (
        db.query(models.Account).filter(models.Account.account_id == account_id).first()
    )
    if db_account is None:
        raise HTTPException(status_code=404, detail="Account not found")
    if db_account.user_id != current_user.user_id:
        raise HTTPException(
            status_code=403, detail="Not authorized to access these transactions"
        )
    transactions = (
        get_visible_transactions_query(db)
        .filter(models.Transaction.account_id == db_account.account_id)
        .order_by(models.Transaction.date.desc())
        .all()
    )
    return build_transaction_list_response(transactions)
