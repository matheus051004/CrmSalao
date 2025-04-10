import os

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates
import app.glob as glob

from app.routers.auth import login

app = FastAPI(title="FastAPI Example", description="A simple FastAPI example")
app.mount('/static', StaticFiles(directory="./static"), name="static")
templates = Jinja2Templates(directory="./templates")

templates.env.globals['v'] = os.environ.get('VERSION')
glob.templates = templates

app.include_router(login.router)