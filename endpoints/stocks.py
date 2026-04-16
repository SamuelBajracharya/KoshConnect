from datetime import timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Security
from sqlalchemy.orm import Session

from database import get_db
import models
import schemas
from security import get_current_user, require_signed_request

router = APIRouter(tags=["Stocks"])


@router.get("/users/{user_id}/stocks", response_model=list[schemas.StockInstrument])
def get_user_stocks(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Security(get_current_user, scopes=["stock:read"]),
):
    if current_user.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to access stocks")

    return (
        db.query(models.StockInstrument)
        .filter(models.StockInstrument.user_id == str(user_id))
        .order_by(models.StockInstrument.symbol.asc())
        .all()
    )


@router.post("/stocks/", response_model=schemas.StockInstrument)
def add_stock_instrument(
    stock: schemas.StockInstrumentCreate,
    request: Request,
    _: None = Depends(require_signed_request),
    db: Session = Depends(get_db),
    current_user: models.User = Security(
        get_current_user, scopes=["transaction:write"]
    ),
):
    if stock.user_id != str(current_user.user_id):
        raise HTTPException(
            status_code=403, detail="Not authorized to add stock for this user"
        )

    exists = (
        db.query(models.StockInstrument)
        .filter(
            models.StockInstrument.user_id == stock.user_id,
            models.StockInstrument.symbol == stock.symbol,
        )
        .first()
    )
    if exists:
        raise HTTPException(
            status_code=400, detail="Stock symbol already exists for this user"
        )

    db_stock = models.StockInstrument(**stock.dict())
    db.add(db_stock)
    db.commit()
    db.refresh(db_stock)
    return db_stock


@router.get("/stock-instruments")
def get_stock_instruments(
    db: Session = Depends(get_db),
    current_user: models.User = Security(get_current_user, scopes=["stock:read"]),
):
    db_stocks = (
        db.query(models.StockInstrument)
        .filter(models.StockInstrument.user_id == str(current_user.user_id))
        .order_by(models.StockInstrument.symbol.asc())
        .all()
    )

    stock_instruments = []
    for stock in db_stocks:
        updated_at = stock.updated_at
        if updated_at is not None:
            if updated_at.tzinfo is None:
                updated_at = updated_at.replace(tzinfo=timezone.utc)
            updated_at_str = (
                updated_at.astimezone(timezone.utc)
                .replace(microsecond=0)
                .isoformat()
                .replace("+00:00", "Z")
            )
        else:
            updated_at_str = None

        stock_instruments.append(
            {
                "instrument_id": str(stock.id),
                "symbol": stock.symbol,
                "name": stock.name,
                "quantity": (
                    float(stock.quantity) if stock.quantity is not None else None
                ),
                "average_buy_price": (
                    float(stock.average_buy_price)
                    if stock.average_buy_price is not None
                    else None
                ),
                "current_price": (
                    float(stock.current_price)
                    if stock.current_price is not None
                    else None
                ),
                "currency": stock.currency,
                "updated_at": updated_at_str,
            }
        )

    return {"stock_instruments": stock_instruments}
