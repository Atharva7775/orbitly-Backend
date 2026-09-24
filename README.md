# orbitly-backend

FastAPI service behind the Orbitly storefront.

## Running locally

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
python -m app.migrate          # applies migrations/*.sql
uvicorn app.main:app --reload
python -m app.workers.runner   # in a second shell
```

Or run the whole stack from `orbitly-cloud`: `docker compose up`.

## API

All routers are mounted at `/api/<name>`:

| Router | Routes |
| --- | --- |
| `auth` | `POST /api/auth/signup`, `POST /api/auth/login`, `POST /api/auth/logout` |
| `products` | `GET /api/products`, `GET /api/products/{product_id}` |
| `cart` | `GET /api/cart`, `POST /api/cart/items`, `PATCH/DELETE /api/cart/items/{product_id}` |
| `orders` | `POST /api/orders`, `GET /api/orders`, `GET /api/orders/{order_id}` |
| `payments` | `POST /api/payments` |
| `users` | `GET /api/users/me`, `PATCH /api/users/me` |

OpenAPI docs: `/api/docs`.

## Events

`app/events/publish.py` writes to Redis Streams:

| Topic | Published by | Consumed by |
| --- | --- | --- |
| `order.placed` | `order_service.place_order` | `app/workers/order_placed.py` (stock reservation, confirmation email) |
| `user.signed_up` | `auth_service.signup` | `app/workers/user_signed_up.py` (welcome email) |

## Database

`DATABASE_URL` points at Postgres. Migrations live in `migrations/` and are applied by
`python -m app.migrate` (an init container in Kubernetes). The DBA-reviewed copy of the schema is
`orbitly-cloud/db/schema.sql`.
