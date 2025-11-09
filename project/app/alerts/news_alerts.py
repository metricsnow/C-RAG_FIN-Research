"""
News alert system module.

Main module for matching news articles against alert rules and sending notifications.
"""

from typing import Dict, List, Optional

from app.alerts.alert_rules import AlertRule, AlertRuleManager
from app.alerts.notifications import NotificationService
from app.utils.config import config
from app.utils.logger import get_logger

logger = get_logger(__name__)


class NewsAlertSystemError(Exception):
    """Custom exception for news alert system errors."""

    pass


class NewsAlertSystem:
    """
    News alert system for matching articles and sending notifications.

    Matches news articles against alert rules and sends notifications
    when matches are found.
    """

    def __init__(
        self,
        rule_manager: Optional[AlertRuleManager] = None,
        notification_service: Optional[NotificationService] = None,
        storage_path: Optional[str] = None,
    ):
        """
        Initialize news alert system.

        Args:
            rule_manager: AlertRuleManager instance (auto-created if not provided)
            notification_service: NotificationService instance (auto-created if not provided)
            storage_path: Path for alert rules storage (default: from config)
        """
        storage_path = storage_path or config.news_alerts_storage_path
        self.rule_manager = rule_manager or AlertRuleManager(storage_path=storage_path)

        # Initialize notification service with config values
        if notification_service is None:
            self.notification_service = NotificationService(
                smtp_server=config.news_alerts_smtp_server,
                smtp_port=config.news_alerts_smtp_port,
                smtp_username=config.news_alerts_smtp_username,
                smtp_password=config.news_alerts_smtp_password,
                from_email=config.news_alerts_from_email,
                rate_limit_minutes=config.news_alerts_rate_limit_minutes,
            )
        else:
            self.notification_service = notification_service

    def match_article(self, article: Dict, rule: AlertRule) -> bool:
        """
        Match article against alert rule criteria.

        Args:
            article: Article dictionary with title, content, tickers, category, etc.
            rule: AlertRule instance

        Returns:
            True if article matches rule criteria, False otherwise
        """
        if not rule.enabled:
            return False

        criteria = rule.criteria
        logic = criteria.get("logic", "OR")

        # Extract article data
        title = article.get("title", "").lower()
        content = article.get("content", "").lower()
        article_text = f"{title} {content}"

        # Get article tickers (normalize to uppercase)
        article_tickers = [t.upper().strip() for t in article.get("tickers", []) if t]
        if isinstance(article.get("tickers"), str):
            # Handle comma-separated string
            article_tickers = [
                t.upper().strip()
                for t in article.get("tickers", "").split(",")
                if t.strip()
            ]

        # Get article category (normalize to lowercase)
        article_category = article.get("category", "").lower()

        # Check criteria
        rule_tickers = criteria.get("tickers", [])
        rule_keywords = criteria.get("keywords", [])
        rule_categories = criteria.get("categories", [])

        matches = []

        # Check ticker match
        if rule_tickers:
            ticker_match = any(ticker in article_tickers for ticker in rule_tickers)
            matches.append(("tickers", ticker_match))

        # Check keyword match
        if rule_keywords:
            keyword_match = any(keyword in article_text for keyword in rule_keywords)
            matches.append(("keywords", keyword_match))

        # Check category match
        if rule_categories:
            category_match = article_category in rule_categories
            matches.append(("categories", category_match))

        # Apply logic
        if logic == "AND":
            # All specified criteria must match
            return all(match[1] for match in matches) if matches else False
        else:
            # OR: At least one criterion must match
            return any(match[1] for match in matches) if matches else False

    def check_article(self, article: Dict) -> List[Dict]:
        """
        Check article against all active alert rules and send notifications.

        Args:
            article: Article dictionary

        Returns:
            List of matched alert rules (with notification status)
        """
        # Get all enabled rules
        rules = self.rule_manager.get_all_rules(enabled_only=True)

        if not rules:
            logger.debug("No active alert rules to check")
            return []

        matches = []

        for rule in rules:
            try:
                if self.match_article(article, rule):
                    logger.info(
                        f"Article matched alert rule: {rule.rule_id} - {rule.name}"
                    )

                    # Send notification
                    notification_sent = False
                    if rule.notification_method == "email" and rule.notification_target:
                        notification_sent = (
                            self.notification_service.send_alert_notification(
                                to_email=rule.notification_target,
                                rule_name=rule.name,
                                article=article,
                            )
                        )

                    matches.append(
                        {
                            "rule_id": rule.rule_id,
                            "rule_name": rule.name,
                            "notification_method": rule.notification_method,
                            "notification_target": rule.notification_target,
                            "notification_sent": notification_sent,
                        }
                    )
            except Exception as e:
                logger.error(
                    f"Error checking article against rule {rule.rule_id}: {str(e)}",
                    exc_info=True,
                )
                continue

        if matches:
            logger.info(f"Article matched {len(matches)} alert rule(s)")
        else:
            logger.debug("Article did not match any alert rules")

        return matches

    def check_articles(self, articles: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Check multiple articles against alert rules.

        Args:
            articles: List of article dictionaries

        Returns:
            Dictionary mapping article URLs to list of matched rules
        """
        results = {}

        for article in articles:
            url = article.get("url", "")
            if not url:
                logger.warning("Article missing URL, skipping alert check")
                continue

            matches = self.check_article(article)
            if matches:
                results[url] = matches

        logger.info(
            f"Checked {len(articles)} articles, {len(results)} matched alert rules"
        )
        return results

    def get_matching_rules(
        self, article: Dict, enabled_only: bool = True
    ) -> List[AlertRule]:
        """
        Get all alert rules that match an article (without sending notifications).

        Args:
            article: Article dictionary
            enabled_only: Return only enabled rules

        Returns:
            List of matching AlertRule instances
        """
        rules = self.rule_manager.get_all_rules(enabled_only=enabled_only)
        matching_rules = []

        for rule in rules:
            if self.match_article(article, rule):
                matching_rules.append(rule)

        return matching_rules
