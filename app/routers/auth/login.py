import os

from fastapi import APIRouter
from fastapi import Request
from starlette.responses import HTMLResponse, RedirectResponse
import app.glob as g

router = APIRouter(
    prefix='/login',
    tags=['login']
)

@router.get("/", response_class=HTMLResponse)
async def login(request: Request):
    return g.templates.TemplateResponse("login.jinja2", {
        'request': request,
    })

@router.post("/", response_class=HTMLResponse)
async def login_post(request: Request):
    form = await request.form()
    username = form.get("username").strip()
    password = form.get("password").strip()

    print(username, password)

    if username == os.environ.get('CRM_USER') and password == os.environ.get("CRM_PASSWORD"):
        response = RedirectResponse(url="/crm/", status_code=303)
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
        response = g.templates.TemplateResponse("login.jinja2", {
            "request": request,
            "error": "Invalid username or password"
        })
        response.set_cookie("username", "false", max_age=60 * 60 * 24 * 7)
        response.set_cookie("password", "false", max_age=60 * 60 * 24 * 7)
        return response


@router.post('logout', response_class=HTMLResponse, name='logout')
async def logout(request: Request):
    response = RedirectResponse(url="/login/", status_code=303)
    response.delete_cookie("username")
    response.delete_cookie("password")
    return response