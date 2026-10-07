import asyncio
from datetime import datetime
import re
from typing import Any, Dict, List, Optional

from app.client.patna_client import PatnaClient
from app.parser.patna_parser import PatnaParser


class PatnaScraper:
    """
    High-level scraper for Patna High Court Case Search by Party Name.
    Endpoint: https://patnahighcourt.gov.in/casesearch/name
    Handles end-to-end flow: session creation, CAPTCHA resolution, form submission, and parsing.
    """

    def __init__(
        self,
        client: Optional[PatnaClient] = None,
        parser: Optional[PatnaParser] = None,
    ):
        self.client = client or PatnaClient()
        self.parser = parser or PatnaParser()

    def _resolve_years(
        self,
        year: Optional[str] = None,
        start_year: Optional[str] = None,
        end_year: Optional[str] = None,
        hearing_date: Optional[str] = None,
        date: Optional[str] = None,
    ) -> List[str]:
        """
        Determines the list of years to search.
        Supports single year, startYear-endYear range, or extracting year from date.
        """
        # 1. Explicit single year
        if year and year.strip():
            return [year.strip()]

        # 2. Year range
        s_yr = start_year.strip() if start_year and start_year.strip() else None
        e_yr = end_year.strip() if end_year and end_year.strip() else None

        if s_yr and e_yr:
            try:
                s_int = int(s_yr)
                e_int = int(e_yr)
                if 1950 <= s_int <= e_int <= 2050:
                    # Limit range to max 5 years to prevent excessive requests
                    diff = e_int - s_int
                    if diff <= 5:
                        return [str(y) for y in range(s_int, e_int + 1)]
                    else:
                        return [str(y) for y in range(max(s_int, e_int - 4), e_int + 1)]
            except ValueError:
                pass
            return [e_yr]

        if s_yr:
            return [s_yr]
        if e_yr:
            return [e_yr]

        # 3. Date string extraction
        date_str = hearing_date or date
        if date_str and date_str.strip():
            match = re.search(r"\b(19\d\d|20\d\d)\b", date_str.strip())
            if match:
                return [match.group(1)]

        # 4. Default to current year
        current_year = str(datetime.now().year)
        return [current_year]

    async def search_by_party_name(
        self,
        party_name: str,
        year: Optional[str] = None,
        start_year: Optional[str] = None,
        end_year: Optional[str] = None,
        hearing_date: Optional[str] = None,
        date: Optional[str] = None,
        case_type: str = "0",
        party_type: str = "0",
    ) -> Dict[str, Any]:
        """
        Asynchronously searches the Patna High Court case status by party/litigant name.
        """
        target_years = self._resolve_years(
            year=year,
            start_year=start_year,
            end_year=end_year,
            hearing_date=hearing_date,
            date=date,
        )

        all_cases: List[Dict[str, Any]] = []
        seen_identifiers = set()
        messages = []

        async def _fetch_for_year(y: str):
            try:
                html = await self.client.search_party_by_name_async(
                    party_name=party_name,
                    year=y,
                    case_type=case_type,
                    party_type=party_type,
                )
                parsed = self.parser.parse_party_name_results(html, fallback_year=y)
                return y, parsed
            except Exception as ex:
                return y, {"total_count": 0, "message": str(ex), "cases": []}

        # Query years concurrently
        tasks = [_fetch_for_year(y) for y in target_years]
        results = await asyncio.gather(*tasks)

        for y, parsed in results:
            if parsed.get("message"):
                messages.append(f"{y}: {parsed.get('message')}")
            for c in parsed.get("cases", []):
                # Deduplicate by cino or token_no
                uniq_key = c.get("cino") or c.get("token_no") or f"{c.get('case_number')}_{c.get('sr_no')}"
                if uniq_key not in seen_identifiers:
                    seen_identifiers.add(uniq_key)
                    all_cases.append(c)

        return {
            "total_count": len(all_cases),
            "party_name": party_name,
            "years": target_years,
            "selected_date": ", ".join(target_years),
            "date_value": ", ".join(target_years),
            "cases": all_cases,
            "message": "; ".join(messages),
        }

    def search_by_party_name_sync(self, *args, **kwargs) -> Dict[str, Any]:
        """Synchronous wrapper for search_by_party_name."""
        return asyncio.run(self.search_by_party_name(*args, **kwargs))

    async def search_by_cnr(self, cnr: str) -> Dict[str, Any]:
        """
        Asynchronously searches a case by CNR number on Patna High Court.
        """
        html = await self.client.search_cnr_async(cnr=cnr)
        return self.parser.parse_cnr_search(html, cnr=cnr)

    def search_by_cnr_sync(self, cnr: str) -> Dict[str, Any]:
        """
        Synchronously searches a case by CNR number on Patna High Court.
        """
        return asyncio.run(self.search_by_cnr(cnr=cnr))

    async def search_by_case_number(
        self,
        case_type: str,
        case_number: str,
        case_year: str,
        side: str = "CR",
    ) -> Dict[str, Any]:
        """
        Asynchronously searches a case by Case Type, Number, and Year on Patna High Court.
        """
        html = await self.client.search_case_number_async(
            case_type=case_type,
            case_number=case_number,
            case_year=case_year,
            side=side,
        )
        return self.parser.parse_case_number_search(html)

    def search_case_number_sync(self, *args, **kwargs) -> Dict[str, Any]:
        """Synchronous wrapper for search_by_case_number."""
        return asyncio.run(self.search_by_case_number(*args, **kwargs))

