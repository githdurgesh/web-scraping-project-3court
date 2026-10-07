import asyncio
import re
from typing import Any, Dict, List, Optional, Tuple
import httpx
from bs4 import BeautifulSoup

from app.config import settings
from app.constants import (
    PATNA_HC_BASE_URL,
    PATNA_HC_CASE_SEARCH_NAME_URL,
    PATNA_HC_CASE_SEARCH_CNR_URL,
    PATNA_HC_CAPTCHA_URL,
)
from app.utils.captcha_solver import PaddleCaptchaSolver


class PatnaClient:
    """
    Asynchronous client for interacting with Patna High Court Case Search portals:
    - Party Name Search: https://patnahighcourt.gov.in/casesearch/name
    - CNR Search: https://patnahighcourt.gov.in/casesearch/cnr_no
    - Case Number Search: https://patnahighcourt.gov.in/ (redirects to /CaseStatus/...)
    Mirrors GujaratHCClient with a clean async httpx interface and automatic captcha solving.
    """

    def __init__(self, timeout: Optional[float] = None):
        self.timeout = timeout or settings.timeout
        self.solver = PaddleCaptchaSolver()
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Referer": f"{PATNA_HC_BASE_URL}/",
            "Origin": PATNA_HC_BASE_URL,
        }
        self.client = httpx.AsyncClient(
            headers=headers,
            follow_redirects=True,
            verify=False,
            timeout=self.timeout,
        )

    async def _get_form_context(self, url: str) -> Tuple[str, Dict[str, str]]:
        """Visits an ASP.NET page and extracts hidden fields (ViewState, EventValidation, etc.)."""
        resp = await self.client.get(url)
        resp.raise_for_status()
        html = resp.text
        soup = BeautifulSoup(html, "html.parser")
        hidden = {}
        for name in [
            "__VIEWSTATE",
            "__VIEWSTATEGENERATOR",
            "__VIEWSTATEENCRYPTED",
            "__EVENTVALIDATION",
            "__EVENTTARGET",
            "__EVENTARGUMENT",
            "__LASTFOCUS",
            "__SCROLLPOSITIONX",
            "__SCROLLPOSITIONY",
        ]:
            inp = soup.find("input", {"name": name})
            hidden[name] = inp.get("value", "") if inp else ""

        for select_name, key_name in [
            ("ctl00$MainContent$ddlCTypeCivil", "__CIVIL_TYPES__"),
            ("ctl00$MainContent$ddlCTypeCri", "__CRI_TYPES__"),
        ]:
            sel = soup.find("select", {"name": select_name})
            if sel:
                mapping = {}
                for opt in sel.find_all("option"):
                    val = opt.get("value", "").strip()
                    txt = opt.get_text(strip=True)
                    if not val:
                        continue
                    mapping[val.lower()] = val
                    mapping[txt.lower()] = val
                    bracket = re.search(r"\[(.*?)\]", txt)
                    if bracket:
                        code = bracket.group(1).strip()
                        mapping[code.lower()] = val
                        mapping[re.sub(r"[^a-zA-Z0-9]", "", code).lower()] = val
                    clean_txt = re.sub(r"[^a-zA-Z0-9]", "", txt).lower()
                    mapping[clean_txt] = val
                hidden[key_name] = mapping
                opt = sel.find("option", selected=True)
                if opt and opt.get("value") is not None:
                    hidden[select_name] = opt.get("value")
                else:
                    first_opt = sel.find("option")
                    if first_opt and first_opt.get("value") is not None:
                        hidden[select_name] = first_opt.get("value")
            else:
                hidden[key_name] = {}

        return html, hidden

    async def fetch_and_solve_captcha(self) -> str:
        """Obtains captcha code from CaptchaImageText cookie or by solving captcha image."""
        try:
            r = await self.client.get(PATNA_HC_CAPTCHA_URL)
            if r.status_code == 200 and r.content:
                cookie_val = self.client.cookies.get("CaptchaImageText")
                if cookie_val and len(cookie_val.strip()) in (3, 4):
                    return cookie_val.strip()
                solved = await asyncio.to_thread(self.solver.solve, r.content)
                cleaned = re.sub(r"[^a-zA-Z0-9]", "", solved).strip()
                if cleaned:
                    return cleaned[:3]
        except Exception:
            pass

        return cookie_val or ""

    def _decompose_cnr(self, cnr: str) -> Tuple[str, str, str]:
        """Decomposes a 16-character CNR into (prefix, token_no, year)."""
        clean = re.sub(r"[^a-zA-Z0-9]", "", cnr).strip().upper()
        if len(clean) >= 16:
            return clean[:6], clean[6:12], clean[12:16]
        elif len(clean) >= 10:
            prefix = clean[:6] if clean[:2].isalpha() else "BRHC01"
            rem = clean[len(prefix):]
            return prefix, rem[:-4].zfill(6), rem[-4:]
        return "BRHC01", clean.zfill(6), "2022"

    async def search_party_by_name_async(
        self,
        party_name: str,
        year: str,
        case_type: str = "0",
        party_type: str = "0",
        max_retries: int = 3,
    ) -> str:
        """Searches case by party name on https://patnahighcourt.gov.in/casesearch/name"""
        for _ in range(max_retries):
            _, hidden = await self._get_form_context(PATNA_HC_CASE_SEARCH_NAME_URL)
            captcha = await self.fetch_and_solve_captcha()
            if not captcha:
                continue

            payload = {
                "__EVENTTARGET": "",
                "__EVENTARGUMENT": "",
                "__VIEWSTATE": hidden.get("__VIEWSTATE", ""),
                "__VIEWSTATEGENERATOR": hidden.get("__VIEWSTATEGENERATOR", ""),
                "__VIEWSTATEENCRYPTED": hidden.get("__VIEWSTATEENCRYPTED", ""),
                "__EVENTVALIDATION": hidden.get("__EVENTVALIDATION", ""),
                "__SCROLLPOSITIONX": "0",
                "__SCROLLPOSITIONY": "0",
                "ctl00$MainContent$ddlCaseType": str(case_type),
                "ctl00$MainContent$txtName": party_name.strip(),
                "ctl00$MainContent$txtYear": str(year).strip(),
                "ctl00$MainContent$rblType": str(party_type),
                "ctl00$MainContent$txtCaptcha": captcha,
                "ctl00$MainContent$btnSeach": "Show",
            }

            resp = await self.client.post(PATNA_HC_CASE_SEARCH_NAME_URL, data=payload)
            resp.raise_for_status()
            if "ctl00_MainContent_gvSearch" in resp.text:
                return resp.text

            soup = BeautifulSoup(resp.text, "html.parser")
            lbl_msg = soup.find(id=lambda x: x and "lblMsg" in str(x))
            msg_text = lbl_msg.get_text(strip=True).lower() if lbl_msg else ""
            if "captcha" in msg_text or "code" in msg_text:
                await asyncio.sleep(0.3)
                continue
            return resp.text

        raise ValueError(f"Failed to fetch Patna HC party search results after {max_retries} attempts.")

    async def search_cnr_async(self, cnr: str, max_retries: int = 3) -> str:
        """Searches case by CNR on https://patnahighcourt.gov.in/casesearch/cnr_no"""
        prefix, token_no, year = self._decompose_cnr(cnr)
        for _ in range(max_retries):
            _, hidden = await self._get_form_context(PATNA_HC_CASE_SEARCH_CNR_URL)
            captcha = await self.fetch_and_solve_captcha()
            if not captcha:
                continue

            payload = {
                "__EVENTTARGET": "",
                "__EVENTARGUMENT": "",
                "__VIEWSTATE": hidden.get("__VIEWSTATE", ""),
                "ctl00$txtSearch": "",
                "ctl00$MainContent$txtPre": prefix,
                "ctl00$MainContent$txtTokenNo": token_no,
                "ctl00$MainContent$txtYear": year,
                "ctl00$MainContent$txtCaptcha": captcha,
                "ctl00$MainContent$btnSeach": "Show",
                "__VIEWSTATEGENERATOR": hidden.get("__VIEWSTATEGENERATOR", ""),
                "__SCROLLPOSITIONX": "0",
                "__SCROLLPOSITIONY": "0",
                "__VIEWSTATEENCRYPTED": hidden.get("__VIEWSTATEENCRYPTED", ""),
                "__EVENTVALIDATION": hidden.get("__EVENTVALIDATION", ""),
            }

            resp = await self.client.post(PATNA_HC_CASE_SEARCH_CNR_URL, data=payload)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            lbl_msg = soup.find(id=lambda x: x and "lblMsg" in str(x))
            msg_text = lbl_msg.get_text(strip=True).lower() if lbl_msg else ""
            if "wrong code" in msg_text or "captcha" in msg_text:
                await asyncio.sleep(0.3)
                continue
            return resp.text

        raise ValueError(f"Failed to fetch Patna HC CNR search results after {max_retries} attempts.")

    @staticmethod
    def _match_dropdown_type(
        mapping: Dict[str, str],
        val: str,
        lower_val: str,
        clean_val: str,
        bracket_val: str,
    ) -> Optional[str]:
        """Helper to match a case type string against dropdown options mapping."""
        return (
            mapping.get(val)
            or mapping.get(lower_val)
            or mapping.get(clean_val)
            or (mapping.get(bracket_val) if bracket_val else None)
        )

    async def search_case_number_async(
        self,
        case_type: str,
        case_number: str,
        case_year: str,
        side: str = "CR",
        max_retries: int = 5,
    ) -> str:
        """
        Searches case by Case Type, Number, and Year on Patna HC homepage:
        POST https://patnahighcourt.gov.in/ (redirects to /CaseStatus/...)
        """
        case_type_str = str(case_type).strip()

        for attempt in range(max_retries):
            _, hidden = await self._get_form_context(f"{PATNA_HC_BASE_URL}/")
            captcha = await self.fetch_and_solve_captcha()
            if not captcha:
                continue

            # Dynamically determine Civil vs Criminal from live page dropdown options
            civil_map = hidden.get("__CIVIL_TYPES__", {})
            cri_map = hidden.get("__CRI_TYPES__", {})
            civil_default = hidden.get("ctl00$MainContent$ddlCTypeCivil", "")
            cri_default = hidden.get("ctl00$MainContent$ddlCTypeCri", "")

            # Resolve case_type to appropriate dropdown option value
            clean_type = re.sub(r"[^a-zA-Z0-9]", "", case_type_str).lower()
            lower_type = case_type_str.lower()
            bracket_match = re.search(r"\[(.*?)\]", case_type_str)
            bracket_code = bracket_match.group(1).strip().lower() if bracket_match else ""

            side_upper = str(side).upper() if side else ""
            prefer_civil = side_upper in ("C", "CIVIL")

            primary_map, secondary_map = (civil_map, cri_map) if prefer_civil else (cri_map, civil_map)
            primary_is_civil, secondary_is_civil = (True, False) if prefer_civil else (False, True)

            resolved_val = self._match_dropdown_type(primary_map, case_type_str, lower_type, clean_type, bracket_code)
            if resolved_val:
                is_civil = primary_is_civil
            else:
                resolved_val = self._match_dropdown_type(secondary_map, case_type_str, lower_type, clean_type, bracket_code)
                if resolved_val:
                    is_civil = secondary_is_civil
                else:
                    is_civil = prefer_civil
                    resolved_val = case_type_str

            payload = {
                "__LASTFOCUS": "",
                "__EVENTTARGET": "",
                "__EVENTARGUMENT": "",
                "__VIEWSTATE": hidden.get("__VIEWSTATE", ""),
                "ctl00$txtSearch": "",
                "ctl00$MainContent$ddlCTypeCivil": resolved_val if is_civil else civil_default,
                "ctl00$MainContent$txtCaseNoCivil": str(case_number) if is_civil else "",
                "ctl00$MainContent$txtCaseYear": str(case_year) if is_civil else "",
                "ctl00$MainContent$txtCaptchaCv": captcha if is_civil else "",
                "ctl00$MainContent$ddlCTypeCri": cri_default if is_civil else resolved_val,
                "ctl00$MainContent$txtCaseNoCri": "" if is_civil else str(case_number),
                "ctl00$MainContent$txtCaseYearCri": "" if is_civil else str(case_year),
                "ctl00$MainContent$txtCaptcha": "" if is_civil else captcha,
                "ctl00$MainContent$btnSearchCivil" if is_civil else "ctl00$MainContent$btnSearchCri": "Search",
                "__VIEWSTATEGENERATOR": hidden.get("__VIEWSTATEGENERATOR", "CA0B0334"),
                "__SCROLLPOSITIONX": "0",
                "__SCROLLPOSITIONY": "77",
                "__VIEWSTATEENCRYPTED": hidden.get("__VIEWSTATEENCRYPTED", ""),
                "__EVENTVALIDATION": hidden.get("__EVENTVALIDATION", ""),
            }

            resp = await self.client.post(f"{PATNA_HC_BASE_URL}/", data=payload)
            resp.raise_for_status()

            # Check if request succeeded or redirected
            is_redirected = bool(resp.history)
            is_case_status_url = any(k in str(resp.url).lower() for k in ["casestatus", "cino", "case_status", "casesearch", "case_not_found"])
            is_error_url = "error.htm" in str(resp.url).lower()
            has_case_content = any(k in resp.text for k in ["fvCaseStatus", "fvCaseStatusCri", "gvProceedings", "gvDefects", "ctl00_MainContent_fvCaseStatus"])

            soup_resp = BeautifulSoup(resp.text, "html.parser")
            lbl_msg = soup_resp.find(id=lambda x: x and "lblMsg" in str(x))
            msg_text = lbl_msg.get_text(strip=True).lower() if lbl_msg else ""
            is_wrong_captcha = "wrong code" in msg_text or "wrong captcha" in msg_text

            print(
                f"Patna HC attempt={attempt + 1}, "
                f"status={resp.status_code}, "
                f"url={resp.url}, "
                f"message={msg_text!r}, "
                f"length={len(resp.text)}"
            )

            if (is_redirected or is_case_status_url or has_case_content) and not is_wrong_captcha and not is_error_url:
                return resp.text

            await asyncio.sleep(0.3)

        raise ValueError(
            f"Failed to fetch Patna HC case search results for Type '{case_type}', Number '{case_number}', Year '{case_year}' after {max_retries} attempts."
        )

    # =========================================================================
    # Synchronous Fallback Helpers (for backwards compatibility)
    # =========================================================================

    def search_party_by_name_sync(self, *args, **kwargs) -> str:
        return asyncio.run(self.search_party_by_name_async(*args, **kwargs))

    def search_cnr_sync(self, *args, **kwargs) -> str:
        return asyncio.run(self.search_cnr_async(*args, **kwargs))

    def search_case_number_sync(self, *args, **kwargs) -> str:
        return asyncio.run(self.search_case_number_async(*args, **kwargs))

    async def close(self):
        """Closes the underlying httpx client."""
        await self.client.aclose()


# Backward compatibility alias
PatnaCauseListClient = PatnaClient
