from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

import models
from config import APP_ENV, ENFORCE_HTTPS
from database import SessionLocal, engine, run_bootstrap_migrations
from endpoints import api_router
from services import seed_stock_instruments


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Creating database tables (if not exist)...")
    models.Base.metadata.create_all(bind=engine)
    run_bootstrap_migrations()
    print("Tables ready!")

    db = SessionLocal()
    try:
        seed_stock_instruments(db)
        print("Stock instruments seeded (if missing).")
    finally:
        db.close()

    yield
    print("Shutting down app...")


app = FastAPI(
    title="Mondex Banking Sandbox API",
    version="2.0",
    description="Modular banking sandbox API with separated endpoints, schemas, models, and services.",
    lifespan=lifespan,
)

origins = [
    "http://localhost:3000",
    "https://koshconnect.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def enforce_https_middleware(request: Request, call_next):
    if ENFORCE_HTTPS and APP_ENV != "development":
        forwarded_proto = request.headers.get("x-forwarded-proto", request.url.scheme)
        if forwarded_proto != "https":
            return JSONResponse(
                status_code=400, content={"detail": "HTTPS is required"}
            )
    return await call_next(request)


app.include_router(api_router)
