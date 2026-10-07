import bs4, re
from urllib.parse import urljoin
from app.constants import PATNA_HC_BASE_URL

sample_html = """
<table class="w-100" cellspacing="0" border="0" id="ctl00_MainContent_fvCaseStatusCri">
	<tr>
		<td colspan="2">
                        <table width="100%" cellpadding="4" class="CSSCaseStatus w-100">
                            <tr>
                                <td colspan="4" class="HeaderTopCurv">
                                    <strong>PRESENT STATUS OF CNR NO. :
                                        <span id="ctl00_MainContent_fvCaseStatusCri_Label18">BRHC010048452022</span>
                                    </strong>
                                </td>
                            </tr>
                            <tr>
                                <th>Token Number :
                                </th>
                                <td>
                                    <span id="ctl00_MainContent_fvCaseStatusCri_lblCaseNo">MA-1215/2022</span>
                                </td>
                                <th>Status :
                                </th>
                                <td>
                                    <span id="ctl00_MainContent_fvCaseStatusCri_Label5">DEFECTIVE</span>
                                </td>
                            </tr>
                            
                            <tr>
                                <th>Petitioner :
                                </th>
                                <td>
                                    <span id="ctl00_MainContent_fvCaseStatusCri_Label6">Tata AIG General Insurance Company Limited, Purnea</span>
                                </td>
                                <th>District :
                                </th>
                                <td>
                                    <span id="ctl00_MainContent_fvCaseStatusCri_Label2">Kolkata</span>
                                </td>
                            </tr>
                            <tr>
                                <th>Respondent :
                                </th>
                                <td colspan="3">
                                    <span id="ctl00_MainContent_fvCaseStatusCri_Label3">Savitri Devi</span>
                                </td>
                            </tr>
                            <tr>
                                <th>Date of Filing :
                                </th>
                                <td>
                                    <span id="ctl00_MainContent_fvCaseStatusCri_Label1">21-Jan-2022</span>
                                </td>
                                <th>Case No. :
                                </th>
                                <td>
                                    <a id="ctl00_MainContent_fvCaseStatusCri_HyperLink1" href="../CaseStatus/QlJIQzAxMDA0ODQ1MjAyMg==-AOCLfYK--ak1--0z8=">MA-36/2022</a>
                                    <span id="ctl00_MainContent_fvCaseStatusCri_Label4"></span>
                                </td>
                            </tr>
                        </table>
                    </td>
	</tr>
</table>
<table class="dataTable" cellspacing="0" rules="all" border="1" id="ctl00_MainContent_gvDefects">
	<tr>
		<th class="hiddencol" scope="col">Sr No.</th><th scope="col">Scrutiny Date</th><th scope="col">OBJECTION</th><th scope="col">DETAILS</th>
	</tr><tr>
		<td class="hiddencol">2</td><td class="Highlight">24-Feb-2022</td><td>FEE</td><td>e-Court fee of Rs.50/- has been filed</td>
	</tr>
</table>
"""

soup = bs4.BeautifulSoup(sample_html, "html.parser")

cnr_tag = soup.find(id=re.compile(r"Label18$"))
cnr = cnr_tag.get_text(strip=True) if cnr_tag else ""

token_tag = soup.find(id=re.compile(r"lblCaseNo$"))
token_no = token_tag.get_text(strip=True) if token_tag else ""

status_tag = soup.find(id=re.compile(r"Label5$"))
status = status_tag.get_text(strip=True) if status_tag else ""

pet_tag = soup.find(id=re.compile(r"Label6$"))
petitioner = pet_tag.get_text(strip=True) if pet_tag else ""

dist_tag = soup.find(id=re.compile(r"Label2$"))
district = dist_tag.get_text(strip=True) if dist_tag else ""

res_tag = soup.find(id=re.compile(r"Label3$"))
respondent = res_tag.get_text(strip=True) if res_tag else ""

date_tag = soup.find(id=re.compile(r"Label1$"))
filing_date = date_tag.get_text(strip=True) if date_tag else ""

case_no_tag = soup.find(id=re.compile(r"HyperLink1$"))
case_no = case_no_tag.get_text(strip=True) if case_no_tag else ""
case_link = case_no_tag.get("href", "") if case_no_tag else ""
full_link = urljoin(f"{PATNA_HC_BASE_URL}/casesearch/", case_link) if case_link else ""

print("CNR:", cnr)
print("Token:", token_no)
print("Status:", status)
print("Petitioner:", petitioner)
print("Respondent:", respondent)
print("District:", district)
print("Filing Date:", filing_date)
print("Case No:", case_no)
print("Case Link:", full_link)

# Parse defects table
table_defects = soup.find("table", id=re.compile(r"gvDefects", re.I))
defects = []
if table_defects:
    for tr in table_defects.find_all("tr")[1:]:
        tds = tr.find_all("td")
        if len(tds) >= 4:
            defects.append({
                "sr_no": tds[0].get_text(strip=True),
                "scrutiny_date": tds[1].get_text(strip=True),
                "objection": tds[2].get_text(strip=True),
                "details": tds[3].get_text(" ", strip=True),
            })
print("Defects count:", len(defects), defects)
