# OMDA — Open Mobile Document Agent Specification

**Version:** 0.1 (draft) · **Date:** 2026-11-26 · **Editor:** Mallikarjunayya Hiremath Sangamesh

OMDA is an open specification for turning paper and digital documents into verified, cited records on a phone, readable by any model and any agent.

The key words **MUST**, **MUST NOT**, **SHOULD**, **SHOULD NOT** and **MAY** are to be interpreted as described in RFC 2119 and RFC 8174. Machine-readable schemas live in [`/schemas`](../schemas); registries live in [`/registry`](../registry).

## Positioning

- **Below OMDA:** page structure. DoclingDocument covers what is on the page; OMDA stays compatible with it.
- **OMDA:** what the page proves — model slots, provenance, evidenced assertions, verification, exchange.
- **Above OMDA:** products. Runtimes compete on reasoning quality, actions, user experience and services; none of that is specified here.

Principle across the spec: **disclose, don't prohibit.** Gaps are allowed when labelled; hidden gaps are non-conformance.

## §0 Scope and non-goals

OMDA covers reading, verifying, storing, answering from and exchanging documents held on the owner's phone.

**In scope:** capture from camera, share sheet, files, screenshots, email attachments and NFC chips; extraction into evidenced assertions; deterministic verification; lineage; on-device store; answers; selective-disclosure export.

**Out of scope:** actions taken on the owner's behalf (forms, renewals, payments, messages); indexing and retrieval algorithms (only the interface is specified); connecting to institutions to fetch documents; medical, legal or financial judgement.

## §1 Conformance

A runtime reports the lowest level it fully meets and lists every gap.

| Level | Name | Requires |
| --- | --- | --- |
| L1 | Read | Capture, provenance, document identity (§3, §4) |
| L2 | Evidenced | Every assertion carries quote, region and page hash (§5) |
| L3 | Verified | Check registry and gate semantics (§6); generated answers cite (Answer model) |
| L4 | Exchange | Signed selective-disclosure packages (§11) |

- Each runtime **MUST** publish a conformance manifest ([schema](../schemas/v0.1/conformance-manifest.schema.json)): level, sections met, gaps. Silence counts as non-conformance.
- Any assertion, answer or export below its claimed level **MUST** carry `nonconformance` reason codes (`no_citation`, `unverified_region`, `model_not_allowlisted`, `checksum_unavailable`, `off_device_processing`, `network_used`, `fuzzy_match`, `check_failed:<id>`).
- A runtime claiming L3 with one L2 gap reports **L2+** and lists the gap.
- Labels **MUST NOT** be stripped by any downstream agent or app.

## §2 Runtime and model slots

A slot is a role with an input/output contract; any model meeting it may fill it — OS-provided, bundled or remote. [Schema](../schemas/v0.1/slot-descriptor.schema.json).

| Slot | Input → output |
| --- | --- |
| `ocr` | Page image → text lines with normalized boxes and confidence |
| `layout` | Page image + OCR → blocks (text, table, MRZ zone, photo, signature), reading order, proposed segments; DoclingDocument-compatible |
| `classifier` | Segment → `doc_type` + profile id (§7) |
| `extraction` | Segment + profile field list → assertions (value, quote, region); output **SHOULD** be JSON-Schema constrained |
| `embedding` | Text or assertion → vector; declares dimension and model |
| `interpreter` | Question → query plan (§9) |
| `answer_generator` | Question + retrieved items → answer with citations |
| `matcher` | Quote + region crop → `fuzzy_match` score (§6) |

- Missing slot → reduced mode, labelled (e.g. no `answer_generator`: `ask` returns only `extracted` and `derived` answers).
- Model upgrade → the runtime **MAY** re-read; results are new assertions; owner decisions are kept.
- Models are listed in [`registry/models.json`](../registry/models.json) with published slot-test metrics. Unlisted models are allowed, labelled `model_not_allowlisted`.
- Device tiers are informative and declared in the manifest: `T1` OCR + rules, no language model; `T2` small quantized language model (~2B parameters or fewer); `T3` OS foundation model or larger model on the NPU.

## §3 Capture and provenance

Every super document records how it entered the runtime. [Schema](../schemas/v0.1/provenance.schema.json).

