from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.routers.auth import login

app = FastAPI(title="FastAPI Example", description="A simple FastAPI example")
app.mount('/static', StaticFiles(directory="./static"), name="static")
app.include_router(login.router)