from fastapi import APIRouter
from fastapi.requests import Request
from fastapi.responses import HTMLResponse

import app.glob as g

router = APIRouter(
    prefix="/dashboard",
    include_in_schema=False
)


@router.get('/', name='dashboard', response_class=HTMLResponse)
async def dashboard(request: Request):
    return g.templates.TemplateResponse('crm-dashboard.jinja2', {
        'request': request,
        'sidebar': 'dashboard',
    })

@router.post('/', name='dashboard', response_class=HTMLResponse)
async def dashboard_post(request: Request):
    return g.templates.TemplateResponse('crm-dashboard.jinja2', {
        'request': request,
        'sidebar': 'dashboard',
    })