**Channels:** `camera`, `scanner`, `share_sheet`, `file_import`, `screenshot`, `email_attachment`, `nfc_chip`, `consumer:<id>`, `note`.

- `original_hash` is taken before any transform; original bytes are kept by default and the owner **MAY** discard them.
- Regions (§5) anchor to the processed page (`page_hash`); transforms are recorded so the mapping to the original is reproducible.
- PDFs: a valid text layer is used and recorded as `text_layer`; a missing, thin or garbled layer triggers rasterization and OCR, with the reason recorded.
- GPS and location EXIF **MUST** be stripped by default; only capture time is kept.
- Capture time is never a document date.
- Captures are never merged; the super document is a hard boundary.
- Owner-written notes are super documents whose assertions carry `method.kind = human`.

## §4 Document identity

[Schema](../schemas/v0.1/identity.schema.json).

| Level | ID | Answers | Status values |
| --- | --- | --- | --- |
| Super document | `sd_` | What was captured together? | `captured`, `processing`, `processed`, `failed` |
| Segment | `sg_` | Which logical document sits in the capture? | `proposed`, `confirmed`, `rejected` |
| Document entity | `de_` | Which real-world document is this? | `active`, `expired`, `superseded`, `archived` |

- The owner **MAY** split or merge segments within one super document.
- `expired` is computed from validity dates; it flags, never hides.
- `superseded` applies only after the owner confirms a `supersedes` relationship.
- `archived` is an owner action, reversible; runtimes **MUST NOT** delete entities on their own.
- Default answers exclude `superseded` and `archived` entities; explicit queries still reach them.

**Relationships:** `supersedes`, `amends`, `attached_to`, `related`, `duplicate_of`. **Status:** `proposed` → `verified` (deterministic evidence) → `confirmed` | `rejected`.

- Effects on answers apply **only** at `confirmed`.
- A pass that finds nothing **MUST** record `no_match` with the candidates checked.
- Matching is scoped to the owner's store, never across owners.
- The owner is whoever captured; ownership never depends on document content.
- *Informative:* OMDA does not define person identity. A runtime **MAY** attach an optional opaque local `subject` label, derived from name assertions plus owner confirmation, never inferred silently, never linked across devices or owners.

## §5 Assertion model

An assertion is one fact read from one document, carrying its own evidence. [Schema](../schemas/v0.1/assertion.schema.json) · [example](../examples/assertion.passport-number.json).

**Status ladder** (strongest first; an answer inherits the weakest status it cites):

| Status | Meaning |
| --- | --- |
| `issuer_signed` | Valid issuer signature (ePassport chip via ICAO passive authentication; ISO 18013-5 mDL) |
| `confirmed` | Owner accepted the value |
| `verified` | Passed a deterministic check |
| `unverified` | Evidence present, no check applies |
| `candidate` | Weak evidence or region mismatch; shown, never hidden |
| `illegible` | The only valid reason to withhold a value |
| `rejected` / `suppressed` | Excluded from answers and exports |

- Quote, region and `page_hash` are **REQUIRED** for `method.kind` `model` and `check`; `derived` assertions cite `derived_from`; `human` assertions need no evidence.
- Regions use normalized 0–1 coordinates, origin top-left, valid only against the page they hash to.
- The quote **MUST** occur in the region's OCR text; otherwise status `candidate` + `unverified_region`.
- Append-only: corrections are new assertions linked by `supersedes`.
- Human outranks machine: re-reads never overwrite `confirmed` or `rejected`.
- `confidence` is optional and never replaces `status`.
- Field names come from domain profiles (§7) as `domain.object.attribute`.
- Multi-value fields: one assertion per value, linked by `group {id, kind, index}`; groups carry no status.
- `method.kind`: `model`, `check`, `derived`, `human`. `method.location`: `device` (default) or `remote`.

## §6 Verification

Checks are deterministic, offline and model-free; only they lift an assertion to `verified`. Models assist the gate only, capped at `candidate`. Registry: [`registry/checks.json`](../registry/checks.json); reference code: [`tools/omda_tools/checks.py`](../tools/omda_tools/checks.py).

