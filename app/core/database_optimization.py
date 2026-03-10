"""Database schema optimization - add missing indexes and improve performance."""

from sqlalchemy import inspect, text
from sqlalchemy.exc import OperationalError

from app.core.database import db_manager
from app.core.logging import get_logger

logger = get_logger(__name__)


class DatabaseOptimizer:
    """Database schema optimization utilities."""

    def __init__(self):
        self.engine = db_manager.engine

    def get_missing_indexes(self) -> list:
        """Identify missing indexes based on common query patterns."""
        missing_indexes = []

        try:
            inspector = inspect(self.engine)

            # Check each table for missing indexes
            tables_to_check = {
                "users": [
                    ("email", "Unique index for login queries"),
                    ("subscription_tier", "Index for tier-based queries"),
                    ("created_at", "Index for user registration analytics"),
                    ("is_active", "Index for active user queries"),
                    ("referral_code", "Index for referral lookups"),
                ],
                "verifications": [
                    ("user_id", "Index for user verification history"),
                    ("status", "Index for status-based queries"),
                    ("created_at", "Index for chronological queries"),
                    ("service", "Index for service-based analytics"),
                    ("phone_number", "Index for phone number lookups"),
                    ("idempotency_key", "Index for duplicate prevention"),
                ],
                "transactions": [
                    ("user_id", "Index for user transaction history"),
                    ("type", "Index for transaction type queries"),
                    ("status", "Index for transaction status queries"),
                    ("created_at", "Index for chronological queries"),
                    ("reference", "Index for reference lookups"),
                ],
                "payment_logs": [
                    ("user_id", "Index for user payment history"),
                    ("reference", "Index for payment reference lookups"),
                    ("state", "Index for payment state queries"),
                    ("created_at", "Index for chronological queries"),
                    ("idempotency_key", "Index for duplicate prevention"),
                ],
                "notifications": [
                    ("user_id", "Index for user notifications"),
                    ("read", "Index for unread notification queries"),
                    ("created_at", "Index for chronological queries"),
                    ("type", "Index for notification type queries"),
                ],
            }

            for table_name, required_indexes in tables_to_check.items():
                if table_name not in inspector.get_table_names():
                    continue

                existing_indexes = inspector.get_indexes(table_name)
                existing_columns = {
                    idx["column_names"][0]
                    for idx in existing_indexes
                    if len(idx["column_names"]) == 1
                }

                for column, description in required_indexes:
                    if column not in existing_columns:
                        missing_indexes.append(
                            {
                                "table": table_name,
                                "column": column,
                                "description": description,
                                "index_name": f"ix_{table_name}_{column}",
                            }
                        )

            return missing_indexes

        except Exception as e:
            logger.error(f"Error checking missing indexes: {e}")
            return []

    def create_missing_indexes(self) -> dict:
        """Create missing indexes to improve query performance."""
        missing_indexes = self.get_missing_indexes()
        results = {"created": [], "failed": [], "skipped": []}

        if not missing_indexes:
            logger.info("No missing indexes found")
            return results

        for index_info in missing_indexes:
            try:
                table = index_info["table"]
                column = index_info["column"]
                index_name = index_info["index_name"]

                # Create index
                sql = f"CREATE INDEX IF NOT EXISTS {index_name} ON {table} ({column})"

                with self.engine.connect() as conn:
                    conn.execute(text(sql))
                    conn.commit()

                results["created"].append(index_info)
                logger.info(f"Created index {index_name} on {table}.{column}")

            except OperationalError as e:
                if "already exists" in str(e).lower():
                    results["skipped"].append(index_info)
                    logger.info(f"Index {index_name} already exists")
                else:
                    results["failed"].append({**index_info, "error": str(e)})
                    logger.error(f"Failed to create index {index_name}: {e}")
            except Exception as e:
                results["failed"].append({**index_info, "error": str(e)})
                logger.error(f"Failed to create index {index_name}: {e}")

        return results

    def analyze_table_stats(self) -> dict:
        """Analyze table statistics for optimization insights."""
        stats = {}

        try:
            inspector = inspect(self.engine)
            tables = inspector.get_table_names()

            for table in tables:
                try:
                    with self.engine.connect() as conn:
                        # Get row count
                        count_result = conn.execute(
                            text(f"SELECT COUNT(*) FROM {table}")
                        )
                        row_count = count_result.scalar()

                        # Get table size (PostgreSQL specific)
                        if "postgresql" in str(self.engine.url):
                            size_result = conn.execute(
                                text(
                                    f"SELECT pg_size_pretty(pg_total_relation_size('{table}'))"
                                )
                            )
                            table_size = size_result.scalar()
                        else:
                            table_size = "N/A (SQLite)"

                        stats[table] = {
                            "row_count": row_count,
                            "table_size": table_size,
                            "indexes": len(inspector.get_indexes(table)),
                        }

                except Exception as e:
                    stats[table] = {"error": str(e)}

        except Exception as e:
            logger.error(f"Error analyzing table stats: {e}")

        return stats

    def optimize_database(self) -> dict:
        """Run comprehensive database optimization."""
        logger.info("Starting database optimization...")

        results = {
            "indexes": self.create_missing_indexes(),
            "stats": self.analyze_table_stats(),
            "recommendations": [],
        }

        # Add recommendations based on analysis
        stats = results["stats"]
        recommendations = []

        for table, table_stats in stats.items():
            if isinstance(table_stats, dict) and "row_count" in table_stats:
                row_count = table_stats["row_count"]
                index_count = table_stats["indexes"]

                if row_count > 10000 and index_count < 3:
                    recommendations.append(
                        f"Table '{table}' has {row_count} rows but only {index_count} indexes. Consider adding more indexes for frequently queried columns."
                    )

                if row_count > 100000:
                    recommendations.append(
                        f"Table '{table}' has {row_count} rows. Consider implementing data archival strategy."
                    )

        results["recommendations"] = recommendations

        logger.info(
            f"Database optimization completed. Created {len(results['indexes']['created'])} indexes."
        )
        return results


# Global optimizer instance
db_optimizer = DatabaseOptimizer()


def optimize_database():
    """Run database optimization (convenience function)."""
    return db_optimizer.optimize_database()


def get_missing_indexes():
    """Get list of missing indexes (convenience function)."""
    return db_optimizer.get_missing_indexes()


def create_indexes():
    """Create missing indexes (convenience function)."""
    return db_optimizer.create_missing_indexes()
