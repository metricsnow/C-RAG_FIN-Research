"""
Services module for background services and daemon processes.

This module contains services that run in the background to perform
automated tasks such as news monitoring, scheduled jobs, etc.
"""

from app.services.news_monitor import NewsMonitor, NewsMonitorError

__all__ = ["NewsMonitor", "NewsMonitorError"]
