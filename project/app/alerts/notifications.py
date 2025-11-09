"""
Notification system for news alerts.

Handles email notifications and rate limiting to prevent spam.
"""

import smtplib
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, List, Optional

from app.utils.logger import get_logger

logger = get_logger(__name__)


class NotificationError(Exception):
    """Custom exception for notification errors."""

    pass


class NotificationService:
    """
    Notification service for sending alerts.

    Supports email notifications with rate limiting to prevent spam.
    """

    def __init__(
        self,
        smtp_server: Optional[str] = None,
        smtp_port: int = 587,
        smtp_username: Optional[str] = None,
        smtp_password: Optional[str] = None,
        from_email: Optional[str] = None,
        rate_limit_minutes: int = 15,
    ):
        """
        Initialize notification service.

        Args:
            smtp_server: SMTP server address (default: from config)
            smtp_port: SMTP server port (default: 587)
            smtp_username: SMTP username (default: from config)
            smtp_password: SMTP password (default: from config)
            from_email: From email address (default: from config)
            rate_limit_minutes: Rate limit in minutes between notifications
                to same recipient (default: 15)
        """
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.smtp_username = smtp_username
        self.smtp_password = smtp_password
        self.from_email = from_email
        self.rate_limit_minutes = rate_limit_minutes

        # Track last notification time per recipient
        self._last_notification: Dict[str, datetime] = {}

    def _check_rate_limit(self, recipient: str) -> bool:
        """
        Check if notification can be sent (rate limit check).

        Args:
            recipient: Notification recipient

        Returns:
            True if notification can be sent, False if rate limited
        """
        if recipient not in self._last_notification:
            return True

        last_time = self._last_notification[recipient]
        time_since = datetime.now() - last_time

        if time_since < timedelta(minutes=self.rate_limit_minutes):
            logger.debug(
                f"Rate limit: {recipient} notified {time_since.total_seconds():.0f}s ago"
            )
            return False

        return True

    def _update_rate_limit(self, recipient: str) -> None:
        """
        Update rate limit tracking for recipient.

        Args:
            recipient: Notification recipient
        """
        self._last_notification[recipient] = datetime.now()

    def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        bypass_rate_limit: bool = False,
    ) -> bool:
        """
        Send email notification.

        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Plain text email body
            html_body: HTML email body (optional)
            bypass_rate_limit: Bypass rate limiting (for testing)

        Returns:
            True if sent successfully, False otherwise
        """
        # Check rate limit
        if not bypass_rate_limit and not self._check_rate_limit(to_email):
            logger.warning(
                f"Rate limit: Skipping email to {to_email} "
                f"(last notification < {self.rate_limit_minutes} minutes ago)"
            )
            return False

        # Validate email configuration
        if not self.smtp_server or not self.from_email:
            logger.error(
                "Email configuration incomplete: smtp_server and from_email required"
            )
            return False

        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["From"] = self.from_email
            msg["To"] = to_email
            msg["Subject"] = subject

            # Add plain text part
            text_part = MIMEText(body, "plain")
            msg.attach(text_part)

            # Add HTML part if provided
            if html_body:
                html_part = MIMEText(html_body, "html")
                msg.attach(html_part)

            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.smtp_username and self.smtp_password:
                    server.starttls()
                    server.login(self.smtp_username, self.smtp_password)

                server.send_message(msg)

            # Update rate limit tracking
            self._update_rate_limit(to_email)

            logger.info(f"Email notification sent to {to_email}: {subject}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}", exc_info=True)
            return False

    def send_alert_notification(
        self,
        to_email: str,
        rule_name: str,
        article: Dict,
        bypass_rate_limit: bool = False,
    ) -> bool:
        """
        Send alert notification for matched article.

        Args:
            to_email: Recipient email address
            rule_name: Alert rule name
            article: Article dictionary with title, url, content, etc.
            bypass_rate_limit: Bypass rate limiting (for testing)

        Returns:
            True if sent successfully, False otherwise
        """
        # Extract article information
        title = article.get("title", "Untitled Article")
        url = article.get("url", "")
        source = article.get("source", "Unknown")
        date = article.get("date", "")
        tickers = article.get("tickers", [])
        category = article.get("category", "general")
        summary = article.get("summary", "")

        # Format date
        if date:
            try:
                if isinstance(date, str):
                    date_obj = datetime.fromisoformat(date.replace("Z", "+00:00"))
                else:
                    date_obj = date
                date_str = date_obj.strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                date_str = str(date)
        else:
            date_str = "Unknown date"

        # Create subject
        subject = f"News Alert: {rule_name} - {title[:60]}"

        # Create plain text body
        body = f"""News Alert: {rule_name}

Article Title: {title}
Source: {source}
Date: {date_str}
Category: {category}
"""

        if tickers:
            body += f"Tickers: {', '.join(tickers)}\n"

        if summary:
            body += f"\nSummary:\n{summary}\n"
        else:
            # Use first 300 characters of content as preview
            content = article.get("content", "")
            if content:
                preview = content[:300] + "..." if len(content) > 300 else content
                body += f"\nPreview:\n{preview}\n"

        body += f"\nRead full article: {url}\n"

        # Create HTML body
        html_body = f"""
        <html>
        <body>
            <h2>News Alert: {rule_name}</h2>
            <h3>{title}</h3>
            <p><strong>Source:</strong> {source}</p>
            <p><strong>Date:</strong> {date_str}</p>
            <p><strong>Category:</strong> {category}</p>
        """

        if tickers:
            html_body += f'<p><strong>Tickers:</strong> {", ".join(tickers)}</p>\n'

        if summary:
            html_body += f"<p><strong>Summary:</strong><br>{summary}</p>\n"
        else:
            content = article.get("content", "")
            if content:
                preview = content[:300] + "..." if len(content) > 300 else content
                html_body += f"<p><strong>Preview:</strong><br>{preview}</p>\n"

        html_body += f'<p><a href="{url}">Read full article</a></p>\n'
        html_body += """
        </body>
        </html>
        """

        return self.send_email(
            to_email=to_email,
            subject=subject,
            body=body,
            html_body=html_body,
            bypass_rate_limit=bypass_rate_limit,
        )

    def get_rate_limit_status(self, recipient: str) -> Optional[Dict]:
        """
        Get rate limit status for recipient.

        Args:
            recipient: Notification recipient

        Returns:
            Dictionary with rate limit status or None if no previous notification
        """
        if recipient not in self._last_notification:
            return None

        last_time = self._last_notification[recipient]
        time_since = datetime.now() - last_time
        minutes_remaining = max(
            0, self.rate_limit_minutes - time_since.total_seconds() / 60
        )

        return {
            "last_notification": last_time.isoformat(),
            "minutes_remaining": round(minutes_remaining, 1),
            "can_send": minutes_remaining == 0,
        }
