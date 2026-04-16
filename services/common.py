from datetime import datetime, timezone
from decimal import Decimal
from typing import List

from sqlalchemy.orm import Session

from encryption_service import decrypt, looks_encrypted, mask_account_number
import models
import schemas


MARKET_DUMMY_STOCKS = [
    {
        "symbol": "NABIL",
        "name": "Nabil Bank Limited",
        "current_price": "645.00",
        "currency": "NPR",
    },
    {
        "symbol": "NICA",
        "name": "NIC Asia Bank Limited",
        "current_price": "522.50",
        "currency": "NPR",
    },
    {
        "symbol": "SCB",
        "name": "Standard Chartered Bank Nepal Limited",
        "current_price": "610.75",
        "currency": "NPR",
    },
    {
        "symbol": "CHCL",
        "name": "Chilime Hydropower Company Limited",
        "current_price": "558.20",
        "currency": "NPR",
    },
    {
        "symbol": "UPPER",
        "name": "Upper Tamakoshi Hydropower Limited",
        "current_price": "332.40",
        "currency": "NPR",
    },
    {
        "symbol": "NTC",
        "name": "Nepal Doorsanchar Company Limited",
        "current_price": "910.00",
        "currency": "NPR",
    },
]


def get_today_utc_end() -> datetime:
    now_utc = datetime.now(timezone.utc)
    return now_utc.replace(hour=23, minute=59, second=59, microsecond=999999)


def get_visible_transactions_query(db: Session):
    return db.query(models.Transaction).filter(
        models.Transaction.date <= get_today_utc_end()
    )


def _to_utc_date(value: datetime):
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    else:
        value = value.astimezone(timezone.utc)
    return value.date()


def _extract_user_phone(user: models.User):
    if user.phonenumber_encrypted:
        try:
            if looks_encrypted(user.phonenumber_encrypted):
                return decrypt(
                    user.phonenumber_encrypted, aad=f"user_phone:{user.user_id}"
                )
        except Exception:
            return None
    return user.phonenumber


def _extract_user_email(user: models.User):
    if user.email_encrypted:
        try:
            if looks_encrypted(user.email_encrypted):
                return decrypt(user.email_encrypted, aad=f"user_email:{user.user_id}")
        except Exception:
            return None
    return None


def build_user_response(user: models.User) -> schemas.User:
    return schemas.User(
        user_id=user.user_id,
        username=user.username,
        phonenumber=_extract_user_phone(user),
        email=_extract_user_email(user),
        full_name=user.full_name,
        created_at=user.created_at,
        accounts=user.accounts,
    )


def get_masked_account_number(account: models.Account) -> str:
    if account.account_number_masked:
        return account.account_number_masked
    if account.account_number_encrypted and looks_encrypted(
        account.account_number_encrypted
    ):
        try:
            plain = decrypt(
                account.account_number_encrypted,
                aad=f"account_number:{account.account_id}",
            )
            return mask_account_number(plain)
        except Exception:
            pass
    return "****"


def build_transaction_response(
    transaction: models.Transaction, latest_visible_date
) -> schemas.Transaction:
    return schemas.Transaction(
        transaction_id=transaction.transaction_id,
        account_id=transaction.account_id,
        date=transaction.date,
        amount=float(transaction.amount),
        currency=transaction.currency,
        type=transaction.type,
        status=transaction.status,
        description=transaction.description,
        merchant=transaction.merchant,
        category=transaction.category,
        is_new=_to_utc_date(transaction.date) == latest_visible_date,
    )


def build_transaction_list_response(transactions: List[models.Transaction]):
    today_date = datetime.now(timezone.utc).date()
    return [build_transaction_response(tx, today_date) for tx in transactions]


def seed_stock_instruments(db: Session):
    users = db.query(models.User).all()
    if not users:
        return

    quantity_templates = ["3.500000", "7.000000", "1.250000", "4.000000"]
    buy_multipliers = ["0.87", "0.93", "1.05", "1.12"]
    nepse_symbols = {stock["symbol"] for stock in MARKET_DUMMY_STOCKS}

    for user_index, user in enumerate(users):
        user_id_str = str(user.user_id)

        db.query(models.StockInstrument).filter(
            models.StockInstrument.user_id == user_id_str,
            ~models.StockInstrument.symbol.in_(nepse_symbols),
        ).delete(synchronize_session=False)

        existing_symbols = {
            row.symbol
            for row in db.query(models.StockInstrument.symbol)
            .filter(models.StockInstrument.user_id == user_id_str)
            .all()
        }

        offset = user_index % len(MARKET_DUMMY_STOCKS)
        assigned = (MARKET_DUMMY_STOCKS[offset:] + MARKET_DUMMY_STOCKS[:offset])[:4]

        for stock_index, stock in enumerate(assigned):
            if stock["symbol"] in existing_symbols:
                continue

            current_price = Decimal(stock["current_price"])
            avg_multiplier = Decimal(buy_multipliers[stock_index])
            quantity = Decimal(quantity_templates[stock_index])

            db.add(
                models.StockInstrument(
                    user_id=user_id_str,
                    symbol=stock["symbol"],
                    name=stock["name"],
                    quantity=quantity,
                    average_buy_price=(current_price * avg_multiplier),
                    current_price=current_price,
                    currency=stock["currency"],
                )
            )

    db.commit()
