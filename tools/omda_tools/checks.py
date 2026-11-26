"""Reference implementations of the OMDA v0.1 core check registry (§6).

All checks are deterministic, offline and model-free.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date

PASS, FAIL, NA = "pass", "fail", "not_applicable"


# ---------------------------------------------------------------- checksum

def luhn(number: str) -> str:
    """Luhn mod 10. Used by e.g. the UAE Emirates ID (jurisdiction `ae`)."""
    digits = re.sub(r"[\s-]", "", number)
    if not digits.isdigit() or len(digits) < 2:
        return NA
    total = 0
    for i, ch in enumerate(reversed(digits)):
        d = int(ch)
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return PASS if total % 10 == 0 else FAIL


_V_D = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9], [1, 2, 3, 4, 0, 6, 7, 8, 9, 5],
    [2, 3, 4, 0, 1, 7, 8, 9, 5, 6], [3, 4, 0, 1, 2, 8, 9, 5, 6, 7],
    [4, 0, 1, 2, 3, 9, 5, 6, 7, 8], [5, 9, 8, 7, 6, 0, 4, 3, 2, 1],
    [6, 5, 9, 8, 7, 1, 0, 4, 3, 2], [7, 6, 5, 9, 8, 2, 1, 0, 4, 3],
    [8, 7, 6, 5, 9, 3, 2, 1, 0, 4], [9, 8, 7, 6, 5, 4, 3, 2, 1, 0],
]
_V_P = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9], [1, 5, 7, 6, 2, 8, 3, 0, 9, 4],
    [5, 8, 0, 3, 7, 9, 6, 1, 4, 2], [8, 9, 1, 6, 0, 4, 3, 5, 2, 7],
    [9, 4, 5, 3, 1, 2, 6, 8, 7, 0], [4, 2, 8, 6, 5, 7, 3, 9, 0, 1],
    [2, 7, 9, 3, 8, 0, 6, 4, 1, 5], [7, 0, 4, 6, 9, 1, 3, 2, 5, 8],
]


def verhoeff(number: str) -> str:
    """Verhoeff. Used by e.g. India's Aadhaar (jurisdiction `in`)."""
    digits = re.sub(r"\s", "", number)
    if not digits.isdigit() or len(digits) < 2:
        return NA
    c = 0
    for i, ch in enumerate(reversed(digits)):
        c = _V_D[c][_V_P[i % 8][int(ch)]]
    return PASS if c == 0 else FAIL


def verhoeff_check_digit(payload: str) -> str:
    """Compute the Verhoeff digit to append to `payload` (for fixtures)."""
    inv = [0, 4, 3, 2, 1, 5, 6, 7, 8, 9]
    c = 0
    for i, ch in enumerate(reversed(payload)):
        c = _V_D[c][_V_P[(i + 1) % 8][int(ch)]]
    return str(inv[c])


def luhn_check_digit(payload: str) -> str:
    """Compute the Luhn digit to append to `payload` (for fixtures)."""
    for d in "0123456789":
        if luhn(payload + d) == PASS:
            return d
    raise ValueError("unreachable")


def iso7064_mod97(iban: str) -> str:
    """ISO 7064 mod 97-10 as used by IBAN."""
    s = re.sub(r"\s", "", iban).upper()
    if not re.fullmatch(r"[A-Z]{2}[0-9]{2}[A-Z0-9]{8,30}", s):
        return NA
    rearranged = s[4:] + s[:4]
    numeric = "".join(str(int(ch, 36)) for ch in rearranged)
    return PASS if int(numeric) % 97 == 1 else FAIL


# --------------------------------------------------------------- ICAO 9303

_MRZ_WEIGHTS = (7, 3, 1)


def _mrz_value(ch: str) -> int:
    if ch.isdigit():
        return int(ch)
    if ch == "<":
        return 0
    if "A" <= ch <= "Z":
        return ord(ch) - 55
    raise ValueError(f"invalid MRZ character {ch!r}")


def icao_check_digit(data: str) -> str:
    return str(sum(_mrz_value(c) * _MRZ_WEIGHTS[i % 3] for i, c in enumerate(data)) % 10)


