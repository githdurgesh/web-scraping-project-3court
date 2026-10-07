from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class GujaratCnrRequest(BaseModel):
    cnr: str = Field(
        ...,
        description="Gujarat HC CNR number e.g. GJHC240243912022"
    )


class AppealMatterItem(BaseModel):
    CaseDetail: Optional[str] = ""
    CaseStatus: Optional[str] = ""
    DisposedDate: Optional[str] = ""
    JudgeName: Optional[str] = ""
    cinolm: Optional[str] = ""


class AppealMatterWrapper(BaseModel):
    AppealMatter: List[AppealMatterItem] = Field(default_factory=list)


class OrderItem(BaseModel):
    CaseDetail: Optional[str] = ""
    JUDGENAME: Optional[str] = ""
    OrderDate: Optional[str] = ""
    Petitioner: Optional[str] = ""
    Respondent: Optional[str] = ""
    EmailSent: Optional[str] = ""
    Details: Optional[str] = ""
    CavJudgement: Optional[str] = "N"
    Judgement: Optional[str] = "ORDER"
    Question: Optional[str] = "-"
    transferred: Optional[str] = "Y"
    transferredby: Optional[str] = ""
    CNR: Optional[str] = ""
    OrderNumber: Optional[str] = "1"
    NC: Optional[str] = "-"
    OrderURL: Optional[str] = ""


class ClassificationWrapper(BaseModel):
    Classification: List[str] = Field(default_factory=list)
    Acts: List[str] = Field(default_factory=list)


class CommonCaseDetails(BaseModel):
    CNR: str
    CaseNumber: Optional[str] = ""
    FillingDate: Optional[Any] = None
    NextHearingDate: Optional[str] = "-"
    SubCourtId: Optional[str] = "20"
    CourtId: Optional[str] = "2"
    DiaryNumber: Optional[Any] = None
    DiaryYear: Optional[Any] = None
    DisposedDate: Optional[str] = "-"
    DecisionDate: Optional[Any] = None
    CaseStatus: Optional[str] = ""
    Petitioner: List[str] = Field(default_factory=list)
    Respondent: List[str] = Field(default_factory=list)
    CaseTitle: Optional[str] = ""
    PetitionerAdvocates: List[str] = Field(default_factory=list)
    RespondentAdvocates: List[str] = Field(default_factory=list)
    Advocates: List[str] = Field(default_factory=list)


class MainDetailItem(BaseModel):
    CNR: Optional[str] = ""
    FillingNumber: Optional[str] = ""
    RegistrationDate: Optional[str] = ""
    NextHearingDate: Optional[str] = "-"
    PresentedOn: Optional[str] = ""
    Coram: Optional[str] = ""
    CaseTitle: Optional[str] = ""
    CaseNumber: Optional[str] = ""
    CasetypeDescription: Optional[str] = ""
    CaseStatus: Optional[str] = ""
    DisposedDate: Optional[str] = "-"
    CourtNumber: Optional[str] = ""
    Bench: Optional[str] = ""
    MainNumber: Optional[str] = "                "
    MainCaseDescription: Optional[str] = "-"
    PurposeOfListing: Optional[str] = ""
    StageCode: Optional[str] = ""
    DistrictName: Optional[str] = ""


class LowerCourtDetailItem(BaseModel):
    LowerCourtCaseDetail: Optional[str] = ""
    LowerCourtName: Optional[str] = ""
    LowerCourtJudgeName: Optional[str] = ""
    JudgementDate: Optional[str] = ""


class LowerCourtDetailWrapper(BaseModel):
    LowerCourtDetail: List[LowerCourtDetailItem] = Field(default_factory=list)


class CourtProceedingItem(BaseModel):
    NotifiedDate: Optional[str] = ""
    CourtCode: Optional[str] = ""
    BoardNumber: Optional[str] = ""
    Stage: Optional[str] = ""
    Action: Optional[str] = ""
    Coram: Optional[str] = ""


