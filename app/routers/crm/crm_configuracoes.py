from fastapi import APIRouter
from fastapi.requests import Request
from fastapi.responses import HTMLResponse

import app.glob as g

router = APIRouter(
    prefix="/configuracoes",
    include_in_schema=False
)


@router.get('/', name='configuracoes', response_class=HTMLResponse)
async def dashboard(request: Request):
    return g.templates.TemplateResponse('crm-config.jinja2', {
        'request': request,
        'sidebar': 'configuracoes',
    })
