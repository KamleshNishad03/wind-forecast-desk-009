# Entry point for Vercel's Python runtime. Reuses the same FastAPI app.
# A vercel.json rewrite sends every /api/... request here as /api/index?p=<route>.
# This wrapper puts the real route back before FastAPI sees the request.
from urllib.parse import parse_qs, urlencode

from backend.app.main import app as fastapi_app


async def app(scope, receive, send):
    if scope["type"] == "http":
        qs = parse_qs(scope.get("query_string", b"").decode())
        route = qs.pop("p", [None])[0]
        if route is not None:
            scope = dict(scope)
            scope["path"] = "/api/" + route.strip("/")
            scope["raw_path"] = scope["path"].encode()
            scope["query_string"] = urlencode({k: v[0] for k, v in qs.items()}).encode()
    await fastapi_app(scope, receive, send)