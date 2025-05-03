from fastapi import APIRouter
from fastapi.requests import Request
from fastapi.responses import HTMLResponse

import app.glob as g
from app.database import SessionLocal
from app.models.app_setting import AppSetting
from app.models.pydantic.crm.Configs import Configs

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


@router.post('/', name='configuracoes_post')
async def configuracoes_post(config: Configs):
    update_setting('salao_name', config.crm_name)
    update_setting('msg_preference', config.msg_preference)
    update_setting('msg_cancel', config.msg_cancel)
    update_setting('follow_up_minutes', str(config.follow_up_minutes))
    update_setting('msg_follow_up', config.msg_follow_up)

    return response(True, "Configurações salvas com sucesso")


def update_setting(key, value):
    db = SessionLocal()
    try:
        setting = db.query(AppSetting).filter(AppSetting.key == key).first()
        if setting:
            setting.value = value
            db.commit()
            return True
        else:
            return False
    finally:
        db.close()


def response(success=True, message="", data=None):
    return {
        "success": success,
        "message": message,
        "data": data
    }
