import re
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from .settings import get_settings

PROTECTED_METHODS = {"POST", "PATCH", "PUT", "DELETE"}
READ_LOG_PATHS = ("/api/audit", "/api/codex/sessions")
SECRET_KEYS = re.compile(r"(token|secret|api[_-]?key|password|credential)", re.I)

def redact(value):
    if isinstance(value, dict):
        return {k: ("[REDACTED]" if SECRET_KEYS.search(str(k)) else redact(v)) for k, v in value.items()}
    if isinstance(value, list):
        return [redact(v) for v in value]
    return value

def actor_from_token(token: str | None) -> str:
    return "local-admin" if token else "anonymous"

class AdminTokenMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        settings = get_settings()
        production = settings.environment.lower() == "production"
        if production and not settings.admin_token:
            return JSONResponse({"detail": "AGENTIC_OS_ADMIN_TOKEN is required in production mode"}, status_code=503)
        protected = request.method in PROTECTED_METHODS or any(request.url.path.startswith(p) for p in READ_LOG_PATHS)
        if protected:
            supplied = request.headers.get("x-admin-token") or request.headers.get("authorization", "").replace("Bearer ", "")
            if settings.admin_token and supplied != settings.admin_token:
                return JSONResponse({"detail": "admin token required"}, status_code=401)
        return await call_next(request)
