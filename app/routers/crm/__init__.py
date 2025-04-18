from fastapi import APIRouter

crm_router = APIRouter(
    prefix="/crm",
    tags=["crm"],
    include_in_schema=False,
)

from . import crm_agendamentos
from . import crm_clientes
from . import crm_dashboard
from . import crm_servicos
from . import crm_add_servico

crm_router.include_router(crm_dashboard.router)
crm_router.include_router(crm_clientes.router)
crm_router.include_router(crm_agendamentos.router)
crm_router.include_router(crm_servicos.router)
crm_router.include_router(crm_add_servico.router)