class OfficeDetailItem(BaseModel):
    advcd: Optional[str] = ""
    FillingDate: Optional[str] = ""
    DocumentName: Optional[str] = ""
    AdvocateName: Optional[str] = ""
    CourtFeeOnDocumenet: Optional[str] = ""
    DocumentDetails: Optional[str] = ""
    LitigantType: Optional[str] = ""


class ObjMessage(BaseModel):
    AppealMatter: Optional[AppealMatterWrapper] = Field(default_factory=AppealMatterWrapper)
    classification: Optional[ClassificationWrapper] = Field(default_factory=ClassificationWrapper)
    PetitionerAdvocates: List[str] = Field(default_factory=list)
    CommonCaseDetails: CommonCaseDetails
    mainDetails: List[MainDetailItem] = Field(default_factory=list)
    lowercourtDetail: Optional[LowerCourtDetailWrapper] = Field(default_factory=LowerCourtDetailWrapper)
    courtproceedingDetail: List[CourtProceedingItem] = Field(default_factory=list)
    RespondentAdvocates: List[str] = Field(default_factory=list)
    Respondent: List[str] = Field(default_factory=list)
    officedetails: List[OfficeDetailItem] = Field(default_factory=list)
    Petitioner: List[str] = Field(default_factory=list)
    Orders: List[OrderItem] = Field(default_factory=list)
    certifiedcopy: List[Any] = Field(default_factory=list)


class GujaratStandardResponse(BaseModel):
    objMessage: ObjMessage
    messageDescription: str = "sending you filtered response"
    refNumber: str = "-1"
    exceptionCode: int = -1
    exceptionDescription: str = "No exceptions were encountered"
    solution: str = ""
    totalLength: str = ""
    requestId: str


class PartySearchItem(BaseModel):
    CNR: str = Field("", alias="CNR")
    CaseNumber: str = Field("", alias="CaseNumber")
    CaseStatus: str = Field("", alias="CaseStatus")
    LITIGANTNAME: str = Field("", alias="LITIGANTNAME")
    HearingDate: str = Field("", alias="HearingDate")
    LITIGANT_TYPE: str = Field("", alias="LITIGANT TYPE")
    DISTRICTNAME: str = Field("", alias="DISTRICTNAME")

    model_config = ConfigDict(populate_by_name=True, by_alias=True)


class GujaratLitigantRequest(BaseModel):
    search_string: str = Field(..., description="Party / Litigant name (e.g. TATA)")
    from_year: str = Field(..., description="Start year (e.g. 2022)")
    to_year: str = Field(..., description="End year (e.g. 2025)")


class GujaratLitigantCaseItem(BaseModel):
    cnr: str = Field(..., description="Case CNR / CCIN number e.g. GJHC240185632024")
    case_detail: str = Field(..., description="Case detail number e.g. R/FA/1643/2024")
    status: str = Field(..., description="PENDING / DISPOSED")
    litigant_name: str = Field(..., description="Name of party/litigant")
    hearing_date: str = Field(..., description="Next or past hearing date")
    litigant_type: str = Field(..., description="PETITIONER / RESPONDENT")
    district: str = Field(..., description="District name e.g. SURAT")
    details: Optional[GujaratStandardResponse] = Field(default=None, description="Detailed case data if fetched")


class GujaratLitigantResponse(BaseModel):
    total_count: int
    count: int
    search_string: str
    from_year: str
    to_year: str
    cases: List[GujaratLitigantCaseItem]


class CaseNumberSearchRequest(BaseModel):
    side: str = Field(..., description="Side (e.g. R, CR, P, C)")
    caseType: str = Field(..., description="Case Type ID (e.g. 9 or 1)")
    caseNumber: str = Field(..., description="Case Number (e.g. 1)")
    caseYear: str = Field(..., description="Case Year (e.g. 2022)")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "side": "string",
                "caseType": "string",
                "caseNumber": "string",
                "caseYear": "string",
            }
        }
    )


