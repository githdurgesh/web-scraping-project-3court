import asyncio
from typing import Any, Dict, Optional

from app.client.gujarat_client import GujaratHCClient
from app.parser.gujarat_parser import GujaratCaseParser


class GujaratScraper:
    def __init__(self, client: Optional[GujaratHCClient] = None):
        self.client = client or GujaratHCClient()
        self.parser = GujaratCaseParser()

    async def search_by_cnr(self, cnr: str, servicecode: str = "2") -> Dict[str, Any]:
        """
        Async case details search by CNR.
        """
        clean_cnr = cnr.replace("C#", "").strip()
        portal_ccin = f"C#{clean_cnr}"

        raw_data = await self.client.get_case_data(ccin=portal_ccin, servicecode=servicecode)
        parsed_response = self.parser.parse(raw_data, cnr=clean_cnr)

        return parsed_response

    async def search_by_case_number(
        self,
        side: Optional[str],
        case_type: str,
        case_number: str,
        case_year: str,
    ) -> Dict[str, Any]:
        """
        Async case details search by Case Number (side, caseType, caseNumber, caseYear).
        Constructs CCIN payload e.g. R#1#1#2024 with servicecode='1'.
        """
        side_clean = (side or "R").strip()
        if side_clean.lower() == "string" or not side_clean:
            side_clean = "R"

        ccin = f"{side_clean}#{str(case_type).strip()}#{str(case_number).strip()}#{str(case_year).strip()}"
        raw_data = await self.client.get_case_data(ccin=ccin, servicecode="1")
        parsed_response = self.parser.parse(raw_data, cnr=ccin)
        return parsed_response

    async def search_by_litigant(
        self,
        search_string: str,
        from_year: str,
        to_year: str,
        litigant_code: str = "0",
        beginning_with: str = "any",
        case_type: str = "select",
        district: str = "select",
        status_type: str = "select",
        counter: str = "1",
        fetch_details: bool = False,
        max_details: int = 1,
    ) -> Dict[str, Any]:
        """
        Async litigant / party search.
        """
        html_content = await self.client.search_litigant(
            search_string=search_string,
            from_year=from_year,
            to_year=to_year,
            litigant_code=litigant_code,
            beginning_with=beginning_with,
            counter=counter,
            case_type=case_type,
            district=district,
            status_type=status_type,
        )

        result = self.parser.parse_litigant_search(html_content)
        cases = result.get("cases", [])

        if fetch_details and cases:
            limit = min(len(cases), max_details)
            for idx in range(limit):
                case = cases[idx]
                case_cnr = case.get("CNR") or case.get("cnr")
                if case_cnr:
                    try:
                        detail = await self.search_by_cnr(cnr=case_cnr, servicecode="2")
                        case["details"] = detail
                    except Exception:
                        case["details"] = None

        return {
            "total_count": result.get("total_count", 0),
            "count": len(cases),
            "search_string": search_string,
            "from_year": from_year,
            "to_year": to_year,
            "cases": cases,
        }
