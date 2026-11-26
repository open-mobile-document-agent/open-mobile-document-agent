"""Validate OMDA JSON documents against the v0.1 schemas.

Usage:
    omda-validate <schema-name> <file.json> [<file.json> ...]
    omda-validate --all-examples

<schema-name> is a file stem in schemas/, e.g. `assertion`, or `identity#entity`.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

_PKG_DATA = Path(__file__).resolve().parent / "_data"
ROOT = _PKG_DATA if (_PKG_DATA / "schemas").is_dir() else Path(__file__).resolve().parents[2]
SCHEMAS = ROOT / "schemas"
BASE = "https://openmobiledocumentagent.org/schemas/v0.1/"


def _registry() -> Registry:
    resources = []
    for p in SCHEMAS.glob("*.schema.json"):
        doc = json.loads(p.read_text())
        resources.append((doc["$id"], Resource.from_contents(doc)))
    return Registry().with_resources(resources)


REGISTRY = _registry()


def validator(name: str) -> Draft202012Validator:
    stem, _, fragment = name.partition("#")
    uri = f"{BASE}{stem}.schema.json"
    schema = {"$ref": f"{uri}#/$defs/{fragment}"} if fragment else {"$ref": uri}
    return Draft202012Validator(schema, registry=REGISTRY, format_checker=FormatChecker())


def errors(name: str, instance) -> list[str]:
    return [
        f"{'/'.join(map(str, e.absolute_path)) or '<root>'}: {e.message}"
        for e in sorted(validator(name).iter_errors(instance), key=lambda e: list(e.absolute_path))
    ]


# examples/<file>.json -> schema name; files named *.invalid.json must FAIL.
EXAMPLE_SCHEMAS = {
    "assertion": "assertion",
    "provenance": "provenance",
    "segment": "identity#segment",
    "entity": "identity#entity",
    "relationship": "identity#relationship",
    "no-match": "identity#no_match",
    "answer": "answer",
    "query-plan": "query-plan",
    "skill-manifest": "skill-manifest",
    "conformance-manifest": "conformance-manifest",
    "evidence-credential": "evidence-credential",
    "slot-descriptor": "slot-descriptor",
}


def schema_for_example(path: Path) -> str:
    stem = path.name.split(".")[0]
    key = next((k for k in sorted(EXAMPLE_SCHEMAS, key=len, reverse=True) if stem.startswith(k)), None)
    if key is None:
        raise KeyError(f"no schema mapping for {path.name}")
    return EXAMPLE_SCHEMAS[key]


def check_examples() -> int:
    failures = 0
    for path in sorted((ROOT / "examples").glob("*.json")):
        name = schema_for_example(path)
        errs = errors(name, json.loads(path.read_text()))
        expect_invalid = ".invalid." in path.name
        ok = bool(errs) if expect_invalid else not errs
        print(f"{'ok  ' if ok else 'FAIL'} {path.name} [{name}]{' (expected invalid)' if expect_invalid else ''}")
        if not ok:
            failures += 1
            for e in errs or ["validated, but was expected to fail"]:
                print(f"       {e}")
    return failures


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if argv == ["--all-examples"]:
        return 1 if check_examples() else 0
    if len(argv) < 2:
        print(__doc__)
        return 2
    name, files = argv[0], argv[1:]
    bad = 0
    for f in files:
        errs = errors(name, json.loads(Path(f).read_text()))
        print(f"{'ok  ' if not errs else 'FAIL'} {f}")
        for e in errs:
            print(f"       {e}")
        bad += bool(errs)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
