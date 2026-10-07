import re
import uuid
from typing import Any, Dict, List
from bs4 import BeautifulSoup
from app.constants import S3_BASE_URL,COURT_ID,SUB_COURT_ID 


class GujaratCaseParser:
    """
    Parses Gujarat High Court GetData API response into standard case schema.
    """

    def _extract_cnr(self, raw_response: Dict[str, Any], main_details: Dict[str, Any], fallback_cnr: str) -> str:
        clean_fallback = fallback_cnr.replace("C#", "").strip()

        # 1. If fallback is already a valid 16-char CNR (e.g. GJHC240185632024) without '#', return it
        if clean_fallback and "#" not in clean_fallback and len(clean_fallback) == 16:
            return clean_fallback

        # 2. Check cino, cnr, ccin fields in main_details
        for key in ["cino", "cnr", "ccin"]:
            val = str(main_details.get(key, "") or "").strip()
            if val and re.match(r'^[A-Z]{4}\d{12}$', val):
                return val

        # 3. Search raw_response JSON string for 16-char CNR pattern (e.g. GJHC240185632024)
        raw_str = str(raw_response)
        cnr_matches = re.findall(r'\b[A-Z]{4}\d{12}\b', raw_str)
        if cnr_matches:
            return cnr_matches[0]

        gjhc_matches = re.findall(r'GJHC\d{12}', raw_str)
        if gjhc_matches:
            return gjhc_matches[0]

        return clean_fallback
        

    def parse(self, raw_response: Dict[str, Any], cnr: str) -> Dict[str, Any]:
        data_list = raw_response.get("data", [])

        main_details_raw: Dict[str, Any] = {}
        litigants_raw: List[Dict[str, Any]] = []
        respondants_raw: List[Dict[str, Any]] = []
        advocates_raw: List[Dict[str, Any]] = []
        order_history_raw: List[Dict[str, Any]] = []
        classification_raw: List[Dict[str, Any]] = []
        lowercourt_raw: List[Dict[str, Any]] = []
        officedetails_raw: List[Dict[str, Any]] = []
        linkedmatters_raw: List[Dict[str, Any]] = []
        lpamatters_raw: List[Dict[str, Any]] = []
        certifiedcopy_raw: Any = []

        for item in data_list:
            if not isinstance(item, dict):
                continue
            if "maindetails" in item and item["maindetails"]:
                main_details_raw = item["maindetails"][0]
            elif "litigant" in item and item["litigant"]:
                litigants_raw.extend(item["litigant"])
            elif "respondant" in item and item["respondant"]:
                respondants_raw.extend(item["respondant"])
            elif "advocate" in item and item["advocate"]:
                advocates_raw.extend(item["advocate"])
            elif "orderhistory" in item and item["orderhistory"]:
                order_history_raw.extend(item["orderhistory"])
            elif "classification" in item and item["classification"]:
                classification_raw.extend(item["classification"])
            elif "lowercourt" in item and item["lowercourt"]:
                lowercourt_raw.extend(item["lowercourt"])
            elif "officedetails" in item and item["officedetails"]:
                officedetails_raw.extend(item["officedetails"])
            elif "linkedmatterscp" in item and item["linkedmatterscp"]:
                linkedmatters_raw.extend(item["linkedmatterscp"])
            elif "lpamatters" in item and item["lpamatters"]:
                lpamatters_raw.extend(item["lpamatters"])
            elif "certifiedcopy" in item:
                cc = item["certifiedcopy"]
                if isinstance(cc, list):
                    certifiedcopy_raw.extend(cc)

        clean_cnr = self._extract_cnr(raw_response, main_details_raw, cnr)

        # Petitioners & Respondents lists
        pet_names = [l.get("litigantname", "").strip() for l in litigants_raw if l.get("litigantname")]
        res_names = [r.get("respondantname", "").strip() for r in respondants_raw if r.get("respondantname")]

        # Advocates
        pet_advs = []
        res_advs = []
        all_advs = []

        for adv in advocates_raw:
            adv_name = adv.get("advocatename", "").strip()
            if not adv_name:
                continue
            if adv_name not in all_advs:
                all_advs.append(adv_name)

            lit_type = adv.get("litiganttype", "") or ""
            lit_code = str(adv.get("litiganttypecode", "") or "")
            if "Appellant" in lit_type or "Petitioner" in lit_type or lit_code == "1":
                if adv_name not in pet_advs:
                    pet_advs.append(adv_name)
            elif "Defendant" in lit_type or "Respondent" in lit_type or lit_code == "2":
                if adv_name not in res_advs:
                    res_advs.append(adv_name)

        # Case Type & Numbers
        case_type = main_details_raw.get("casetype", "") or ""
        reg_number = str(main_details_raw.get("casenumber", "") or "").strip()
        reg_year = str(main_details_raw.get("caseyear", "") or "").strip()
        case_number = (
            f"{case_type}/{reg_number}/{reg_year}"
            if case_type and reg_number and reg_year
            else main_details_raw.get("stampnumber", "")
        )

    

        # 1. AppealMatter
        appeal_matter_list = []
        for lpa in lpamatters_raw:
            appeal_matter_list.append({
                "CaseDetail": lpa.get("casedescriptionlm", "") or "",
                "CaseStatus": lpa.get("statusnamelm", "") or "",
                "DisposedDate": lpa.get("disposaldatelm", "") or "",
                "JudgeName": lpa.get("JUDGESlm", "") or "",
                "cinolm": lpa.get("cinolm", "") or "",
            })
        appeal_matter = {"AppealMatter": appeal_matter_list}

        # 2. Orders
        parsed_orders = []
        for ord_item in order_history_raw:
            order_date = str(ord_item.get("orderdate") or ord_item.get("dsdate") or "").strip()
            nc_val = str(ord_item.get("nc", "") or "").strip()

            order_url = ""
              # Condition 1: Agar raw response ke "nc" field me direct HTTP link hai
            if nc_val and nc_val != "-" and nc_val.startswith("http"):
                order_url = nc_val
              # Condition 2: Agar direct link nahi hai, toh S3 Bucket PDF URL construct karo
            elif order_date and clean_cnr:
                date_formatted = order_date.replace("/", "_").replace("-", "_")
                if not date_formatted.endswith(".pdf"):
                    date_formatted += ".pdf"
                order_url = (f"{S3_BASE_URL}/"f"onprem/IND_HC/{COURT_ID}/{SUB_COURT_ID}/"f"{clean_cnr}/{date_formatted}")

            parsed_orders.append({
                "CaseDetail": ord_item.get("descriptionoh") or case_number,
                "JUDGENAME": ord_item.get("judgesoh", "") or "",
                "OrderDate": order_date,
                "CavJudgement": ord_item.get("cavjudgement", "N"),
                "Judgement": "ORDER" if ord_item.get("judgement") in ["N", "ORDER", None] else str(ord_item.get("judgement")),
                "Question": ord_item.get("questions", "-"),
                "transferred": ord_item.get("transferred", "Y"),
                "transferredby": ord_item.get("transferredby", ""),
                "CNR": ord_item.get("ccinoh") or clean_cnr,
                "OrderNumber": str(ord_item.get("ordernooh", "1")),
                "NC": nc_val if nc_val else "-",
                "OrderURL": order_url,
            })

        # 3. classification
        classifications = []
        acts = []
        for c in classification_raw:
            desc = (c.get("description") or "").strip()
            code = str(c.get("classcode") or "")
            if code == "0":
                if desc and desc not in classifications:
                    classifications.append(desc)
            else:
                if desc and desc not in acts:
                    acts.append(desc)
        classification_dict = {
            "Classification": classifications,
            "Acts": acts,
        }

        # 4. CommonCaseDetails
        pet_title = pet_names[0] if pet_names else ""
        res_title = res_names[0] if res_names else ""
        case_title = f"{pet_title} vs {res_title}" if pet_title and res_title else ""

        next_hearing = main_details_raw.get("listingdate", "") or "-"
        disposal_date = main_details_raw.get("disposaldate", "") or "-"

        common_case_details = {
            "CNR": clean_cnr,
            "CaseNumber": case_number,
            "FillingDate": main_details_raw.get("presentdate") or None,
            "NextHearingDate": next_hearing if next_hearing != "" else "-",
            "SubCourtId": SUB_COURT_ID,
            "CourtId": COURT_ID,
            "DiaryNumber": None,
            "DiaryYear": None,
            "DisposedDate": disposal_date if disposal_date != "" else "-",
            "DecisionDate": None,
            "CaseStatus": main_details_raw.get("casestatus", "") or "",
            "Petitioner": pet_names,
            "Respondent": res_names,
            "CaseTitle": case_title,
            "PetitionerAdvocates": pet_advs,
            "RespondentAdvocates": res_advs,
            "Advocates": all_advs,
        }

        # 5. mainDetails
        casedesc = main_details_raw.get("casedesc", "") or ""
        main_details_list = [{
            "CNR": clean_cnr,
            "FillingNumber": main_details_raw.get("stampnumber", "") or "",
            "RegistrationDate": main_details_raw.get("registrationdate", "") or "",
            "NextHearingDate": next_hearing,
            "PresentedOn": main_details_raw.get("presentdate", "") or "",
            "Coram": main_details_raw.get("judges", "") or "",
            "CaseTitle": f"{casedesc} -" if casedesc else "",
            "CaseNumber": case_number,
            "CasetypeDescription": casedesc,
            "CaseStatus": main_details_raw.get("casestatus", "") or "",
            "DisposedDate": disposal_date,
            "CourtNumber": str(main_details_raw.get("courtcode", "") or "").strip(),
            "Bench": main_details_raw.get("benchname", "") or "",
            "MainNumber": main_details_raw.get("mainnumber", "                "),
            "MainCaseDescription": main_details_raw.get("maincasedesc", "-") or "-",
            "PurposeOfListing": main_details_raw.get("stagename", "") or "",
            "StageCode": str(main_details_raw.get("stagecode", "") or "").strip(),
            "DistrictName": main_details_raw.get("districtname", "") or "",
        }]

        # 6. lowercourtDetail
        lc_list = []
        for lc in lowercourt_raw:
            lc_list.append({
                "LowerCourtCaseDetail": lc.get("lccasedescription", "") or "",
                "LowerCourtName": lc.get("lowercourtname", "") or "",
                "LowerCourtJudgeName": lc.get("lcjudgename", "") or "",
                "JudgementDate": lc.get("LCJUDGEMENTDATE", "") or "",
            })
        lowercourt_detail = {"LowerCourtDetail": lc_list}

        # 7. courtproceedingDetail
        cp_list = []
        for cp in linkedmatters_raw:
            cp_list.append({
                "NotifiedDate": cp.get("PROCEEDINGDATElmcp", "") or "",
                "CourtCode": str(cp.get("COURTCODElmcp", "") or "").strip(),
                "BoardNumber": str(cp.get("BOARDSRNOlmcp", "") or "").strip(),
                "Stage": cp.get("STAGENAMElmcp", "") or "",
                "Action": cp.get("ACTIONNAMElmcp", "") or "",
                "Coram": cp.get("JUDGESlmcp", "") or "",
            })

        # 8. officedetails
        od_list = []
        for od in officedetails_raw:
            doc_details = od.get("documentdetails", "") or ""
            doc_details_clean = re.sub(r'^<P>-', '', doc_details).strip()
            od_list.append({
                "advcd": str(od.get("advcd", "") or ""),
                "FillingDate": od.get("FILINGDATE", "") or "",
                "DocumentName": od.get("DOCUMENTNAME", "") or "",
                "AdvocateName": od.get("ADVOCATEDISPLAYNAME", "") or "",
                "CourtFeeOnDocumenet": str(od.get("documentfee", "") or ""),
                "DocumentDetails": doc_details_clean,
                "LitigantType": od.get("litgantypes", "") or "",
            })

        obj_message = {
            "mainDetails": main_details_list,
            "courtproceedingDetail": cp_list,
            "AppealMatter": appeal_matter,
            "Orders": parsed_orders,
            "classification": classification_dict,
            "PetitionerAdvocates": pet_advs,
            "CommonCaseDetails": common_case_details,
            "lowercourtDetail": lowercourt_detail,
            "RespondentAdvocates": res_advs,
            "Respondent": res_names,
            "officedetails": od_list,
            "Petitioner": pet_names,
            "certifiedcopy": certifiedcopy_raw if isinstance(certifiedcopy_raw, list) else [],
        }

        return {
            "objMessage": obj_message,
            "messageDescription": "sending you filtered response",
            "refNumber": "-1",
            "exceptionCode": -1,
            "exceptionDescription": "No exceptions were encountered",
            "solution": "",
            "totalLength": "",
            "requestId": str(uuid.uuid4()),
        }

    def parse_litigant_search(self, html_content: str) -> Dict[str, Any]:
        """
        Parses the HTML table returned by SearchLitigant.
        Extracts cases with CNR, case detail, status, litigant name, hearing date, litigant type, district.
        Also parses total count if present in '###<total_count>###<counter>'.
        """
        total_count = 0
        if "###" in html_content:
            parts = html_content.split("###")
            if len(parts) > 1 and parts[1].strip().isdigit():
                total_count = int(parts[1].strip())

        soup = BeautifulSoup(html_content, "html.parser")
        rows = soup.select("table#master tbody tr")

        cases = []
        for tr in rows:
            onclick = tr.get("onclick", "") or ""
            # e.g. javascript:GoButtonConfirmation("GJHC240185632024");
            cnr_match = re.search(r'GoButtonConfirmation\(["\']([^"\']+)["\']\)', onclick)
            cnr = cnr_match.group(1).strip() if cnr_match else ""

            tds = [td.get_text(strip=True) for td in tr.find_all("td")]
            if not tds:
                continue

            case_detail = tds[0] if len(tds) > 0 else ""
            status = tds[1] if len(tds) > 1 else ""
            litigant_name = tds[2] if len(tds) > 2 else ""
            hearing_date = tds[3] if len(tds) > 3 else ""
            litigant_type = tds[4] if len(tds) > 4 else ""
            district = tds[5] if len(tds) > 5 else ""

            cases.append({
                "CNR": cnr,
                "CaseNumber": case_detail,
                "CaseStatus": status,
                "LITIGANTNAME": litigant_name,
                "HearingDate": hearing_date,
                "LITIGANT TYPE": litigant_type,
                "DISTRICTNAME": district,
            })

        if total_count == 0 and cases:
            total_count = len(cases)

        return {
            "total_count": total_count,
            "count": len(cases),
            "cases": cases,
        }
