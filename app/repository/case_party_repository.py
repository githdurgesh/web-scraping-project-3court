from sqlalchemy import delete

from app.models.case_party import CaseParty


class CasePartyRepository:

    def __init__(self, session):
        self.session = session

    async def replace_parties(
        self,
        case_id: int,
        petitioners: list[str],
        respondents: list[str],
    ) -> None:

        # Existing parties remove
        await self.session.execute(
            delete(CaseParty).where(
                CaseParty.case_id == case_id
            )
        )

        # Petitioners
        for party_name in petitioners:

            party_name = party_name.strip()

            if not party_name:
                continue

            party = CaseParty(
                case_id=case_id,
                party_name=party_name,
                party_type="PETITIONER",
            )

            self.session.add(party)

        # Respondents
        for party_name in respondents:

            party_name = party_name.strip()

            if not party_name:
                continue

            party = CaseParty(
                case_id=case_id,
                party_name=party_name,
                party_type="RESPONDENT",
            )

            self.session.add(party)

        await self.session.flush()