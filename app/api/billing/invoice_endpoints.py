"""Invoice endpoints — downloadable PDF receipts."""

import io

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.models.transaction import Transaction
from app.models.user import User

router = APIRouter()


@router.get("/{transaction_id}")
async def download_invoice(
    transaction_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    tx = (
        db.query(Transaction)
        .filter(
            Transaction.id == transaction_id,
            Transaction.user_id == user_id,
        )
        .first()
    )
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")

    user = db.query(User).filter(User.id == user_id).first()

    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import (Paragraph, SimpleDocTemplate, Spacer,
                                    Table, TableStyle)

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("Namaskah", styles["Title"]))
    elements.append(Paragraph("Invoice / Receipt", styles["Heading2"]))
    elements.append(Spacer(1, 12))

    date_str = tx.created_at.strftime("%B %d, %Y") if tx.created_at else "—"
    data = [
        ["Invoice ID", f"INV-{tx.id[:8].upper()}"],
        ["Reference", getattr(tx, "reference", tx.id) or tx.id],
        ["Date", date_str],
        ["Billed To", user.email if user else "—"],
        ["Description", tx.description or tx.type or "—"],
        ["Amount", f"${abs(tx.amount):.2f} USD"],
        ["Status", (tx.status or "completed").capitalize()],
    ]

    table = Table(data, colWidths=[150, 320])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f3f4f6")),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
                (
                    "ROWBACKGROUNDS",
                    (0, 0),
                    (-1, -1),
                    [colors.white, colors.HexColor("#fafafa")],
                ),
                ("PADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    elements.append(table)
    elements.append(Spacer(1, 24))
    elements.append(Paragraph("Thank you for using Namaskah.", styles["Normal"]))

    doc.build(elements)
    buf.seek(0)

    return StreamingResponse(
        buf,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=invoice-{tx.id[:8]}.pdf"
        },
    )
