"""Russian taxpayer number (ИНН) check digits. Until the INN lookup is connected this is the
only check a company's legal details get."""

ORGANISATION_LENGTH = 10
PERSON_LENGTH = 12
_TEN = (2, 4, 10, 3, 5, 9, 4, 6, 8)
_ELEVEN = (7, 2, 4, 10, 3, 5, 9, 4, 6, 8)
_TWELVE = (3, 7, 2, 4, 10, 3, 5, 9, 4, 6, 8)


def _check_digit(digits: list[int], weights: tuple[int, ...]) -> int:
    return sum(d * w for d, w in zip(digits, weights, strict=False)) % 11 % 10


def is_valid_inn(value: str) -> bool:
    """10 digits for an organisation, 12 for a sole trader, check digits must match."""
    if not value.isascii() or not value.isdigit():
        return False
    digits = [int(char) for char in value]
    if len(digits) == ORGANISATION_LENGTH:
        return _check_digit(digits, _TEN) == digits[9]
    if len(digits) == PERSON_LENGTH:
        return (
            _check_digit(digits, _ELEVEN) == digits[10]
            and _check_digit(digits, _TWELVE) == digits[11]
        )
    return False
