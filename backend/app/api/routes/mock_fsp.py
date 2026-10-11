"""Emulated FSP ID realm (Keycloak paths) and FSP registry. Mounted only with `FSP_ID_MODE=mock`.

The sign-in page stands in for the federation's login form: it lets the demo pick a participant
and returns the browser to the platform with an authorization code, as Keycloak would.
"""

import html
import re
from typing import Annotated, Any, Final
from urllib.parse import urlencode, urlsplit

from fastapi import APIRouter, Form, Header
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response

from app.core.config import Settings
from app.dependencies.common import SettingsDep
from app.integrations.fsp import mock
from app.integrations.fsp.provider import MEMBER_CLAIM, SCOPES, FspIdError, redirect_allowed
from app.integrations.fsp.registry import FspRegistryError
from app.integrations.fsp.schemas import FspMemberRecord
from app.models.enums import FspOutcome

REALM_PATH: Final = "/mock/fsp-id/realms/fsp"
_OIDC: Final = f"{REALM_PATH}/protocol/openid-connect"
# Absolute: a relative action breaks after a failed login, when the browser is already on /confirm.
_CONFIRM: Final = f"/api/v1{_OIDC}/auth/confirm"
_MEMBER_ID: Final = re.compile(r"^[A-Za-z0-9._-]{1,64}$")
_OUTCOME_LABELS: Final = {
    FspOutcome.WINNER: "победитель",
    FspOutcome.PRIZEWINNER: "призёр",
    FspOutcome.FINALIST: "финалист",
    FspOutcome.PARTICIPANT: "участник",
}

router = APIRouter(tags=["mock-fsp"], include_in_schema=True)


@router.get(
    f"{REALM_PATH}/.well-known/openid-configuration",
    summary="Mock FSP ID: OIDC discovery document",
)
async def discovery(settings: SettingsDep) -> dict[str, Any]:
    issuer = settings.fsp_id_issuer.rstrip("/")
    endpoints = f"{issuer}/protocol/openid-connect"
    return {
        "issuer": issuer,
        "authorization_endpoint": f"{endpoints}/auth",
        "token_endpoint": f"{endpoints}/token",
        "userinfo_endpoint": f"{endpoints}/userinfo",
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code"],
        "code_challenge_methods_supported": ["S256"],
        "scopes_supported": SCOPES.split(),
        "claims_supported": ["sub", "name", MEMBER_CLAIM],
        "id_token_signing_alg_values_supported": ["HS256"],
    }


@router.get(f"{_OIDC}/auth", summary="Mock FSP ID: sign-in page", response_class=HTMLResponse)
async def authorize(
    *,
    settings: SettingsDep,
    client_id: str,
    redirect_uri: str,
    state: str,
    nonce: str,
    code_challenge: str,
    response_type: str = "code",
    code_challenge_method: str = "S256",
    scope: str = "openid",
) -> Response:
    problem = _request_problem(settings, client_id, redirect_uri)
    if problem is None and (response_type != "code" or code_challenge_method != "S256"):
        problem = "Поддерживается только response_type=code с PKCE S256"
    if problem is None and "openid" not in scope.split():
        problem = "Нужен scope openid"
    if problem is not None:
        return _page(settings, "Ошибка входа", f"<p>{html.escape(problem)}</p>", status=400)
    hidden = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "state": state,
        "nonce": nonce,
        "code_challenge": code_challenge,
    }
    return _page(
        settings,
        "Вход через ФСП ID",
        _sign_in_form(hidden),
        redirect_uri=redirect_uri,
    )


@router.get(f"{_OIDC}/auth/confirm", summary="Mock FSP ID: the participant signed in")
async def confirm(
    *,
    settings: SettingsDep,
    client_id: str,
    redirect_uri: str,
    state: str,
    nonce: str,
    code_challenge: str,
    member: str = "",
    custom: str = "",
    login: str = "",
    password: str = "",
    action: str = "allow",
) -> Response:
    return _finish_sign_in(
        settings,
        client_id=client_id,
        redirect_uri=redirect_uri,
        state=state,
        nonce=nonce,
        code_challenge=code_challenge,
        member=member,
        custom=custom,
        login=login,
        password=password,
        action=action,
    )


@router.post(f"{_OIDC}/auth/confirm", summary="Mock FSP ID: sign in with a demo login")
async def confirm_login(
    *,
    settings: SettingsDep,
    client_id: Annotated[str, Form()],
    redirect_uri: Annotated[str, Form()],
    state: Annotated[str, Form()],
    nonce: Annotated[str, Form()],
    code_challenge: Annotated[str, Form()],
    login: Annotated[str, Form()] = "",
    password: Annotated[str, Form()] = "",
    custom: Annotated[str, Form()] = "",
    action: Annotated[str, Form()] = "allow",
) -> Response:
    return _finish_sign_in(
        settings,
        client_id=client_id,
        redirect_uri=redirect_uri,
        state=state,
        nonce=nonce,
        code_challenge=code_challenge,
        member="",
        custom=custom,
        login=login,
        password=password,
        action=action,
    )


