import os

from fastapi import APIRouter
from fastapi import Request
import requests

router = APIRouter(
    prefix="/ajax-evo",
    tags=["ajax-evo"]
)


@router.post('/simple-message', name='ajax-evo-simple-message')
async def simple_message(request: Request):
    form = await request.form()
    number = form.get('number')
    message = form.get('message')

    headers = {
        'apikey': os.environ.get('EVOLUTION_API_KEY')
    }
    body = {
        'number': number,
        'text': message
    }
    result = requests.post(
        url=f"{os.environ.get('EVOLUTION_API_URL')}/message/sendText/{os.environ.get('EVOLUTION_INSTANCE')}",
        headers=headers,
        json=body
    )
    json_result = result.json()
    return {
        'status': 200 if json_result['status'] == 'PENDING' else 400,
        'message': json_result['error'] if 'error' in json_result else 'Mensagem enviada com sucesso'
    }