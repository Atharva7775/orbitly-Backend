from app.main import app

EXPECTED = {
    ("POST", "/api/auth/signup"),
    ("POST", "/api/auth/login"),
    ("POST", "/api/auth/logout"),
    ("GET", "/api/products"),
    ("GET", "/api/products/{product_id}"),
    ("GET", "/api/cart"),
    ("POST", "/api/cart/items"),
    ("PATCH", "/api/cart/items/{product_id}"),
    ("DELETE", "/api/cart/items/{product_id}"),
    ("POST", "/api/orders"),
    ("GET", "/api/orders"),
    ("GET", "/api/orders/{order_id}"),
    ("POST", "/api/orders/{order_id}/cancel"),
    ("POST", "/api/payments"),
    ("GET", "/api/users/me"),
    ("PATCH", "/api/users/me"),
}


def test_public_routes_are_stable():
    """orbitly-frontend hard-codes these paths; changing one is a breaking change."""
    routes = {(m, r.path) for r in app.routes for m in getattr(r, "methods", set()) if r.path.startswith("/api/")}
    routes = {(m, p) for m, p in routes if not p.startswith("/api/docs") and p != "/api/openapi.json"}
    assert EXPECTED <= routes
