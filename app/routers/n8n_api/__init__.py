from fastapi import APIRouter

n8n_api_router = APIRouter(
    prefix="/n8n-api",
    include_in_schema=True,
)

from app.routers.n8n_api import agendamentos
from app.routers.n8n_api import leads
from app.routers.n8n_api import config
from app.routers.n8n_api import follow_up

n8n_api_router.include_router(agendamentos.agendamentos_router, tags=['agendamentos'])
n8n_api_router.include_router(leads.leads_router, tags=['leads'])
n8n_api_router.include_router(config.config_router, tags=['configs'])
n8n_api_router.include_router(follow_up.follow_up_router, tags=['follow-up'])