"""Transactional email via Resend.

Plug-in point: set `RESEND_API_KEY` and `RESEND_FROM` (a verified sender). With an empty key the
message is not sent — development logs the code, production fails the request.
"""

import asyncio
import json
import logging
import urllib.error
import urllib.request
from typing import Protocol

from app.core.config import Settings
from app.core.errors import EmailDeliveryError

logger = logging.getLogger(__name__)

RESEND_URL = "https://api.resend.com/emails"
CODE_TTL_MINUTES = 15


class EmailSender(Protocol):
    async def send_verification_code(self, *, to: str, code: str) -> None: ...


class ResendEmailSender:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def send_verification_code(self, *, to: str, code: str) -> None:
        api_key = self._settings.resend_api_key.get_secret_value().strip()
        if not api_key:
            if self._settings.is_production:
                raise EmailDeliveryError("RESEND_API_KEY не задан")
            # The code stays out of production logs. Locally it is the only way to finish signup
            # before the Resend key is connected.
            if self._settings.app_env == "development":
                logger.warning("RESEND_API_KEY is empty; verification code for %s: %s", to, code)
            else:
                logger.warning("RESEND_API_KEY is empty; verification email to %s was not sent", to)
            return

        payload: dict[str, object] = {
            "from": self._settings.resend_from,
            "to": [to],
            "subject": "Код подтверждения — КАДРЫ",
            "html": render_verification_email(to=to, code=code),
        }
        try:
            await asyncio.to_thread(_post_resend, api_key, payload)
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            logger.error("Resend rejected the email (%s): %s", exc.code, body)
            raise EmailDeliveryError() from exc
        except urllib.error.URLError as exc:
            logger.error("Resend is unreachable: %s", exc.reason)
            raise EmailDeliveryError() from exc


def render_verification_email(*, to: str, code: str) -> str:
    """Layout mirrors a code-in-a-card letter: greeting, the 6 digits, expiry, footer."""
    local_part = to.split("@", 1)[0]
    digits = " ".join(code)
    card = "max-width:560px;margin:0 auto;background:#ffffff;border-radius:12px;"
    mark = (
        "display:inline-block;width:56px;height:56px;line-height:56px;"
        "border-radius:12px;background:#ece9ff;color:#402fff;font-weight:700;"
    )
    return (
        '<!DOCTYPE html><html lang="ru"><body style="margin:0;padding:32px 16px;'
        'background:#f4f4f5;font-family:Helvetica,Arial,sans-serif;color:#1b1c21;">'
        f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="{card}">'
        '<tr><td style="padding:40px 36px 8px;text-align:center;">'
        f'<div style="{mark}">КД</div>'
        '<h1 style="margin:20px 0 0;font-size:28px;font-weight:700;">Добро пожаловать в КАДРЫ</h1>'
        "</td></tr>"
        '<tr><td style="padding:24px 36px;font-size:16px;line-height:1.5;color:#3f3f46;">'
        f'<p style="margin:0 0 12px;">Здравствуйте, {local_part}.</p>'
        '<p style="margin:0;">Спасибо за регистрацию. Введите код, чтобы подтвердить почту:</p>'
        "</td></tr>"
        '<tr><td style="padding:0 36px 8px;">'
        '<div style="background:#f4f4f5;border-radius:12px;padding:24px;text-align:center;">'
        '<div style="color:#402fff;font-size:12px;letter-spacing:0.16em;font-weight:700;">'
        "ВАШ КОД ПОДТВЕРЖДЕНИЯ</div>"
        '<div style="margin-top:12px;font-size:36px;font-weight:700;'
        f'letter-spacing:0.28em;">{digits}</div></div></td></tr>'
        '<tr><td style="padding:16px 36px 28px;font-size:15px;line-height:1.5;color:#3f3f46;">'
        f'<p style="margin:0;">Код действует <strong style="color:#402fff;">'
        f"{CODE_TTL_MINUTES} минут</strong>.</p>"
        '<p style="margin:8px 0 0;">Если вы не создавали аккаунт, проигнорируйте письмо.</p>'
        "</td></tr>"
        '<tr><td style="padding:0 36px 32px;font-size:13px;color:#71717a;text-align:center;">'
        "Это автоматическое сообщение, отвечать на него не нужно."
        "</td></tr></table></body></html>"
    )


def _post_resend(api_key: str, payload: dict[str, object]) -> None:
    request = urllib.request.Request(
        RESEND_URL,
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "kadry-backend",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=10) as response:  # noqa: S310
        response.read()
