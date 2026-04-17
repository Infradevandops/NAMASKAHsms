from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.admin.admin_router import require_admin
from app.core.database import get_db
from app.models.purchase_outcome import PurchaseOutcome
from app.services.area_code_geo import NANPA_DATA

router = APIRouter()


@router.get("/analytics/area-codes")
async def get_area_code_analytics(
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db),
    user_id: str = Depends(require_admin),
) -> Dict[str, Any]:
    """Admin analytics for area code performance."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    outcomes = (
        db.query(PurchaseOutcome).filter(PurchaseOutcome.created_at >= cutoff).all()
    )

    if not outcomes:
        return {
            "period": f"{days}d",
            "total_purchases": 0,
            "match_rate": 0.0,
            "top_requested": [],
            "worst_performing": [],
            "data_coverage": 0.0,
        }

    total_purchases = len(outcomes)
    matched_purchases = sum(1 for o in outcomes if o.matched)

    # Calculate stats per area code and service
    ac_stats = {}
    total_area_codes_known = set()

    for outcome in outcomes:
        req = outcome.requested_code
        if not req:
            if outcome.assigned_code:
                total_area_codes_known.add(outcome.assigned_code)
            continue

        total_area_codes_known.add(req)

        assigned = outcome.assigned_code
        service = outcome.service

        key = (req, service)
        if key not in ac_stats:
            ac_stats[key] = {"requests": 0, "successes": 0}

        ac_stats[key]["requests"] += 1
        if req == assigned:
            ac_stats[key]["successes"] += 1

    # Format and sort
    results = []
    for (ac, svc), stats in ac_stats.items():
        results.append(
            {
                "area_code": ac,
                "service": svc,
                "requests": stats["requests"],
                "success_rate": round(stats["successes"] / stats["requests"], 2),
            }
        )

    results.sort(key=lambda x: x["requests"], reverse=True)

    top_requested = [r for r in results if r["requests"] >= 5][:10]
    if not top_requested:
        top_requested = results[:10]

    worst_performing = sorted(
        [r for r in results if r["requests"] >= 5], key=lambda x: x["success_rate"]
    )[:10]

    return {
        "period": f"{days}d",
        "total_purchases": total_purchases,
        "match_rate": (
            round(matched_purchases / total_purchases, 2)
            if total_purchases > 0
            else 0.0
        ),
        "top_requested": top_requested,
        "worst_performing": worst_performing,
        "data_coverage": round(
            len(total_area_codes_known) / 350, 2
        ),  # Rough approximation of total US area codes
    }


@router.get("/analytics/carriers")
async def get_carrier_analytics(
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db),
    user_id: str = Depends(require_admin),
) -> Dict[str, Any]:
    """Admin analytics for carrier performance."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    outcomes = (
        db.query(PurchaseOutcome).filter(PurchaseOutcome.created_at >= cutoff).all()
    )

    if not outcomes:
        return {
            "period": f"{days}d",
            "carrier_distribution": [],
            "carrier_by_service": [],
            "voip_rate": 0.0,
            "landline_rate": 0.0,
        }

    # Analyze carriers
    total = len(outcomes)
    voip = sum(1 for o in outcomes if o.carrier_type == "voip")
    landline = sum(1 for o in outcomes if o.carrier_type == "landline")

    carrier_stats = {}
    service_carrier_stats = {}

    for o in outcomes:
        c = o.assigned_carrier or "unknown"
        svc = o.service

        if c not in carrier_stats:
            carrier_stats[c] = {"count": 0, "sms_total": 0, "sms_success": 0}
        carrier_stats[c]["count"] += 1

        if o.sms_received is not None:
            carrier_stats[c]["sms_total"] += 1
            if o.sms_received:
                carrier_stats[c]["sms_success"] += 1

        key = (svc, c)
        if key not in service_carrier_stats:
            service_carrier_stats[key] = {"count": 0, "sms_total": 0, "sms_success": 0}
        service_carrier_stats[key]["count"] += 1
        if o.sms_received is not None:
            service_carrier_stats[key]["sms_total"] += 1
            if o.sms_received:
                service_carrier_stats[key]["sms_success"] += 1

    distribution = []
    for c, stats in carrier_stats.items():
        if c == "unknown" and stats["count"] < 5:
            continue
        sr = (
            stats["sms_success"] / stats["sms_total"] if stats["sms_total"] > 0 else 0.0
        )
        pct = stats["count"] / total if total > 0 else 0.0
        distribution.append(
            {
                "carrier": c,
                "count": stats["count"],
                "pct": round(pct, 2),
                "sms_delivery_rate": round(sr, 2),
            }
        )

    distribution.sort(key=lambda x: x["count"], reverse=True)

    by_service = []
    for (svc, c), stats in service_carrier_stats.items():
        sr = (
            stats["sms_success"] / stats["sms_total"] if stats["sms_total"] > 0 else 0.0
        )
        by_service.append(
            {
                "service": svc,
                "carrier": c,
                "count": stats["count"],
                "sms_delivery_rate": round(sr, 2),
            }
        )

    by_service.sort(key=lambda x: x["count"], reverse=True)

    return {
        "period": f"{days}d",
        "carrier_distribution": distribution[:15],
        "carrier_by_service": by_service[:20],
        "voip_rate": round(voip / total, 2) if total > 0 else 0.0,
        "landline_rate": round(landline / total, 2) if total > 0 else 0.0,
    }


