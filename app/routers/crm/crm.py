import math

from fastapi import APIRouter
from fastapi.requests import Request
from fastapi.responses import HTMLResponse

import app.glob as g
from app import Cliente
from app.database import SessionLocal

router = APIRouter(
    prefix="/crm",
    tags=["crm"]
)

@router.get('/', name='crm', response_class=HTMLResponse)
async def crm(request: Request):
    return await dashboard(request)

@router.get('/dashboard', name='dashboard', response_class=HTMLResponse)
async def dashboard(request: Request):
    return g.templates.TemplateResponse('crm-dashboard.jinja2', {
        'request': request,
        'sidebar': 'dashboard',
    })

@router.get('/clientes', name='clientes', response_class=HTMLResponse)
async def clientes(request: Request, page: int = 1, order_by: str = 'id', order: str = 'asc'):
    # Get per_page from the db function result
    items, total, per_page = get_clients(order_by=order_by, order=order, page=page)

    # Calculate total pages
    total_pages = math.ceil(total / per_page)

    return g.templates.TemplateResponse('crm-clientes.jinja2', {
        'request': request,
        'sidebar': 'clientes',
        'items': items,
        'total': total,
        'page': page,
        'total_pages': total_pages, # Pass total_pages to the template
        'order_by': order_by,       # Pass sorting parameters for link generation
        'order': order,
    })


# db functions
def get_clients(order_by: str = 'id', order: str = 'asc', page: int = 1, per_page: int = 10) -> tuple | None:
    db = SessionLocal()
    try:
        query = db.query(Cliente).order_by(getattr(Cliente, order_by).desc() if order == 'desc' else getattr(Cliente, order_by))
        total = query.count()
        items = query.offset((page - 1) * per_page).limit(per_page).all()
        # Return per_page along with items and total
        return items, total, per_page
    finally:
        db.close()