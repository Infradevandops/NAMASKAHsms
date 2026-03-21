"""Database query optimization for tier identification system.

Implements:
- Index optimization
- Query analysis
- Connection pooling
- Query caching
"""

import logging
from typing import List, Dict, Any
from sqlalchemy import text, event
from sqlalchemy.orm import Session
from sqlalchemy.pool import QueuePool

logger = logging.getLogger(__name__)


class DatabaseOptimizer:
    """Optimizes database performance."""

    @staticmethod
    def create_indexes(engine):
        """Create optimized indexes.
        
        Args:
            engine: SQLAlchemy engine
        """
        try:
            with engine.connect() as conn:
                # Tier identification indexes
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_user_tier 
                    ON users(id, tier) 
                    WHERE deleted_at IS NULL
                """))

                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_user_tier_updated 
                    ON users(id, tier_updated_at) 
                    WHERE deleted_at IS NULL
                """))

                # Feature access indexes
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_tier_features 
                    ON subscription_tiers(name, features)
                """))

                # Verification indexes
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_verification_user 
                    ON verifications(user_id, created_at)
                """))

                # Transaction indexes
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_transaction_user 
                    ON transactions(user_id, created_at)
                """))

                conn.commit()
                logger.info("Database indexes created")

        except Exception as e:
            logger.error(f"Index creation failed: {e}")

    @staticmethod
    def analyze_query(db: Session, query_str: str) -> Dict[str, Any]:
        """Analyze query performance.
        
        Args:
            db: Database session
            query_str: SQL query string
            
        Returns:
            Query analysis results
        """
        try:
            # Use EXPLAIN ANALYZE
            result = db.execute(text(f"EXPLAIN ANALYZE {query_str}")).fetchall()

            analysis = {
                "query": query_str,
                "plan": [row[0] for row in result],
            }

            logger.debug(f"Query analysis: {analysis}")
            return analysis

        except Exception as e:
            logger.error(f"Query analysis failed: {e}")
            return {}

    @staticmethod
    def optimize_connection_pool(engine, pool_size: int = 20, max_overflow: int = 40):
        """Optimize connection pool.
        
        Args:
            engine: SQLAlchemy engine
            pool_size: Pool size
            max_overflow: Max overflow connections
        """
        try:
            # Recreate engine with optimized pool
            from sqlalchemy import create_engine

            # Get connection string
            url = str(engine.url)

            # Create new engine with optimized pool
            new_engine = create_engine(
                url,
                poolclass=QueuePool,
                pool_size=pool_size,
                max_overflow=max_overflow,
                pool_pre_ping=True,  # Test connections before using
                pool_recycle=3600,  # Recycle connections after 1 hour
            )

            logger.info(
                f"Connection pool optimized: "
                f"pool_size={pool_size}, max_overflow={max_overflow}"
            )

            return new_engine

        except Exception as e:
            logger.error(f"Connection pool optimization failed: {e}")
            return engine


class QueryCache:
    """Caches query results."""

    def __init__(self, redis_client=None, ttl: int = 300):
        """Initialize query cache.
        
        Args:
            redis_client: Redis client
            ttl: Cache TTL in seconds
        """
        self.redis = redis_client
        self.ttl = ttl

    def get(self, query_key: str) -> Any:
        """Get cached query result.
        
        Args:
            query_key: Query cache key
            
        Returns:
            Cached result or None
        """
        try:
            if not self.redis:
                return None

            cached = self.redis.get(f"query:{query_key}")
            if cached:
                logger.debug(f"Query cache hit: {query_key}")
                return cached

            return None

        except Exception as e:
            logger.error(f"Query cache get failed: {e}")
            return None

    def set(self, query_key: str, value: Any) -> bool:
        """Set cached query result.
        
        Args:
            query_key: Query cache key
            value: Query result
            
        Returns:
            True if successful
        """
        try:
            if not self.redis:
                return False

            self.redis.setex(f"query:{query_key}", self.ttl, value)
            logger.debug(f"Query cached: {query_key}")

            return True

        except Exception as e:
            logger.error(f"Query cache set failed: {e}")
            return False

    def invalidate(self, pattern: str) -> int:
        """Invalidate cached queries.
        
        Args:
            pattern: Pattern to match
            
        Returns:
            Number of keys deleted
        """
        try:
            if not self.redis:
                return 0

            keys = self.redis.keys(f"query:{pattern}")
            if keys:
                deleted = self.redis.delete(*keys)
                logger.debug(f"Query cache invalidated: {pattern} ({deleted} keys)")
                return deleted

            return 0

        except Exception as e:
            logger.error(f"Query cache invalidation failed: {e}")
            return 0


class SlowQueryLogger:
    """Logs slow queries for analysis."""

    def __init__(self, threshold_ms: float = 100):
        """Initialize slow query logger.
        
        Args:
            threshold_ms: Threshold in milliseconds
        """
        self.threshold_ms = threshold_ms
        self.slow_queries = []

    def log_query(self, query_str: str, duration_ms: float):
        """Log query if slow.
        
        Args:
            query_str: SQL query string
            duration_ms: Query duration in milliseconds
        """
        if duration_ms > self.threshold_ms:
            self.slow_queries.append({
                "query": query_str,
                "duration_ms": duration_ms,
            })

            logger.warning(
                f"Slow query detected ({duration_ms:.2f}ms): {query_str[:100]}..."
            )

    def get_slow_queries(self) -> List[Dict[str, Any]]:
        """Get list of slow queries.
        
        Returns:
            List of slow queries
        """
        return self.slow_queries

    def clear_slow_queries(self):
        """Clear slow query log."""
        self.slow_queries = []


def setup_query_monitoring(engine):
    """Setup query monitoring.
    
    Args:
        engine: SQLAlchemy engine
    """
    slow_query_logger = SlowQueryLogger(threshold_ms=100)

    @event.listens_for(engine, "before_cursor_execute")
    def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        """Log query start."""
        import time
        conn.info.setdefault("query_start_time", []).append(time.time())

    @event.listens_for(engine, "after_cursor_execute")
    def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        """Log query end."""
        import time

        total_time = time.time() - conn.info["query_start_time"].pop(-1)
        duration_ms = total_time * 1000

        slow_query_logger.log_query(statement, duration_ms)

    logger.info("Query monitoring setup complete")
    return slow_query_logger
