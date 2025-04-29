import math

from fastapi import APIRouter
from fastapi.requests import Request
from fastapi.responses import HTMLResponse

import app.glob as g
from app import Servico
from app.database import SessionLocal
from app.models.pydantic.crm import ServicoAdd

router = APIRouter(
    prefix="/servicos",
    include_in_schema=False
)


@router.get('/', name='servicos', response_class=HTMLResponse)
async def servicos(request: Request, page: int = 1, order_by: str = 'id', order: str = 'asc', per_page: int = 10,
                   search: str = None):
    valid_per_page_values = [10, 25, 50, 100]
    if per_page not in valid_per_page_values:
        per_page = 10

    # Get clients with pagination
    items, total, _ = get_items(order_by=order_by, order=order, page=page, per_page=per_page, search=search)

    # Calculate total pages
    total_pages = math.ceil(total / per_page)

    # Calculate start and end item numbers for display
    start_item = ((page - 1) * per_page) + 1 if total > 0 else 0
    end_item = min(page * per_page, total)

    return g.templates.TemplateResponse('crm-servicos.jinja2', {
        'request': request,
        'sidebar': 'servicos',
        'items': items,
        'total': total,
        'page': page,
        'per_page': per_page,
        'total_pages': total_pages,
        'order_by': order_by,
        'order': order,
        'start_item': start_item,
        'end_item': end_item,
        'search': search
    })


# db functions
def get_items(order_by: str = 'id', order: str = 'asc', page: int = 1, per_page: int = 10,
              search: str = None) -> tuple | None:
    db = SessionLocal()
    try:
        query = db.query(Servico)

        # Aplicar filtro de pesquisa se fornecido
        if search:
            search_term = f"%{search}%"
            query = query.filter(Servico.name.ilike(search_term))

        # Aplicar ordenação
        query = query.order_by(getattr(Servico, order_by).desc() if order == 'desc' else getattr(Servico, order_by))

        total = query.count()
        items = query.offset((page - 1) * per_page).limit(per_page).all()
        return items, total, per_page
    finally:
        db.close()


@router.get('/add-servico', name='add-servico', response_class=HTMLResponse)
async def add_servico(request: Request):
    return g.templates.TemplateResponse('crm-add-servico.jinja2', {
        'request': request,
        'sidebar': 'servicos',
    })


@router.post('/add-servico', name='add-servico-post')
async def add_servico_post(servico_add: ServicoAdd):
    db = SessionLocal()
    sexos = ['unissex', 'feminino', 'masculino']

    if servico_add.sexo not in sexos:
        return response(False, 'Sexo inválido. Aceito: unissex, feminino ou masculino.')

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

    return response(True, message)


def response(success=True, message="", data=None):
    return {
        "success": success,
        "message": message,
        "data": data
    }
