import os

from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.requests import Request


class ApiMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Rotas que precisam de autenticação
        protected_paths = ['/n8n-api']

        needs_auth = any(request.url.path.startswith(path) for path in protected_paths)

        if not needs_auth:
            response = await call_next(request)
            return response

        api_key = request.headers.get('apiKey')

        if not api_key or api_key != os.environ.get('API_KEY'):
            return {
                "status": "error",
                "message": "Unauthorized",
                "code": 401
            }

        response = await call_next(request)
        return response
