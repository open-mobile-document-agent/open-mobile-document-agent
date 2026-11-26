"""Signed conformance reports (§12, OD-044): RFC 8785 canonical form, RFC 7638 thumbprint, detached ES256 JWS verification.

`canonical_json` and `jwk_thumbprint` need only the standard library; `verify_report` needs the `cryptography` package
(`pip install "omda-tools[sign]"`).
"""
from __future__ import annotations

import base64
import hashlib
import json
import math
from decimal import Decimal

REPORT_JWS_TYP = "omda-conformance+jws"


def _b64u(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()


def _unb64u(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def _number(x: int | float) -> str:
    """ECMAScript Number::toString, as RFC 8785 §3.2.2.3 requires."""
    if isinstance(x, int):
        return str(x)
    if not math.isfinite(x):
        raise ValueError("RFC 8785: non-finite number")
    if x == 0:
        return "0"
    sign = "-" if x < 0 else ""
    _, digits, exp = Decimal(repr(abs(x))).normalize().as_tuple()
    s = "".join(map(str, digits))
    k, n = len(s), exp + len(s)
    if k <= n <= 21:
        out = s + "0" * (n - k)
    elif 0 < n <= 21:
        out = f"{s[:n]}.{s[n:]}"
    elif -6 < n <= 0:
        out = "0." + "0" * -n + s
    else:
        e = n - 1
        out = s[0] + (f".{s[1:]}" if k > 1 else "") + f"e{'+' if e >= 0 else '-'}{abs(e)}"
    return sign + out


def canonical_json(v) -> str:
    """RFC 8785 (JCS): keys sorted by UTF-16 code units, no whitespace, ECMAScript number form, minimal string escaping."""
    if v is None or isinstance(v, bool) or isinstance(v, str):
        return json.dumps(v, ensure_ascii=False)
    if isinstance(v, (int, float)):
        return _number(v)
    if isinstance(v, list):
        return "[" + ",".join(canonical_json(x) for x in v) + "]"
    if isinstance(v, dict):
        keys = sorted(v, key=lambda k: k.encode("utf-16-be"))
        return "{" + ",".join(f"{json.dumps(k, ensure_ascii=False)}:{canonical_json(v[k])}" for k in keys) + "}"
    raise TypeError(f"not JSON: {type(v).__name__}")


def jwk_thumbprint(jwk: dict) -> str:
    """RFC 7638 thumbprint of an EC public key: SHA-256, base64url without padding."""
    members = {"crv": jwk["crv"], "kty": jwk["kty"], "x": jwk["x"], "y": jwk["y"]}
    return _b64u(hashlib.sha256(canonical_json(members).encode()).digest())


def signing_input(manifest: dict, header_b64: str) -> bytes:
    """`<protected header as received>.<base64url of the canonical manifest with report.signature = "">`."""
    blank = {**manifest, "report": {**manifest["report"], "signature": ""}}
    return f"{header_b64}.{_b64u(canonical_json(blank).encode())}".encode()


def verify_report(manifest: dict, jwk: dict) -> str:
    """Verify a manifest's detached ES256 JWS; returns the kid, raises ValueError (or InvalidSignature) when it does not verify."""
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.hazmat.primitives.asymmetric.utils import encode_dss_signature

    parts = manifest["report"]["signature"].split(".")
    if len(parts) != 3 or parts[1] != "":
        raise ValueError("signature is not a detached compact JWS")
    header = json.loads(_unb64u(parts[0]))
    kid = jwk_thumbprint(jwk)
    if header.get("alg") != "ES256" or header.get("typ") != REPORT_JWS_TYP:
        raise ValueError(f"unexpected JWS header: {header}")
    if header.get("kid") != kid:
        raise ValueError("signed with another key")
    if (jwk.get("kty"), jwk.get("crv")) != ("EC", "P-256"):
        raise ValueError("publisher key must be P-256")
    raw = _unb64u(parts[2])
    if len(raw) != 64:
        raise ValueError("ES256 signature must be 64 bytes")
    key = ec.EllipticCurvePublicNumbers(int.from_bytes(_unb64u(jwk["x"]), "big"), int.from_bytes(_unb64u(jwk["y"]), "big"), ec.SECP256R1()).public_key()
    sig = encode_dss_signature(int.from_bytes(raw[:32], "big"), int.from_bytes(raw[32:], "big"))
    key.verify(sig, signing_input(manifest, parts[0]), ec.ECDSA(hashes.SHA256()))
    return kid
