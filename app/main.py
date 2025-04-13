from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import app.glob as glob
from app.database import create_all_tables
from app.jinja import prepare_jinja
from app.middlewares.AuthMiddleware import AuthMiddleware
from app.routers.auth import login
from app.routers.crm import crm_router
from app.routers.ajax import ajax_router

from app.routers.n8n_api import n8n_api_router

app = FastAPI(title="CRM n8n", description="CRM n8n", version="0.1.0")
app.mount('/static', StaticFiles(directory="./static"), name="static")
templates = Jinja2Templates(directory="./templates")

glob.templates = templates
prepare_jinja(glob.templates)

app.include_router(login.router)
app.include_router(crm_router)
app.include_router(n8n_api_router)
app.include_router(ajax_router)

# middlewares
app.add_middleware(AuthMiddleware)

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@app.on_event("startup")
async def startup_event():
    create_all_tables()
    logger.info("Tabelas criadas com sucesso")
