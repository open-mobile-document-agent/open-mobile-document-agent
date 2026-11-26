import json
from datetime import date
from pathlib import Path

import pytest

from omda_tools import checks
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
    """OD-044: each listed manifest's detached ES256 JWS verifies with its publisher key."""
    import base64, hashlib
    ec = pytest.importorskip("cryptography.hazmat.primitives.asymmetric.ec")
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric.utils import encode_dss_signature
    d = lambda s: base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))
    e = lambda b: base64.urlsafe_b64encode(b).rstrip(b"=").decode()
    for r in json.loads((ROOT / "registry" / "runtimes.json").read_text())["runtimes"]:
        manifest = json.loads((ROOT / "registry" / r["manifest"]).read_text())
        jwk = json.loads((ROOT / "registry" / r["publisher_key"]).read_text())
        header, empty, sig = manifest["report"]["signature"].split(".")
        assert empty == "" and json.loads(d(header)) == {"alg": "ES256", "typ": "omda-conformance+jws", "kid": r["kid"]}
        thumb = json.dumps({"crv": jwk["crv"], "kty": jwk["kty"], "x": jwk["x"], "y": jwk["y"]}, separators=(",", ":"))
        assert e(hashlib.sha256(thumb.encode()).digest()) == r["kid"]
        manifest["report"]["signature"] = ""
        payload = json.dumps(manifest, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
        key = ec.EllipticCurvePublicNumbers(int.from_bytes(d(jwk["x"]), "big"), int.from_bytes(d(jwk["y"]), "big"), ec.SECP256R1()).public_key()
        raw = d(sig)
        key.verify(encode_dss_signature(int.from_bytes(raw[:32], "big"), int.from_bytes(raw[32:], "big")), f"{header}.{e(payload)}".encode(), ec.ECDSA(hashes.SHA256()))


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
