from datetime import date, datetime

from sqlalchemy import Date, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class CourtCase(Base):

    __tablename__ = "court_cases"
    __table_args__ = {
        "schema": "webscrap_tables"
    }

    case_id: Mapped[int] = mapped_column(Integer,primary_key=True,autoincrement=True,)

    court: Mapped[str] = mapped_column(String(100),nullable=False,)

    cnr_number: Mapped[str | None] = mapped_column(String(100),unique=True,nullable=True,)

    case_number: Mapped[str | None] = mapped_column(String(100),nullable=True,)

    case_type: Mapped[str | None] = mapped_column(String(100),nullable=True,)

    filing_date: Mapped[date | None] = mapped_column(Date,nullable=True,)

    registration_date: Mapped[date | None] = mapped_column(Date,nullable=True,)

    status: Mapped[str | None] = mapped_column(String(100),nullable=True,)

    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True),server_default=func.now(),)

    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True),server_default=func.now(),onupdate=func.now(),)