def _finish_sign_in(
    settings: Settings,
    *,
    client_id: str,
    redirect_uri: str,
    state: str,
    nonce: str,
    code_challenge: str,
    member: str,
    custom: str,
    login: str,
    password: str,
    action: str,
) -> Response:
    hidden = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "state": state,
        "nonce": nonce,
        "code_challenge": code_challenge,
    }
    problem = _request_problem(settings, client_id, redirect_uri)
    if problem is not None:
        return _page(settings, "Ошибка входа", f"<p>{html.escape(problem)}</p>", status=400)
    if action != "allow":
        return _back(redirect_uri, {"error": "access_denied", "state": state})
    member_id, failure = _resolve_member(login, password, member, custom)
    if member_id is None:
        status = 401 if failure == "Неверный логин или пароль" else 400
        return _page(
            settings, "Вход через ФСП ID", _sign_in_form(hidden, failure or ""), status=status
        )
    code = mock.issue_code(
        settings,
        member_id=member_id,
        client_id=client_id,
        redirect_uri=redirect_uri,
        code_challenge=code_challenge,
        nonce=nonce,
    )
    return _back(redirect_uri, {"code": code, "state": state})


def _resolve_member(
    login: str, password: str, member: str, custom: str
) -> tuple[str | None, str | None]:
    """A demo login, or an explicit participant id from the old query form."""
    if login.strip() or password:
        account = mock.account_by_login(login)
        if account is None or not mock.password_matches(password, account.password):
            return None, "Неверный логин или пароль"
        return account.member_id, None
    member_id = custom.strip() or member.strip()
    if not member_id:
        return None, "Введите логин и пароль"
    if not _MEMBER_ID.fullmatch(member_id):
        return None, "ID участника: латиница, цифры, точка, дефис, до 64 символов."
    return member_id, None


@router.post(f"{_OIDC}/token", summary="Mock FSP ID: exchange the code for tokens")
async def token(
    *,
    settings: SettingsDep,
    grant_type: Annotated[str, Form()],
    code: Annotated[str, Form()],
    redirect_uri: Annotated[str, Form()],
    client_id: Annotated[str, Form()],
    code_verifier: Annotated[str, Form()],
    client_secret: Annotated[str, Form()] = "",
) -> JSONResponse:
    if grant_type != "authorization_code":
        return _oauth_error("unsupported_grant_type", "Only authorization_code is emulated")
    if client_id != settings.fsp_id_client_id:
        return _oauth_error("invalid_client", "Unknown client", status=401)
    try:
        tokens = mock.redeem_code(
            settings,
            code=code,
            client_id=client_id,
            redirect_uri=redirect_uri,
            code_verifier=code_verifier,
        )
    except FspIdError as exc:
        return _oauth_error("invalid_grant", exc.message)
    return JSONResponse(tokens, headers={"Cache-Control": "no-store"})


@router.get(f"{_OIDC}/userinfo", summary="Mock FSP ID: claims of the access token")
async def read_userinfo(
    settings: SettingsDep, authorization: Annotated[str, Header()] = ""
) -> JSONResponse:
    scheme, _, value = authorization.partition(" ")
    if scheme.lower() != "bearer" or not value:
        return _oauth_error("invalid_token", "Bearer token required", status=401)
    try:
        return JSONResponse(mock.userinfo(settings, value))
    except FspIdError as exc:
        return _oauth_error("invalid_token", exc.message, status=401)


@router.get(
    "/mock/fsp-registry/members/{member_id}",
    summary="Mock FSP registry: a participant's achievements and sport titles",
)
async def read_member(member_id: str) -> JSONResponse:
    try:
        record = mock.member_record(member_id)
    except FspRegistryError as exc:
        return JSONResponse({"error": exc.message}, status_code=503)
    return JSONResponse(record.model_dump(mode="json", by_alias=True))


def _request_problem(settings: Settings, client_id: str, redirect_uri: str) -> str | None:
    if client_id != settings.fsp_id_client_id:
        return "Неизвестное приложение"
    if not redirect_allowed(settings, redirect_uri):
        return "Адрес возврата не зарегистрирован для приложения"
    return None


def _back(redirect_uri: str, params: dict[str, str]) -> RedirectResponse:
    separator = "&" if urlsplit(redirect_uri).query else "?"
    return RedirectResponse(f"{redirect_uri}{separator}{urlencode(params)}", status_code=302)


