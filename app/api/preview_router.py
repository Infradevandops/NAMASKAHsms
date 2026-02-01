"""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

Preview Router - Theme Selector and Preview Routes
Handles routing for different UI themes (minimal, dark, soft)
"""


router = APIRouter(prefix="/preview", tags=["preview"])
templates = Jinja2Templates(directory="templates")


# Theme selector
@router.get("/themes", response_class=HTMLResponse)
async def theme_selector(request: Request):
    return templates.TemplateResponse("theme_selector.html", {"request": request})


# Landing pages
@router.get("/landing/minimal", response_class=HTMLResponse)
async def landing_minimal(request: Request):
    return templates.TemplateResponse("landing_minimal.html", {"request": request})


@router.get("/landing/dark", response_class=HTMLResponse)
async def landing_dark(request: Request):
    return templates.TemplateResponse("landing_dark.html", {"request": request})


@router.get("/landing/soft", response_class=HTMLResponse)
async def landing_soft(request: Request):
    return templates.TemplateResponse("landing_soft.html", {"request": request})


# Dashboard previews
@router.get("/dashboard/minimal", response_class=HTMLResponse)
async def dashboard_minimal(request: Request):
    return templates.TemplateResponse("preview_option_a.html", {"request": request})


@router.get("/dashboard/dark", response_class=HTMLResponse)
async def dashboard_dark(request: Request):
    return templates.TemplateResponse("preview_option_b.html", {"request": request})


@router.get("/dashboard/soft", response_class=HTMLResponse)
async def dashboard_soft(request: Request):
    return templates.TemplateResponse("preview_option_c.html", {"request": request})
