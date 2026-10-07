from app.schemas.common import ApiModel


class OptionCount(ApiModel):
    """A filter option and how many results the list would have after choosing it."""

    value: str
    count: int
