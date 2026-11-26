import json
from datetime import date
from pathlib import Path

import pytest

from omda_tools import checks, signing
from omda_tools.validate import check_examples, errors

ROOT = Path(__file__).resolve().parents[2]
REG = json.loads((ROOT / "registry" / "checks.json").read_text())


def _run(check_id, vector):
    i = vector["input"]
    if check_id == "icao9303.mrz":
        return checks.icao9303_mrz(*i)
    if check_id == "cross.mrz_number":
        mrz = checks.TD3("", "", "", "", i["mrz"], "", "", "", "", "", {})
        return checks.mrz_vs_printed_number(mrz, i["printed"])
    if check_id == "consistency.issue_before_expiry":
        return checks.dates_ordered(date.fromisoformat(i["issue"]), date.fromisoformat(i["expiry"]))
    if check_id == "format.iso3166_alpha3":
        return checks.iso3166_alpha3(i)
    return checks.CORE[check_id](i)


@pytest.mark.parametrize(
    "check_id,vector",
    [(c["id"], v) for c in REG["checks"] for v in c["test_vectors"]],
)
def test_registry_vectors(check_id, vector):
    assert _run(check_id, vector) == vector["result"]


def test_registry_valid():
    assert errors("registry#checkRegistry", REG) == []
    models = json.loads((ROOT / "registry" / "models.json").read_text())
    assert errors("registry#modelRegistry", models) == []


def test_runtimes_listed():
    runtimes = json.loads((ROOT / "registry" / "runtimes.json").read_text())
    assert errors("registry#runtimeRegistry", runtimes) == []
    for r in runtimes["runtimes"]:
        manifest = json.loads((ROOT / "registry" / r["manifest"]).read_text())
        jwk = json.loads((ROOT / "registry" / r["publisher_key"]).read_text())
        assert errors("conformance-manifest", manifest) == []
        assert (manifest["level"], manifest["tier"], manifest["runtime"]["version"]) == (r["level"], r["tier"], r["version"])
        assert jwk.get("kid") == r["kid"]


def test_runtime_signatures():
    """OD-044: each listed manifest's detached ES256 JWS verifies with its publisher key, and any edit breaks it."""
    for r in json.loads((ROOT / "registry" / "runtimes.json").read_text())["runtimes"]:
        manifest = json.loads((ROOT / "registry" / r["manifest"]).read_text())
        jwk = json.loads((ROOT / "registry" / r["publisher_key"]).read_text())
        assert signing.verify_report(manifest, jwk) == r["kid"]
        tampered = json.loads(json.dumps(manifest))
        tampered["gaps"] = tampered["gaps"][1:]
        with pytest.raises(Exception):
            signing.verify_report(tampered, jwk)


@pytest.mark.parametrize("value, expected", [
    ({"b": 1, "a": [True, None, "é"]}, '{"a":[true,null,"é"],"b":1}'),
    (1.0, "1"), (0.818, "0.818"), (1e-7, "1e-7"), (0.000001, "0.000001"), (1e16, "10000000000000000"), (1e21, "1e+21"), (-0.5, "-0.5"),
    ({"\U0001F600": 1, "\uFFFF": 2}, '{"\U0001F600":1,"\uFFFF":2}'),
])
def test_canonical_json(value, expected):
    assert signing.canonical_json(value) == expected


@pytest.mark.parametrize("path", sorted((ROOT / "registry" / "profiles").glob("*.json")), ids=lambda p: p.name)
def test_profiles_valid(path):
    assert errors("profile", json.loads(path.read_text())) == []


def test_profile_checks_exist():
    ids = {c["id"] for c in REG["checks"]}
    for path in (ROOT / "registry" / "profiles").glob("*.json"):
        prof = json.loads(path.read_text())
        for dt in prof["doc_types"].values():
            for f in dt["fields"].values():
                for c in f.get("checks", []) + [x for v in f.get("jurisdiction_checks", {}).values() for x in v]:
                    assert c in ids, f"{path.name}: unknown check {c}"
            for k in dt["entity_key"]:
                assert k in dt["fields"]


def test_examples():
    assert check_examples() == 0


def test_td3_parse():
    t = checks.parse_td3(
        "P<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<<<<<<",
        "L898902C36UTO7408122F1204159ZE184226B<<<<<10",
    )
    assert t.valid and t.number == "L898902C3" and t.surname == "ERIKSSON" and t.given_names == "ANNA MARIA"
    assert checks.yymmdd_to_date(t.date_of_birth, today=date(2026, 11, 26)) == date(1974, 8, 12)


def test_mrz_outranks_print():
    t = checks.parse_td3(
        "P<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<<<<<<",
        "L898902C36UTO7408122F1204159ZE184226B<<<<<10",
    )
    assert checks.mrz_vs_printed_number(t, "L898902C8") == "fail"


def test_fixture_generators():
    eid = "78419900000001" + checks.luhn_check_digit("78419900000001")
    aad = "99990000001" + checks.verhoeff_check_digit("99990000001")
    assert checks.luhn(eid) == "pass" and checks.verhoeff(aad) == "pass"