@router.get("/analytics/geography")
async def get_geography_analytics(
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db),
    user_id: str = Depends(require_admin),
) -> Dict[str, Any]:
    """Admin analytics for geographic performance."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    outcomes = (
        db.query(PurchaseOutcome).filter(PurchaseOutcome.created_at >= cutoff).all()
    )

    if not outcomes:
        return {"period": f"{days}d", "top_cities": [], "top_states": []}

    city_stats = {}
    state_stats = {}

    for o in outcomes:
        ac = o.assigned_code or o.requested_code
        if not ac or ac not in NANPA_DATA:
            continue

        city = NANPA_DATA[ac].get("major_city", "Unknown")
        state = NANPA_DATA[ac].get("state", "Unknown")

        city_key = f"{city}, {state}"
        if city_key not in city_stats:
            city_stats[city_key] = {
                "city": city,
                "state": state,
                "purchases": 0,
                "sms_success": 0,
                "sms_total": 0,
            }

        city_stats[city_key]["purchases"] += 1
        if o.sms_received is not None:
            city_stats[city_key]["sms_total"] += 1
            if o.sms_received:
                city_stats[city_key]["sms_success"] += 1

        if state not in state_stats:
            state_stats[state] = {"purchases": 0, "unique_area_codes": set()}

        state_stats[state]["purchases"] += 1
        state_stats[state]["unique_area_codes"].add(ac)

    top_cities = []
    for st in city_stats.values():
        sr = st["sms_success"] / st["sms_total"] if st["sms_total"] > 0 else 0.0
        top_cities.append(
            {
                "city": st["city"],
                "state": st["state"],
                "purchases": st["purchases"],
                "sms_delivery_rate": round(sr, 2),
            }
        )

    top_cities.sort(key=lambda x: x["purchases"], reverse=True)

    top_states = []
    for s, st in state_stats.items():
        top_states.append(
            {
                "state": s,
                "purchases": st["purchases"],
                "unique_area_codes": len(st["unique_area_codes"]),
            }
        )

    top_states.sort(key=lambda x: x["purchases"], reverse=True)

    return {
        "period": f"{days}d",
        "top_cities": top_cities[:15],
        "top_states": top_states[:15],
    }


@router.get("/analytics/learning")
async def get_learning_progress(
    db: Session = Depends(get_db), user_id: str = Depends(require_admin)
) -> Dict[str, Any]:
    """Track ML cold-start progress and alternative selection stats."""

    cutoff = datetime.now(timezone.utc) - timedelta(days=7)

    # 1. Total coverage
    all_outcomes = db.query(PurchaseOutcome).all()
    known_ac_services = set()
    total_purchases = len(all_outcomes)
    alternative_selections = 0
    alternative_requests = 0

    new_this_week = 0

    for o in all_outcomes:
        ac = o.assigned_code or o.requested_code
        if ac:
            key = f"{o.service}:{ac}"
            if key not in known_ac_services:
                known_ac_services.add(key)
                if getattr(o, "created_at", None) and o.created_at >= cutoff:
                    new_this_week += 1

        # Tracker for "users who wanted X accepted Y"
        if getattr(o, "selected_from_alternatives", False):
            alternative_selections += 1
        if getattr(o, "original_request", None):
            alternative_requests += 1

    return {
        "total_combinations_tracked": len(known_ac_services),
        "new_combinations_7d": new_this_week,
        "alternative_selections_total": alternative_selections,
        "alternative_selection_rate": (
            round(alternative_selections / total_purchases, 2)
            if total_purchases > 0
            else 0.0
        ),
        "total_purchases": total_purchases,
        "message": f"System has purchase data for {len(known_ac_services)} unique area-code/service combinations. Added {new_this_week} new combinations this week.",
    }


@router.get("/analytics/providers")
async def get_provider_analytics(
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db),
    user_id: str = Depends(require_admin),
) -> Dict[str, Any]:
    """Admin analytics for provider performance (Institutional Grade)."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    outcomes = (
        db.query(PurchaseOutcome).filter(PurchaseOutcome.created_at >= cutoff).all()
    )

    if not outcomes:
        return {"period": f"{days}d", "provider_performance": []}

    provider_stats = {}

    for o in outcomes:
        p = o.provider or "unknown"
        if p not in provider_stats:
            provider_stats[p] = {
                "name": p,
                "total_attempts": 0,
                "sms_success": 0,
                "mismatches": 0,
                "refunds": 0,
                "total_refund_amount": 0.0,
                "total_cost": 0.0,
                "total_revenue": 0.0,
                "latencies": [],
            }

        stats = provider_stats[p]
        stats["total_attempts"] += 1

        if o.sms_received is True:
            stats["sms_success"] += 1
        if o.matched is False:
            stats["mismatches"] += 1
        if o.is_refunded:
            stats["refunds"] += 1
            stats["total_refund_amount"] += o.refund_amount or 0.0

        # Financial aggregation
        stats["total_cost"] += o.provider_cost or 0.0
        stats["total_revenue"] += o.user_price or 0.0

        if o.latency_seconds:
            stats["latencies"].append(o.latency_seconds)

    performance = []
    for p, stats in provider_stats.items():
        total = stats["total_attempts"]
        success_rate = stats["sms_success"] / total if total > 0 else 0.0
        refund_rate = stats["refunds"] / total if total > 0 else 0.0

        # Profit calculations
        # Gross profit = Revenue - Raw Provider Cost
        # (Before refunds are deducted from revenue)
        gross_profit = stats["total_revenue"] - stats["total_cost"]

        # Net profit = Revenue - Raw Provider Cost - Refund Amount
        net_profit = gross_profit - stats["total_refund_amount"]

        # ROI = (Gross Profit / Total Cost) * 100
        roi = (
            (gross_profit / stats["total_cost"] * 100)
            if stats["total_cost"] > 0
            else 0.0
        )

        avg_latency = (
            sum(stats["latencies"]) / len(stats["latencies"])
            if stats["latencies"]
            else 0.0
        )

        performance.append(
            {
                "provider": p,
                "total_attempts": total,
                "success_rate": round(success_rate, 2),
                "refund_rate": round(refund_rate, 2),
                "avg_latency": round(avg_latency, 1),
                "financials": {
                    "total_cost": round(stats["total_cost"], 2),
                    "total_revenue": round(stats["total_revenue"], 2),
                    "gross_profit": round(gross_profit, 2),
                    "net_profit": round(net_profit, 2),
                    "roi_pct": round(roi, 1),
                },
            }
        )

    performance.sort(key=lambda x: x["total_attempts"], reverse=True)

    return {
        "period": f"{days}d",
        "provider_performance": performance,
        "total_attempts_period": len(outcomes),
    }
