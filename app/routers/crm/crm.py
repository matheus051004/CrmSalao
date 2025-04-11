from fastapi import APIRouter
from starlette.requests import Request
from starlette.responses import HTMLResponse

import app.glob as g

router = APIRouter(
    prefix="/crm",
    tags=["crm"]
)

@router.get('/', name='crm', response_class=HTMLResponse)
async def crm(request: Request):
    return await dashboard(request)

@router.get('/dashboard', name='dashboard', response_class=HTMLResponse)
async def dashboard(request: Request):
    return g.templates.TemplateResponse('crm.jinja2', {
        'request': request,
        'sidebar': 'dashboard',
    })