@dataclass
class TD3:
    doc_code: str
    issuing_country: str
    surname: str
    given_names: str
    number: str
    nationality: str
    date_of_birth: str  # YYMMDD
    sex: str
    expiry_date: str  # YYMMDD
    optional: str
    results: dict  # check name -> pass/fail

    @property
    def valid(self) -> bool:
        return all(v == PASS for v in self.results.values())


def parse_td3(line1: str, line2: str) -> TD3:
    """Parse and validate a two-line, 44-character passport MRZ (TD3)."""
    l1, l2 = line1.strip().upper(), line2.strip().upper()
    if len(l1) != 44 or len(l2) != 44:
        raise ValueError("TD3 lines must be 44 characters")
    names = l1[5:].split("<<", 1)
    surname = names[0].replace("<", " ").strip()
    given = names[1].replace("<", " ").strip() if len(names) > 1 else ""

    def chk(field: str, digit: str) -> str:
        if digit == "<" and set(field) <= {"<"}:
            return PASS
        return PASS if icao_check_digit(field) == digit else FAIL

    number, n_cd = l2[0:9], l2[9]
    dob, dob_cd = l2[13:19], l2[19]
    exp, exp_cd = l2[21:27], l2[27]
    opt, opt_cd = l2[28:42], l2[42]
    composite = l2[0:10] + l2[13:20] + l2[21:43]
    results = {
        "number": chk(number, n_cd),
        "date_of_birth": chk(dob, dob_cd),
        "expiry_date": chk(exp, exp_cd),
        "optional": chk(opt, opt_cd),
        "composite": PASS if icao_check_digit(composite) == l2[43] else FAIL,
    }
    return TD3(
        doc_code=l1[0:2].replace("<", ""), issuing_country=l1[2:5].replace("<", ""),
        surname=surname, given_names=given, number=number.replace("<", ""),
        nationality=l2[10:13].replace("<", ""), date_of_birth=dob, sex=l2[20],
        expiry_date=exp, optional=opt.replace("<", ""), results=results,
    )


def icao9303_mrz(line1: str, line2: str) -> str:
    """Core check `icao9303.mrz` (kind: structure)."""
    try:
        return PASS if parse_td3(line1, line2).valid else FAIL
    except ValueError:
        return NA


# ------------------------------------------------------------- cross_field

def _norm(s: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", s.upper())


def mrz_vs_printed_number(mrz: TD3, printed: str) -> str:
    """Core check `cross.mrz_number` — MRZ outranks print when they differ."""
    return PASS if _norm(mrz.number) == _norm(printed) else FAIL


def yymmdd_to_date(s: str, *, future: bool = False, today: date | None = None) -> date:
    """Resolve the two-digit year: birth dates in the past, expiry dates in the future."""
    today = today or date.today()
    yy, mm, dd = int(s[0:2]), int(s[2:4]), int(s[4:6])
    century = (today.year // 100) * 100
    year = century + yy
    if future:
        if year < today.year - 50:
            year += 100
    elif year > today.year:
        year -= 100
    return date(year, mm, dd)


# ------------------------------------------------------------- consistency

def dates_ordered(issue: date, expiry: date) -> str:
    """Core check `consistency.issue_before_expiry`. Never lifts to verified."""
    return PASS if issue < expiry else FAIL


# ------------------------------------------------------------------ format

_ISO3166_ALPHA3_SAMPLE = {
    "ARE", "AUS", "CAN", "DEU", "FRA", "GBR", "IND", "JPN", "NLD", "SAU", "SGP", "USA", "UTO",
}


def iso3166_alpha3(code: str) -> str:
    """Core check `format.iso3166_alpha3`. Sample list; the registry carries the full list.

    `UTO` is ICAO's fictional specimen state and is accepted for fixtures.
    """
    if not re.fullmatch(r"[A-Z]{3}", code):
        return FAIL
    return PASS if code in _ISO3166_ALPHA3_SAMPLE else NA


CORE = {
    "luhn": luhn,
    "verhoeff": verhoeff,
    "iso7064.mod97": iso7064_mod97,
    "icao9303.mrz": icao9303_mrz,
}
