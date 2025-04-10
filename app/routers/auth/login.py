import os

from fastapi import APIRouter
from fastapi import Request
from starlette.responses import HTMLResponse, RedirectResponse
from starlette.templating import Jinja2Templates

router = APIRouter(
    prefix='/login',
    tags=['login']
)

templates = Jinja2Templates(directory="./././templates")

@router.get("/", response_class=HTMLResponse)
async def login(request: Request):
    return templates.TemplateResponse("login.jinja", {
        'v': os.environ.get('VERSION'),
        'request': request,
    })

@router.post("/", response_class=HTMLResponse)
async def login_post(request: Request):
    form = await request.form()
    username = form.get("username")
    password = form.get("password")

    if username == os.environ["CRM_USER"] and password == os.environ["CRM_PASSWORD"]:
        response = RedirectResponse(url="/crm", status_code=303)
        response.set_cookie(
            key="username",
            value=username,
            max_age=60 * 60 * 24 * 7,
            httponly=False
        )
        response.set_cookie(
            key="password",
            value=password,
            max_age=60 * 60 * 24 * 7,
            httponly=False
        )
        return response
    else:
        response = templates.TemplateResponse("login.jinja", {
            "v": os.environ.get("VERSION"),
            "request": request,
            "error": "Invalid username or password"
        })
        response.set_cookie("username", "false", max_age=60 * 60 * 24 * 7)
        response.set_cookie("password", "false", max_age=60 * 60 * 24 * 7)
        return response