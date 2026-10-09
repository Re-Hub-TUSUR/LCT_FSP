"""Tag descriptions for the OpenAPI spec and the live Swagger UI at `docs_url`.

FastAPI's default docs page loads `swagger-ui-dist` from a CDN and starts it with an inline
`<script>`; both are blocked by the API's default policy (`default-src 'none'` in
`app/core/headers.py`), which otherwise keeps the JSON API locked down — so the page stayed blank
in deployments that actually enforce it. The docs page gets its own, narrower policy instead of
loosening the one the rest of the API relies on; `app/api/routes/mock_fsp.py`'s sign-in page sets
its own policy the same way.
"""

from fastapi import FastAPI
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse

_SWAGGER_CDN = "https://cdn.jsdelivr.net"
# script/style: the CDN bundle plus FastAPI's inline init script and swagger-ui's injected
# styles — neither can be external without self-hosting swagger-ui-dist. connect-src: same-origin
# calls to `openapi_url` and to "Try it out". img-src covers icons swagger-ui draws as data URIs.
_DOCS_CSP = (
    "default-src 'none'; "
    f"script-src {_SWAGGER_CDN} 'unsafe-inline'; "
    f"style-src {_SWAGGER_CDN} 'unsafe-inline'; "
    "img-src 'self' data:; "
    "connect-src 'self'; "
    "frame-ancestors 'none'"
)

# Order here is the order Swagger UI groups operations in; it follows `app/api/router.py`.
TAGS_METADATA: list[dict[str, str]] = [
    {"name": "health", "description": "Живость и готовность сервиса."},
    {
        "name": "auth",
        "description": "Регистрация, вход, код подтверждения почты, повторная отправка, "
        "обновление и отзыв токена.",
    },
    {"name": "users", "description": "Текущий аккаунт."},
    {"name": "categories", "description": "Справочник специализаций и грейдов."},
    {
        "name": "candidates",
        "description": "Банк кандидатов: поиск, резюме, фильтры и сохранённые поиски, "
        "PDF-резюме, привязка и синхронизация ФСП.",
    },
    {"name": "fsp-id", "description": "Вход через FSP ID (OIDC + PKCE)."},
    {
        "name": "companies",
        "description": "Профиль компании, логотип, банк задач, тестовые задания, "
        "верификация IT-аккредитации.",
    },
    {
        "name": "vacancies",
        "description": "Вакансии: публичный список, свои вакансии, лента подбора для "
        "соискателя, реакции.",
    },
    {"name": "invitations", "description": "Приглашения кандидатов работодателем и ответ на них."},
    {
        "name": "applications",
        "description": "Заявки соискателя. Пока отвечает `501 not_implemented`.",
    },
    {
        "name": "matching",
        "description": "Подбор под потребность. Пока отвечает `501 not_implemented`.",
    },
    {
        "name": "calendar",
        "description": "Встречи: список за период, создание, перенос, отмена, подтверждение.",
    },
    {"name": "responses", "description": "Входящие лайки и ответный лайк."},
    {"name": "conversations", "description": "Чаты и вложения."},
    {
        "name": "notifications",
        "description": "Поток событий (Server-Sent Events): лайки, сообщения, решение по "
        "IT-аккредитации, новые результаты сохранённых поисков.",
    },
    {
        "name": "assessments",
        "description": "Тестирование на грейд: попытки, запуск кода, ИИ-собеседование, "
        "тестовые задания от работодателя.",
    },
    {
        "name": "ats",
        "description": "Подключение внешней ATS, опрос новых откликов и их автоматический "
        "скрининг. Банк кандидатов не меняет.",
    },
    {
        "name": "admin",
        "description": "Администрирование: пользователи, банк заданий, верификация компаний, "
        "аналитика.",
    },
    {
        "name": "mock-fsp",
        "description": "Эмуляция реалма FSP ID и реестра ФСП внутри API — подключается только "
        "при `FSP_ID_MODE=mock`.",
    },
]


def register_docs(app: FastAPI, *, docs_url: str, openapi_url: str) -> None:
    """Serves Swagger UI at `docs_url`, under a policy that allows only what it needs to run.

    Call with `docs_url=None` passed to `FastAPI(...)` instead of the built-in docs route, so
    this is the only route generating the page and the only one setting its policy.
    """

    @app.get(docs_url, include_in_schema=False)
    async def swagger_ui() -> HTMLResponse:
        response = get_swagger_ui_html(
            openapi_url=openapi_url,
            title=f"{app.title} — Swagger UI",
            # The default favicon is a cross-origin fetch the policy above has no reason to
            # allow; an empty URL resolves to this same page, which `img-src 'self'` already
            # permits, and the browser quietly discards it as not an image.
            swagger_favicon_url="",
            swagger_ui_parameters={"persistAuthorization": True},
        )
        response.headers["Content-Security-Policy"] = _DOCS_CSP
        return response
