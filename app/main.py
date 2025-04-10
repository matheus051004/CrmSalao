from fastapi import FastAPI
from starlette.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates
from fastapi import Request

app = FastAPI(title="FastAPI Example", description="A simple FastAPI example", version="1.0.0")

templates = Jinja2Templates(directory="./templates")
app.mount('/static', StaticFiles(directory="./static"), name="static")

@app.get("/login", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("login.jinja", {"request": request})