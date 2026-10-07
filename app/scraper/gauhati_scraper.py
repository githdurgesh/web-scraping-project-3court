from typing import Any, Dict, List, Optional

from app.client.gauhati_client import GauhatiClient
from app.parser.gauhati_parser import GauhatiParser


class GauhatiScraper:
    """
    High-level scraper for Gauhati High Court services (subCourtId='24').
    """

    def __init__(self, client: Optional[GauhatiClient] = None):
        self.client = client or GauhatiClient()
        self.parser = GauhatiParser()

    async def search_by_party_name(
        self,
        party_name: str,
        start_year: Optional[str] = None,
        end_year: Optional[str] = None,
        pet_pet_res: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Asynchronously searches cases by Party / Litigant name on Gauhati High Court.
        """
        records = await self.client.search_party_by_name_async(
            party_name=party_name,
            start_year=start_year,
            end_year=end_year,
            pet_pet_res=pet_pet_res,
        )
        return self.parser.parse_party_search(records, search_string=party_name)

    def search_by_party_name_sync(
        self,
        party_name: str,
        start_year: Optional[str] = None,
        end_year: Optional[str] = None,
        pet_pet_res: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Synchronous search wrapper for Gauhati High Court party name search.
        """
        records = self.client.search_party_by_name_sync(
            party_name=party_name,
            start_year=start_year,
            end_year=end_year,
            pet_pet_res=pet_pet_res,
        )
        return self.parser.parse_party_search(records, search_string=party_name)

    async def search_by_cnr(self, cnr: str) -> Dict[str, Any]:
        """
        Asynchronously searches a case by CNR number on Gauhati High Court.
        """
        records = await self.client.search_cnr_async(cnr=cnr)
        return self.parser.parse_cnr_search(records, cnr=cnr)

    def search_by_cnr_sync(self, cnr: str) -> Dict[str, Any]:
        """
        Synchronous search wrapper for Gauhati High Court CNR search.
        """
        records = self.client.search_cnr_sync(cnr=cnr)
        return self.parser.parse_cnr_search(records, cnr=cnr)

    async def search_by_case_number(
        self,
        case_type: str,
        case_number: str,
        case_year: str,
        side: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Asynchronously searches a case by Case Type, Number, and Year on Gauhati High Court.
        """
        records = await self.client.search_case_number_async(
            case_type=case_type,
            case_number=case_number,
            case_year=case_year,
        )
        return self.parser.parse_case_number_search(
            records,
            case_type=case_type,
            case_number=case_number,
            case_year=case_year,
        )

    def search_by_case_number_sync(
        self,
        case_type: str,
        case_number: str,
        case_year: str,
        side: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Synchronous search wrapper for Gauhati High Court Case Number search.
        """
        records = self.client.search_case_number_sync(
            case_type=case_type,
            case_number=case_number,
            case_year=case_year,
        )
        return self.parser.parse_case_number_search(
            records,
            case_type=case_type,
            case_number=case_number,
            case_year=case_year,
        )