| Kind | Tests | Lifts to `verified` |
| --- | --- | --- |
| `checksum` | Check digit on one field (Verhoeff, Luhn, ISO 7064 mod 97) | yes |
| `structure` | Check digits across a structure (ICAO 9303 MRZ incl. composite) | yes |
| `cross_field` | Two sources agree (MRZ vs printed) | yes |
| `consistency` | Logical sense (issue before expiry) | no |
| `format` | Patterns and code lists (ISO 3166) | no |

- `fail` → `candidate` + `check_failed:<id>`; still shown to the owner.
- MRZ outranks print: if the MRZ passes and the printed value differs, the printed assertion becomes `candidate` and the MRZ value is proposed with `method.kind = check`; the owner decides.
- **Gate:** exact match after normalization (NFKC, collapsed whitespace, case-fold where allowed) → evidence holds. Fuzzy match **MAY** use the `matcher` slot (OCR confusion pairs, visual re-read, learned similarity); recorded as `fuzzy_match`, capped at `candidate`. No match → `candidate` + `unverified_region`.
- A runtime **SHOULD** turn every `candidate` into an owner question; answers become `human` assertions honoured on every re-read.
- Checks live in a separate versioned registry; vendors register as `x-<vendor>.<name>`; every check **MUST** publish its algorithm and test vectors.

## §7 Domain profiles

A profile is a versioned registry file. v0.1 ships [`identity`](../registry/profiles/identity.json) complete plus a [template](../registry/profiles/_template.json); health (FHIR mapping), education, travel, finance, insurance and property follow in v0.2. [Schema](../schemas/v0.1/profile.schema.json).

- Field types: `string`, `date`, `country` (ISO 3166-1 alpha-3), `sex` (ICAO F/M/X), `name`, `amount`, `code`, `image`.
- Sensitivity tiers: `basic` → `personal` → `identifier` → `special`; they set default visibility (§8) and export warnings (§11).
- Each doc type declares `entity_key` (for `duplicate_of` / `supersedes`) and `validity` (for `expired`).
- Jurisdiction-specific IDs use one generic `national_id` type whose `jurisdiction` binds checks (`in` → Verhoeff, `ae` → Luhn).
- The as-printed name is primary; structured parts are derived assertions citing it.
- `photo` and `signature` are region-only `image` assertions, never exported by default.

## §8 Store and security

- The phone owner is the tenant: one OS user profile = one store.
- Page images, OCR text, assertions, relationships and answers stay on the device and **MUST** be encrypted at rest: a hardware-held master key (Android Keystore StrongBox/TEE, iOS Secure Enclave) and a data key per entity, enabling crypto-erase.
- The owner may delete anything; the runtime never deletes on its own.
- Unlock: `identifier` **SHOULD** and `special` **MUST** require biometric or device credential.
- Consumers get nothing by default; grants are per consumer, per tier or field, revocable and worded as plain sentences. Every consumer read is logged on the device and visible to the owner.
- Off-device processing **MAY** be used only after owner opt-in per document type; its assertions carry `method.location = remote` and `off_device_processing`.
- A conforming runtime **MUST** export and import the whole store as one encrypted archive keyed by the owner, preserving statuses, owner decisions, lineage and labels unchanged.

## §9 Agent interface

