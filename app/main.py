import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app import __version__
from app.api import auth, cart, orders, payments, products
from app.config import get_settings
from app.db import engine

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

settings = get_settings()

app = FastAPI(title="Orbitly API", version=__version__, docs_url="/api/docs", openapi_url="/api/openapi.json")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,  # session cookie is sent cross-origin from the storefront
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Idempotency-Key"],
)

# Every router is mounted at /api/<name>; the frontend relies on these exact prefixes.
for name, module in {
    "auth": auth,
    "products": products,
    "cart": cart,
    "orders": orders,
    "payments": payments,
}.items():
    app.include_router(module.router, prefix=f"/api/{name}", tags=[name])


@app.get("/healthz", include_in_schema=False)
def healthz() -> dict[str, str]:
    return {"status": "ok", "version": __version__}


@app.get("/readyz", include_in_schema=False)
def readyz() -> dict[str, str]:
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return {"status": "ready"}
