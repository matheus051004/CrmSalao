from fastapi import APIRouter

ajax_router = APIRouter(
    prefix="/ajax",
    tags=["ajax"],
    include_in_schema=False
)

from . import ajax_clientes
from . import ajax_dashboard
from . import ajax_evolution
from . import ajax_agendamentos
from . import ajax_servicos

ajax_router.include_router(ajax_clientes.router)
ajax_router.include_router(ajax_dashboard.router)
ajax_router.include_router(ajax_evolution.router)
ajax_router.include_router(ajax_agendamentos.router)
ajax_router.include_router(ajax_servicos.router)