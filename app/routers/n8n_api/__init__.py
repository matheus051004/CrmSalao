from fastapi import APIRouter

n8n_api_router = APIRouter(
    prefix="/n8n-api",
    tags=["n8n-api"],
    include_in_schema=False,
)

from app.routers.n8n_api import agendamentos
from app.routers.n8n_api import leads

n8n_api_router.include_router(agendamentos.agendamentos_router, tags=['agendamentos'])
n8n_api_router.include_router(leads.leads_router, tags=['leads'])