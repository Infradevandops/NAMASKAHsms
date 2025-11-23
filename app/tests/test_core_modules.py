"""Tests for core modules to complete 100% coverage."""
from app.core.async_processing import BackgroundTaskManager


class TestAsyncProcessing:
    """Test async processing module."""

    def test_background_task_manager(self):
        """Test background task manager."""
        manager = BackgroundTaskManager()
        assert manager.running is False
        assert len(manager.tasks) == 0


class TestCaching:
    """Test caching module."""

    def test_cache_manager_init(self):
        """Test cache manager initialization."""
        cache = CacheManager()
        assert cache._connected is False


class TestFeatureFlags:
    """Test feature flags module."""

    def test_feature_flag_manager(self):
        """Test feature flag manager."""
        manager = FeatureFlagManager()
        assert len(manager.flags) > 0

        # Test flag checking
        result = manager.is_enabled("redis_caching")
        assert isinstance(result, bool)


class TestMonitoring:
    """Test monitoring module."""

    def test_metrics_collector(self):
        """Test metrics collector."""
        collector = MetricsCollector()

        # Test increment
        collector.increment("test_metric", 1.0)
        assert "test_metric" in collector.counters

        # Test gauge
        collector.gauge("test_gauge", 100.0)
        assert "test_gauge" in collector.gauges
