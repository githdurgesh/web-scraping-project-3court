import re

from app.repository.case_party_repository import CasePartyRepository
from app.repository.court_case_repository import CourtCaseRepository
from app.utils.date_utils import parse_date


CNR_PATTERN = re.compile(r"^[A-Z]{4}\d{12}$")

GUJARAT_HIGH_COURT = "Gujarat High Court"


class CaseService:

    def __init__(self, session):

        self.session = session

        self.case_repository = CourtCaseRepository(
            session
        )

        self.party_repository = CasePartyRepository(
            session
        )

    async def save_case(
        self,
        response: dict,
    ):

        obj_message = response.get(
            "objMessage",
            {}
        )

        common = obj_message.get(
            "CommonCaseDetails",
            {}
        )

        main_details_list = obj_message.get(
            "mainDetails",
            []
        )

        main_details = (
            main_details_list[0]
            if main_details_list
            else {}
        )

        # --------------------------------
        # CNR
        # --------------------------------

        cnr = (
            common.get("CNR")
            or main_details.get("CNR")
            or ""
        )

        cnr = str(cnr).strip()

        # Fake case-number-search identifier
        # ko CNR ke roop mein save nahi karna
        if not CNR_PATTERN.fullmatch(cnr):
            cnr = None

        # --------------------------------
        # Case Number
        # --------------------------------

        case_number = (
            common.get("CaseNumber")
            or main_details.get("CaseNumber")
            or None
        )

        case_number = (
            str(case_number).strip()
            if case_number
            else None
        )

        # --------------------------------
        # Case Type
        # --------------------------------

        case_type = (
            main_details.get("CasetypeDescription")
            or None
        )

        if case_type:
            case_type = str(case_type).strip()

        # --------------------------------
        # Dates
        # --------------------------------

        filing_date = parse_date(
            common.get("FillingDate")
        )

        registration_date = parse_date(
            main_details.get("RegistrationDate")
        )

        # --------------------------------
        # Status
        # --------------------------------

        status = (
            common.get("CaseStatus")
            or main_details.get("CaseStatus")
            or None
        )

        if status:
            status = str(status).strip()

        # --------------------------------
        # Find existing case
        # --------------------------------

        case = None

        if cnr:
            case = await self.case_repository.get_by_cnr(
                cnr
            )

        # Fallback only when CNR is not available
        if case is None and case_number:
            case = await self.case_repository.get_by_case_number(
                case_number
            )

        # --------------------------------
        # Save / Update
        # --------------------------------

        case_data = {
            "court": GUJARAT_HIGH_COURT,
            "cnr_number": cnr,
            "case_number": case_number,
            "case_type": case_type,
            "filing_date": filing_date,
            "registration_date": registration_date,
            "status": status,
        }

        if case is None:

            case = await self.case_repository.create(
                **case_data
            )

        else:

            case = await self.case_repository.update(
                case,
                **case_data
            )

        # --------------------------------
        # Parties
        # --------------------------------

        petitioners = common.get(
            "Petitioner",
            []
        )

        respondents = common.get(
            "Respondent",
            []
        )

        await self.party_repository.replace_parties(
            case_id=case.case_id,
            petitioners=petitioners,
            respondents=respondents,
        )

        # --------------------------------
        # Commit
        # --------------------------------

        await self.session.commit()

        return case