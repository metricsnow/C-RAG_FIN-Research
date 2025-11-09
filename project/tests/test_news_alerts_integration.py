"""
Integration tests for news alert system.
"""

import tempfile
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from app.alerts.alert_rules import AlertRuleManager
from app.alerts.news_alerts import NewsAlertSystem
from app.alerts.notifications import NotificationService


@pytest.fixture
def temp_storage():
    """Create temporary storage directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def sample_articles():
    """Create sample news articles for testing."""
    return [
        {
            "title": "Apple Reports Strong Quarterly Earnings",
            "content": "Apple Inc. reported strong quarterly earnings today, exceeding analyst expectations...",
            "url": "https://example.com/apple-earnings",
            "source": "reuters",
            "date": datetime.now().isoformat(),
            "author": "John Doe",
            "tickers": ["AAPL"],
            "category": "earnings",
        },
        {
            "title": "Microsoft Announces New Product",
            "content": "Microsoft Corporation announced a new product line today...",
            "url": "https://example.com/microsoft-product",
            "source": "cnbc",
            "date": datetime.now().isoformat(),
            "author": "Jane Smith",
            "tickers": ["MSFT"],
            "category": "general",
        },
        {
            "title": "Tech Stocks Rally on Market News",
            "content": "Technology stocks including Apple, Microsoft, and Google rallied today...",
            "url": "https://example.com/tech-rally",
            "source": "bloomberg",
            "date": datetime.now().isoformat(),
            "author": "Bob Johnson",
            "tickers": ["AAPL", "MSFT", "GOOGL"],
            "category": "markets",
        },
    ]


class TestNewsAlertSystemIntegration:
    """Integration tests for NewsAlertSystem."""

    @patch("app.alerts.notifications.NotificationService.send_alert_notification")
    def test_full_workflow_with_email(
        self, mock_send_notification, temp_storage, sample_articles
    ):
        """Test full alert workflow with email notifications."""
        mock_send_notification.return_value = True

        # Create alert system
        system = NewsAlertSystem(storage_path=temp_storage)

        # Create alert rules
        rule1 = system.rule_manager.create_rule(
            name="AAPL Earnings Alert",
            criteria={
                "tickers": ["AAPL"],
                "keywords": ["earnings"],
                "categories": ["earnings"],
                "logic": "AND",
            },
            notification_method="email",
            notification_target="user1@example.com",
        )

        rule2 = system.rule_manager.create_rule(
            name="Tech Stocks Alert",
            criteria={"tickers": ["AAPL", "MSFT", "GOOGL"], "logic": "OR"},
            notification_method="email",
            notification_target="user2@example.com",
        )

        # Check articles
        results = system.check_articles(sample_articles)

        # Verify results - all 3 articles matched at least one rule
        assert len(results) == 3  # All three articles matched
        assert "https://example.com/apple-earnings" in results
        assert "https://example.com/microsoft-product" in results
        assert "https://example.com/tech-rally" in results

        # Verify notifications were sent (at least 3, could be more if multiple rules match)
        assert mock_send_notification.call_count >= 3

    def test_rule_persistence_and_matching(self, temp_storage, sample_articles):
        """Test rule persistence and matching across system restarts."""
        # Create first system instance and add rule
        system1 = NewsAlertSystem(storage_path=temp_storage)
        rule = system1.rule_manager.create_rule(
            name="Persistent Rule",
            criteria={"tickers": ["AAPL"], "logic": "OR"},
        )

        # Create second system instance (simulates restart)
        system2 = NewsAlertSystem(storage_path=temp_storage)

        # Verify rule is loaded
        rules = system2.rule_manager.get_all_rules()
        assert len(rules) == 1
        assert rules[0].rule_id == rule.rule_id

        # Verify matching still works
        matching = system2.get_matching_rules(sample_articles[0])
        assert len(matching) == 1
        assert matching[0].rule_id == rule.rule_id

    def test_multiple_rules_multiple_articles(self, temp_storage, sample_articles):
        """Test multiple rules matching multiple articles."""
        system = NewsAlertSystem(storage_path=temp_storage)

        # Create multiple rules
        system.rule_manager.create_rule(
            name="AAPL Rule",
            criteria={"tickers": ["AAPL"], "logic": "OR"},
            notification_method="email",
            notification_target="user1@example.com",
        )

        system.rule_manager.create_rule(
            name="MSFT Rule",
            criteria={"tickers": ["MSFT"], "logic": "OR"},
            notification_method="email",
            notification_target="user2@example.com",
        )

        system.rule_manager.create_rule(
            name="Markets Rule",
            criteria={"categories": ["markets"], "logic": "OR"},
            notification_method="email",
            notification_target="user3@example.com",
        )

        # Check articles
        with patch.object(
            system.notification_service, "send_alert_notification", return_value=True
        ) as mock_send:
            results = system.check_articles(sample_articles)

            # Verify multiple matches
            assert len(results) == 3  # All three articles matched at least one rule
            assert mock_send.call_count >= 3

    def test_disabled_rules_not_matched(self, temp_storage, sample_articles):
        """Test that disabled rules don't match articles."""
        system = NewsAlertSystem(storage_path=temp_storage)

        # Create and disable rule
        rule = system.rule_manager.create_rule(
            name="Disabled Rule",
            criteria={"tickers": ["AAPL"], "logic": "OR"},
            enabled=True,
        )
        system.rule_manager.disable_rule(rule.rule_id)

        # Check articles
        matching = system.get_matching_rules(sample_articles[0])
        assert len(matching) == 0

    def test_and_logic_requires_all_criteria(self, temp_storage):
        """Test that AND logic requires all criteria to match."""
        system = NewsAlertSystem(storage_path=temp_storage)

        rule = system.rule_manager.create_rule(
            name="Strict Rule",
            criteria={
                "tickers": ["AAPL"],
                "categories": ["earnings"],
                "keywords": ["quarterly"],
                "logic": "AND",
            },
        )

        # Article matching all criteria
        article1 = {
            "title": "Apple Quarterly Earnings Report",
            "content": "Apple reported quarterly earnings...",
            "url": "https://example.com/1",
            "tickers": ["AAPL"],
            "category": "earnings",
        }
        assert system.match_article(article1, rule) is True

        # Article missing one criterion
        article2 = {
            "title": "Apple Market Update",
            "content": "Apple stock update...",
            "url": "https://example.com/2",
            "tickers": ["AAPL"],
            "category": "markets",  # Wrong category
        }
        assert system.match_article(article2, rule) is False

    def test_or_logic_requires_any_criteria(self, temp_storage):
        """Test that OR logic requires any criterion to match."""
        system = NewsAlertSystem(storage_path=temp_storage)

        rule = system.rule_manager.create_rule(
            name="Flexible Rule",
            criteria={
                "tickers": ["AAPL"],
                "categories": ["earnings"],
                "logic": "OR",
            },
        )

        # Article matching ticker
        article1 = {
            "title": "Apple News",
            "content": "Apple content...",
            "url": "https://example.com/1",
            "tickers": ["AAPL"],
            "category": "general",
        }
        assert system.match_article(article1, rule) is True

        # Article matching category
        article2 = {
            "title": "Earnings Report",
            "content": "Earnings content...",
            "url": "https://example.com/2",
            "tickers": [],
            "category": "earnings",
        }
        assert system.match_article(article2, rule) is True

        # Article matching neither
        article3 = {
            "title": "Other News",
            "content": "Other content...",
            "url": "https://example.com/3",
            "tickers": [],
            "category": "general",
        }
        assert system.match_article(article3, rule) is False
