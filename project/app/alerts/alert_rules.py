"""
Alert rule management module.

Handles creation, storage, and management of alert rules for news articles.
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set

from app.utils.logger import get_logger

logger = get_logger(__name__)


class AlertRuleError(Exception):
    """Custom exception for alert rule errors."""

    pass


class AlertRule:
    """
    Alert rule for matching news articles.

    Defines criteria for matching articles (tickers, keywords, categories)
    and notification preferences.
    """

    def __init__(
        self,
        name: str,
        criteria: Dict,
        notification_method: str = "email",
        notification_target: str = "",
        user_id: Optional[str] = None,
        enabled: bool = True,
        rule_id: Optional[str] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        """
        Initialize alert rule.

        Args:
            name: Alert rule name
            criteria: Matching criteria dictionary with:
                - tickers: List of ticker symbols (optional)
                - keywords: List of keywords (optional)
                - categories: List of categories (optional)
                - logic: "AND" or "OR" (default: "OR")
            notification_method: Notification method ("email", "in-app", etc.)
            notification_target: Target for notifications (email address, user ID, etc.)
            user_id: User ID for user-specific rules (optional)
            enabled: Whether rule is enabled
            rule_id: Unique rule ID (auto-generated if not provided)
            created_at: Creation timestamp (auto-generated if not provided)
            updated_at: Update timestamp (auto-generated if not provided)
        """
        self.rule_id = rule_id or str(uuid.uuid4())
        self.name = name
        self.user_id = user_id
        self.criteria = criteria
        self.notification_method = notification_method
        self.notification_target = notification_target
        self.enabled = enabled
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()

        # Validate criteria
        self._validate_criteria()

    def _validate_criteria(self) -> None:
        """Validate alert rule criteria."""
        if not isinstance(self.criteria, dict):
            raise AlertRuleError("Criteria must be a dictionary")

        # Validate logic
        logic = self.criteria.get("logic", "OR")
        if logic not in ["AND", "OR"]:
            raise AlertRuleError(f"Invalid logic: {logic}. Must be 'AND' or 'OR'")

        # Ensure at least one criterion is specified
        tickers = self.criteria.get("tickers", [])
        keywords = self.criteria.get("keywords", [])
        categories = self.criteria.get("categories", [])

        if not tickers and not keywords and not categories:
            raise AlertRuleError(
                "At least one criterion (tickers, keywords, or categories) must be specified"
            )

        # Normalize criteria
        self.criteria["tickers"] = [t.upper() for t in tickers] if tickers else []
        self.criteria["keywords"] = [k.lower() for k in keywords] if keywords else []
        self.criteria["categories"] = (
            [c.lower() for c in categories] if categories else []
        )
        self.criteria["logic"] = logic

    def to_dict(self) -> Dict:
        """
        Convert alert rule to dictionary.

        Returns:
            Dictionary representation of alert rule
        """
        return {
            "rule_id": self.rule_id,
            "name": self.name,
            "user_id": self.user_id,
            "criteria": self.criteria,
            "notification_method": self.notification_method,
            "notification_target": self.notification_target,
            "enabled": self.enabled,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "AlertRule":
        """
        Create alert rule from dictionary.

        Args:
            data: Dictionary containing alert rule data

        Returns:
            AlertRule instance
        """
        return cls(
            rule_id=data.get("rule_id"),
            name=data["name"],
            user_id=data.get("user_id"),
            criteria=data["criteria"],
            notification_method=data.get("notification_method", "email"),
            notification_target=data.get("notification_target", ""),
            enabled=data.get("enabled", True),
            created_at=(
                datetime.fromisoformat(data["created_at"])
                if isinstance(data.get("created_at"), str)
                else data.get("created_at")
            ),
            updated_at=(
                datetime.fromisoformat(data["updated_at"])
                if isinstance(data.get("updated_at"), str)
                else data.get("updated_at")
            ),
        )

    def update(self, **kwargs) -> None:
        """
        Update alert rule fields.

        Args:
            **kwargs: Fields to update
        """
        if "name" in kwargs:
            self.name = kwargs["name"]
        if "criteria" in kwargs:
            self.criteria = kwargs["criteria"]
            self._validate_criteria()
        if "notification_method" in kwargs:
            self.notification_method = kwargs["notification_method"]
        if "notification_target" in kwargs:
            self.notification_target = kwargs["notification_target"]
        if "enabled" in kwargs:
            self.enabled = kwargs["enabled"]

        self.updated_at = datetime.now()


class AlertRuleManager:
    """
    Manager for alert rules storage and retrieval.

    Handles persistence of alert rules to file system.
    """

    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize alert rule manager.

        Args:
            storage_path: Path to storage directory (default: ./data/alerts)
        """
        if storage_path is None:
            storage_path = "./data/alerts"
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.rules_file = self.storage_path / "alert_rules.json"

        # In-memory cache of rules
        self._rules: Dict[str, AlertRule] = {}

        # Load existing rules
        self._load_rules()

    def _load_rules(self) -> None:
        """Load alert rules from storage."""
        if not self.rules_file.exists():
            logger.info("No existing alert rules file found, starting fresh")
            return

        try:
            with open(self.rules_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            for rule_data in data.get("rules", []):
                try:
                    rule = AlertRule.from_dict(rule_data)
                    self._rules[rule.rule_id] = rule
                except Exception as e:
                    logger.warning(
                        f"Failed to load alert rule {rule_data.get('rule_id')}: {str(e)}"
                    )

            logger.info(f"Loaded {len(self._rules)} alert rules from storage")
        except Exception as e:
            logger.error(f"Failed to load alert rules: {str(e)}")
            raise AlertRuleError(f"Failed to load alert rules: {str(e)}") from e

    def _save_rules(self) -> None:
        """Save alert rules to storage."""
        try:
            data = {
                "rules": [rule.to_dict() for rule in self._rules.values()],
                "updated_at": datetime.now().isoformat(),
            }

            # Write to temporary file first, then rename (atomic operation)
            temp_file = self.rules_file.with_suffix(".tmp")
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            temp_file.replace(self.rules_file)
            logger.debug(f"Saved {len(self._rules)} alert rules to storage")
        except Exception as e:
            logger.error(f"Failed to save alert rules: {str(e)}")
            raise AlertRuleError(f"Failed to save alert rules: {str(e)}") from e

    def create_rule(
        self,
        name: str,
        criteria: Dict,
        notification_method: str = "email",
        notification_target: str = "",
        user_id: Optional[str] = None,
        enabled: bool = True,
    ) -> AlertRule:
        """
        Create a new alert rule.

        Args:
            name: Alert rule name
            criteria: Matching criteria dictionary
            notification_method: Notification method
            notification_target: Target for notifications
            user_id: User ID (optional)
            enabled: Whether rule is enabled

        Returns:
            Created AlertRule instance
        """
        rule = AlertRule(
            name=name,
            criteria=criteria,
            notification_method=notification_method,
            notification_target=notification_target,
            user_id=user_id,
            enabled=enabled,
        )

        self._rules[rule.rule_id] = rule
        self._save_rules()

        logger.info(f"Created alert rule: {rule.rule_id} - {rule.name}")
        return rule

    def get_rule(self, rule_id: str) -> Optional[AlertRule]:
        """
        Get alert rule by ID.

        Args:
            rule_id: Rule ID

        Returns:
            AlertRule instance or None if not found
        """
        return self._rules.get(rule_id)

    def get_all_rules(
        self, user_id: Optional[str] = None, enabled_only: bool = False
    ) -> List[AlertRule]:
        """
        Get all alert rules.

        Args:
            user_id: Filter by user ID (optional)
            enabled_only: Return only enabled rules

        Returns:
            List of AlertRule instances
        """
        rules = list(self._rules.values())

        if user_id:
            rules = [r for r in rules if r.user_id == user_id]

        if enabled_only:
            rules = [r for r in rules if r.enabled]

        return rules

    def update_rule(self, rule_id: str, **kwargs) -> Optional[AlertRule]:
        """
        Update alert rule.

        Args:
            rule_id: Rule ID
            **kwargs: Fields to update

        Returns:
            Updated AlertRule instance or None if not found
        """
        rule = self._rules.get(rule_id)
        if not rule:
            return None

        rule.update(**kwargs)
        self._save_rules()

        logger.info(f"Updated alert rule: {rule_id}")
        return rule

    def delete_rule(self, rule_id: str) -> bool:
        """
        Delete alert rule.

        Args:
            rule_id: Rule ID

        Returns:
            True if deleted, False if not found
        """
        if rule_id not in self._rules:
            return False

        del self._rules[rule_id]
        self._save_rules()

        logger.info(f"Deleted alert rule: {rule_id}")
        return True

    def enable_rule(self, rule_id: str) -> bool:
        """
        Enable alert rule.

        Args:
            rule_id: Rule ID

        Returns:
            True if enabled, False if not found
        """
        rule = self._rules.get(rule_id)
        if not rule:
            return False

        rule.enabled = True
        rule.updated_at = datetime.now()
        self._save_rules()

        logger.info(f"Enabled alert rule: {rule_id}")
        return True

    def disable_rule(self, rule_id: str) -> bool:
        """
        Disable alert rule.

        Args:
            rule_id: Rule ID

        Returns:
            True if disabled, False if not found
        """
        rule = self._rules.get(rule_id)
        if not rule:
            return False

        rule.enabled = False
        rule.updated_at = datetime.now()
        self._save_rules()

        logger.info(f"Disabled alert rule: {rule_id}")
        return True
