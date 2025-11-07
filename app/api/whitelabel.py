"""White-label platform API endpoints."""
from fastapi import APIRouter, HTTPException, Request, Depends
from sqlalchemy.orm import Session
from app.core.dependencies import get_db, get_current_admin_user
from app.services.whitelabel_service import whitelabel_service
from app.models.user import User
from pydantic import BaseModel

router = APIRouter(prefix="/whitelabel", tags=["whitelabel"])

class WhiteLabelCreate(BaseModel):
    domain: str
    company_name: str
    logo_url: str = None
    primary_color: str = "#667eea"
    secondary_color: str = "#10b981"
    custom_css: str = None
    api_subdomain: str = None

@router.get("/config")
async def get_whitelabel_config(request: Request):
    """Get white-label configuration for current domain."""
    domain = request.headers.get("host", "").split(":")[0]
    
    config = await whitelabel_service.get_config_by_domain(domain)
    if not config:
        return {"is_whitelabel": False}
    
    return {"is_whitelabel": True, **config}

@router.post("/create")
async def create_whitelabel_config(
    config_data: WhiteLabelCreate,
    admin_user: User = Depends(get_current_admin_user)
):
    """Create new white-label configuration (admin only)."""
    try:
        result = await whitelabel_service.create_config(
            config_data.domain, 
            config_data.dict()
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))