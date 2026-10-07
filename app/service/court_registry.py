from typing import Any, Callable, Dict, List, Optional
from fastapi import HTTPException
import httpx

from app.scraper.gujarat_scraper import GujaratScraper
from app.scraper.patna_scraper import PatnaScraper
from app.scraper.gauhati_scraper import GauhatiScraper


# =============================================================================
# Court Dispatcher Handlers
# =============================================================================

async def _handle_gujarat_party_search(
    party_name: str,
    start_year: Optional[str] = None,
    end_year: Optional[str] = None,
    hearing_date: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Handler for Gujarat High Court party / litigant search.
    """
    from_yr = start_year.strip() if start_year and start_year.strip() else "2020"
    to_yr = end_year.strip() if end_year and end_year.strip() else "2026"

    scraper = GujaratScraper()
    result = await scraper.search_by_litigant(
        search_string=party_name,
        from_year=from_yr,
        to_year=to_yr,
    )
    cases_raw = result.get("cases", [])
    output = []
    for case in cases_raw:
        output.append({
            "CNR": case.get("CNR") or "",
            "CaseNumber": case.get("CaseNumber") or "",
            "CaseStatus": case.get("CaseStatus") or "",
            "LITIGANTNAME": case.get("LITIGANTNAME") or "",
            "HearingDate": case.get("HearingDate") or "",
            "LITIGANT TYPE": case.get("LITIGANT TYPE") or "",
            "DISTRICTNAME": case.get("DISTRICTNAME") or "",
        })
    return output


async def _handle_patna_party_search(
    party_name: str,
    start_year: Optional[str] = None,
    end_year: Optional[str] = None,
    hearing_date: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Handler for Patna High Court Case Search by party name.
    Target endpoint: https://patnahighcourt.gov.in/casesearch/name
    Returns rich case information: CNR, token_no, CaseNumber, Petitioner, Respondent, FilingDate, etc.
    """
    scraper = PatnaScraper()
    result = await scraper.search_by_party_name(
        party_name=party_name,
        start_year=start_year,
        end_year=end_year,
        hearing_date=hearing_date,
    )
    cases_raw = result.get("cases", [])

    output = []
    for case in cases_raw:
        output.append({
            "sr_no": case.get("sr_no", ""),
            "token_no": case.get("token_no", ""),
            "CaseNumber": case.get("case_number") or case.get("token_no", ""),
            "CNR": case.get("CNR") or "",
            "LITIGANTNAME": case.get("party_name", ""),
            "Petitioner": case.get("petitioner", ""),
            "Respondent": case.get("respondent", ""),
            "FilingDate": case.get("filing_date", ""),
            "PetitionerAdvocate": case.get("petitioner_advocate", ""),
            "cino": case.get("cino", ""),
            "CaseStatusUrl": case.get("case_status_url", ""),
            "Year": case.get("year", ""),
        })
    return output


async def _handle_gauhati_party_search(
    party_name: str,
    start_year: Optional[str] = None,
    end_year: Optional[str] = None,
    hearing_date: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Handler for Gauhati High Court Case Search by party name (subCourtId='24', courtId='2').
    Target endpoint: https://ghcservices.assam.gov.in/casestatus/getrecord.php
    """
    scraper = GauhatiScraper()
    result = await scraper.search_by_party_name(
        party_name=party_name,
        start_year=start_year,
        end_year=end_year,
    )
    cases_raw = result.get("cases", [])
    output = []
    for case in cases_raw:
        output.append({
            "CNR": case.get("CNR") or "",
            "CaseNumber": case.get("CaseNumber") or "",
            "CaseType": case.get("CaseType", ""),
            "RegistrationNumber": case.get("RegistrationNumber", ""),
            "RegistrationYear": case.get("RegistrationYear", ""),
            "LITIGANTNAME": case.get("CaseTitle", ""),
            "Petitioner": case.get("Petitioner", ""),
            "Respondent": case.get("Respondent", ""),
            "PetitionerAdvocate": case.get("PetitionerAdvocates", ""),
            "RespondentAdvocate": case.get("RespondentAdvocates", ""),
            "RegistrationDate": case.get("RegistrationDate", ""),
            "FilingDate": case.get("FilingDate", ""),
            "CaseStatus": case.get("CaseStatus", ""),
        })
    return output


async def _handle_gujarat_cnr_search(cnr: str) -> Any:
    """
    Handler for Gujarat High Court CNR search.
    """
    scraper = GujaratScraper()
    return await scraper.search_by_cnr(cnr=cnr)


async def _handle_patna_cnr_search(cnr: str) -> Any:
    """
    Handler for Patna High Court CNR search.
    """
    scraper = PatnaScraper()
    return await scraper.search_by_cnr(cnr=cnr)


async def _handle_gauhati_cnr_search(cnr: str) -> Any:
    """
    Handler for Gauhati High Court CNR search (subCourtId='24', courtId='2').
    Target endpoint: https://ghcservices.assam.gov.in/casestatus/getrecord.php
    """
    scraper = GauhatiScraper()
    return await scraper.search_by_cnr(cnr=cnr)


async def _handle_gujarat_case_number_search(
    case_type: str,
    case_number: str,
    case_year: str,
    side: Optional[str] = "R",
) -> Any:
    """
    Handler for Gujarat High Court case number search.
    """
    scraper = GujaratScraper()
    return await scraper.search_by_case_number(
        side=side or "R",
        case_type=case_type,
        case_number=case_number,
        case_year=case_year,
    )


async def _handle_patna_case_number_search(
    case_type: str,
    case_number: str,
    case_year: str,
    side: Optional[str] = "CR",
) -> Any:
    """
    Handler for Patna High Court case number search.
    """
    scraper = PatnaScraper()
    return await scraper.search_by_case_number(
        case_type=case_type,
        case_number=case_number,
        case_year=case_year,
        side=side or "CR",
    )


async def _handle_gauhati_case_number_search(
    case_type: str,
    case_number: str,
    case_year: str,
    side: Optional[str] = None,
) -> Any:
    """
    Handler for Gauhati High Court case number search (subCourtId='24', courtId='2').
    Target endpoint: https://ghcservices.assam.gov.in/casestatus/getrecord.php
    """
    scraper = GauhatiScraper()
    return await scraper.search_by_case_number(
        case_type=case_type,
        case_number=case_number,
        case_year=case_year,
        side=side,
    )


# =============================================================================
# Court Registry: subCourtId -> Court Configuration & Handlers
# Kal agar koi naya court add karna ho (e.g. Bombay, Delhi), bas yahan entry add karein!
# =============================================================================
COURT_REGISTRY: Dict[str, Dict[str, Any]] = {
    "20": {
        "court_name": "Gujarat High Court",
        "default_court_id": "2",
        "supported_court_ids": {"2"},
        "party_search_handler": _handle_gujarat_party_search,
        "cnr_search_handler": _handle_gujarat_cnr_search,
        "case_number_search_handler": _handle_gujarat_case_number_search,
        "supports_cnr": True,
        "supports_case_number": True,
    },
    "22": {
        "court_name": "Patna High Court",
        "default_court_id": "2",
        "supported_court_ids": {"2"},
        "party_search_handler": _handle_patna_party_search,
        "cnr_search_handler": _handle_patna_cnr_search,
        "case_number_search_handler": _handle_patna_case_number_search,
        "supports_cnr": True,
        "supports_case_number": True,
    },
    "24": {
        "court_name": "Gauhati High Court",
        "default_court_id": "2",
        "supported_court_ids": {"2"},
        "party_search_handler": _handle_gauhati_party_search,
        "cnr_search_handler": _handle_gauhati_cnr_search,
        "case_number_search_handler": _handle_gauhati_case_number_search,
        "supports_cnr": True,
        "supports_case_number": True,
    },
}




def get_court_config(court_id: str, sub_court_id: str) -> Dict[str, Any]:
    """
    Resolves court configuration strictly by subCourtId ('20' for Gujarat, '22' for Patna).
    """
    scid = str(sub_court_id).strip()
    cid = str(court_id).strip()

    if scid in COURT_REGISTRY:
        court_info = COURT_REGISTRY[scid]
        if cid and cid not in court_info["supported_court_ids"]:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid courtId '{court_id}' for {court_info['court_name']}. Expected courtId='{court_info['default_court_id']}'.",
            )
        return court_info

    supported_list = ", ".join(
        f"subCourtId='{sid}' ({info['court_name']}, courtId='{info['default_court_id']}')"
        for sid, info in COURT_REGISTRY.items()
    )
    raise HTTPException(
        status_code=400,
        detail=(
            f"Court ID '{court_id}' with SubCourt ID '{sub_court_id}' is not supported. "
            f"Supported courts: {supported_list}."
        ),
    )


def validate_court(court_id: str, sub_court_id: str) -> Dict[str, Any]:
    """
    Helper function to validate court parameters against registry.
    """
    return get_court_config(court_id, sub_court_id)


async def search_party_by_court(
    court_id: str,
    sub_court_id: str,
    party_name: str,
    start_year: Optional[str] = None,
    end_year: Optional[str] = None,
    hearing_date: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Dispatches party search to the appropriate court scraper based on subCourtId.
    """
    court_config = get_court_config(court_id, sub_court_id)
    handler: Optional[Callable] = court_config.get("party_search_handler")

    if not handler:
        raise HTTPException(
            status_code=501,
            detail=f"Party name search is not yet implemented for {court_config['court_name']}.",
        )

    try:
        return await handler(
            party_name=party_name,
            start_year=start_year,
            end_year=end_year,
            hearing_date=hearing_date,
        )
    except httpx.TimeoutException as e:
        raise HTTPException(
            status_code=504,
            detail=f"Connection to {court_config['court_name']} portal timed out. The portal is slow or unreachable.",
        ) from e
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to connect to {court_config['court_name']} portal: {str(e)}",
        ) from e
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        ) from e
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred: {str(e)}",
        ) from e


