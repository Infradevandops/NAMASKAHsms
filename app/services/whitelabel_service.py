"""Whitelabel service for custom domain and branding management"""

import logging
import re
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import dns.resolver
import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.user import User
from app.models.whitelabel_models import (
    WhitelabelBranding,
    WhitelabelDomain,
    WhitelabelEmailTemplate,
)

logger = logging.getLogger(__name__)


class WhitelabelService:
    """Service for managing whitelabel domains and branding"""

    def __init__(self):
        self.dns_resolver = dns.resolver.Resolver()
        self.dns_resolver.timeout = 5
        self.dns_resolver.lifetime = 5

    def validate_domain(self, domain: str) -> tuple[bool, Optional[str]]:
        """
        Validate domain format

        Args:
            domain: Domain to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Remove protocol if present
        domain = domain.replace("http://", "").replace("https://", "").split("/")[0]

        # Basic format validation
        domain_pattern = (
            r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$"
        )
        if not re.match(domain_pattern, domain):
            return False, "Invalid domain format"

        # Check if domain is too short
        if len(domain) < 4:
            return False, "Domain too short"

        # Check if domain is localhost or IP
        if domain in ["localhost", "127.0.0.1"] or domain.startswith("192.168."):
            return False, "Cannot use localhost or private IP"

        # Check if domain is already the platform domain
        platform_domain = (
            settings.base_url.replace("http://", "")
            .replace("https://", "")
            .split("/")[0]
        )
        if domain == platform_domain:
            return False, "Cannot use platform domain"

        return True, None

    def generate_verification_token(self) -> str:
        """Generate a secure verification token"""
        return secrets.token_urlsafe(32)

    async def verify_domain_txt_record(
        self, domain: str, verification_token: str
    ) -> tuple[bool, Optional[str]]:
        """
        Verify domain ownership via TXT record

        Args:
            domain: Domain to verify
            verification_token: Expected token value

        Returns:
            Tuple of (is_verified, error_message)
        """
        try:
            # Query TXT records for _namaskah-verify subdomain
            txt_domain = f"_namaskah-verify.{domain}"
            answers = self.dns_resolver.resolve(txt_domain, "TXT")

            # Check if any TXT record matches our token
            for rdata in answers:
                txt_value = rdata.to_text().strip('"')
                if txt_value == verification_token:
                    logger.info(f"Domain {domain} verified via TXT record")
                    return True, None

            return False, "Verification token not found in TXT records"

        except dns.resolver.NXDOMAIN:
            return False, f"TXT record not found for {txt_domain}"
        except dns.resolver.NoAnswer:
            return False, f"No TXT records found for {txt_domain}"
        except dns.resolver.Timeout:
            return False, "DNS query timed out"
        except Exception as e:
            logger.error(f"DNS verification error: {e}")
            return False, f"DNS verification failed: {str(e)}"

    async def verify_domain_meta_tag(
        self, domain: str, verification_token: str
    ) -> tuple[bool, Optional[str]]:
        """
        Verify domain ownership via meta tag

        Args:
            domain: Domain to verify
            verification_token: Expected token value

        Returns:
            Tuple of (is_verified, error_message)
        """
        try:
            url = f"https://{domain}"
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                response = await client.get(url)
                response.raise_for_status()

                # Check for meta tag in HTML
                html = response.text
                meta_pattern = f"<meta\\s+name=[\"']namaskah-verification[\"']\\s+content=[\"']({verification_token})[\"']"
                if re.search(meta_pattern, html, re.IGNORECASE):
                    logger.info(f"Domain {domain} verified via meta tag")
                    return True, None

                return False, "Verification meta tag not found"

        except httpx.HTTPStatusError as e:
            return False, f"HTTP error: {e.response.status_code}"
        except httpx.TimeoutException:
            return False, "Request timed out"
        except Exception as e:
            logger.error(f"Meta tag verification error: {e}")
            return False, f"Verification failed: {str(e)}"

    async def verify_domain_file(
        self, domain: str, verification_token: str
    ) -> tuple[bool, Optional[str]]:
        """
        Verify domain ownership via file upload

        Args:
            domain: Domain to verify
            verification_token: Expected token value

        Returns:
            Tuple of (is_verified, error_message)
        """
        try:
            url = f"https://{domain}/.well-known/namaskah-verification.txt"
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                response = await client.get(url)
                response.raise_for_status()

                # Check if file content matches token
                content = response.text.strip()
                if content == verification_token:
                    logger.info(f"Domain {domain} verified via file")
                    return True, None

                return False, "Verification file content does not match"

        except httpx.HTTPStatusError as e:
            return False, f"HTTP error: {e.response.status_code}"
        except httpx.TimeoutException:
            return False, "Request timed out"
        except Exception as e:
            logger.error(f"File verification error: {e}")
            return False, f"Verification failed: {str(e)}"

    async def verify_domain(
        self, db: Session, domain_id: int, user_id: int
    ) -> tuple[bool, Optional[str]]:
        """
        Verify domain ownership using configured method

        Args:
            db: Database session
            domain_id: Domain ID
            user_id: User ID

        Returns:
            Tuple of (is_verified, error_message)
        """
        domain = (
            db.query(WhitelabelDomain)
            .filter(
                WhitelabelDomain.id == domain_id, WhitelabelDomain.user_id == user_id
            )
            .first()
        )

        if not domain:
            return False, "Domain not found"

        if domain.verified:
            return True, None

        # Verify based on method
        if domain.verification_method == "txt_record":
            verified, error = await self.verify_domain_txt_record(
                domain.domain, domain.verification_token
            )
        elif domain.verification_method == "meta_tag":
            verified, error = await self.verify_domain_meta_tag(
                domain.domain, domain.verification_token
            )
        elif domain.verification_method == "file_upload":
            verified, error = await self.verify_domain_file(
                domain.domain, domain.verification_token
            )
        else:
            return False, "Invalid verification method"

        if verified:
            domain.verified = True
            domain.updated_at = datetime.now(timezone.utc)
            db.commit()
            # Sanitize domain for logging
            safe_domain = domain.domain.replace("\n", "").replace("\r", "")
            logger.info(f"Domain verified successfully", extra={"domain": safe_domain})

        return verified, error

    def create_domain(
        self,
        db: Session,
        user_id: int,
        domain: str,
        verification_method: str = "txt_record",
    ) -> tuple[Optional[WhitelabelDomain], Optional[str]]:
        """
        Create a new whitelabel domain

        Args:
            db: Database session
            user_id: User ID
            domain: Domain name
            verification_method: Verification method (txt_record, meta_tag, file_upload)

        Returns:
            Tuple of (domain_object, error_message)
        """
        # Validate domain
        is_valid, error = self.validate_domain(domain)
        if not is_valid:
            return None, error

        # Check if domain already exists
        existing = (
            db.query(WhitelabelDomain).filter(WhitelabelDomain.domain == domain).first()
        )

        if existing:
            return None, "Domain already registered"

        # Check user tier (Pro+ only)
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None, "User not found"

        if user.subscription_tier not in ["pro", "custom", "enterprise"]:
            return None, "Whitelabel requires Pro tier or higher"

        # Generate verification token
        verification_token = self.generate_verification_token()

        # Create domain
        domain_obj = WhitelabelDomain(
            user_id=user_id,
            domain=domain,
            verification_token=verification_token,
            verification_method=verification_method,
            verified=False,
            active=True,
        )

        db.add(domain_obj)
        db.commit()
        db.refresh(domain_obj)

        logger.info(f"Created whitelabel domain {domain} for user {user_id}")
        return domain_obj, None

    def get_or_create_branding(self, db: Session, user_id: int) -> WhitelabelBranding:
        """
        Get or create branding configuration

        Args:
            db: Database session
            user_id: User ID

        Returns:
            WhitelabelBranding object
        """
        branding = (
            db.query(WhitelabelBranding)
            .filter(WhitelabelBranding.user_id == user_id)
            .first()
        )

        if not branding:
            branding = WhitelabelBranding(user_id=user_id)
            db.add(branding)
            db.commit()
            db.refresh(branding)

        return branding

    def update_branding(
        self, db: Session, user_id: int, **kwargs
    ) -> WhitelabelBranding:
        """
        Update branding configuration

        Args:
            db: Database session
            user_id: User ID
            **kwargs: Branding fields to update

        Returns:
            Updated WhitelabelBranding object
        """
        branding = self.get_or_create_branding(db, user_id)

        # Update fields
        for key, value in kwargs.items():
            if hasattr(branding, key) and value is not None:
                setattr(branding, key, value)

        branding.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(branding)

        logger.info("Updated branding for user", extra={"user_id": user_id})
        return branding

    def get_branding_by_domain(
        self, db: Session, domain: str
    ) -> Optional[WhitelabelBranding]:
        """
        Get branding configuration by domain

        Args:
            db: Database session
            domain: Domain name

        Returns:
            WhitelabelBranding object or None
        """
        domain_obj = (
            db.query(WhitelabelDomain)
            .filter(
                WhitelabelDomain.domain == domain,
                WhitelabelDomain.verified == True,
                WhitelabelDomain.active == True,
            )
            .first()
        )

        if domain_obj is None:
            return None

        return (
            db.query(WhitelabelBranding)
            .filter(WhitelabelBranding.user_id == domain_obj.user_id)
            .first()
        )


# Singleton instance
whitelabel_service = WhitelabelService()
