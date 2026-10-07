import pytest
from app.parser.gauhati_parser import GauhatiParser
from app.service.court_registry import get_court_config, COURT_REGISTRY


def test_gauhati_registry():
    assert "24" in COURT_REGISTRY
    config = get_court_config(court_id="2", sub_court_id="24")
    assert config["court_name"] == "Gauhati High Court"
    assert config["default_court_id"] == "2"
    assert config["party_search_handler"] is not None
    assert config["cnr_search_handler"] is not None
    assert config["supports_cnr"] is True


def test_gauhati_parser_party_search():
    sample_records = [
        {
            "cino": "GAHC010174342026",
            "type_name": "RP(FAM.CT.)",
            "reg_no": 0,
            "reg_year": 0,
            "pet_name": "TATA AIG GENERAL INSURANCE COLTD",
            "res_name": "SMTI DULAN PAUL ALIAS DULAN PAL",
            "pet_adv": "MONDAKINI SAIKIA",
            "res_adv": "",
            "dt_regis": None,
        }
    ]

    parser = GauhatiParser()
    result = parser.parse_party_search(sample_records, search_string="tata")

    assert result["total_count"] == 1
    assert result["count"] == 1
    assert result["search_string"] == "tata"
    assert "Cases" in result

    case = result["Cases"][0]
    assert case["CNR"] == "GAHC010174342026"
    assert case["CaseType"] == "RP(FAM.CT.)"
    assert case["Petitioner"] == "TATA AIG GENERAL INSURANCE COLTD"
    assert case["Respondent"] == "SMTI DULAN PAUL ALIAS DULAN PAL"
    assert case["PetitionerAdvocates"] == "MONDAKINI SAIKIA"
    assert case["RegistrationDate"] == ""


def test_gauhati_cnr_parser_full_structure():
    sample_records = [
        {
            "cino": "GAHC010023122013",
            "type_name": "WP(C)",
            "reg_no": 4091,
            "reg_year": 2013,
            "pet_name": "TATA MAGIC OWNERS ASSOCIATION and 2 ORS",
            "res_name": "THE STATE OF ASSAM AND 3 ORS",
            "pet_adv": "MR.I A TALUKDAR",
            "res_adv": "MS.U BARUAH",
            "dt_regis": "23-07-2013",
        }
    ]

    parser = GauhatiParser()
    result = parser.parse_cnr_search(sample_records, cnr="GAHC010023122013")

    assert "Cases" in result
    cases = result["Cases"]
    assert len(cases) == 1
    case = cases[0]

    assert case["CNR"] == "GAHC010023122013"
    assert case["Case_Number"] == "WP(C)/4091/2013"
    assert case["RegistrationDate"] == "2013-07-23"
    assert case["PetitionerAdvocates"] == "MR.I A TALUKDAR"
    assert case["Petitioner"] == "TATA MAGIC OWNERS ASSOCIATION and 2 ORS"
    assert case["RegistrationNumber"] == "4091"
    assert case["RegistrationYear"] == "2013"
    assert case["RespondentAdvocates"] == "MS.U BARUAH"
    assert case["Respondent"] == "THE STATE OF ASSAM AND 3 ORS"
    assert case["CaseType"] == "WP(C)"

    assert "CaseDetails" in case
    assert len(case["CaseDetails"]) == 1
    detail = case["CaseDetails"][0]
    assert detail["CNR"] == "GAHC010023122013"
    assert detail["CourtNumber"] == "0"
    assert detail["CaseNumber"] == "WP(C)/4091/2013"
    assert detail["Petitioner"] == "TATA MAGIC OWNERS ASSOCIATION and 2 ORS"
    assert detail["Respondent"] == "THE STATE OF ASSAM AND 3 ORS"
    assert detail["RegistrationDate"] == "2013-07-23"
    assert detail["PetitionerAdvocates"] == "MR.I A TALUKDAR"

    assert "PartyDetails" in case
    assert case["PartyDetails"][0]["Petitioner"] == "TATA MAGIC OWNERS ASSOCIATION and 2 ORS"
    assert case["PartyDetails"][0]["Respondent"] == "THE STATE OF ASSAM AND 3 ORS"

    assert case["CaseTitle"] == "TATA MAGIC OWNERS ASSOCIATION and 2 ORS v/s THE STATE OF ASSAM AND 3 ORS"
    assert "MR.I A TALUKDAR" in case["Advocates"]
    assert "MS.U BARUAH" in case["Advocates"]


def test_gauhati_case_number_parser():
    sample_records = [
        {
            "cino": "GAHC010064362017",
            "type_name": "Test.App.",
            "reg_no": 2,
            "reg_year": 2023,
            "pet_name": "SMTI PURABI RAJBONGSHI",
            "res_name": "SRI BIMAL GOHAIN and 3 ORS",
            "pet_adv": "MS. P SAHARIA",
            "res_adv": "MR B PUSHILAL",
            "dt_regis": "10-02-2023",
        },
        {
            "cino": "GAHC010244512018",
            "type_name": "Intest.Cas.",
            "reg_no": 2,
            "reg_year": 2023,
            "pet_name": "SMTI LILA DEVI",
            "res_name": "SMTI MOINA ENGLENGPI AND 5 ORS",
            "pet_adv": "MR. U SAIKIA",
            "res_adv": "MR. I H BARBHUIYA",
            "dt_regis": "09-03-2023",
        },
    ]

    parser = GauhatiParser()
    result = parser.parse_case_number_search(
        sample_records,
        case_type="2",
        case_number="2",
        case_year="2023",
    )

    assert "Cases" in result
    cases = result["Cases"]
    assert len(cases) == 2

    case1 = cases[0]
    assert case1["CNR"] == "GAHC010064362017"
    assert case1["Case_Number"] == "Test.App./2/2023"
    assert case1["CaseType"] == "Test.App."
    assert case1["RegistrationNumber"] == "2"
    assert case1["RegistrationYear"] == "2023"
    assert case1["Petitioner"] == "SMTI PURABI RAJBONGSHI"
    assert case1["Respondent"] == "SRI BIMAL GOHAIN and 3 ORS"
    assert case1["PetitionerAdvocates"] == "MS. P SAHARIA"
    assert case1["RespondentAdvocates"] == "MR B PUSHILAL"
    assert case1["RegistrationDate"] == "2023-02-10"

    case2 = cases[1]
    assert case2["CNR"] == "GAHC010244512018"
    assert case2["Case_Number"] == "Intest.Cas./2/2023"
    assert case2["CaseType"] == "Intest.Cas."
    assert case2["Petitioner"] == "SMTI LILA DEVI"
    assert case2["Respondent"] == "SMTI MOINA ENGLENGPI AND 5 ORS"
    assert case2["PetitionerAdvocates"] == "MR. U SAIKIA"
    assert case2["RespondentAdvocates"] == "MR. I H BARBHUIYA"
    assert case2["RegistrationDate"] == "2023-03-09"


