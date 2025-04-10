from fastapi import APIRouter
from starlette.requests import Request
from starlette.responses import HTMLResponse

import app.globals as g

router = APIRouter(
    prefix="/crm",
    tags=["crm"]
)


@router.get('/', response_class=HTMLResponse)
async def crm(request: Request):
    return g.templates.TemplateResponse('crm.jinja2', {
        'request': request,
    })
