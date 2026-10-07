from sqlalchemy import select

from app.models.court_case import CourtCase


class CourtCaseRepository:

    def __init__(self, session):
        self.session = session

    async def get_by_cnr(
        self,
        cnr_number: str,
    ) -> CourtCase | None:

        result = await self.session.execute(
            select(CourtCase).where(
                CourtCase.cnr_number == cnr_number
            )
        )

        return result.scalar_one_or_none()

    async def get_by_case_number(
        self,
        case_number: str,
    ) -> CourtCase | None:

        result = await self.session.execute(
            select(CourtCase).where(
                CourtCase.case_number == case_number
            )
        )

        return result.scalar_one_or_none()

    async def create(
        self,
        **data,
    ) -> CourtCase:

        case = CourtCase(**data)

        self.session.add(case)

        await self.session.flush()

        return case

    async def update(
        self,
        case: CourtCase,
        **data,
    ) -> CourtCase:

        for key, value in data.items():
            setattr(case, key, value)

        await self.session.flush()

        return case