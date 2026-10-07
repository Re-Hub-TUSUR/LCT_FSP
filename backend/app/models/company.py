import uuid

from sqlalchemy import ForeignKey, LargeBinary, String, Text, column, exists, table
from sqlalchemy.orm import Mapped, column_property, deferred, mapped_column

from app.db.base import Base, TimestampMixin

# The admin module owns the verification table; a light table clause keeps this model free of it.
_verifications = table("company_verifications", column("company_id"), column("status"))


class Company(TimestampMixin, Base):
    """Employer profile. MVP: one company per employer account."""

    __tablename__ = "companies"

    # Declared here, not via the mixin: `it_accredited` below refers to this column.
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True
    )
    name: Mapped[str] = mapped_column(String(200))
    industry: Mapped[str | None] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    city: Mapped[str | None] = mapped_column(String(100))
    # Headcount bucket, e.g. "201–500".
    size: Mapped[str | None] = mapped_column(String(16))
    website: Mapped[str | None] = mapped_column(String(500))
    contact_email: Mapped[str | None] = mapped_column(String(320))

    # Legal details. Entered by hand until the INN lookup is connected.
    inn: Mapped[str | None] = mapped_column(String(12), unique=True)
    ogrn: Mapped[str | None] = mapped_column(String(15))
    kpp: Mapped[str | None] = mapped_column(String(9))
    legal_address: Mapped[str | None] = mapped_column(String(500))

    # Deferred: lists must not pull the image bytes.
    logo: Mapped[bytes | None] = deferred(mapped_column(LargeBinary))
    logo_type: Mapped[str | None] = mapped_column(String(32))

    # An admin approved the Минцифры registry extract the company uploaded.
    it_accredited: Mapped[bool] = column_property(
        exists()
        .where(_verifications.c.company_id == id)
        .where(_verifications.c.status == "approved")
    )
