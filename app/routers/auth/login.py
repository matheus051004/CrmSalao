from fastapi import APIRouter
from starlette.requests import Request
from starlette.responses import HTMLResponse
from starlette.templating import Jinja2Templates

router = APIRouter(
    prefix='/login',
    tags=['login']
)

templates = Jinja2Templates(directory="./././templates")

@router.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("login.jinja", {
        'v': "1.0.2",
        'request': request,
    })