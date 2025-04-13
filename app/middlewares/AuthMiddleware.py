import os

from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.requests import Request
from fastapi.responses import RedirectResponse


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Rotas que precisam de autenticação
        protected_paths = ['/crm', '/ajax']

        # Verifica se o caminho atual precisa de autenticação
        needs_auth = any(request.url.path.startswith(path) for path in protected_paths)

        # Se o caminho não precisa de autenticação, continua para a próxima etapa
        if not needs_auth:
            response = await call_next(request)
            return response

        # Verifica se o usuário está autenticado através dos cookies
        username = request.cookies.get("username")
        password = request.cookies.get("password")

        # Se não houver cookies ou forem inválidos, redireciona para o login
        if not username or not password or username != os.environ.get('CRM_USER') or password != os.environ.get(
                'CRM_PASSWORD'):
            return RedirectResponse(url="/login/", status_code=303)

        # Se estiver autenticado, continua para a próxima etapa
        response = await call_next(request)
        return response
