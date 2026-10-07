from typing import Any, Dict, List, Optional, Union
from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession
import httpx

from app.schemas.gujarat_schema import (
    CaseNumberSearchRequest,
    GujaratCnrRequest,
    GujaratStandardResponse,
)
from app.scraper.gujarat_scraper import GujaratScraper
from app.database.session import get_db
from app.service.case_service import CaseService
from app.service.court_registry import (
    search_party_by_court,
    search_cnr_by_court,
    search_case_number_by_court,
    validate_court,
    get_court_config,
)

router = APIRouter(
    prefix="/api/cases",
    tags=["Case Search API"],
)


@router.get("/party-name", response_model=List[Dict[str, Any]])
async def search_by_party_name(
    courtId: str = Query(..., description="Court ID e.g. '2' (High Court)"),
    subCourtId: str = Query(..., description="SubCourt ID e.g. '20' (Gujarat), '22' (Patna), '24' (Gauhati)"),
    partyName: str = Query(..., description="Party or litigant name to search"),
    startYear: Optional[str] = Query(None, description="Start year (for courts supporting year filter e.g. Gujarat, Gauhati)"),
    endYear: Optional[str] = Query(None, description="End year (for courts supporting year filter e.g. Gujarat, Gauhati)"),
):
    """
    Search cases by Party / Litigant Name across supported High Courts.
    Supported: Gujarat (subCourtId='20'), Patna (subCourtId='22'), Gauhati (subCourtId='24').
    Dispatched dynamically via the Court Registry service based on `courtId` and `subCourtId`.
    """
    return await search_party_by_court(
        court_id=courtId,
        sub_court_id=subCourtId,
        party_name=partyName,
        start_year=startYear,
        end_year=endYear,
    )


@router.get("/cnr", response_model=Union[GujaratStandardResponse, Dict[str, Any]])
async def search_by_cnr(
    courtId: str = Query(..., description="Court ID e.g. '2'"),
    subCourtId: str = Query(..., description="SubCourt ID e.g. '20' (Gujarat), '22' (Patna), '24' (Gauhati)"),
    cnrNumber: str = Query(..., description="CNR Number"),
):
    """
    Search case details by CNR number across supported High Courts.
    Query parameters: courtId, subCourtId, cnrNumber
    Supported: Gujarat (subCourtId='20'), Patna (subCourtId='22'), Gauhati (subCourtId='24').
    """
    return await search_cnr_by_court(
        court_id=courtId,
        sub_court_id=subCourtId,
        cnr_number=cnrNumber,
    )



@router.post("/case-number", response_model=Union[GujaratStandardResponse, Dict[str, Any]])
async def search_by_case_number(
    request: CaseNumberSearchRequest,
    courtId: str = Query(..., description="courtId"),
    subCourtId: str = Query(..., description="subCourtId"),
):
    """
    Search case details by Case Type, Number, and Year across supported High Courts.
    Supported: Gujarat (subCourtId='20'), Patna (subCourtId='22'), Gauhati (subCourtId='24').
    """
    return await search_case_number_by_court(
        court_id=courtId,
        sub_court_id=subCourtId,
        case_type=request.caseType,
        case_number=request.caseNumber,
        case_year=request.caseYear,
        side=request.side,
    )

