"""
News alert system module.

Provides alert rule management, article matching, and notification capabilities
for financial news articles.
"""

from app.alerts.alert_rules import AlertRule, AlertRuleManager
from app.alerts.news_alerts import NewsAlertSystem
from app.alerts.notifications import NotificationService

__all__ = [
    "AlertRule",
    "AlertRuleManager",
    "NewsAlertSystem",
    "NotificationService",
]
