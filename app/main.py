import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app import __version__
from app.config import get_settings
from app.db import engine
from app.routers import auth, cart, orders, payments, products, users

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

settings = get_settings()

app = FastAPI(title="Orbitly API", version=__version__, docs_url="/api/docs", openapi_url="/api/openapi.json")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type", "Idempotency-Key"],
)

# Every router is mounted at /api/<name>; the frontend relies on these exact prefixes.
for name, module in {
    "auth": auth,
    "products": products,
    "cart": cart,
    "orders": orders,
    "payments": payments,
    "users": users,
}.items():
    app.include_router(module.router, prefix=f"/api/{name}", tags=[name])


@app.middleware("http")
async def region_header(request, call_next):
    # Lets support and the CDN verify which regional stack served a request.
    response = await call_next(request)
    response.headers["X-Orbitly-Region"] = settings.data_region
    return response


@app.get("/healthz", include_in_schema=False)
def healthz() -> dict[str, str]:
    return {"status": "ok", "version": __version__, "region": settings.data_region}


@app.get("/readyz", include_in_schema=False)
def readyz() -> dict[str, str]:
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return {"status": "ready"}
