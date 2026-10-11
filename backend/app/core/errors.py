"""Domain errors and their mapping to the uniform HTTP error envelope.

Every error response has the shape `{"error": {"code", "message", "details"}}`; the frontend
`ApiError` relies on it.
"""

import logging
from typing import Any, ClassVar

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


class AppError(Exception):
    status_code: ClassVar[int] = status.HTTP_400_BAD_REQUEST
    code: ClassVar[str] = "bad_request"
    default_message: ClassVar[str] = "Некорректный запрос"

    def __init__(self, message: str | None = None, *, details: Any = None) -> None:
        self.message = message or self.default_message
        self.details = details
        super().__init__(self.message)


class AuthenticationError(AppError):
    status_code = status.HTTP_401_UNAUTHORIZED
    code = "unauthorized"
    default_message = "Требуется авторизация"


class AccountBannedError(AppError):
    """The banlist matches this account. `details` carries reason and supportEmail."""

    status_code = status.HTTP_403_FORBIDDEN
    code = "account_banned"
    default_message = "Вы были забанены"


class PermissionDeniedError(AppError):
    status_code = status.HTTP_403_FORBIDDEN
    code = "forbidden"
    default_message = "Недостаточно прав"


class NotFoundError(AppError):
    status_code = status.HTTP_404_NOT_FOUND
    code = "not_found"
    default_message = "Объект не найден"


class ConflictError(AppError):
    status_code = status.HTTP_409_CONFLICT
    code = "conflict"
    default_message = "Конфликт данных"


class ServiceUnavailableError(AppError):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    code = "service_unavailable"
    default_message = "Сервис временно недоступен"


class EmailNotVerifiedError(AppError):
    """Password is correct, but the address still has to be confirmed with the emailed code."""

    status_code = status.HTTP_403_FORBIDDEN
    code = "email_not_verified"
    default_message = "Подтвердите почту: мы отправили 6-значный код"


class TooManyRequestsError(AppError):
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    code = "too_many_requests"
    default_message = "Слишком много запросов. Подождите немного."


class EmailDeliveryError(AppError):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    code = "email_delivery_failed"
    default_message = "Не удалось отправить письмо. Попробуйте ещё раз."


class NotImplementedYetError(AppError):
    """Marks documented API contracts whose business logic is not implemented yet."""

    status_code = status.HTTP_501_NOT_IMPLEMENTED
    code = "not_implemented"
    default_message = "Метод ещё не реализован"


def _envelope(status_code: int, code: str, message: str, details: Any = None) -> JSONResponse:
    body = {"error": {"code": code, "message": message, "details": jsonable_encoder(details)}}
    headers = (
        {"WWW-Authenticate": "Bearer"} if status_code == status.HTTP_401_UNAUTHORIZED else None
    )
    return JSONResponse(status_code=status_code, content=body, headers=headers)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error(_: Request, exc: AppError) -> JSONResponse:
        return _envelope(exc.status_code, exc.code, exc.message, exc.details)

    @app.exception_handler(RequestValidationError)
    async def _validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        return _envelope(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "validation_error",
            "Проверьте корректность данных",
            # `input` is dropped on purpose: it would echo passwords and other submitted data.
            [
                {"loc": list(error["loc"]), "msg": error["msg"], "type": error["type"]}
                for error in exc.errors()
            ],
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http_error(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        return _envelope(exc.status_code, f"http_{exc.status_code}", str(exc.detail))

    @app.exception_handler(Exception)
    async def _unhandled_error(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled error on %s %s", request.method, request.url.path, exc_info=exc)
        return _envelope(
            status.HTTP_500_INTERNAL_SERVER_ERROR, "internal_error", "Внутренняя ошибка сервера"
        )
