# OMDA — Open Mobile Document Agent

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.24553127.svg)](https://doi.org/10.5281/zenodo.24553127) · [openmobiledocumentagent.org](https://openmobiledocumentagent.org)

**An open specification for turning documents into verified, cited records on the phone — readable by any model and any agent.**

Phones are gaining on-device models that can read documents. What they lack is a shared answer to *what a document proves*: which value came from where on the page, which deterministic check confirmed it, what the owner approved, and what can safely be shown to an app, an assistant or an institution. OMDA standardizes that layer.

```
  Products        reasoning, actions, UX, services   ← runtimes compete here
  ─────────────────────────────────────────────────
  OMDA            slots · provenance · evidenced assertions · verification · exchange
  ─────────────────────────────────────────────────
  Page structure  OCR, layout (DoclingDocument-compatible)
```

## Principles

- **Disclose, don't prohibit.** Gaps are allowed when labelled (`nonconformance`); hidden gaps are non-conformance.
- **Evidence travels with every fact.** Value, quote, region and page hash — or it is a `candidate`.
- **AI proposes; checks or the owner confirm.** Only deterministic checks (Verhoeff, Luhn, ICAO 9303 MRZ, …) or the owner lift a value to `verified` / `confirmed`.
- **The phone owner is the tenant.** On-device, hardware-encrypted, portable between runtimes.
- **Share proof, not documents.** Selective disclosure and predicates (`age_over_18`) over W3C Verifiable Credentials 2.0 + SD-JWT.

## Repository

| Path | Contents |
| --- | --- |
| [`spec/omda-v0.1.md`](spec/omda-v0.1.md) | The specification (§0–§12 + Answer model) |
| [`spec/DECISIONS.md`](spec/DECISIONS.md) | 43 numbered design decisions |
| [`schemas/v0.1/`](schemas/v0.1) | JSON Schemas (draft 2020-12): assertion, provenance, identity, answer, query plan, skill manifest, conformance manifest, evidence credential, profile, registries |
| [`registry/checks.json`](registry/checks.json) | Core check registry with algorithms and test vectors |
| [`registry/profiles/`](registry/profiles) | `identity` domain profile (passport, national ID, residence permit, driving licence, visa, birth certificate) + template |
| [`registry/models.json`](registry/models.json) | Model registry (listed, not approved) |
| [`registry/runtimes.json`](registry/runtimes.json) | Runtimes with signed, self-certified conformance reports (listed, not approved) |
| [`examples/`](examples) | Valid examples and `*.invalid.json` counter-examples |
| [`tools/`](tools) | Python reference checks and `omda-validate` |

## Quick start

```bash
pip install omda-tools               # from PyPI
omda-validate --all-examples
```

From source:

```bash
cd tools
pip install -e ".[test]"
omda-validate --all-examples          # every example passes, every counter-example fails
omda-validate assertion my-assertion.json
pytest                                # registry test vectors, profiles, examples
```

## Status

v0.1 draft, November 2026, Apache-2.0. Feedback via issues and pull requests. Fixtures in examples use ICAO's fictional specimen state `UTO` and generated identifiers; no real personal data.

## Related

- [Open Resume Agent (ORA)](https://openresumeagent.org) — resumes as model-agnostic agent files.
