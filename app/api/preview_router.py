"""Preview Router - Theme Selector and Preview Routes
Handles routing for different UI themes (minimal, dark, soft)
"""

import logging

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/preview", tags=["preview"])
templates = Jinja2Templates(directory="templates")


# Theme selector
@router.get("/themes", response_class=HTMLResponse)
async def theme_selector(request: Request):
    try:
        return templates.TemplateResponse("theme_selector.html", {"request": request})
    except Exception as e:
        logger.error(f"Error rendering theme selector: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to load theme selector")


# Landing pages
@router.get("/landing/minimal", response_class=HTMLResponse)
async def landing_minimal(request: Request):
    try:
        return templates.TemplateResponse("landing_minimal.html", {"request": request})
    except Exception as e:
        logger.error(f"Error rendering minimal landing: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to load page")


@router.get("/landing/dark", response_class=HTMLResponse)
async def landing_dark(request: Request):
    try:
        return templates.TemplateResponse("landing_dark.html", {"request": request})
    except Exception as e:
        logger.error(f"Error rendering dark landing: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to load page")


@router.get("/landing/soft", response_class=HTMLResponse)
async def landing_soft(request: Request):
    try:
        return templates.TemplateResponse("landing_soft.html", {"request": request})
    except Exception as e:
        logger.error(f"Error rendering soft landing: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to load page")


# Dashboard previews
@router.get("/dashboard/minimal", response_class=HTMLResponse)
async def dashboard_minimal(request: Request):
    try:
        return templates.TemplateResponse("preview_option_a.html", {"request": request})
    except Exception as e:
        logger.error(f"Error rendering minimal dashboard: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to load page")


@router.get("/dashboard/dark", response_class=HTMLResponse)
async def dashboard_dark(request: Request):
    try:
        return templates.TemplateResponse("preview_option_b.html", {"request": request})
    except Exception as e:
        logger.error(f"Error rendering dark dashboard: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to load page")


@router.get("/dashboard/soft", response_class=HTMLResponse)
async def dashboard_soft(request: Request):
    try:
        return templates.TemplateResponse("preview_option_c.html", {"request": request})
    except Exception as e:
        logger.error(f"Error rendering soft dashboard: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to load page")
