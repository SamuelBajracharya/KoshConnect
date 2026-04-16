from fastapi import APIRouter

from endpoints.auth import router as auth_router
from endpoints.users import router as users_router
from endpoints.accounts import router as accounts_router
from endpoints.transactions import router as transactions_router
from endpoints.stocks import router as stocks_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(accounts_router)
api_router.include_router(transactions_router)
api_router.include_router(stocks_router)

__all__ = ["api_router"]
