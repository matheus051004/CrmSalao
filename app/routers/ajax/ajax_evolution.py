import os

from fastapi import APIRouter
from fastapi import Request

from app.Evolution import Evolution

router = APIRouter(
    prefix="/ajax-evo",
    include_in_schema=False
)


@router.post('/simple-message', name='ajax-evo-simple-message')
async def simple_message(request: Request):
    form = await request.form()
    number = form.get('number')
    message = form.get('message')

    ev = Evolution(os.environ.get('WAHA_API_URL'), os.environ.get('WAHA_API_KEY'),
                   os.environ.get('WAHA_INSTANCE'))
    ev.simple_text(number, message)
    return {
        'status': 200,
        'message': 'Mensagem enviada com sucesso'
    }