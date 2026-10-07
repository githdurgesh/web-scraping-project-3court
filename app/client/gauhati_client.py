import asyncio
import json
from typing import Any, Dict, List, Optional
import httpx

from app.config import settings
from app.constants import (
    GHC_BASE_URL,
    GHC_CASE_STATUS_URL,
    GHC_GET_RECORD_URL,
)


class GauhatiClient:
    """
    HTTP client for Gauhati High Court Case Status services.
    Portal: https://ghcservices.assam.gov.in/casestatus/
    Endpoint: https://ghcservices.assam.gov.in/casestatus/getrecord.php
    """

    def __init__(self, timeout: Optional[float] = None):
        self.timeout = timeout or settings.timeout or 30.0
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest",
            "Origin": GHC_BASE_URL,
            "Referer": GHC_CASE_STATUS_URL,
        }
        self.client = httpx.AsyncClient(
            headers=headers,
            follow_redirects=True,
            verify=False,
            timeout=self.timeout,
        )

    async def _post_record(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Reusable internal method to query getrecord.php and parse JSON response.
        Eliminates duplicate request/parse code across search methods.
        """
        response = await self.client.post(GHC_GET_RECORD_URL, data=payload)
        response.raise_for_status()

        response_text = response.text.strip()
        if not response_text:
            return []

        try:
            data = response.json()
            if isinstance(data, list):
                return data
            if isinstance(data, dict):
                return data.get("data") or data.get("records") or []
            return []
        except (ValueError, json.JSONDecodeError):
            if "[" in response_text and "]" in response_text:
                json_start = response_text.find("[")
                json_end = response_text.rfind("]") + 1
                try:
                    return json.loads(response_text[json_start:json_end])
                except Exception:
                    pass
            return []

    async def search_party_by_name_async(
        self,
        party_name: str,
        start_year: Optional[str] = None,
        end_year: Optional[str] = None,
        pet_pet_res: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Searches cases by Party / Litigant name on Gauhati High Court portal.
        Only sends the relevant parameters without unnecessary empty fields.
        """
        payload: Dict[str, Any] = {
            "pet_input": str(party_name).strip(),
        }
        reg_yr = (start_year or end_year or "").strip()
        if reg_yr:
            payload["reg_year"] = reg_yr
        if pet_pet_res:
            payload["pet_pet_res"] = pet_pet_res.strip()

        return await self._post_record(payload)

    def search_party_by_name_sync(self, *args, **kwargs) -> List[Dict[str, Any]]:
        """Synchronous wrapper for search_party_by_name_async."""
        return asyncio.run(self.search_party_by_name_async(*args, **kwargs))

    async def search_cnr_async(self, cnr: str) -> List[Dict[str, Any]]:
        """
        Searches cases by CNR number on Gauhati High Court portal.
        Only sends the relevant CNR parameter.
        """
        payload: Dict[str, Any] = {
            "CNR": str(cnr).strip(),
        }
        return await self._post_record(payload)

    def search_cnr_sync(self, cnr: str) -> List[Dict[str, Any]]:
        """Synchronous wrapper for search_cnr_async."""
        return asyncio.run(self.search_cnr_async(cnr=cnr))

    async def search_case_number_async(
        self,
        case_type: str,
        case_number: str,
        case_year: str,
    ) -> List[Dict[str, Any]]:
        """
        Searches cases by Case Type, Number, and Year on Gauhati High Court portal.
        """
        ctype = str(case_type).strip() if case_type else ""
        if ctype.lower() in ("string", "0", "select", "all", "none"):
            ctype = ""

        cnum = str(case_number).strip() if case_number else ""
        if cnum.lower() == "string":
            cnum = ""

        cyear = str(case_year).strip() if case_year else ""
        if cyear.lower() == "string":
            cyear = ""

        payload: Dict[str, Any] = {
            "category": "",
            "type": ctype,
            "reg_number": cnum,
            "reg_year": cyear,
        }
        return await self._post_record(payload)

    def search_case_number_sync(self, *args, **kwargs) -> List[Dict[str, Any]]:
        """Synchronous wrapper for search_case_number_async."""
        return asyncio.run(self.search_case_number_async(*args, **kwargs))

    async def close(self):
        """Closes the underlying httpx client session."""
        await self.client.aclose()

