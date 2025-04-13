import os

from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.requests import Request
from fastapi.responses import JSONResponse


class ApiMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Rotas que precisam de autenticação
        protected_paths = ['/n8n-api']

        needs_auth = any(request.url.path.startswith(path) for path in protected_paths)

        if not needs_auth:
            response = await call_next(request)
            return response

        if 'apiKey' not in request.headers:
            from fastapi.responses import JSONResponse
            return JSONResponse(
                content={
                    "status": "error",
                    "message": "Unauthorized",
                    "code": 401
                },
                status_code=401
            )

        api_key = request.headers.get('apiKey')
        if not api_key or api_key != os.environ.get('API_KEY'):
            from fastapi.responses import JSONResponse
            return JSONResponse(
                content={
                    "status": "error",
                    "message": "Unauthorized",
                    "code": 401
                },
                status_code=401
            )

        response = await call_next(request)
        return response
