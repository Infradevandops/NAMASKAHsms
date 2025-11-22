"""Document service for KYC file handling and processing."""
import os
import hashlib
import mimetypes
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from pathlib import Path
from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session
try:
    from PIL import Image
except ImportError:
    Image = None
import json

from app.models.kyc import KYCDocument, KYCProfile
from app.core.logging import get_logger
from app.core.config import get_settings
from app.utils.path_security import validate_safe_path, sanitize_filename

logger = get_logger(__name__)
settings = get_settings()


class DocumentService:
    """Service for document upload and processing."""

    def __init__(self, db: Session):
        self.db = db
        self.upload_dir = Path("uploads/kyc")
        self.upload_dir.mkdir(parents=True, exist_ok=True)

        # Allowed file types
        self.allowed_types = {
            "image/jpeg", "image/jpg", "image/png", "image/webp",
            "application/pdf"
        }

        # Max file size (10MB)
        self.max_file_size = 10 * 1024 * 1024

        # Document type requirements
        self.document_requirements = {
            "passport": {"types": ["image/jpeg", "image/png",
                                   "application/pdf"], "max_size": 5 * 1024 * 1024},
            "license": {"types": ["image/jpeg",
                                  "image/png"], "max_size": 5 * 1024 * 1024},
            "id_card": {"types": ["image/jpeg",
                                  "image/png"], "max_size": 5 * 1024 * 1024},
            "utility_bill": {"types": ["image/jpeg", "image/png",
                                       "application/pdf"], "max_size": 5 * 1024 * 1024},
            "selfie": {"types": ["image/jpeg",
                                 "image/png"], "max_size": 3 * 1024 * 1024}
        }

    async def upload_document(
        self,
        file: UploadFile,
        document_type: str,
        kyc_profile_id: str
    ) -> KYCDocument:
        """Upload and process KYC document."""
        try:
            # Validate KYC profile exists
            kyc_profile = self.db.query(KYCProfile).filter(KYCProfile.id == kyc_profile_id).first()
            if not kyc_profile:
                raise HTTPException(status_code=404, detail="KYC profile not found")

            # Validate file
            await self._validate_file(file, document_type)

            # Generate unique filename with security validation
            safe_original_name = sanitize_filename(file.filename)
            file_extension = Path(safe_original_name).suffix.lower()
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            filename = f"{kyc_profile_id}_{document_type}_{timestamp}{file_extension}"
            file_path = validate_safe_path(filename, self.upload_dir)

            # Save file
            content = await file.read()
            with open(file_path, "wb") as f:
                f.write(content)

            # Generate file hash
            file_hash = self._generate_file_hash(content)

            # Process image if needed
            extracted_data = {}
            if file.content_type.startswith("image/"):
                extracted_data = await self._process_image(file_path, document_type)

            # Create document record
            document = KYCDocument(
                kyc_profile_id=kyc_profile_id,
                document_type=document_type,
                file_path=str(file_path),
                file_name=file.filename,
                file_size=len(content),
                file_hash=file_hash,
                mime_type=file.content_type,
                verification_status="pending",
                verification_method="automated",
                extracted_data=extracted_data,
                is_encrypted=False  # Would implement encryption in production
            )

            self.db.add(document)
            self.db.commit()
            self.db.refresh(document)

            # Perform automated verification
            await self._perform_automated_verification(document)

            return document

        except HTTPException:
            raise
        except Exception as e:
            logger.error("Document upload failed: %s", str(e))
            # Clean up file if it was created
            if 'file_path' in locals() and file_path.exists():
                file_path.unlink()
            raise HTTPException(status_code=500, detail="Document upload failed")

    async def _validate_file(self, file: UploadFile, document_type: str):
        """Validate uploaded file."""
        # Check document type
        if document_type not in self.document_requirements:
            raise HTTPException(status_code=400, detail=f"Invalid document type: {document_type}")

        requirements = self.document_requirements[document_type]

        # Check file type
        if file.content_type not in requirements["types"]:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type for {document_type}. Allowed: {requirements['types']}"
            )

        # Check file size
        file.file.seek(0, 2)  # Seek to end
        file_size = file.file.tell()
        file.file.seek(0)  # Reset to beginning

        if file_size > requirements["max_size"]:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Max size: {requirements['max_size'] / 1024 / 1024:.1f}MB"
            )

        if file_size == 0:
            raise HTTPException(status_code=400, detail="Empty file")

        # Check filename
        if not file.filename or len(file.filename) > 255:
            raise HTTPException(status_code=400, detail="Invalid filename")

    def _generate_file_hash(self, content: bytes) -> str:
        """Generate SHA - 256 hash of file content."""
        return hashlib.sha256(content).hexdigest()

    async def _process_image(self, file_path: Path,
                             document_type: str) -> Dict[str, Any]:
        """Process image and extract metadata."""
        try:
            extracted_data = {}

            if Image:
                with Image.open(file_path) as img:
                    # Basic image info
                    extracted_data["image_info"] = {
                    "format": img.format,
                    "mode": img.mode,
                    "size": img.size,
                    "has_transparency": img.mode in ("RGBA", "LA")
                    or "transparency" in img.info
                }

                # EXIF data (if available)
                if hasattr(img, '_getexif') and img._getexif():
                    exif_data = img._getexif()
                    extracted_data["exif"] = {
                        "make": exif_data.get(271),
                        "model": exif_data.get(272),
                        "datetime": exif_data.get(306),
                        "gps_info": exif_data.get(34853) is not None
                    }

                    # Image quality assessment
                    extracted_data["quality_assessment"] = self._assess_image_quality(img)

                    # Document - specific processing
                    if document_type in ["passport", "license", "id_card"]:
                        extracted_data["document_analysis"] = await self._analyze_id_document(img)
                    elif document_type == "selfie":
                        extracted_data["face_analysis"] = await self._analyze_selfie(img)
            else:
                extracted_data["error"] = "Image processing unavailable"

            return extracted_data

        except Exception as e:
            logger.error("Image processing failed: %s", str(e))
            return {"error": str(e)}

    def _assess_image_quality(self, img: Image.Image) -> Dict[str, Any]:
        """Assess image quality for document verification."""
        try:
            # Basic quality metrics
            width, height = img.size
            total_pixels = width * height

            # Convert to grayscale for analysis
            gray_img = img.convert('L')

            # Calculate basic statistics
            try:
                import numpy as np
                img_array = np.array(gray_img)
            except ImportError:
                return {"quality_score": 0.5, "error": "NumPy not available"}

            quality_score = 1.0
            issues = []

            # Resolution check
            if total_pixels < 500000:  # Less than 0.5MP
                quality_score -= 0.3
                issues.append("low_resolution")

            # Brightness check
            mean_brightness = np.mean(img_array)
            if mean_brightness < 50:
                quality_score -= 0.2
                issues.append("too_dark")
            elif mean_brightness > 200:
                quality_score -= 0.2
                issues.append("too_bright")

            # Contrast check (simplified)
            contrast = np.std(img_array)
            if contrast < 30:
                quality_score -= 0.2
                issues.append("low_contrast")

            return {
                "quality_score": max(0.0, quality_score),
                "resolution": {"width": width,
                               "height": height, "total_pixels": total_pixels},
                "brightness": float(mean_brightness),
                "contrast": float(contrast),
                "issues": issues
            }

        except Exception as e:
            logger.error("Quality assessment failed: %s", str(e))
            return {"quality_score": 0.5, "error": str(e)}

    async def _analyze_id_document(self, img: Image.Image) -> Dict[str, Any]:
        """Analyze ID document for authenticity markers."""
        try:
            # Simplified document analysis
            analysis = {
                "document_detected": True,
                "text_regions": [],
                "security_features": [],
                "authenticity_score": 0.8  # Placeholder
            }

            # In production, this would use OCR and ML models
            # to detect text, security features, tampering, etc.

            return analysis

        except Exception as e:
            logger.error("Document analysis failed: %s", str(e))
            return {"error": str(e)}

    async def _analyze_selfie(self, img: Image.Image) -> Dict[str, Any]:
        """Analyze selfie for face detection and liveness."""
        try:
            # Simplified face analysis
            analysis = {
                "faces_detected": 1,
                "face_quality": 0.85,
                "liveness_score": 0.9,
                "face_bounds": [100, 100, 300, 300]  # Placeholder coordinates
            }

            # In production, this would use face detection libraries
            # like face_recognition or cloud APIs

            return analysis

        except Exception as e:
            logger.error("Selfie analysis failed: %s", str(e))
            return {"error": str(e)}

    async def _perform_automated_verification(self, document: KYCDocument):
        """Perform automated document verification."""
        try:
            confidence_score = 0.0
            verification_status = "pending"

            if document.extracted_data:
                # Calculate confidence based on extracted data
                if "quality_assessment" in document.extracted_data:
                    quality = document.extracted_data["quality_assessment"]
                    confidence_score += quality.get("quality_score", 0) * 0.4

                if "document_analysis" in document.extracted_data:
                    doc_analysis = document.extracted_data["document_analysis"]
                    confidence_score += doc_analysis.get("authenticity_score", 0) * 0.4

                if "face_analysis" in document.extracted_data:
                    face_analysis = document.extracted_data["face_analysis"]
                    confidence_score += face_analysis.get("face_quality", 0) * 0.2

                # Auto - approve if confidence is high enough
                if confidence_score > 0.8:
                    verification_status = "verified"
                elif confidence_score < 0.3:
                    verification_status = "rejected"

            # Update document
            document.confidence_score = confidence_score
            document.verification_status = verification_status

            self.db.commit()

        except Exception as e:
            logger.error("Automated verification failed: %s", str(e))

    def get_document_url(self, document_id: str, user_id: str) -> Optional[str]:
        """Get secure URL for document access."""
        try:
            document = self.db.query(KYCDocument).join(KYCProfile).filter(
                KYCDocument.id == document_id,
                KYCProfile.user_id == user_id
            ).first()

            if not document:
                return None

            # Update access tracking
            document.access_count += 1
            document.last_accessed = datetime.now(timezone.utc)
            self.db.commit()

            # In production, return signed URL or serve through secure endpoint
            return f"/kyc/documents/{document_id}/view"

        except Exception as e:
            logger.error("Failed to get document URL: %s", str(e))
            return None

    def delete_document(self, document_id: str, user_id: str) -> bool:
        """Delete document (if allowed)."""
        try:
            document = self.db.query(KYCDocument).join(KYCProfile).filter(
                KYCDocument.id == document_id,
                KYCProfile.user_id == user_id,
                KYCProfile.status != "verified"  # Can't delete from verified profiles
            ).first()

            if not document:
                return False

            # Delete file with path validation
            file_path = Path(document.file_path)
            # Ensure file is within upload directory
            if file_path.exists() and file_path.is_relative_to(self.upload_dir):
                file_path.unlink()

            # Delete record
            self.db.delete(document)
            self.db.commit()

            return True

        except Exception as e:
            logger.error("Document deletion failed: %s", str(e))
            return False


def get_document_service(db: Session) -> DocumentService:
    """Get document service instance."""
    return DocumentService(db)
