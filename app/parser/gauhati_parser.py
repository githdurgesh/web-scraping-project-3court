from typing import Any, Dict, List, Optional


def _format_date(d: Optional[Any]) -> str:
    """Formats date strings like '23-07-2013' to ISO '2013-07-23' if applicable."""
    if not d:
        return ""
    d_str = str(d).strip()
    parts = d_str.split("-")
    if len(parts) == 3 and len(parts[0]) == 2 and len(parts[2]) == 4:
        return f"{parts[2]}-{parts[1]}-{parts[0]}"
    return d_str


class GauhatiParser:
    """
    Parser for Gauhati High Court case search JSON responses.
    Produces the standard 'Cases' structure with CaseDetails, PartyDetails, Advocates, etc.
    """

    def _build_case_item(
        self,
        item: Dict[str, Any],
        fallback_cnr: str = "",
    ) -> Dict[str, Any]:
        """
        Transforms a raw case record dictionary into the target structured case object.
        """
        cino = str(item.get("cino") or item.get("CNR") or fallback_cnr).strip()
        type_name = str(item.get("type_name") or item.get("CaseType") or "").strip()
        reg_no = item.get("reg_no") if item.get("reg_no") is not None else item.get("RegistrationNumber")
        reg_year = item.get("reg_year") if item.get("reg_year") is not None else item.get("RegistrationYear")
        pet_name = str(item.get("pet_name") or item.get("Petitioner") or "").strip()
        res_name = str(item.get("res_name") or item.get("Respondent") or "").strip()
        pet_adv = str(item.get("pet_adv") or item.get("PetitionerAdvocates") or "").strip()
        res_adv = str(item.get("res_adv") or item.get("RespondentAdvocates") or "").strip()
        dt_regis = item.get("dt_regis") or item.get("RegistrationDate")
        reg_date = _format_date(dt_regis)

        reg_no_str = str(reg_no).strip() if reg_no is not None else ""
        reg_year_str = str(reg_year).strip() if reg_year is not None else ""

        if reg_no_str and reg_year_str and reg_no_str != "0" and reg_year_str != "0":
            case_number = f"{type_name}/{reg_no_str}/{reg_year_str}"
        elif reg_no_str and reg_no_str != "0":
            case_number = f"{type_name}/{reg_no_str}"
        else:
            case_number = type_name or cino

        case_title = (
            f"{pet_name} v/s {res_name}"
            if pet_name and res_name
            else (pet_name or res_name)
        )

        # CaseDetails list
        existing_case_details = item.get("CaseDetails")
        if isinstance(existing_case_details, list) and existing_case_details:
            case_details = existing_case_details
        else:
            filling_no = str(
                item.get("FillingNumber")
                or item.get("filing_no")
                or item.get("Case_no")
                or ""
            )
            filling_date = _format_date(
                item.get("FillingDate") or item.get("filing_date") or ""
            )
            disposed_date = _format_date(
                item.get("DisposedDate") or item.get("disposed_date") or ""
            )
            case_status = str(
                item.get("CaseStatus")
                or item.get("case_status")
                or ("disposed" if disposed_date else "")
            )

            case_details = [
                {
                    "CNR": cino,
                    "CourtNumber": str(item.get("CourtNumber") or "0"),
                    "CaseNumber": case_number,
                    "FillingNumber": filling_no,
                    "Petitioner": pet_name,
                    "Respondent": res_name,
                    "FillingDate": filling_date,
                    "RegistrationDate": reg_date,
                    "Bench": item.get("Bench", None),
                    "BenchId": str(item.get("BenchId") or ""),
                    "MainCaseNumber": str(item.get("MainCaseNumber") or ""),
                    "MainMattercino": str(item.get("MainMattercino") or ""),
                    "Case_no": filling_no or case_number,
                    "NextHearingDate": item.get("NextHearingDate", None),
                    "DisposedDate": disposed_date,
                    "CaseStatus": case_status,
                    "PetitionerAdvocates": pet_adv,
                }
            ]

        # PartyDetails
        party_details = item.get("PartyDetails") or [
            {
                "Respondent": res_name,
                "Petitioner": pet_name,
            }
        ]

        # Advocates list
        existing_advocates = item.get("Advocates")
        if isinstance(existing_advocates, list) and existing_advocates:
            advocates = existing_advocates
        else:
            advocates = [a for a in [pet_adv, res_adv] if a]

        # Petitioners / Respondents lists
        petitioners = item.get("Petitioners") or ([pet_name] if pet_name else [])
        respondents = item.get("Respondents") or ([res_name] if res_name else [])

        filing_date = _format_date(
            item.get("FilingDate")
            or item.get("filing_date")
            or (case_details[0]["FillingDate"] if case_details else "")
        )
        case_status = str(
            item.get("CaseStatus")
            or item.get("case_status")
            or (case_details[0]["CaseStatus"] if case_details else "")
        )
        decision_date = _format_date(
            item.get("DecisionDate")
            or item.get("decision_date")
            or (case_details[0]["DisposedDate"] if case_details else "")
        )
        next_hearing_date = str(item.get("NextHearingDate") or "")

        return {
            "CNR": cino,
            "CaseNumber": case_number,
            "Case_Number": case_number,
            "CaseTitle": case_title,
            "CaseType": type_name,
            "CaseStatus": case_status,
            "RegistrationNumber": reg_no_str,
            "RegistrationYear": reg_year_str,
            "RegistrationDate": reg_date,
            "FilingDate": filing_date,
            "DecisionDate": decision_date,
            "NextHearingDate": next_hearing_date,
            "Petitioner": pet_name,
            "Respondent": res_name,
            "PetitionerAdvocates": pet_adv,
            "RespondentAdvocates": res_adv,
            "Advocates": advocates,
            "Petitioners": petitioners,
            "Respondents": respondents,
            "CaseDetails": case_details,
            "PartyDetails": party_details,
            "Orders": item.get("Orders") or [],
        }

    def parse_cnr_search(
        self,
        raw_records: List[Dict[str, Any]],
        cnr: str = "",
    ) -> Dict[str, Any]:
        """
        Parses CNR search response and returns {"Cases": [...]} matching the user's schema.
        """
        cases = [
            self._build_case_item(item, fallback_cnr=cnr)
            for item in raw_records
            if isinstance(item, dict)
        ]
        return {
            "Cases": cases,
        }

    def parse_party_search(
        self,
        raw_records: List[Dict[str, Any]],
        search_string: str = "",
    ) -> Dict[str, Any]:
        """
        Parses party search response and returns cases list for party search endpoint.
        """
        cases = [
            self._build_case_item(item)
            for item in raw_records
            if isinstance(item, dict)
        ]
        return {
            "Cases": cases,
            "total_count": len(cases),
            "count": len(cases),
            "search_string": search_string,
            "cases": cases,
        }

    def parse_case_number_search(
        self,
        raw_records: List[Dict[str, Any]],
        case_type: str = "",
        case_number: str = "",
        case_year: str = "",
    ) -> Dict[str, Any]:
        """
        Parses case number search response and returns {"Cases": [...]} matching standard structure.
        """
        cases = [
            self._build_case_item(item, fallback_cnr="")
            for item in raw_records
            if isinstance(item, dict)
        ]
        return {
            "Cases": cases,
        }

