from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class CaseParty(Base):

    __tablename__ = "case_parties"
    __table_args__ = {
        "schema": "webscrap_tables"
    }

    case_party_id: Mapped[int] = mapped_column(Integer,primary_key=True,autoincrement=True,)

    case_id: Mapped[int] = mapped_column(Integer,ForeignKey("webscrap_tables.court_cases.case_id",ondelete="CASCADE",),nullable=False,)

    party_name: Mapped[str] = mapped_column(Text,nullable=False,)

    party_type: Mapped[str | None] = mapped_column( String(30),nullable=True,)

    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True),server_default=func.now(),)