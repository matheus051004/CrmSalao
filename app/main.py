import os

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import app.glob as glob
from app.jinja import prepare_jinja

from app.routers.auth import login
from app.routers.crm import crm_dashboard
from app.routers.crm import crm_clientes
from app.routers.crm import crm_agendamentos

from app.routers.ajax import ajax_dashboard
from app.routers.ajax import ajax_evolution
from app.routers.ajax import ajax_clientes

from app.database import create_all_tables

from app.middlewares.AuthMiddleware import AuthMiddleware

app = FastAPI(title="FastAPI Example", description="A simple FastAPI example")
app.mount('/static', StaticFiles(directory="./static"), name="static")
templates = Jinja2Templates(directory="./templates")

glob.templates = templates
prepare_jinja(glob.templates)

app.include_router(login.router)
app.include_router(crm_dashboard.router)
app.include_router(crm_clientes.router)
app.include_router(crm_agendamentos.router)
app.include_router(ajax_dashboard.router)
app.include_router(ajax_evolution.router)
app.include_router(ajax_clientes.router)

# middlewares
app.add_middleware(AuthMiddleware)

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@app.on_event("startup")
async def startup_event():
    create_all_tables()
    logger.info("Tabelas criadas com sucesso")
