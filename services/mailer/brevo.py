"""
Brevo (formerly Sendinblue) transactional email client.

Uses the HTTP API directly via httpx so we don't pull in the sib-api SDK.
Reads BREVO_API_KEY, BREVO_SENDER_EMAIL, BREVO_SENDER_NAME from Settings.
"""
# Email HTML template lines are intentionally long.
# ruff: noqa: E501

from __future__ import annotations

import contextlib
from dataclasses import dataclass

import httpx

from backend.app.core.config import settings
from backend.app.core.logging import get_logger

log = get_logger("mailer.brevo")

BREVO_SEND_URL = "https://api.brevo.com/v3/smtp/email"


class MailerError(RuntimeError):
    pass


class MailerNotConfiguredError(MailerError):
    pass


@dataclass
class BrevoMailer:
    api_key: str
    sender_email: str
    sender_name: str
    timeout: float = 10.0

    @classmethod
    def from_settings(cls) -> BrevoMailer:
        if not settings.brevo_api_key or not settings.brevo_sender_email:
            raise MailerNotConfiguredError(
                "BREVO_API_KEY and BREVO_SENDER_EMAIL must be set to send mail."
            )
        return cls(
            api_key=settings.brevo_api_key,
            sender_email=settings.brevo_sender_email,
            sender_name=settings.brevo_sender_name or "CVPilot",
        )

    def send(
        self,
        *,
        to_email: str,
        to_name: str | None,
        subject: str,
        html: str,
        text: str | None = None,
    ) -> str:
        payload: dict = {
            "sender": {"email": self.sender_email, "name": self.sender_name},
            "to": [{"email": to_email, **({"name": to_name} if to_name else {})}],
            "subject": subject,
            "htmlContent": html,
        }
        if text:
            payload["textContent"] = text

        headers = {
            "api-key": self.api_key,
            "content-type": "application/json",
            "accept": "application/json",
        }

        try:
            resp = httpx.post(
                BREVO_SEND_URL, json=payload, headers=headers, timeout=self.timeout
            )
        except httpx.HTTPError as exc:
            log.error("brevo_request_failed", error=str(exc))
            raise MailerError("Failed to reach Brevo.") from exc

        if resp.status_code >= 400:
            log.error(
                "brevo_send_failed",
                status=resp.status_code,
                body=resp.text[:500],
                to=to_email,
            )
            raise MailerError(f"Brevo returned {resp.status_code}.")

        message_id = ""
        with contextlib.suppress(ValueError):
            message_id = resp.json().get("messageId", "")
        log.info("brevo_sent", to=to_email, message_id=message_id)
        return message_id


def _reset_email_html(name: str | None, reset_url: str, ttl_min: int) -> str:
    greeting = f"Hi {name}," if name else "Hi,"
    return f"""\
<!doctype html>
<html>
  <body style="font-family:Inter,Arial,sans-serif;background:#efece4;padding:32px;color:#1c1c17;">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:520px;margin:0 auto;background:#fcf9f1;border-radius:16px;border:1px solid #cdc5bc;">
      <tr><td style="padding:32px;">
        <h1 style="font-family:'Literata',Georgia,serif;font-weight:700;font-size:24px;margin:0 0 12px;">Reset your CVPilot password</h1>
        <p style="font-size:15px;line-height:1.55;margin:0 0 20px;">{greeting}</p>
        <p style="font-size:15px;line-height:1.55;margin:0 0 24px;">
          We received a request to reset the password on your CVPilot account.
          Click the button below to choose a new one. This link expires in {ttl_min} minutes.
        </p>
        <p style="margin:0 0 28px;">
          <a href="{reset_url}" style="display:inline-block;background:#1c1c17;color:#fff;text-decoration:none;font-weight:600;padding:12px 22px;border-radius:10px;font-size:15px;">Reset password</a>
        </p>
        <p style="font-size:13px;color:#4b463f;line-height:1.55;margin:0 0 8px;">
          If the button doesn't work, paste this URL into your browser:
        </p>
        <p style="font-size:12px;word-break:break-all;color:#4b463f;margin:0 0 24px;">{reset_url}</p>
        <hr style="border:none;border-top:1px solid #cdc5bc;margin:24px 0;">
        <p style="font-size:12px;color:#7c766e;line-height:1.55;margin:0;">
          If you didn't request this, you can ignore this email — your password won't change.
        </p>
      </td></tr>
    </table>
  </body>
</html>
"""


def _reset_email_text(name: str | None, reset_url: str, ttl_min: int) -> str:
    greeting = f"Hi {name}," if name else "Hi,"
    return (
        f"{greeting}\n\n"
        "We received a request to reset the password on your CVPilot account.\n"
        f"Open this link to choose a new one (expires in {ttl_min} minutes):\n\n"
        f"{reset_url}\n\n"
        "If you didn't request this, you can ignore this email — your password won't change.\n"
    )


def send_password_reset_email(
    *,
    to_email: str,
    to_name: str | None,
    reset_url: str,
    ttl_min: int,
    mailer: BrevoMailer | None = None,
) -> str:
    """Send the password-reset email. Returns the Brevo messageId."""
    m = mailer or BrevoMailer.from_settings()
    return m.send(
        to_email=to_email,
        to_name=to_name,
        subject="Reset your CVPilot password",
        html=_reset_email_html(to_name, reset_url, ttl_min),
        text=_reset_email_text(to_name, reset_url, ttl_min),
    )
