import logging

logger = logging.getLogger(__name__)
"""Custom analytics reports endpoints."""

import uuid
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.models.user import User
from app.models.verification import Verification

router = APIRouter(prefix="/api/admin/analytics/reports", tags=["Analytics Reports"])


async def require_admin(
    user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)
):
    """Verify admin access."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user_id


class ReportConfig(BaseModel):
    name: str
    start_date: str
    end_date: str
    metrics: List[str]
    group_by: str
    filters: dict


# In-memory storage for saved reports (would use database in production)
saved_reports = {}


@router.get("/saved")
async def get_saved_reports(
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    try:
        """Get all saved custom reports."""
        return {
            "reports": [
                {
                    "id": report_id,
                    "name": report["name"],
                    "description": f"Custom report with {len(report['metrics'])} metrics",
                    "metrics": report["metrics"],
                    "group_by": report["group_by"],
                    "created_at": report.get("created_at", datetime.now().isoformat()),
                }
                for report_id, report in saved_reports.items()
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_saved_reports: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/generate")
async def generate_report(
    config: ReportConfig,
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    try:
        """Generate a custom report based on configuration."""
        start_date = datetime.fromisoformat(config.start_date)
        end_date = datetime.fromisoformat(config.end_date)

        # Query verifications
        query = db.query(Verification).filter(
            Verification.created_at >= start_date, Verification.created_at <= end_date
        )

        # Apply filters
        if config.filters.get("service"):
            query = query.filter(Verification.service_name == config.filters["service"])
        if config.filters.get("country"):
            query = query.filter(Verification.country_code == config.filters["country"])

        verifications = query.all()

        # Group data
        results = []
        if config.group_by == "day":
            # Group by day
            days = {}
            for v in verifications:
                day = v.created_at.date().isoformat()
                if day not in days:
                    days[day] = {
                        "label": day,
                        "verifications": 0,
                        "revenue": 0,
                        "refunds": 0,
                        "users": set(),
                    }
                days[day]["verifications"] += 1
                days[day]["revenue"] += float(v.cost or 0)
                if v.refunded:
                    days[day]["refunds"] += 1
                days[day]["users"].add(v.user_id)

            for day, data in sorted(days.items()):
                results.append(
                    {
                        "label": day,
                        "verifications": data["verifications"],
                        "revenue": data["revenue"],
                        "refunds": data["refunds"],
                        "users": len(data["users"]),
                    }
                )

        elif config.group_by == "service":
            # Group by service
            services = {}
            for v in verifications:
                service = v.service_name or "Unknown"
                if service not in services:
                    services[service] = {
                        "label": service,
                        "verifications": 0,
                        "revenue": 0,
                        "refunds": 0,
                        "users": set(),
                    }
                services[service]["verifications"] += 1
                services[service]["revenue"] += float(v.cost or 0)
                if v.refunded:
                    services[service]["refunds"] += 1
                services[service]["users"].add(v.user_id)

            for service, data in sorted(
                services.items(), key=lambda x: x[1]["verifications"], reverse=True
            ):
                results.append(
                    {
                        "label": service,
                        "verifications": data["verifications"],
                        "revenue": data["revenue"],
                        "refunds": data["refunds"],
                        "users": len(data["users"]),
                    }
                )

        elif config.group_by == "country":
            # Group by country
            countries = {}
            for v in verifications:
                country = v.country_code or "Unknown"
                if country not in countries:
                    countries[country] = {
                        "label": country,
                        "verifications": 0,
                        "revenue": 0,
                        "refunds": 0,
                        "users": set(),
                    }
                countries[country]["verifications"] += 1
                countries[country]["revenue"] += float(v.cost or 0)
                if v.refunded:
                    countries[country]["refunds"] += 1
                countries[country]["users"].add(v.user_id)

            for country, data in sorted(
                countries.items(), key=lambda x: x[1]["verifications"], reverse=True
            ):
                results.append(
                    {
                        "label": country,
                        "verifications": data["verifications"],
                        "revenue": data["revenue"],
                        "refunds": data["refunds"],
                        "users": len(data["users"]),
                    }
                )

        return {
            "name": config.name,
            "start_date": config.start_date,
            "end_date": config.end_date,
            "group_by": config.group_by,
            "metrics": config.metrics,
            "results": results,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in generate_report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/save")
async def save_report(
    config: ReportConfig,
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    try:
        """Save a custom report configuration."""
        report_id = str(uuid.uuid4())
        saved_reports[report_id] = {
            "name": config.name,
            "start_date": config.start_date,
            "end_date": config.end_date,
            "metrics": config.metrics,
            "group_by": config.group_by,
            "filters": config.filters,
            "created_at": datetime.now().isoformat(),
        }

        return {"status": "saved", "report_id": report_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in save_report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{report_id}")
async def get_report(
    report_id: str,
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    try:
        """Load and execute a saved report."""
        if report_id not in saved_reports:
            raise HTTPException(status_code=404, detail="Report not found")

        config_dict = saved_reports[report_id]
        config = ReportConfig(**config_dict)

        return await generate_report(config, admin_id, db)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/download")
async def download_report(
    format: str = "csv",
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    try:
        """Download report in specified format."""
        import csv
        import io

        from fastapi.responses import StreamingResponse

        # Mock data for download
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Label", "Verifications", "Revenue", "Refunds", "Users"])
        writer.writerow(["2026-05-01", "150", "$450.00", "5", "45"])
        writer.writerow(["2026-05-02", "180", "$540.00", "3", "52"])

        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=custom_report_{datetime.now().strftime('%Y%m%d')}.csv"
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in download_report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
