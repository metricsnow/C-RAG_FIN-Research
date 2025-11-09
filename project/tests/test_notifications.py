"""
Unit tests for notification service module.
"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, Mock, patch

import pytest

from app.alerts.notifications import NotificationError, NotificationService


class TestNotificationService:
    """Test NotificationService class."""

    def test_check_rate_limit_no_previous_notification(self):
        """Test rate limit check with no previous notification."""
        service = NotificationService(rate_limit_minutes=15)
        assert service._check_rate_limit("user@example.com") is True

    def test_check_rate_limit_within_limit(self):
        """Test rate limit check within rate limit window."""
        service = NotificationService(rate_limit_minutes=15)
        service._last_notification["user@example.com"] = datetime.now()
        assert service._check_rate_limit("user@example.com") is False

    def test_check_rate_limit_after_limit(self):
        """Test rate limit check after rate limit window."""
        service = NotificationService(rate_limit_minutes=15)
        service._last_notification["user@example.com"] = datetime.now() - timedelta(
            minutes=16
        )
        assert service._check_rate_limit("user@example.com") is True

    def test_update_rate_limit(self):
        """Test updating rate limit tracking."""
        service = NotificationService()
        service._update_rate_limit("user@example.com")
        assert "user@example.com" in service._last_notification

    @patch("smtplib.SMTP")
    def test_send_email_success(self, mock_smtp_class):
        """Test sending email successfully."""
        mock_smtp = MagicMock()
        mock_smtp_class.return_value.__enter__.return_value = mock_smtp

        service = NotificationService(
            smtp_server="smtp.example.com",
            smtp_port=587,
            smtp_username="user",
            smtp_password="pass",
            from_email="from@example.com",
        )

        result = service.send_email(
            to_email="to@example.com",
            subject="Test Subject",
            body="Test Body",
            bypass_rate_limit=True,
        )

        assert result is True
        mock_smtp.starttls.assert_called_once()
        mock_smtp.login.assert_called_once_with("user", "pass")
        mock_smtp.send_message.assert_called_once()

    @patch("smtplib.SMTP")
    def test_send_email_with_html(self, mock_smtp_class):
        """Test sending email with HTML body."""
        mock_smtp = MagicMock()
        mock_smtp_class.return_value.__enter__.return_value = mock_smtp

        service = NotificationService(
            smtp_server="smtp.example.com",
            from_email="from@example.com",
        )

        result = service.send_email(
            to_email="to@example.com",
            subject="Test Subject",
            body="Test Body",
            html_body="<html>Test HTML</html>",
            bypass_rate_limit=True,
        )

        assert result is True
        mock_smtp.send_message.assert_called_once()

    def test_send_email_missing_config(self):
        """Test sending email with missing configuration."""
        service = NotificationService()
        result = service.send_email(
            to_email="to@example.com",
            subject="Test",
            body="Test",
            bypass_rate_limit=True,
        )
        assert result is False

    @patch("smtplib.SMTP")
    def test_send_email_rate_limited(self, mock_smtp_class):
        """Test sending email when rate limited."""
        service = NotificationService(
            smtp_server="smtp.example.com",
            from_email="from@example.com",
            rate_limit_minutes=15,
        )
        service._last_notification["to@example.com"] = datetime.now()

        result = service.send_email(
            to_email="to@example.com",
            subject="Test",
            body="Test",
        )
        assert result is False
        mock_smtp_class.assert_not_called()

    @patch("smtplib.SMTP")
    def test_send_email_smtp_error(self, mock_smtp_class):
        """Test sending email with SMTP error."""
        mock_smtp = MagicMock()
        mock_smtp_class.return_value.__enter__.return_value = mock_smtp
        mock_smtp.send_message.side_effect = Exception("SMTP Error")

        service = NotificationService(
            smtp_server="smtp.example.com",
            from_email="from@example.com",
        )

        result = service.send_email(
            to_email="to@example.com",
            subject="Test",
            body="Test",
            bypass_rate_limit=True,
        )
        assert result is False

    @patch("smtplib.SMTP")
    def test_send_alert_notification(self, mock_smtp_class):
        """Test sending alert notification."""
        mock_smtp = MagicMock()
        mock_smtp_class.return_value.__enter__.return_value = mock_smtp

        service = NotificationService(
            smtp_server="smtp.example.com",
            from_email="from@example.com",
        )

        article = {
            "title": "Apple Reports Earnings",
            "content": "Apple reported strong earnings...",
            "url": "https://example.com/article",
            "source": "reuters",
            "date": datetime.now().isoformat(),
            "tickers": ["AAPL"],
            "category": "earnings",
            "summary": "Apple reported strong quarterly earnings",
        }

        result = service.send_alert_notification(
            to_email="user@example.com",
            rule_name="AAPL Earnings Alert",
            article=article,
            bypass_rate_limit=True,
        )

        assert result is True
        mock_smtp.send_message.assert_called_once()

    def test_get_rate_limit_status_no_previous(self):
        """Test getting rate limit status with no previous notification."""
        service = NotificationService()
        status = service.get_rate_limit_status("user@example.com")
        assert status is None

    def test_get_rate_limit_status_with_previous(self):
        """Test getting rate limit status with previous notification."""
        service = NotificationService(rate_limit_minutes=15)
        service._last_notification["user@example.com"] = datetime.now() - timedelta(
            minutes=5
        )

        status = service.get_rate_limit_status("user@example.com")
        assert status is not None
        assert status["can_send"] is False
        assert status["minutes_remaining"] > 0
