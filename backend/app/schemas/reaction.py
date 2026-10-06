import uuid
from datetime import datetime
from typing import Literal

from app.models.enums import ReactionKind
from app.schemas.common import ApiModel

# Which cards a feed returns:
# - `all`: everything except skipped cards; `unseen`: only the ones not decided on (swipe deck);
# - `liked` / `skipped`: what the user decided, the latest decision first;
# - `matched`: liked cards whose other side liked the user back.
FeedView = Literal["all", "unseen", "liked", "matched", "skipped"]


class ReactionCounts(ApiModel):
    """How many cards the user has in each list of their own decisions."""

    liked: int
    matched: int
    skipped: int


class ReactionRequest(ApiModel):
    kind: ReactionKind


class CandidateReactionRequest(ReactionRequest):
    # The vacancy the recruiter is hiring for, to group favourites by vacancy later.
    vacancy_id: uuid.UUID | None = None


class ReactionRead(ApiModel):
    kind: ReactionKind
    updated_at: datetime
