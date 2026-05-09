"""Whitelabel API endpoints for custom domain and branding management"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.models.whitelabel_models import WhitelabelBranding, WhitelabelDomain
from app.services.whitelabel_service import whitelabel_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/whitelabel", tags=["whitelabel"])


# Schemas
class DomainSetupRequest(BaseModel):
    """Domain setup request"""

    domain: str = Field(..., description="Domain name (e.g., verify.example.com)")
    verification_method: str = Field(
        default="txt_record", description="txt_record, meta_tag, or file_upload"
    )


class DomainResponse(BaseModel):
    """Domain response"""

    id: int
    domain: str
    verified: bool
    verification_token: str
    verification_method: str
    ssl_status: str
    active: bool
    created_at: str


class BrandingUpdateRequest(BaseModel):
    """Branding update request"""

    logo_url: Optional[str] = None
    favicon_url: Optional[str] = None
    primary_color: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$")
    secondary_color: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$")
    accent_color: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$")
    font_family: Optional[str] = None
    company_name: Optional[str] = None
    support_email: Optional[str] = None
    support_url: Optional[str] = None


class BrandingResponse(BaseModel):
    """Branding response"""

    id: int
    user_id: int
    logo_url: Optional[str]
    favicon_url: Optional[str]
    primary_color: str
    secondary_color: str
    accent_color: str
    font_family: str
    company_name: Optional[str]
    support_email: Optional[str]
    support_url: Optional[str]


class WhitelabelConfigResponse(BaseModel):
    """Complete whitelabel configuration"""

    enabled: bool
    domains: List[DomainResponse]
    branding: Optional[BrandingResponse]


class VerificationInstructionsResponse(BaseModel):
    """Domain verification instructions"""

    method: str
    instructions: str
    verification_token: str


# Endpoints
@router.post("/setup", response_model=DomainResponse)
async def setup_whitelabel_domain(
    request: DomainSetupRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Setup a new whitelabel domain

    Requires Pro tier or higher.
    """
    # Check tier
    if current_user.subscription_tier not in ["pro", "custom", "enterprise"]:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Whitelabel requires Pro tier or higher. Please upgrade your plan.",
        )

    # Create domain
    domain, error = whitelabel_service.create_domain(
        db=db,
        user_id=current_user.id,
        domain=request.domain,
        verification_method=request.verification_method,
    )

    if error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)

    return DomainResponse(
        id=domain.id,
        domain=domain.domain,
        verified=domain.verified,
        verification_token=domain.verification_token,
        verification_method=domain.verification_method,
        ssl_status=domain.ssl_status,
        active=domain.active,
        created_at=domain.created_at.isoformat(),
    )


@router.get("/config", response_model=WhitelabelConfigResponse)
async def get_whitelabel_config(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Get current whitelabel configuration"""
    # Get domains
    domains = (
        db.query(WhitelabelDomain)
        .filter(WhitelabelDomain.user_id == current_user.id)
        .all()
    )

    domain_list = [
        DomainResponse(
            id=d.id,
            domain=d.domain,
            verified=d.verified,
            verification_token=d.verification_token,
            verification_method=d.verification_method,
            ssl_status=d.ssl_status,
            active=d.active,
            created_at=d.created_at.isoformat(),
        )
        for d in domains
    ]

    # Get branding
    branding = (
        db.query(WhitelabelBranding)
        .filter(WhitelabelBranding.user_id == current_user.id)
        .first()
    )

    branding_response = None
    if branding:
        branding_response = BrandingResponse(
            id=branding.id,
            user_id=branding.user_id,
            logo_url=branding.logo_url,
            favicon_url=branding.favicon_url,
            primary_color=branding.primary_color,
            secondary_color=branding.secondary_color,
            accent_color=branding.accent_color,
            font_family=branding.font_family,
            company_name=branding.company_name,
            support_email=branding.support_email,
            support_url=branding.support_url,
        )

    return WhitelabelConfigResponse(
        enabled=len(domains) > 0, domains=domain_list, branding=branding_response
    )


@router.put("/branding", response_model=BrandingResponse)
async def update_branding(
    request: BrandingUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update whitelabel branding"""
    # Check tier
    if current_user.subscription_tier not in ["pro", "custom", "enterprise"]:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Whitelabel requires Pro tier or higher",
        )

    # Update branding
    branding = whitelabel_service.update_branding(
        db=db, user_id=current_user.id, **request.dict(exclude_unset=True)
    )

    return BrandingResponse(
        id=branding.id,
        user_id=branding.user_id,
        logo_url=branding.logo_url,
        favicon_url=branding.favicon_url,
        primary_color=branding.primary_color,
        secondary_color=branding.secondary_color,
        accent_color=branding.accent_color,
        font_family=branding.font_family,
        company_name=branding.company_name,
        support_email=branding.support_email,
        support_url=branding.support_url,
    )


@router.post("/verify-domain/{domain_id}")
async def verify_domain(
    domain_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Trigger domain verification

    Checks DNS records, meta tags, or file upload based on verification method.
    """
    verified, error = await whitelabel_service.verify_domain(
        db=db, domain_id=domain_id, user_id=current_user.id
    )

    if error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)

    if not verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Domain verification failed"
        )

    return {"message": "Domain verified successfully", "verified": True}


@router.get("/domains", response_model=List[DomainResponse])
async def list_domains(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """List all whitelabel domains for current user"""
    domains = (
        db.query(WhitelabelDomain)
        .filter(WhitelabelDomain.user_id == current_user.id)
        .all()
    )

    return [
        DomainResponse(
            id=d.id,
            domain=d.domain,
            verified=d.verified,
            verification_token=d.verification_token,
            verification_method=d.verification_method,
            ssl_status=d.ssl_status,
            active=d.active,
            created_at=d.created_at.isoformat(),
        )
        for d in domains
    ]


@router.delete("/domain/{domain_id}")
async def remove_domain(
    domain_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Remove a whitelabel domain"""
    domain = (
        db.query(WhitelabelDomain)
        .filter(
            WhitelabelDomain.id == domain_id,
            WhitelabelDomain.user_id == current_user.id,
        )
        .first()
    )

    if not domain:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Domain not found"
        )

    db.delete(domain)
    db.commit()

    return {"message": "Domain removed successfully"}


@router.get(
    "/verification-instructions/{domain_id}",
    response_model=VerificationInstructionsResponse,
)
async def get_verification_instructions(
    domain_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get domain verification instructions"""
    domain = (
        db.query(WhitelabelDomain)
        .filter(
            WhitelabelDomain.id == domain_id,
            WhitelabelDomain.user_id == current_user.id,
        )
        .first()
    )

    if not domain:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Domain not found"
        )

    instructions = ""
    if domain.verification_method == "txt_record":
        instructions = f"""
Add the following TXT record to your DNS:

Host: _namaskah-verify.{domain.domain}
Type: TXT
Value: {domain.verification_token}

Wait 5-10 minutes for DNS propagation, then click "Verify Domain".
        """.strip()
    elif domain.verification_method == "meta_tag":
        instructions = f"""
Add the following meta tag to your website's <head> section:

<meta name="namaskah-verification" content="{domain.verification_token}">

Then click "Verify Domain".
        """.strip()
    elif domain.verification_method == "file_upload":
        instructions = f"""
Create a file at:
https://{domain.domain}/.well-known/namaskah-verification.txt

With the following content:
{domain.verification_token}

Then click "Verify Domain".
        """.strip()

    return VerificationInstructionsResponse(
        method=domain.verification_method,
        instructions=instructions,
        verification_token=domain.verification_token,
    )
