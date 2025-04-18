from fastapi import APIRouter
from fastapi.requests import Request
from fastapi.responses import HTMLResponse

import app.glob as g
from app import Servico
from app.database import SessionLocal
from app.models.pydantic.crm.ServicoAdd import ServicoAdd

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


@router.post('/add-servico', name='add-servico-post', response_class=HTMLResponse)
async def add_servico_post(request: Request, servico_add: ServicoAdd):
    db = SessionLocal()
    message = ''
    try:
        servico = Servico(
            name=servico_add.servico,
            description=servico_add.descricao,
            price=servico_add.preco,
            minutes=servico_add.minutos,
            sexo=servico_add.sexo
        )

        db.add(servico)
        db.commit()
        message = 'Serviço registrado com sucesso!'
    finally:
        db.close()

    return g.templates.TemplateResponse('crm-add-servico.jinja2', {
        'request': request,
        'sidebar': 'servicos',
        'message': message,
    })
