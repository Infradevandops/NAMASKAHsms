"""Tax reporting and calculation service."""

from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.tax_report import (
    TaxExemptionCertificate,
    TaxJurisdictionConfig,
    TaxReport,
    WithholdingTaxRecord,
)
from app.models.transaction import Transaction

logger = get_logger(__name__)


class TaxService:
    """Service for tax reporting and calculation."""

    def __init__(self, db: Session):
        self.db = db

    async def generate_tax_report(
        self,
        period: str,
        jurisdiction: str,
        report_type: str,
    ) -> Dict:
        """Generate tax report for a period and jurisdiction.

        Args:
            period: Period (YYYY-MM, YYYY-Q1, or YYYY)
            jurisdiction: Jurisdiction code
            report_type: Report type (VAT, GST, INCOME, WITHHOLDING)

        Returns:
            Generated tax report
        """
        try:
            # Get configuration
            config = (
                self.db.query(TaxJurisdictionConfig)
                .filter(TaxJurisdictionConfig.jurisdiction_code == jurisdiction)
                .first()
            )
            if not config:
                raise ValueError(f"Jurisdiction {jurisdiction} not configured")

            # Parse period
            if period.endswith("Q1"):
                months = [1, 2, 3]
            elif period.endswith("Q2"):
                months = [4, 5, 6]
            elif period.endswith("Q3"):
                months = [7, 8, 9]
            elif period.endswith("Q4"):
                months = [10, 11, 12]
            else:
                month = int(period.split("-")[1])
                months = [month]

            year = int(period.split("-")[0])

            # Calculate totals
            from sqlalchemy import extract
            transactions = (
                self.db.query(Transaction)
                .filter(
                    and_(
                        extract("year", Transaction.created_at) == year,
                        Transaction.status == "completed",
                    )
                )
                .all()
            )

            # Filter by month for period
            period_transactions = [
                t
                for t in transactions
                if t.created_at.month in months
                and t.created_at.year == year
            ]

            gross_revenue = sum(
                t.amount for t in period_transactions if t.type == "credit"
            )
            taxable_revenue = gross_revenue
            refunded_revenue = abs(
                sum(t.amount for t in period_transactions if t.type == "refund")
            )

            # Calculate tax
            tax_rate = config.standard_tax_rate
            tax_amount = taxable_revenue * tax_rate

            # Create report
            report = TaxReport(
                period=period,
                jurisdiction=jurisdiction,
                report_type=report_type,
                gross_revenue=gross_revenue,
                taxable_revenue=taxable_revenue,
                tax_exempt_revenue=0.0,
                refunded_revenue=refunded_revenue,
                tax_rate=tax_rate,
                tax_amount_due=tax_amount,
                tax_paid=0.0,
                tax_balance=tax_amount,
                vat_output_tax=tax_amount,
                transaction_count=len(period_transactions),
                status="draft",
                due_date=datetime.now(timezone.utc) + timedelta(days=30),
            )

            self.db.add(report)
            self.db.commit()

            logger.info(
                f"Tax report generated for {jurisdiction} {period}: ${tax_amount:.2f}"
            )

            return {
                "status": "success",
                "report_id": report.id,
                "period": period,
                "jurisdiction": jurisdiction,
                "gross_revenue": gross_revenue,
                "tax_amount_due": tax_amount,
                "tax_rate": tax_rate * 100,
            }

        except Exception as e:
            logger.error(f"Tax report generation failed: {str(e)}")
            self.db.rollback()
            raise

    async def record_tax_payment(
        self,
        report_id: str,
        payment_amount: float,
        payment_method: str,
        payment_reference: str,
    ) -> Dict:
        """Record tax payment against report.

        Args:
            report_id: Tax report ID
            payment_amount: Amount paid
            payment_method: Payment method
            payment_reference: Payment reference

        Returns:
            Updated report
        """
        try:
            report = (
                self.db.query(TaxReport).filter(TaxReport.id == report_id).first()
            )
            if not report:
                raise ValueError(f"Report {report_id} not found")

            report.tax_paid += payment_amount
            report.tax_balance = report.tax_amount_due - report.tax_paid
            report.payment_date = datetime.now(timezone.utc)
            report.payment_method = payment_method
            report.payment_reference = payment_reference

            # Update status
            if report.tax_balance <= 0:
                report.status = "paid"
            elif report.tax_balance < report.tax_amount_due:
                report.status = "partial"
            else:
                report.status = "pending"

            self.db.commit()

            logger.info(
                f"Tax payment recorded for report {report_id}: ${payment_amount:.2f}"
            )

            return {
                "status": "success",
                "report_id": report_id,
                "tax_paid": report.tax_paid,
                "balance": report.tax_balance,
                "payment_status": report.status,
            }

        except Exception as e:
            logger.error(f"Tax payment recording failed: {str(e)}")
            self.db.rollback()
            raise

    async def get_tax_summary(
        self, year: int, user_id: Optional[str] = None
    ) -> Dict:
        """Get tax summary for year.

        Args:
            year: Year
            user_id: Optional filter by user

        Returns:
            Tax summary
        """
        reports = (
            self.db.query(TaxReport)
            .filter(TaxReport.period.like(f"{year}-%"))
            .all()
        )

        total_gross = sum(r.gross_revenue for r in reports)
        total_tax_due = sum(r.tax_amount_due for r in reports)
        total_tax_paid = sum(r.tax_paid for r in reports)

        return {
            "year": year,
            "periods": len(reports),
            "gross_revenue": total_gross,
            "total_tax_due": total_tax_due,
            "total_tax_paid": total_tax_paid,
            "tax_balance": total_tax_due - total_tax_paid,
            "jurisdiction_breakdown": self._get_jurisdiction_breakdown(reports),
        }

    def _get_jurisdiction_breakdown(self, reports: List) -> Dict:
        """Break down reports by jurisdiction."""
        breakdown = {}
        for report in reports:
            if report.jurisdiction not in breakdown:
                breakdown[report.jurisdiction] = {
                    "gross_revenue": 0,
                    "tax_due": 0,
                    "tax_paid": 0,
                }
            breakdown[report.jurisdiction]["gross_revenue"] += report.gross_revenue
            breakdown[report.jurisdiction]["tax_due"] += report.tax_amount_due
            breakdown[report.jurisdiction]["tax_paid"] += report.tax_paid

        return breakdown

    async def create_tax_exemption(
        self,
        user_id: str,
        jurisdiction: str,
        certificate_type: str,
        certificate_number: str,
        expiry_date: datetime,
    ) -> Dict:
        """Create tax exemption certificate.

        Args:
            user_id: User ID
            jurisdiction: Jurisdiction code
            certificate_type: Type of exemption
            certificate_number: Certificate number
            expiry_date: Expiry date

        Returns:
            Exemption certificate
        """
        try:
            exemption = TaxExemptionCertificate(
                user_id=user_id,
                jurisdiction=jurisdiction,
                certificate_number=certificate_number,
                certificate_type=certificate_type,
                expiry_date=expiry_date,
                issued_date=datetime.now(timezone.utc),
                is_valid=True,
                exemption_reason=f"{certificate_type} exemption",
            )

            self.db.add(exemption)
            self.db.commit()

            logger.info(
                f"Tax exemption created for {user_id}: {certificate_type} in {jurisdiction}"
            )

            return {
                "status": "success",
                "exemption_id": exemption.id,
                "user_id": user_id,
                "jurisdiction": jurisdiction,
                "certificate_type": certificate_type,
            }

        except Exception as e:
            logger.error(f"Tax exemption creation failed: {str(e)}")
            self.db.rollback()
            raise

    async def record_withholding_tax(
        self,
        payee_id: str,
        payer_id: str,
        jurisdiction: str,
        gross_amount: float,
        withholding_rate: float,
        transaction_id: str,
    ) -> Dict:
        """Record withholding tax obligation.

        Args:
            payee_id: Payee ID
            payer_id: Payer ID
            jurisdiction: Jurisdiction code
            gross_amount: Gross amount
            withholding_rate: Withholding rate
            transaction_id: Transaction ID

        Returns:
            Withholding record
        """
        try:
            withholding_amount = gross_amount * withholding_rate
            net_payment = gross_amount - withholding_amount

            record = WithholdingTaxRecord(
                payee_id=payee_id,
                payer_id=payer_id,
                jurisdiction=jurisdiction,
                transaction_id=transaction_id,
                payment_date=datetime.now(timezone.utc),
                gross_amount=gross_amount,
                withholding_rate=withholding_rate,
                withholding_amount=withholding_amount,
                net_payment=net_payment,
                withheld=True,
                withholding_date=datetime.now(timezone.utc),
            )

            self.db.add(record)
            self.db.commit()

            logger.info(
                f"Withholding tax recorded: ${withholding_amount:.2f} for {payee_id}"
            )

            return {
                "status": "success",
                "withholding_id": record.id,
                "gross_amount": gross_amount,
                "withholding_amount": withholding_amount,
                "net_payment": net_payment,
            }

        except Exception as e:
            logger.error(f"Withholding tax recording failed: {str(e)}")
            self.db.rollback()
            raise

    async def get_withholding_tax_summary(self, payer_id: str, year: int) -> Dict:
        """Get withholding tax summary for payer.

        Args:
            payer_id: Payer ID
            year: Year

        Returns:
            Summary
        """
        records = (
            self.db.query(WithholdingTaxRecord)
            .filter(
                and_(
                    WithholdingTaxRecord.payer_id == payer_id,
                    WithholdingTaxRecord.payment_date.isoformat().like(
                        f"{year}-%"
                    ),
                )
            )
            .all()
        )

        total_gross = sum(r.gross_amount for r in records)
        total_withheld = sum(r.withholding_amount for r in records)
        remitted = sum(r.withholding_amount for r in records if r.remitted_to_authority)

        return {
            "year": year,
            "total_records": len(records),
            "total_gross": total_gross,
            "total_withheld": total_withheld,
            "remitted_amount": remitted,
            "pending_remittance": total_withheld - remitted,
        }
