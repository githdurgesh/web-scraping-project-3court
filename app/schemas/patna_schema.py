from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class PatnaCaseItem(BaseModel):
    sr_no: str = Field("", description="Serial number in the results")
    token_no: str = Field("", description="Token / Filing Number e.g. MA-1215/2022")
    case_number: str = Field("", description="Case / Token Number")
    petitioner: Optional[str] = Field("", description="Petitioner name")
    respondent: Optional[str] = Field("", description="Respondent name")
    party_name: str = Field("", description="Party name (Petitioner vs Respondent)")
    filing_date: Optional[str] = Field("", description="Filing date e.g. 21-Jan-2022")
    petitioner_advocate: Optional[str] = Field("", description="Petitioner Advocate name(s)")
    respondent_advocate: Optional[str] = Field("", description="Respondent Advocate name(s)")
    cnr: Optional[str] = Field("", description="16-character CNR number decoded from CINO (e.g. BRHC010048452022)")
    CNR: Optional[str] = Field("", description="16-character CNR number")
    cino: Optional[str] = Field("", description="Raw / Encoded CINO identifier")
    case_status_url: Optional[str] = Field("", description="Direct URL to defect / case status details")
    year: Optional[str] = Field("", description="Year of the case")
    court_no: Optional[str] = Field("", description="Court Room Number")
    judges: List[str] = Field(default_factory=list, description="Presiding Judges")
    stage: Optional[str] = Field("", description="Hearing stage")
    hearing_time: Optional[str] = Field("", description="Listing time")
    current_position: Optional[str] = Field("", description="Current position / defect status")

    model_config = ConfigDict(populate_by_name=True)


class PatnaDateOption(BaseModel):
    value: str = Field(..., description="Option value for form e.g. '0' or '2214'")
    date_text: str = Field(..., description="Display date text e.g. '28-09-2026'")


class PatnaPartySearchRequest(BaseModel):
    party_name: str = Field(..., description="Party or litigant name to search for (e.g. 'tata', 'Singh')")
    year: Optional[str] = Field(None, description="Year of the case e.g. '2022'")
    date: Optional[str] = Field(None, description="Optional date parameter for backward compatibility")


class PatnaPartySearchResponse(BaseModel):
    total_count: int = Field(..., description="Total matching cases found")
    party_name: str = Field(..., description="Searched party name")
    year: Optional[str] = Field("", description="Searched year")
    selected_date: Optional[str] = Field("", description="Date info if applicable")
    date_value: Optional[str] = Field("", description="Option value submitted")
    cases: List[PatnaCaseItem] = Field(default_factory=list, description="List of matching cases")

