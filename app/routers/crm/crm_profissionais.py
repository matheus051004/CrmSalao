import math

from fastapi import APIRouter
from fastapi.requests import Request
from fastapi.responses import HTMLResponse

import app.glob as g
from app import Profissional
from app.database import SessionLocal

router = APIRouter(
    prefix="/profissionais",
    include_in_schema=False
)


@router.get('/', name='profissionais', response_class=HTMLResponse)
async def profissionais(request: Request, page: int = 1, order_by: str = 'id', order: str = 'asc', per_page: int = 10):
    valid_per_page_values = [10, 25, 50, 100]
    if per_page not in valid_per_page_values:
        per_page = 10

    # Get clients with pagination
    items, total, _ = get_items(order_by=order_by, order=order, page=page, per_page=per_page)

    # Calculate total pages
    total_pages = math.ceil(total / per_page)

    # Calculate start and end item numbers for display
    start_item = ((page - 1) * per_page) + 1 if total > 0 else 0
    end_item = min(page * per_page, total)

    return g.templates.TemplateResponse('crm-profissionais.jinja2', {
        'request': request,
        'sidebar': 'profissionais',
        'items': items,
        'total': total,
        'page': page,
        'per_page': per_page,
        'total_pages': total_pages,
        'order_by': order_by,
        'order': order,
        'start_item': start_item,
        'end_item': end_item
    })


# db functions
def get_items(order_by: str = 'id', order: str = 'asc', page: int = 1, per_page: int = 10) -> tuple | None:
    db = SessionLocal()
    try:
        query = db.query(Profissional)

        # Aplicar ordenação
        query = query.order_by(getattr(Profissional, order_by).desc() if order == 'desc' else getattr(Profissional, order_by))

        total = query.count()
        items = query.offset((page - 1) * per_page).limit(per_page).all()
        return items, total, per_page
    finally:
        db.close()


def response(success=True, message="", data=None):
    return {
        "success": success,
        "message": message,
        "data": data
    }
