from typing import NoReturn

from app.core.errors import NotImplementedYetError


def not_implemented(operation: str) -> NoReturn:
    """Endpoint contract (path, schemas, auth) is final; the business logic is a later milestone."""
    raise NotImplementedYetError(
        f"{operation}: ещё не реализовано", details={"operation": operation}
    )