One operation set, defined as MCP tools and bound one-to-one to Android AppFunctions (the platform's on-device MCP) and iOS App Intents. Query plan [schema](../schemas/v0.1/query-plan.schema.json).

| Operation | Purpose |
| --- | --- |
| `omda.query` | Structured query plan → assertions or entities with citations |
| `omda.ask` | Natural-language question → answer (Answer model) |
| `omda.retrieve` | Chunks or assertions with scores and regions, for the consumer's own RAG |
| `omda.list_entities` / `omda.get_entity` | Browse by doc type, entity status or subject |
| `omda.ingest` | Hand a document into the store (channel `consumer:<id>`) |
| `omda.request_grant` | Ask the owner for access (§8) |
| `omda.propose_disclosure` | Build an exchange package (§11) for owner approval |

- Every response carries assertion ids, statuses, `nonconformance`, the answer kind and the grant scope applied.
- Consumers may ingest; only the owner changes assertions, statuses or relationships.
- Partial grant in a domain → ungranted fields returned as `withheld:no_grant`.
- No grant in a domain → the response is identical in content and shape to an empty domain.

## §10 Skills manifest

A skill runs inside the runtime and analyses the owner's store. Skills read and report; actions belong to products. [Schema](../schemas/v0.1/skill-manifest.schema.json).

- `reads` (fields or tiers) generate a plain-sentence permission; `triggers`: `on_ingest`, `on_query`, `on_entity_status`, `schedule:*`; `outputs`: `finding`, `reminder`, `answer`, `form_answers` (never submitted), `proposed_assertion`.
- Sandboxed; events carry field names, never values; outputs **MUST** cite and follow the Answer model; an output is visible only to someone who can read every assertion it cites; every run is logged.
- Network: none by default; declared hosts only, after owner grant, logged, outputs labelled `network_used`.
- v0.1 standardizes the manifest; v0.2 adds a portable WASM sandbox.

## §11 Exchange

A package proves that a genuine conforming runtime read these values from a document the owner holds and that these checks passed. It does **not** prove the document is genuine unless a value is `issuer_signed`. [Schema](../schemas/v0.1/evidence-credential.schema.json) · [example](../examples/evidence-credential.hotel.json).

- Format: a W3C Verifiable Credentials 2.0 credential of type `OMDAEvidenceCredential`, secured with SD-JWT (VC JOSE-COSE).
- Signed with a device-bound runtime key attested by the platform (Android Key Attestation, iOS App Attest); the attestation vouches for the runtime, not the document.
- Each field disclosure carries `value`, `status`, `checks`, `method.kind`, `method.location`; never quote, region or page hash.
- Flow: verifier requests fields or predicates and states its purpose → runtime builds the package → owner approves field by field → presentation bound to nonce, audience and expiry → logged.
- Default disclosures: `extracted` and `derived` values from `issuer_signed`, `confirmed` or `verified` assertions. The owner **MAY** include `unverified` or `candidate` fields, status-labelled. Generated and `ungrounded` answers never enter a package.
- **Predicates** (`age_over_18`, `passport_valid_on:<date>`) disclose only the result plus the status and checks of their basis.
- Where a document carries an issuer signature, the runtime **SHOULD** verify it and **MAY** pass the issuer's signed data through.

## §12 Conformance suite

Conformance is proven by running a runtime against shared synthetic fixtures through the MCP binding.

- Fixtures are synthetic only (no real personal data): clean, degraded (blur, glare, skew, low resolution, occlusion) and adversarial (MRZ/print mismatch, failed check digit, quote outside region, duplicate capture, renewal pair, multi-document bundle), each with expected assertions, statuses, labels and relationships.
- Tests per level: L1 provenance and identity; L2 schema, quote-in-region, page hash; L3 check vectors, MRZ-outranks-print, citations, status propagation; L4 SD-JWT verification, no evidence leakage, predicates, nonce binding; all levels: no-grant indistinguishability and store round trip.
- Accuracy (field accuracy, recall) is reported as metrics, never gated.
- v0.1 is self-certified: a signed report becomes the manifest; conforming runtimes are listed in [`registry/runtimes.json`](../registry/runtimes.json).
- `report.signature` is a detached compact JWS (RFC 7515 Appendix F), `alg` ES256, `typ` `omda-conformance+jws`, `kid` the RFC 7638 thumbprint of the publisher's P-256 key, over the manifest in RFC 8785 canonical form with `report.signature` set to `""`. The listing names the manifest and the publisher's public key (OD-044).
- Known limitation: no-grant indistinguishability covers content and shape, not timing.

## Answer model

| Kind | Produced by | Exportable |
| --- | --- | --- |
| `extracted` | Value taken directly from an assertion | Yes (§11 rules) |
| `derived` | Deterministic computation | Yes (§11 rules) |
| `generated` | Model composition via RAG over the store | Never |

- A generated answer **MUST** cite at least one assertion or text region (L3). [Schema](../schemas/v0.1/answer.schema.json).
- A runtime **MAY** return an uncited answer but **MUST** label it `ungrounded` with `no_citation` on every surface.
- An answer inherits the weakest status among its citations.
- OMDA specifies what retrieval returns, not how runtimes index.

## Decision log

See [`DECISIONS.md`](DECISIONS.md).
