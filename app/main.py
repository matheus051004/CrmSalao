import os

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates
import app.glob as glob

from app.routers.auth import login
from app.routers.crm import crm
from app.database import create_all_tables

from app.middlewares.AuthMiddleware import AuthMiddleware

app = FastAPI(title="FastAPI Example", description="A simple FastAPI example")
app.mount('/static', StaticFiles(directory="./static"), name="static")
templates = Jinja2Templates(directory="./templates")

templates.env.globals['v'] = os.environ.get('VERSION')
templates.env.globals['crm_name'] = os.environ.get('CRM_NAME')
glob.templates = templates

app.include_router(login.router)
app.include_router(crm.router)

# middlewares
app.add_middleware(AuthMiddleware)

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@app.on_event("startup")
async def startup_event():
    create_all_tables()
    logger.info("Tabelas criadas com sucesso")
