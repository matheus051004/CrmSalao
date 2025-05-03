from fastapi import APIRouter
from fastapi.requests import Request
from fastapi.responses import HTMLResponse

import app.glob as g
from app.database import SessionLocal
from app.models.app_setting import AppSetting
from app.models.pydantic.crm import Configs

router = APIRouter(
    prefix="/configuracoes",
    include_in_schema=False
)


@router.get('/', name='configuracoes', response_class=HTMLResponse)
async def configuracoes(request: Request):
    return g.templates.TemplateResponse('crm-config.jinja2', {
        'request': request,
        'sidebar': 'configuracoes',
    })

@router.post('/', name='configuracoes_postt')
async def configuracoes_post(config: Configs):
    s1 = AppSetting(key='salao_name', value=config.crm_name)
    s2 = AppSetting(key='msg_preference', value=config.msg_preference)
    s3 = AppSetting(key='msg_cancel', value=config.msg_cancel)
    s4 = AppSetting(key='follow_up_minutes', value=config.follow_up_minutes)
    s5 = AppSetting(key='msg_follow_up', value=config.msg_follow_up)
    db = SessionLocal()
    try:
        db.add(s1)
        db.add(s2)
        db.add(s3)
        db.add(s4)
        db.add(s5)
        db.commit()
    finally:
        db.close()

    return response(True, "Configurações salvas com sucesso")

def response(success=True, message="", data=None):
    return {
        "success": success,
        "message": message,
        "data": data
    }