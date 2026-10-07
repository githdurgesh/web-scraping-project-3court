import base64
import re
import urllib.parse
from typing import Any, Dict, List, Optional
from bs4 import BeautifulSoup

from app.constants import PATNA_HC_BASE_URL, PATNA_HC_DEFECT_STATUS_URL


class PatnaParser:
    """
    Parse Patna High Court party-result lists and case-detail pages.

    Party-name results use parse_party_name_results. CNR and case-number searches
    share the same details layout through _parse_case_details_response.
    """

    def __init__(self, base_url: str = PATNA_HC_BASE_URL):
        self.base_url = base_url

    def parse_hidden_fields(self, html: str) -> Dict[str, str]:
        """
        Extracts ASP.NET hidden fields from the HTML.
        """
        soup = BeautifulSoup(html, "html.parser")
        hidden_fields = {}
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
            element = soup.find("input", {"name": name})
            if element:
                hidden_fields[name] = element.get("value", "")
            else:
                hidden_fields[name] = ""
        return hidden_fields

    def parse_party_name_results(self, html: str, fallback_year: str = "") -> Dict[str, Any]:
        """
        Parses the result list from Patna HC Case Search by Party Name:
        https://patnahighcourt.gov.in/casesearch/name
        Maps each row by its visible column headings.
        """
        soup = BeautifulSoup(html, "html.parser")

        message = self._extract_page_message(soup)
        cases: List[Dict[str, Any]] = []
        table_data = self._headered_table_rows(
            soup, {"token_no", "petitioner", "respondent", "filingdate", "petitioneradvocate"}
        )

        if table_data:
            headers, rows = table_data
            for tr in rows:
                cells = tr.find_all("td", recursive=False)
                if len(cells) < len(headers):
                    continue
                values = {
                    header: cells[index].get_text(" ", strip=True)
                    for index, header in enumerate(headers)
                    if header
                }

                sr_no = values.get("srno", "")
                token_no = values.get("token_no", "") 
                petitioner = values.get("petitioner", "")
                respondent = values.get("respondent", "")
                filing_date = values.get("filingdate", "")
                petitioner_advocate = values.get("petitioneradvocate", "")

                # Extract CINO and decode CNR
                cino = ""
                cnr = ""
                case_status_url = ""
                cino_link = tr.find("a", attrs={"data-cino": True})
                if cino_link:
                    cino = cino_link.get("data-cino", "").strip()
                    case_status_url = f"{PATNA_HC_DEFECT_STATUS_URL}?CINO={cino}"
                    try:
                        # CINO format is URL-encoded: <Base64CNR>-<HMAC/Nonce>
                        unquoted = urllib.parse.unquote(cino)
                        b64_part = unquoted.split("-")[0]
                        decoded_cnr = base64.b64decode(b64_part).decode("utf-8", errors="ignore").strip()
                        if decoded_cnr:
                            cnr = decoded_cnr
                    except Exception:
                        cnr = ""

                # Extract year from token_no (e.g. "MA-1215/2022" -> "2022") or fallback
                year_match = re.search(r"/(\d{4})$", token_no)
                case_year = year_match.group(1) if year_match else fallback_year

                party_title = f"{petitioner} vs {respondent}" if respondent else petitioner

                cases.append({
                    "sr_no": sr_no,
                    "token_no": token_no,
                    "case_number": token_no,
                    "petitioner": petitioner,
                    "respondent": respondent,
                    "party_name": party_title,
                    "filing_date": filing_date,
                    "petitioner_advocate": petitioner_advocate,
                    "CNR": cnr,
                    "cino": cino,
                    "case_status_url": case_status_url,
                    "year": case_year,
                })

        return {
            "total_count": len(cases),
            "message": message,
            "cases": cases,
        }

    def parse_case_search(self, html: str, fallback_year: str = "") -> Dict[str, Any]:
        """Backward-compatible alias for party-name result parsing."""
        return self.parse_party_name_results(html, fallback_year=fallback_year)

    def parse_party_search(self, html: str, fallback_year: str = "") -> Dict[str, Any]:
        """
        Compatibility entry point for party-name result lists and legacy cause lists.
        """
        soup = BeautifulSoup(html, "html.parser")
        if self._headered_table_rows(
            soup, {"token_no", "petitioner", "respondent", "filingdate", "petitioneradvocate"}
        ):
            return self.parse_party_name_results(html, fallback_year=fallback_year)

        # Legacy Cause List parsing fallback
        message = self._extract_page_message(soup)

        cases: List[Dict[str, Any]] = []
        all_trs = soup.find_all("tr")
        current_court = ""
        current_judges: List[str] = []
        current_stage = ""

        for tr in all_trs:
            if tr.find("table"):
                continue
            tds = tr.find_all(["td", "th"])
            if not tds:
                continue
            text_cols = [td.get_text(" ", strip=True) for td in tds]
            first_col = text_cols[0] if text_cols else ""

            if "SR. NO." in first_col or "CASE NUMBER" in text_cols:
                continue

            if len(tds) == 1:
                if first_col.startswith("Court No."):
                    current_court = first_col
                    current_judges = []
                    current_stage = ""
                    continue
                elif "Justice" in first_col or "Chief Justice" in first_col:
                    if first_col not in current_judges:
                        current_judges.append(first_col)
                    continue
                elif first_col.startswith("FOR ") or first_col.startswith("AFTER ") or first_col.isupper():
                    current_stage = first_col
                    continue

            case_link_tag = tr.find("a", href=lambda h: h and "CaseStatus" in h)
            if case_link_tag and len(tds) >= 6:
                sr_no = text_cols[0]
                case_no = case_link_tag.text.strip() or (text_cols[1] if len(text_cols) > 1 else "")
                cases.append({
                    "sr_no": sr_no,
                    "case_number": case_no,
                    "token_no": case_no,
                    "party_name": text_cols[2] if len(text_cols) > 2 else "",
                    "petitioner_advocate": text_cols[3] if len(text_cols) > 3 else "",
                    "respondent_advocate": text_cols[4] if len(text_cols) > 4 else "",
                    "court_no": current_court,
                    "judges": list(current_judges),
                    "stage": current_stage,
                    "hearing_time": text_cols[5] if len(text_cols) > 5 else "",
                    "current_position": text_cols[6] if len(text_cols) > 6 else "",
                })

        return {
            "total_count": len(cases),
            "message": message,
            "cases": cases,
        }

    @staticmethod
    def _canonical_table_label(label: str) -> str:
        normalized = re.sub(r"[^a-z0-9]", "", label.casefold())
        aliases = {
            "caseno": "casenumber",
            "slno": "srno",
            "serialno": "srno",
            "tokenno": "token_no",
            "tokennumber": "token_no",
            "dateoffiling": "filingdate",
            "dateofregistration": "registrationdate",
            "nexthearingactiondate": "nexthearingdate",
            "actiondate": "nexthearingdate",
            "presentstatus": "status",
            "subject": "casetypedescription",
            "purpose": "purposeoflisting",
            "currentposition": "stagecode",
            "court": "coram",
            "orderno": "ordernumber",
            "orderdateof": "orderdate",
            "petitionersname": "petitionername",
            "respondentsname": "respondentname",
            "listingdate": "listingdate",
            "nextlistingdate": "nextlistingdate",
        }
        return aliases.get(normalized, normalized)

    @staticmethod
    def _cell_value(cell) -> str:
        text = cell.get_text(" ", strip=True)
        if text:
            return text
        control = cell.find(["input", "button"], attrs={"value": True})
        return control.get("value", "").strip() if control else ""

    @classmethod
    def _extract_orders(cls, soup: BeautifulSoup, cnr: str, case_number: str) -> List[Dict[str, str]]:
        orders_heading = next((
            heading for heading in soup.find_all(["strong", "h1", "h2", "h3", "h4"])
            if cls._canonical_table_label(heading.get_text(" ", strip=True)) == "orders"
        ), None)
        if not orders_heading:
            return []

        section_rows = []
        for element in orders_heading.next_elements:
            if getattr(element, "name", None) in {"strong", "h1", "h2", "h3", "h4"}:
                heading_label = cls._canonical_table_label(element.get_text(" ", strip=True))
                if heading_label and heading_label != "orders":
                    break
            if getattr(element, "name", None) == "tr":
                section_rows.append(element)

        orders = []
        date_pattern = re.compile(r"\b\d{1,2}[-/][A-Za-z0-9]{3,9}[-/]\d{4}\b")
        for section in section_rows:
            for row in section.find_all("tr"):
                if row.find("table"):
                    continue
                cells = row.find_all("td", recursive=False)
                row_text = row.get_text(" ", strip=True)
                normalized_row = cls._canonical_table_label(row_text)
                if normalized_row in {"orders", "norecords", "recordnotfound"}:
                    continue

                headers = []
                table = row.find_parent("table")
                if table:
                    table_rows = [
                        table_row for table_row in table.find_all("tr")
                        if table_row.find_parent("table") is table
                    ]
                    row_index = table_rows.index(row)
                    for previous_row in reversed(table_rows[:row_index]):
                        headers = [
                            cls._canonical_table_label(cell.get_text(" ", strip=True))
                            for cell in previous_row.find_all("th", recursive=False)
                        ]
                        if headers:
                            break

                values = {
                    header: cls._cell_value(cells[index])
                    for index, header in enumerate(headers)
                    if header and index < len(cells)
                }
                date_match = date_pattern.search(row_text)
                links = row.find_all("a", href=True)
                if not cells and not links:
                    continue

                for link in links or [None]:
                    orders.append({
                        "CaseDetail": values.get("casedetail") or values.get("casenumber") or case_number,
                        "JUDGENAME": values.get("judgename") or values.get("judge") or values.get("coram", ""),
                        "OrderDate": values.get("orderdate") or (date_match.group(0) if date_match else ""),
                        "Petitioner": values.get("petitionername", ""),
                        "Respondent": values.get("respondentname", ""),
                        "EmailSent": values.get("emailsent", ""),
                        "Details": values.get("details", ""),
                        "CNR": values.get("cnr") or cnr,
                        "OrderNumber": values.get("ordernumber") or str(len(orders) + 1),
                        "OrderURL": urllib.parse.urljoin(
                            f"{PATNA_HC_BASE_URL}/", link.get("href", "")
                        ) if link else "",
                    })
        return orders

    @staticmethod
    def _extract_page_message(soup: BeautifulSoup) -> str:
        for row in soup.find_all("tr"):
            cells = row.find_all(["th", "td"], recursive=False)
            if len(cells) != 1 or not cells[0].has_attr("colspan"):
                continue
            spans = cells[0].find_all("span")
            message = cells[0].get_text(" ", strip=True)
            if len(spans) == 1 and spans[0].get_text(" ", strip=True) == message:
                if message:
                    return message
        return ""

    @classmethod
    def  _headered_table_rows(cls, soup: BeautifulSoup, required_headers: set):
        candidates = []
        for table in soup.find_all("table"):
            rows = [
                row for row in table.find_all("tr")
                if row.find_parent("table") is table
            ]
            for row_index, row in enumerate(rows):
                headers = [
                    cls._canonical_table_label(cell.get_text(" ", strip=True))
                    for cell in row.find_all("th", recursive=False)
                ]
                if required_headers.issubset(headers):
                    candidates.append((len(headers), headers, rows[row_index + 1:]))
        if not candidates:
            return None
        _, headers, rows = min(candidates, key=lambda candidate: candidate[0])
        return headers, rows

    @classmethod
    def _find_case_details_table(cls, soup: BeautifulSoup):
        required_labels = {"petitioner", "respondent", "casenumber"}
        candidates = []
        for table in soup.find_all("table"):
            labels = {
                cls._canonical_table_label(th.get_text(" ", strip=True))
                for th in table.find_all("th")
            }
            if required_labels.issubset(labels):
                candidates.append((len(labels), table))
        return min(candidates, key=lambda candidate: candidate[0])[1] if candidates else None

    @classmethod
    def _records_from_header_table(cls, soup: BeautifulSoup, required_headers: set):
        table_data = cls._headered_table_rows(soup, required_headers)
        if not table_data:
            return []
        headers, rows = table_data
        records = []
        for row in rows:
            cells = row.find_all("td", recursive=False)
            if len(cells) < len(headers):
                continue
            records.append({
                header: cells[index].get_text(" ", strip=True)
                for index, header in enumerate(headers)
                if header
            })
        return records

    @classmethod
    def _labeled_value_cells(cls, container):
        for row in container.find_all("tr"):
            for header in row.find_all("th", recursive=False):
                value_cell = header.find_next_sibling("td")
                if value_cell:
                    yield cls._canonical_table_label(header.get_text(" ", strip=True)), value_cell

    def _parse_case_details_response(self, html: str, cnr: str = "") -> Dict[str, Any]:
        """
        Shared case-details mapper for both CNR and case-number search pages.
        The page fields are identified by their visible table labels.
        """
        soup = BeautifulSoup(html, "html.parser")

        # Extract any page-level message (e.g., "No records found") before parsing details.
        
        message = self._extract_page_message(soup)  

        # Default parsed values
        parsed_case: Dict[str, Any] = {
            "CNR": cnr,
            "cnr": cnr,
            "CaseNumber": "",
            "case_number": "",
            "token_no": "",
            "Petitioner": [],
            "petitioner": "",
            "Respondent": [],
            "respondent": "",
            "DistrictName": "",
            "district": "",
            "CaseTitle": "",
            "party_name": "",
            "FilingDate": "",
            "filing_date": "",
            "PetitionerAdvocates": [],
            "petitioner_advocate": "",
            "RespondentAdvocates": [],
            "respondent_advocate": "",
            "CaseStatus": "",
            "case_status": "",
            "cino": "",
            "case_status_url": "",
            "year": cnr[-4:] if len(cnr) >= 4 and cnr[-4:].isdigit() else "",
            "raw_message": message,
        }

        # Read the case summary from visible row labels, not generated IDs or CSS classes.
        case_status_table = self._find_case_details_table(soup)
        registration_date = ""
        next_hearing_date = "-"
        coram = ""

        if case_status_table:
            cnr_match = re.search(r"\bBRHC\d{12}\b", case_status_table.get_text(" ", strip=True))
            if cnr_match:
                parsed_case["CNR"] = cnr_match.group(0)
                parsed_case["cnr"] = parsed_case["CNR"]

        form = soup.find("form", action=True)
        if form:
            action_path = urllib.parse.urlsplit(form.get("action", "")).path
            action_token = urllib.parse.unquote(action_path.rsplit("/", 1)[-1])
            cino_match = re.fullmatch(r"([A-Za-z0-9+/=]{10,}-[A-Za-z0-9+/=]+)", action_token)
            if cino_match:
                cino = cino_match.group(1)
                parsed_case["cino"] = cino
                if not cnr:
                    try:
                        decoded_cnr = base64.b64decode(cino.split("-", 1)[0]).decode("utf-8").strip()
                        if decoded_cnr.startswith("BRHC"):
                            parsed_case["CNR"] = decoded_cnr
                            parsed_case["cnr"] = decoded_cnr
                    except (ValueError, UnicodeDecodeError):
                        pass

        summary_scope = case_status_table or soup
        for label, value_cell in self._labeled_value_cells(summary_scope):
            value = value_cell.get_text(" ", strip=True)
            if label == "token_no":
                parsed_case["token_no"] = value
            elif label == "status":
                parsed_case["CaseStatus"] = parsed_case["case_status"] = value
            elif label == "petitioner":
                parsed_case["petitioner"] = value
                parsed_case["Petitioner"] = [value] if value else []
            elif label == "respondent":
                parsed_case["respondent"] = value
                parsed_case["Respondent"] = [value] if value else []
            elif label == "filingdate":
                parsed_case["filing_date"] = parsed_case["FilingDate"] = value
            elif label == "registrationdate":
                registration_date = value
            elif label == "nexthearingdate":
                next_hearing_date = value or "-"
            elif label in {"coram", "judge", "coramjudge"}:
                coram = value
            elif label == "casetypedescription":
                parsed_case["CasetypeDescription"] = value
            elif label == "purposeoflisting":
                parsed_case["PurposeOfListing"] = value
            elif label == "stagecode":
                parsed_case["StageCode"] = value
            elif label == "district":
                parsed_case["district"] = parsed_case["DistrictName"] = value
            elif label == "petitioneradvocate":
                parsed_case["petitioner_advocate"] = value
                parsed_case["PetitionerAdvocates"] = [value] if value else []
            elif label == "respondentadvocate":
                parsed_case["respondent_advocate"] = value
                parsed_case["RespondentAdvocates"] = [value] if value else []
            elif label == "casenumber":
                case_link = value_cell.find("a")
                parsed_case["case_number"] = case_link.get_text(" ", strip=True) if case_link else value
                parsed_case["CaseNumber"] = parsed_case["case_number"]
                if case_link and case_link.get("href"):
                    parsed_case["case_status_url"] = urllib.parse.urljoin(
                        f"{self.base_url}/casesearch/", case_link["href"]
                    )

        if not registration_date:
            registration_date = parsed_case["FilingDate"]
        if not parsed_case["case_number"]:
            parsed_case["case_number"] = parsed_case["token_no"]
            parsed_case["CaseNumber"] = parsed_case["token_no"]

        # Add parties only when a table explicitly labels their role and name.
        for party in self._records_from_header_table(soup, {"partytype", "partyname"}):
            party_type = party.get("partytype", "").casefold()
            party_name = party.get("partyname", "").strip()
            if not party_name or party_name.upper() == "NO RECORDS":
                continue
            if "petitioner" in party_type and party_name not in parsed_case["Petitioner"]:
                parsed_case["Petitioner"].append(party_name)
            elif "respondent" in party_type and party_name not in parsed_case["Respondent"]:
                parsed_case["Respondent"].append(party_name)

        for header, party_list in (
            ("petitionername", parsed_case["Petitioner"]),
            ("respondentname", parsed_case["Respondent"]),
        ):
            for party in self._records_from_header_table(soup, {header}):
                party_name = party.get(header, "").strip()
                if party_name and party_name.upper() != "NO RECORDS" and party_name not in party_list:
                    party_list.append(party_name)
        # Compose Case Title
        if not parsed_case["CaseTitle"] and (parsed_case["Petitioner"] or parsed_case["Respondent"]):
            pet_str = ", ".join(parsed_case["Petitioner"]) if parsed_case["Petitioner"] else ""
            res_str = ", ".join(parsed_case["Respondent"]) if parsed_case["Respondent"] else ""
            if pet_str and res_str:
                parsed_case["CaseTitle"] = f"{pet_str} vs {res_str}"
            else:
                parsed_case["CaseTitle"] = pet_str or res_str
            parsed_case["party_name"] = parsed_case["CaseTitle"]

        # Read objections from their visible column headings.
        defects = self._records_from_header_table(
            soup, {"srno", "scrutinydate", "objection", "details"}
        )

        proceeding_mappings = (
            (
                {"coram", "stage", "notifieddate", "action", "boardnumber"},
                {"Coram": "coram", "Stage": "stage", "NotifiedDate": "notifieddate",
                 "Action": "action", "BoardNumber": "boardnumber"},
            ),
            (
                {"coram", "purposeoflisting", "listingdate", "action", "nextlistingdate"},
                {"Coram": "coram", "Stage": "purposeoflisting", "NotifiedDate": "listingdate",
                 "Action": "action", "BoardNumber": "nextlistingdate"},
            ),
        )
        proceedings = [
            {output: row.get(source, "") for output, source in field_mapping.items()}
            for required_headers, field_mapping in proceeding_mappings
            for row in self._records_from_header_table(soup, required_headers)
        ]
        officedetails = [
            {
                "FillingDate": defect.get("scrutinydate", ""),
                "DocumentName": defect.get("objection", ""),
                "DocumentDetails": defect.get("details", ""),
                "LitigantType": "",
            }
            for defect in defects
        ]
        orders = self._extract_orders(soup, parsed_case["CNR"], parsed_case["CaseNumber"])

        # Build objMessage for GujaratStandardResponse compatibility
        obj_message = {
            "CommonCaseDetails": {
                "CNR": parsed_case["CNR"],
                "CaseNumber": parsed_case["CaseNumber"],
                "FillingDate": parsed_case["FilingDate"],
                "NextHearingDate": next_hearing_date,
                "SubCourtId": "22",
                "CourtId": "2",
                "CaseStatus": parsed_case["CaseStatus"],
                "Petitioner": parsed_case["Petitioner"],
                "Respondent": parsed_case["Respondent"],
                "CaseTitle": parsed_case["CaseTitle"],
                "PetitionerAdvocates": parsed_case["PetitionerAdvocates"],
                "RespondentAdvocates": parsed_case["RespondentAdvocates"],
                "Advocates": parsed_case["PetitionerAdvocates"] + parsed_case["RespondentAdvocates"],
            },
            "mainDetails": [
                {
                    "CNR": parsed_case["CNR"],
                    "CaseNumber": parsed_case["CaseNumber"],
                    "CaseTitle": parsed_case["CaseTitle"],
                    "CaseStatus": parsed_case["CaseStatus"],
                    "RegistrationDate": registration_date,
                    "NextHearingDate": next_hearing_date,
                    "Coram": coram,
                    "DistrictName": parsed_case.get("DistrictName", ""),
                    "MainNumber": parsed_case["token_no"],
                    "CasetypeDescription": parsed_case.get("CasetypeDescription", ""),
                    "PurposeOfListing": parsed_case.get("PurposeOfListing", ""),
                    "StageCode": parsed_case.get("StageCode", ""),
                }
            ] if parsed_case["CaseNumber"] else [],
            "officedetails": officedetails,
            "courtproceedingDetail": proceedings,
            "Petitioner": parsed_case["Petitioner"],
            "Orders": orders,
            "Respondent": parsed_case["Respondent"],
            "PetitionerAdvocates": parsed_case["PetitionerAdvocates"],
            "RespondentAdvocates": parsed_case["RespondentAdvocates"],
        }

        return {
            "objMessage": obj_message,
            "messageDescription": "Patna High Court case search response",
            "refNumber": "-1",
            "exceptionCode": 0 if parsed_case["CaseNumber"] else -1,
            "exceptionDescription": message or "Success",
            "solution": "",
            "totalLength": "",
            "requestId": cnr or parsed_case["CaseNumber"],
        }

    def parse_cnr_search(self, html: str, cnr: str = "") -> Dict[str, Any]:
        """Parse a CNR search result using the shared case-details mapper."""
        return self._parse_case_details_response(html, cnr=cnr)

    def parse_case_number_search(self, html: str) -> Dict[str, Any]:
        """Parse a case-number result using the shared case-details mapper."""
        return self._parse_case_details_response(html)


    def parse_date_options(self, html: str) -> List[Dict[str, str]]:
        """
        Extracts date options without relying on the dropdown's generated ASP.NET ID.
        """
        soup = BeautifulSoup(html, "html.parser")
        date_pattern = re.compile(
            r"\b(?:\d{1,2}[-/]\d{1,2}[-/]\d{4}|"
            r"\d{1,2}[-/ ][A-Za-z]{3,9}[-/ ]\d{4}|"
            r"\d{4}[-/]\d{1,2}[-/]\d{1,2})\b"
        )
        candidates = []
        for select in soup.find_all("select"):
            options = [
                {"value": opt.get("value", "").strip(), "date_text": opt.get_text(" ", strip=True)}
                for opt in select.find_all("option")
                if opt.get_text(" ", strip=True)
            ]
            matching_dates = sum(bool(date_pattern.search(option["date_text"])) for option in options)
            if matching_dates:
                candidates.append((matching_dates, options))

        if not candidates:
            return []
        return max(candidates, key=lambda candidate: candidate[0])[1]


# Backward compatibility alias
PatnaCauseListParser = PatnaParser

