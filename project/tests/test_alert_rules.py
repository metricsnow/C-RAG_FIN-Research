"""
Unit tests for alert rules management module.
"""

import json
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest

from app.alerts.alert_rules import AlertRule, AlertRuleError, AlertRuleManager


@pytest.fixture
def temp_storage():
    """Create temporary storage directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def sample_rule():
    """Create a sample alert rule."""
    return AlertRule(
        name="AAPL Earnings Alert",
        criteria={
            "tickers": ["AAPL"],
            "keywords": ["earnings", "quarterly"],
            "categories": ["earnings"],
            "logic": "AND",
        },
        notification_method="email",
        notification_target="user@example.com",
        user_id="user_123",
    )


class TestAlertRule:
    """Test AlertRule class."""

    def test_create_alert_rule(self, sample_rule):
        """Test creating an alert rule."""
        assert sample_rule.name == "AAPL Earnings Alert"
        assert sample_rule.criteria["tickers"] == ["AAPL"]
        assert sample_rule.criteria["keywords"] == ["earnings", "quarterly"]
        assert sample_rule.criteria["logic"] == "AND"
        assert sample_rule.enabled is True
        assert sample_rule.rule_id is not None

    def test_alert_rule_with_or_logic(self):
        """Test alert rule with OR logic."""
        rule = AlertRule(
            name="Tech Stocks Alert",
            criteria={
                "tickers": ["AAPL", "MSFT"],
                "logic": "OR",
            },
        )
        assert rule.criteria["logic"] == "OR"

    def test_alert_rule_validation_no_criteria(self):
        """Test alert rule validation fails with no criteria."""
        with pytest.raises(AlertRuleError, match="At least one criterion"):
            AlertRule(
                name="Empty Rule",
                criteria={},
            )

    def test_alert_rule_validation_invalid_logic(self):
        """Test alert rule validation fails with invalid logic."""
        with pytest.raises(AlertRuleError, match="Invalid logic"):
            AlertRule(
                name="Invalid Logic",
                criteria={"tickers": ["AAPL"], "logic": "XOR"},
            )

    def test_alert_rule_normalizes_tickers(self):
        """Test alert rule normalizes tickers to uppercase."""
        rule = AlertRule(
            name="Test",
            criteria={"tickers": ["aapl", "msft"]},
        )
        assert rule.criteria["tickers"] == ["AAPL", "MSFT"]

    def test_alert_rule_normalizes_keywords(self):
        """Test alert rule normalizes keywords to lowercase."""
        rule = AlertRule(
            name="Test",
            criteria={"keywords": ["EARNINGS", "REVENUE"]},
        )
        assert rule.criteria["keywords"] == ["earnings", "revenue"]

    def test_alert_rule_to_dict(self, sample_rule):
        """Test converting alert rule to dictionary."""
        data = sample_rule.to_dict()
        assert data["name"] == "AAPL Earnings Alert"
        assert data["rule_id"] == sample_rule.rule_id
        assert "created_at" in data
        assert "updated_at" in data

    def test_alert_rule_from_dict(self, sample_rule):
        """Test creating alert rule from dictionary."""
        data = sample_rule.to_dict()
        rule = AlertRule.from_dict(data)
        assert rule.name == sample_rule.name
        assert rule.rule_id == sample_rule.rule_id
        assert rule.criteria == sample_rule.criteria

    def test_alert_rule_update(self, sample_rule):
        """Test updating alert rule."""
        original_updated = sample_rule.updated_at
        sample_rule.update(name="Updated Name", enabled=False)
        assert sample_rule.name == "Updated Name"
        assert sample_rule.enabled is False
        assert sample_rule.updated_at > original_updated

    def test_alert_rule_update_validates_criteria(self, sample_rule):
        """Test updating criteria validates new criteria."""
        with pytest.raises(AlertRuleError):
            sample_rule.update(criteria={})


class TestAlertRuleManager:
    """Test AlertRuleManager class."""

    def test_create_rule_manager(self, temp_storage):
        """Test creating alert rule manager."""
        manager = AlertRuleManager(storage_path=temp_storage)
        assert manager.storage_path == Path(temp_storage)
        assert len(manager.get_all_rules()) == 0

    def test_create_rule(self, temp_storage):
        """Test creating a new alert rule."""
        manager = AlertRuleManager(storage_path=temp_storage)
        rule = manager.create_rule(
            name="Test Rule",
            criteria={"tickers": ["AAPL"]},
            notification_method="email",
            notification_target="test@example.com",
        )
        assert rule.name == "Test Rule"
        assert rule.rule_id is not None

        # Verify rule is saved
        rules = manager.get_all_rules()
        assert len(rules) == 1
        assert rules[0].rule_id == rule.rule_id

    def test_get_rule(self, temp_storage):
        """Test getting alert rule by ID."""
        manager = AlertRuleManager(storage_path=temp_storage)
        rule = manager.create_rule(
            name="Test Rule",
            criteria={"tickers": ["AAPL"]},
        )
        retrieved = manager.get_rule(rule.rule_id)
        assert retrieved is not None
        assert retrieved.rule_id == rule.rule_id

    def test_get_rule_not_found(self, temp_storage):
        """Test getting non-existent rule."""
        manager = AlertRuleManager(storage_path=temp_storage)
        rule = manager.get_rule("nonexistent")
        assert rule is None

    def test_get_all_rules(self, temp_storage):
        """Test getting all alert rules."""
        manager = AlertRuleManager(storage_path=temp_storage)
        rule1 = manager.create_rule(
            name="Rule 1",
            criteria={"tickers": ["AAPL"]},
            user_id="user_1",
        )
        rule2 = manager.create_rule(
            name="Rule 2",
            criteria={"tickers": ["MSFT"]},
            user_id="user_2",
        )
        rule3 = manager.create_rule(
            name="Rule 3",
            criteria={"tickers": ["GOOGL"]},
            user_id="user_1",
            enabled=False,
        )

        all_rules = manager.get_all_rules()
        assert len(all_rules) == 3

        # Filter by user
        user1_rules = manager.get_all_rules(user_id="user_1")
        assert len(user1_rules) == 2

        # Filter enabled only
        enabled_rules = manager.get_all_rules(enabled_only=True)
        assert len(enabled_rules) == 2

    def test_update_rule(self, temp_storage):
        """Test updating alert rule."""
        manager = AlertRuleManager(storage_path=temp_storage)
        rule = manager.create_rule(
            name="Original Name",
            criteria={"tickers": ["AAPL"]},
        )
        updated = manager.update_rule(rule.rule_id, name="Updated Name", enabled=False)
        assert updated is not None
        assert updated.name == "Updated Name"
        assert updated.enabled is False

    def test_delete_rule(self, temp_storage):
        """Test deleting alert rule."""
        manager = AlertRuleManager(storage_path=temp_storage)
        rule = manager.create_rule(
            name="Test Rule",
            criteria={"tickers": ["AAPL"]},
        )
        deleted = manager.delete_rule(rule.rule_id)
        assert deleted is True
        assert manager.get_rule(rule.rule_id) is None

    def test_enable_disable_rule(self, temp_storage):
        """Test enabling and disabling alert rule."""
        manager = AlertRuleManager(storage_path=temp_storage)
        rule = manager.create_rule(
            name="Test Rule",
            criteria={"tickers": ["AAPL"]},
            enabled=True,
        )
        assert rule.enabled is True

        manager.disable_rule(rule.rule_id)
        rule = manager.get_rule(rule.rule_id)
        assert rule.enabled is False

        manager.enable_rule(rule.rule_id)
        rule = manager.get_rule(rule.rule_id)
        assert rule.enabled is True

    def test_persistence(self, temp_storage):
        """Test alert rules persistence across manager instances."""
        # Create manager and add rule
        manager1 = AlertRuleManager(storage_path=temp_storage)
        rule = manager1.create_rule(
            name="Persistent Rule",
            criteria={"tickers": ["AAPL"]},
        )

        # Create new manager instance (simulates restart)
        manager2 = AlertRuleManager(storage_path=temp_storage)
        rules = manager2.get_all_rules()
        assert len(rules) == 1
        assert rules[0].name == "Persistent Rule"
        assert rules[0].rule_id == rule.rule_id
