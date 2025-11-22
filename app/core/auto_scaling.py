"""Auto-scaling configuration."""
from typing import Any, Dict

import psutil


class AutoScaler:
    def __init__(self, cpu_threshold: float = 80.0, memory_threshold: float = 85.0):
        self.cpu_threshold = cpu_threshold
        self.memory_threshold = memory_threshold

    def get_system_metrics(self) -> Dict[str, Any]:
        """Get current system metrics."""
        return {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent,
            'active_connections': len(psutil.net_connections())
        }

    def should_scale_up(self) -> bool:
        """Check if system should scale up."""
        metrics = self.get_system_metrics()
        return (
            metrics['cpu_percent'] > self.cpu_threshold
            or metrics['memory_percent'] > self.memory_threshold
        )

    def should_scale_down(self) -> bool:
        """Check if system can scale down."""
        metrics = self.get_system_metrics()
        return (
            metrics['cpu_percent'] < 30.0
            and metrics['memory_percent'] < 50.0
        )
