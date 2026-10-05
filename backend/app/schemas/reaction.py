import uuid
from datetime import datetime
from typing import Literal

from app.models.enums import ReactionKind
from app.schemas.common import ApiModel

# Which cards a feed returns: everything except hidden ones, only the ones not decided on yet
# (the swipe deck), or favourites.
FeedView = Literal["all", "unseen", "liked"]


class ReactionRequest(ApiModel):
    kind: ReactionKind


class CandidateReactionRequest(ReactionRequest):
    # The vacancy the recruiter is hiring for, to group favourites by vacancy later.
    vacancy_id: uuid.UUID | None = None


class ReactionRead(ApiModel):
    kind: ReactionKind
    updated_at: datetime
