import math

from fastapi import APIRouter
from fastapi.requests import Request
from fastapi.responses import HTMLResponse

import app.glob as g
from app import Servico
from app.database import SessionLocal

router = APIRouter(
    prefix="/servicos",
    include_in_schema=False
)


@router.get('/add-servico', name='add-servico', response_class=HTMLResponse)
async def add_servico(request: Request):
    return g.templates.TemplateResponse('crm-add-servico.jinja2', {
        'request': request,
        'sidebar': 'servicos',
    })