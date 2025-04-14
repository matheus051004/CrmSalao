import math

from fastapi import APIRouter
from fastapi.requests import Request
from fastapi.responses import HTMLResponse

import app.glob as g
from app import Agendamento, Cliente
from app.database import SessionLocal

router = APIRouter(
    prefix="/agendamentos",
    include_in_schema=False
)


@router.get('/', name='agendamentos', response_class=HTMLResponse)
async def agendamentos(
        request: Request,
        page: int = 1,
        order_by: str = 'id',
        order: str = 'asc',
        per_page: int = 10,
        cliente_id: int = 0,
        status: str = 'todos'
):
    valid_per_page_values = [10, 25, 50, 100]
    if per_page not in valid_per_page_values:
        per_page = 10

    # Get clients with pagination and filters
    items, total, _ = get_items(
        order_by=order_by,
        order=order,
        page=page,
        per_page=per_page,
        cliente_id=cliente_id,
        status=status
    )

    # Obter lista de clientes para o menu dropdown
    db = SessionLocal()
    try:
        clientes = db.query(Cliente).order_by(Cliente.name).all()
    finally:
        db.close()

    # Calculate total pages
    total_pages = math.ceil(total / per_page)

    # Calculate start and end item numbers for display
    start_item = ((page - 1) * per_page) + 1 if total > 0 else 0
    end_item = min(page * per_page, total)

    return g.templates.TemplateResponse('crm-agendamentos.jinja2', {
        'request': request,
        'sidebar': 'agendamentos',
        'items': items,
        'total': total,
        'page': page,
        'per_page': per_page,
        'total_pages': total_pages,
        'order_by': order_by,
        'order': order,
        'start_item': start_item,
        'end_item': end_item,
        'cliente_id': cliente_id,
        'status': status,
        'clientes': clientes
    })


# db functions
def get_items(order_by: str = 'id', order: str = 'asc', page: int = 1, per_page: int = 10,
              cliente_id: int = None, status: str = None) -> tuple | None:
    db = SessionLocal()
    try:
        query = db.query(Agendamento).order_by(
            getattr(Agendamento, order_by).desc() if order == 'desc' else getattr(Agendamento, order_by))

        # Aplicar filtros se fornecidos
        if cliente_id is not None and cliente_id > 0:
            query = query.filter(Agendamento.cliente_id == cliente_id)

        if status and status != 'todos':
            query = query.filter(Agendamento.status == status)

        total = query.count()
        items = query.offset((page - 1) * per_page).limit(per_page).all()
        return items, total, per_page
    finally:
        db.close()
