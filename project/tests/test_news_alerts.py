"""
Unit tests for news alert system module.
"""

from datetime import datetime
from unittest.mock import MagicMock, Mock, patch

import pytest

from app.alerts.alert_rules import AlertRule, AlertRuleManager
from app.alerts.news_alerts import NewsAlertSystem
from app.alerts.notifications import NotificationService


@pytest.fixture
def mock_rule_manager():
    """Create a mock AlertRuleManager."""
    return Mock(spec=AlertRuleManager)


@pytest.fixture
def mock_notification_service():
    """Create a mock NotificationService."""
    return Mock(spec=NotificationService)


@pytest.fixture
def sample_article():
    """Create a sample news article."""
    return {
        "title": "Apple Reports Strong Earnings",
        "content": "Apple Inc. reported strong quarterly earnings today...",
        "url": "https://example.com/article1",
        "source": "reuters",
        "date": datetime.now().isoformat(),
        "author": "John Doe",
        "tickers": ["AAPL"],
        "category": "earnings",
    }


@pytest.fixture
def sample_rule():
    """Create a sample alert rule."""
    return AlertRule(
        name="AAPL Earnings Alert",
        criteria={
            "tickers": ["AAPL"],
            "keywords": ["earnings"],
            "categories": ["earnings"],
            "logic": "AND",
        },
        notification_method="email",
        notification_target="user@example.com",
    )