async def search_cnr_by_court(
    court_id: str,
    sub_court_id: str,
    cnr_number: str,
) -> Any:
    """
    Dispatches CNR search to the appropriate court scraper based on subCourtId.
    Supported: Gujarat (subCourtId='20'), Patna (subCourtId='22').
    """
    court_config = get_court_config(court_id, sub_court_id)
    if not court_config.get("supports_cnr"):
        raise HTTPException(
            status_code=400,
            detail=f"CNR search is not supported for {court_config['court_name']} (subCourtId='{sub_court_id}').",
        )

    handler: Optional[Callable] = court_config.get("cnr_search_handler")
    if not handler:
        raise HTTPException(
            status_code=501,
            detail=f"CNR search handler is not configured for {court_config['court_name']}.",
        )

    try:
        return await handler(cnr=cnr_number)
    except httpx.TimeoutException as e:
        raise HTTPException(
            status_code=504,
            detail=f"Connection to {court_config['court_name']} portal timed out. The portal is slow or unreachable.",
        ) from e
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to connect to {court_config['court_name']} portal: {str(e)}",
        ) from e
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        ) from e
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred: {str(e)}",
        ) from e


async def search_case_number_by_court(
    court_id: str,
    sub_court_id: str,
    case_type: str,
    case_number: str,
    case_year: str,
    side: Optional[str] = "R",
) -> Any:
    """
    Dispatches Case Number search to the appropriate court scraper based on subCourtId.
    Supported: Gujarat (subCourtId='20'), Patna (subCourtId='22').
    """
    court_config = get_court_config(court_id, sub_court_id)
    if not court_config.get("supports_case_number"):
        raise HTTPException(
            status_code=400,
            detail=f"Case number search is not supported for {court_config['court_name']} (subCourtId='{sub_court_id}').",
        )

    handler: Optional[Callable] = court_config.get("case_number_search_handler")
    if not handler:
        raise HTTPException(
            status_code=501,
            detail=f"Case number search handler is not configured for {court_config['court_name']}.",
        )

    try:
        return await handler(
            case_type=case_type,
            case_number=case_number,
            case_year=case_year,
            side=side,
        )
    except httpx.TimeoutException as e:
        raise HTTPException(
            status_code=504,
            detail=f"Connection to {court_config['court_name']} portal timed out. The portal is slow or unreachable.",
        ) from e
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to connect to {court_config['court_name']} portal: {str(e)}",
        ) from e
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        ) from e
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred: {str(e)}",
        ) from e


