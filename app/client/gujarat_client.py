import asyncio
import time
from typing import Any, Dict
import httpx
from pathlib import Path

from app.config import settings
from app.constants import (
    GUJARAT_HC_BASE_URL,
    GUJARAT_HC_CAPTCHA_URL,
    GUJARAT_HC_GET_DATA_URL,
    GUJARAT_HC_SEARCH_LITIGANT_URL,
    GUJARAT_HC_ORDER_DOWNLOAD_URL,
)
from app.utils.captcha_solver import PaddleCaptchaSolver


class GujaratHCClient:
    

    def __init__(self):
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "*/*",
            "Referer": f"{GUJARAT_HC_BASE_URL}/",
            "Origin": "https://gujarathc-casestatus.nic.in",
        }
        self.client = httpx.AsyncClient(headers=headers, follow_redirects=True, timeout=settings.timeout)
        self.solver = PaddleCaptchaSolver()
        self._session_initialized = False

    async def _ensure_session(self) -> None:
        """Visits litigantDetails page if not already visited to obtain JSESSIONID cookie."""
        if not self._session_initialized or "JSESSIONID" not in self.client.cookies:
            resp = await self.client.get(
                f"{GUJARAT_HC_BASE_URL}/ui-pages/litigantDetails.jsp",
                timeout=settings.timeout,
            )
            resp.raise_for_status()
            self._session_initialized = True

    # async def fetch_and_solve_captcha(self, expected_length: int = 5) -> str:
    async def fetch_and_solve_captcha(self) -> str:
        """
        Calls CaptchaServlet asynchronously with timestamp and passes image bytes to PaddleOCR.
        """
        await self._ensure_session()
        timestamp_ms = int(time.time() * 1000)
        params = {
            "ct": "S",
            "tm": timestamp_ms,
        }

        response = await self.client.get(
            GUJARAT_HC_CAPTCHA_URL,
            params=params,
            timeout=settings.timeout,
        )
        response.raise_for_status()

        # Run OCR in background thread pool so it does not block the asyncio event loop
        # return await asyncio.to_thread(self.solver.solve, response.content, expected_length)

        return await asyncio.to_thread(self.solver.solve,response.content)


    async def get_case_data(
        self,
        ccin: str,
        servicecode: str = "2",
        max_retries: int = 5,
    ) -> Dict[str, Any]:
        """
        Fetches case data for a given CCIN and servicecode asynchronously.
        Automatically solves captchas and retries if recognition fails or invalid captcha is returned.
        """
        last_error = None

        for attempt in range(1, max_retries + 1):
            challenge_string = await self.fetch_and_solve_captcha()
            if not challenge_string:
                continue

            payload = {
                "ccin": ccin,
                "servicecode": servicecode,
                "challengeString": challenge_string,
            }

            response = await self.client.post(
                GUJARAT_HC_GET_DATA_URL,
                data=payload,
                timeout=settings.timeout,
            )
            response.raise_for_status()

            try:
                res_json = response.json()
            except Exception:
                last_error = f"Non-JSON response: {response.text[:200]}"
                continue

            data_list = res_json.get("data")
            if not data_list or not isinstance(data_list, list):
                continue

            # Check if server returned an error (e.g. {'ERROR': 'Invalid Captcha'})
            has_error = any(
                isinstance(item, dict) and "ERROR" in item
                for item in data_list
            )

            if not has_error and len(data_list) > 0:
                return res_json

            last_error = f"Attempt {attempt}: Captcha verification failed ('{challenge_string}')"
            await asyncio.sleep(0.3)

        raise ValueError(
            f"Failed to fetch case data for CCIN '{ccin}' after {max_retries} attempts. "
            f"Last error: {last_error}"
        )

    async def search_litigant(
        self,
        search_string: str,
        from_year: str,
        to_year: str,
        litigant_code: str = "0",
        beginning_with: str = "any",
        counter: str = "1",
        case_type: str = "select",
        district: str = "select",
        status_type: str = "select",
    ) -> str:
        """
        Submits litigant / party name search to Gujarat High Court portal asynchronously.
        Returns HTML table string.
        """
        await self._ensure_session()

        payload = {
            "litigantcode": str(litigant_code),
            "beginningwith": str(beginning_with),
            "searchString": str(search_string).strip(),
            "fromyear": str(from_year).strip(),
            "toyear": str(to_year).strip(),
            "counter": str(counter),
            "casetypelt": str(case_type),
            "district": str(district),
            "statustype": str(status_type),
        }

        response = await self.client.post(
            GUJARAT_HC_SEARCH_LITIGANT_URL,
            data=payload,
            timeout=settings.timeout,
        )
        response.raise_for_status()

        return response.text
    
    # orders pdf code
    
    async def download_order(
     self,
     ccin: str,
     order_no: str,
     order_date: str,
     case_detail: str,
     citation: str,
     file_path: str,
    ) -> str:

     await self._ensure_session()

     payload = {
         "ccin_no": ccin,
         "order_no": order_no,
         "order_date": order_date,
         "flag": "d",
         "casedetail": case_detail,
         "nc": citation,
         "download_token_value_id": "",
        }

     response = await self.client.post(
        GUJARAT_HC_ORDER_DOWNLOAD_URL,
        data=payload,
        timeout=settings.timeout,
     )

     print("STATUS:", response.status_code)
     print("CONTENT TYPE:", response.headers.get("Content-Type"))
     print("CONTENT LENGTH:", len(response.content))

     response.raise_for_status()

     output_path = Path(file_path)
     output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
     )

     with open(output_path, "wb") as file:
        file.write(response.content)

     return str(output_path)

    async def close(self):
        await self.client.aclose()
