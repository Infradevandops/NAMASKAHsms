"""Feature flag system for task 13.4."""

import json
from enum import Enum
from typing import Dict, Optional


class RolloutStrategy(Enum):
    """Feature rollout strategies."""

    ALL_USERS = "all_users"
    PERCENTAGE = "percentage"
    USER_LIST = "user_list"
    ADMIN_ONLY = "admin_only"


class FeatureFlag:
    """Individual feature flag."""

    def __init__(
        self,
        name: str,
        enabled: bool = False,
        strategy: RolloutStrategy = RolloutStrategy.ALL_USERS,
        config: Dict = None,
    ):
        self.name = name
        self.enabled = enabled
        self.strategy = strategy
        self.config = config or {}


class FeatureFlagManager:
    """Feature flag management system."""

    def __init__(self):
        self.flags = {}
        self._load_default_flags()

    def _load_default_flags(self):
        """Load default feature flags."""
        default_flags = {
            "new_verification_ui": FeatureFlag(
                "new_verification_ui",
                False,
                RolloutStrategy.PERCENTAGE,
                {"percentage": 10},
            ),
            "enhanced_analytics": FeatureFlag("enhanced_analytics", False, RolloutStrategy.ADMIN_ONLY),
            "redis_caching": FeatureFlag("redis_caching", True, RolloutStrategy.ALL_USERS),
            "webhook_v2": FeatureFlag(
                "webhook_v2",
                False,
                RolloutStrategy.USER_LIST,
                {"users": ["admin@namaskah.app"]},
            ),
        }
        self.flags.update(default_flags)

    def is_enabled(self, flag_name: str, user_id: Optional[str] = None, is_admin: bool = False) -> bool:
        """Check if feature flag is enabled for user."""
        if flag_name not in self.flags:
            return False

        flag = self.flags[flag_name]

        if not flag.enabled:
            return False

        if flag.strategy == RolloutStrategy.ALL_USERS:
            return True

        elif flag.strategy == RolloutStrategy.ADMIN_ONLY:
            return is_admin

        elif flag.strategy == RolloutStrategy.PERCENTAGE:
            if not user_id:
                return False
            percentage = flag.config.get("percentage", 0)
            user_hash = hash(user_id) % 100
            return user_hash < percentage

        elif flag.strategy == RolloutStrategy.USER_LIST:
            if not user_id:
                return False
            allowed_users = flag.config.get("users", [])
            return user_id in allowed_users

        return False

    def update_flag(
        self,
        flag_name: str,
        enabled: bool,
        strategy: RolloutStrategy = None,
        config: Dict = None,
    ):
        """Update feature flag configuration."""
        if flag_name in self.flags:
            flag = self.flags[flag_name]
            flag.enabled = enabled
            if strategy:
                flag.strategy = strategy
            if config:
                flag.config.update(config)
        else:
            self.flags[flag_name] = FeatureFlag(flag_name, enabled, strategy or RolloutStrategy.ALL_USERS, config or {})

    def get_user_flags(self, user_id: str, is_admin: bool = False) -> Dict[str, bool]:
        """Get all feature flags for a specific user."""
        return {flag_name: self.is_enabled(flag_name, user_id, is_admin) for flag_name in self.flags}

    def export_config(self) -> str:
        """Export feature flag configuration as JSON."""
        config = {}
        for name, flag in self.flags.items():
            config[name] = {
                "enabled": flag.enabled,
                "strategy": flag.strategy.value,
                "config": flag.config,
            }
        return json.dumps(config, indent=2)


# Global feature flag manager
feature_flags = FeatureFlagManager()


def is_feature_enabled(flag_name: str, user_id: Optional[str] = None, is_admin: bool = False) -> bool:
    """Convenience function to check feature flags."""
    return feature_flags.is_enabled(flag_name, user_id, is_admin)


def feature_flag_middleware(request, user_id: Optional[str] = None, is_admin: bool = False):
    """Middleware to inject feature flags into request context."""
    if hasattr(request, "state"):
        request.state.feature_flags = feature_flags.get_user_flags(user_id, is_admin)
    return request