class TestNewsAlertSystem:
    """Test NewsAlertSystem class."""

    def test_match_article_ticker_match(self, sample_article, sample_rule):
        """Test article matching with ticker criteria."""
        system = NewsAlertSystem()
        assert system.match_article(sample_article, sample_rule) is True

    def test_match_article_ticker_no_match(self, sample_article):
        """Test article matching with no ticker match."""
        rule = AlertRule(
            name="MSFT Alert",
            criteria={"tickers": ["MSFT"], "logic": "OR"},
        )
        system = NewsAlertSystem()
        assert system.match_article(sample_article, rule) is False

    def test_match_article_keyword_match(self):
        """Test article matching with keyword criteria."""
        article = {
            "title": "Tech Company Reports Earnings",
            "content": "The company reported strong earnings this quarter...",
            "tickers": [],
            "category": "general",
        }
        rule = AlertRule(
            name="Earnings Keyword Alert",
            criteria={"keywords": ["earnings"], "logic": "OR"},
        )
        system = NewsAlertSystem()
        assert system.match_article(article, rule) is True

    def test_match_article_category_match(self, sample_article):
        """Test article matching with category criteria."""
        rule = AlertRule(
            name="Earnings Category Alert",
            criteria={"categories": ["earnings"], "logic": "OR"},
        )
        system = NewsAlertSystem()
        assert system.match_article(sample_article, rule) is True

    def test_match_article_and_logic(self):
        """Test article matching with AND logic."""
        article = {
            "title": "Apple Reports Earnings",
            "content": "Apple reported strong earnings this quarter...",
            "tickers": ["AAPL"],
            "category": "earnings",
        }
        rule = AlertRule(
            name="AAPL Earnings AND Alert",
            criteria={
                "tickers": ["AAPL"],
                "keywords": ["earnings"],
                "categories": ["earnings"],
                "logic": "AND",
            },
        )
        system = NewsAlertSystem()
        assert system.match_article(article, rule) is True

    def test_match_article_and_logic_partial_match(self):
        """Test article matching with AND logic - partial match fails."""
        article = {
            "title": "Apple Reports Revenue",
            "content": "Apple reported strong revenue...",
            "tickers": ["AAPL"],
            "category": "markets",  # Wrong category
        }
        rule = AlertRule(
            name="AAPL Earnings AND Alert",
            criteria={
                "tickers": ["AAPL"],
                "categories": ["earnings"],
                "logic": "AND",
            },
        )
        system = NewsAlertSystem()
        assert system.match_article(article, rule) is False

    def test_match_article_or_logic(self):
        """Test article matching with OR logic."""
        article = {
            "title": "Tech News",
            "content": "General tech news article...",
            "tickers": ["MSFT"],
            "category": "general",
        }
        rule = AlertRule(
            name="AAPL or MSFT Alert",
            criteria={"tickers": ["AAPL", "MSFT"], "logic": "OR"},
        )
        system = NewsAlertSystem()
        assert system.match_article(article, rule) is True

    def test_match_article_disabled_rule(self, sample_article, sample_rule):
        """Test that disabled rules don't match."""
        sample_rule.enabled = False
        system = NewsAlertSystem()
        assert system.match_article(sample_article, sample_rule) is False

    def test_check_article_sends_notification(
        self, sample_article, mock_rule_manager, mock_notification_service
    ):
        """Test checking article sends notification when matched."""
        rule = AlertRule(
            name="Test Rule",
            criteria={"tickers": ["AAPL"], "logic": "OR"},
            notification_method="email",
            notification_target="user@example.com",
        )
        mock_rule_manager.get_all_rules.return_value = [rule]
        mock_notification_service.send_alert_notification.return_value = True

        system = NewsAlertSystem(
            rule_manager=mock_rule_manager,
            notification_service=mock_notification_service,
        )

        matches = system.check_article(sample_article)
        assert len(matches) == 1
        assert matches[0]["rule_id"] == rule.rule_id
        assert matches[0]["notification_sent"] is True
        mock_notification_service.send_alert_notification.assert_called_once()

    def test_check_article_no_match(
        self, sample_article, mock_rule_manager, mock_notification_service
    ):
        """Test checking article with no match."""
        rule = AlertRule(
            name="MSFT Rule",
            criteria={"tickers": ["MSFT"], "logic": "OR"},
        )
        mock_rule_manager.get_all_rules.return_value = [rule]

        system = NewsAlertSystem(
            rule_manager=mock_rule_manager,
            notification_service=mock_notification_service,
        )

        matches = system.check_article(sample_article)
        assert len(matches) == 0
        mock_notification_service.send_alert_notification.assert_not_called()

    def test_check_articles_multiple(
        self, mock_rule_manager, mock_notification_service
    ):
        """Test checking multiple articles."""
        rule = AlertRule(
            name="AAPL Rule",
            criteria={"tickers": ["AAPL"], "logic": "OR"},
            notification_method="email",
            notification_target="user@example.com",
        )
        mock_rule_manager.get_all_rules.return_value = [rule]
        mock_notification_service.send_alert_notification.return_value = True

        articles = [
            {
                "title": "Apple News",
                "content": "Apple content...",
                "url": "https://example.com/1",
                "tickers": ["AAPL"],
                "category": "general",
            },
            {
                "title": "Microsoft News",
                "content": "Microsoft content...",
                "url": "https://example.com/2",
                "tickers": ["MSFT"],
                "category": "general",
            },
        ]

        system = NewsAlertSystem(
            rule_manager=mock_rule_manager,
            notification_service=mock_notification_service,
        )

        results = system.check_articles(articles)
        assert len(results) == 1
        assert "https://example.com/1" in results
        assert mock_notification_service.send_alert_notification.call_count == 1

    def test_get_matching_rules(self, sample_article, mock_rule_manager):
        """Test getting matching rules without sending notifications."""
        rule1 = AlertRule(
            name="AAPL Rule",
            criteria={"tickers": ["AAPL"], "logic": "OR"},
        )
        rule2 = AlertRule(
            name="MSFT Rule",
            criteria={"tickers": ["MSFT"], "logic": "OR"},
        )
        mock_rule_manager.get_all_rules.return_value = [rule1, rule2]

        system = NewsAlertSystem(rule_manager=mock_rule_manager)
        matching = system.get_matching_rules(sample_article)
        assert len(matching) == 1
        assert matching[0].rule_id == rule1.rule_id
