import os

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import RedirectResponse


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Rotas que não precisam de autenticação
        public_paths = ['/login', '/static']

        # Verifica se o caminho atual é público
        if any(request.url.path.startswith(path) for path in public_paths):
            response = await call_next(request)
            return response

        # Verifica se o usuário está autenticado através dos cookies
        username = request.cookies.get("username")
        password = request.cookies.get("password")

        # Se não houver cookies ou forem inválidos, redireciona para o login
        if not username or not password or username != os.environ.get('CRM_USER') or password != os.environ.get(
                'CRM_PASSWORD'):
            return RedirectResponse(url="/login")

        # Se estiver autenticado, continua para a próxima etapa
        response = await call_next(request)
        return response