def _oauth_error(error: str, description: str, *, status: int = 400) -> JSONResponse:
    return JSONResponse({"error": error, "error_description": description}, status_code=status)


def _summary(record: FspMemberRecord) -> str:
    if not record.achievements:
        return "нет истории в ФСП"
    best = min(record.achievements, key=lambda item: list(FspOutcome).index(item.result))
    count = len(record.achievements)
    titles = f", званий: {len(record.titles)}" if record.titles else ""
    best_text = f"{_OUTCOME_LABELS[best.result]}, {best.event_name}"
    return f"результатов: {count}{titles}; лучший — {best_text}"


def _describe(member_id: str) -> str:
    if member_id == mock.REGISTRY_DOWN_ID:
        return "реестр не отвечает — проверка ошибки синхронизации"
    try:
        return _summary(mock.member_record(member_id))
    except FspRegistryError:  # pragma: no cover - only REGISTRY_DOWN_ID fails
        return "реестр не отвечает"


def _sign_in_form(hidden: dict[str, str], error: str = "") -> str:
    fields = "".join(
        f'<input type="hidden" name="{name}" value="{html.escape(value)}">'
        for name, value in hidden.items()
    )
    banner = f'<p class="error" role="alert">{html.escape(error)}</p>' if error else ""
    accounts = "".join(
        "<tr><td><code>"
        f"{html.escape(account.login)}</code></td><td>{html.escape(account.name)}</td>"
        f"<td><code>{html.escape(account.member_id)}</code></td>"
        f"<td>{html.escape(_describe(account.member_id))}</td></tr>"
        for account in mock.DEMO_ACCOUNTS
    )
    return (
        "<p>Демо-режим: это вход Keycloak ФСП ID. "
        "Платформа получит номер участника и результаты из реестра.</p>"
        f"{banner}"
        f'<form method="post" action="{_CONFIRM}">{fields}'
        '<label class="custom">Логин <input name="login" autocomplete="username"></label>'
        '<label class="custom">Пароль <input name="password" type="password" '
        'autocomplete="current-password"></label>'
        '<label class="custom">Или ID участника без пароля '
        '<input name="custom" maxlength="64" placeholder="FSP-123456"></label>'
        '<div class="actions"><button name="action" value="allow">Войти</button>'
        '<button name="action" value="deny" class="secondary">Отмена</button></div></form>'
        f"<p>Пароль у всех аккаунтов: <code>{html.escape(mock.DEMO_PASSWORD)}</code></p>"
        "<table><thead><tr><th>Логин</th><th>Имя</th><th>ID</th><th>Реестр</th></tr></thead>"
        f"<tbody>{accounts}</tbody></table>"
    )


_STYLE: Final = (
    "body{font:16px/1.5 system-ui,sans-serif;background:#0b1020;color:#e8ecf5;margin:0;"
    "display:grid;place-items:center;min-height:100vh}"
    "main{max-width:720px;padding:32px;background:#141b31;border-radius:16px}"
    "h1{font-size:22px;margin:0 0 12px}.custom{display:block;margin:10px 0}"
    "input{display:block;width:100%;box-sizing:border-box;margin-top:6px;padding:8px;"
    "border-radius:8px;border:1px solid #3a4566;background:#0b1020;color:inherit}"
    ".error{color:#ffb4b4}.actions{display:flex;gap:12px;margin-top:20px}"
    "button{padding:10px 18px;border:0;border-radius:8px;background:#3b6cff;color:#fff;"
    "font:inherit;cursor:pointer}button.secondary{background:#2a334d}"
    "table{width:100%;border-collapse:collapse;font-size:14px;margin-top:8px}"
    "th,td{text-align:left;padding:6px 8px 6px 0;vertical-align:top}"
    "code{font-family:ui-monospace,monospace}"
)


def _page(
    settings: Settings,
    title: str,
    body: str,
    *,
    status: int = 200,
    redirect_uri: str | None = None,
) -> HTMLResponse:
    targets = ["'self'"]
    if redirect_uri:
        parts = urlsplit(redirect_uri)
        targets.append(f"{parts.scheme}://{parts.netloc}")
    csp = (
        "default-src 'none'; style-src 'unsafe-inline'; "
        f"form-action {' '.join(targets)}; frame-ancestors 'none'"
    )
    document = (
        '<!doctype html><html lang="ru"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>{html.escape(title)}</title><style>{_STYLE}</style></head>"
        f"<body><main><h1>{html.escape(title)}</h1>{body}"
        f"<p><small>Реалм {html.escape(settings.fsp_id_issuer)}</small></p></main></body></html>"
    )
    return HTMLResponse(document, status_code=status, headers={"Content-Security-Policy": csp})
