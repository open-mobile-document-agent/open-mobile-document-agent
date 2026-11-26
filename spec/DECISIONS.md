# OMDA v0.1 decision log

Newest first.

| # | Decision |
| --- | --- |
| OD-044 | Conformance reports signed as a detached ES256 JWS over the RFC 8785 manifest; runtimes listed in `registry/runtimes.json` with the publisher key |
| OD-043 | Owner-written notes are documents with `method.kind = human` |
| OD-042 | GPS/location EXIF stripped by default |
| OD-041 | Original capture bytes kept by default; owner may discard |
| OD-040 | Models listed in a registry with metrics, not allowlisted; unlisted models allowed with a label |
| OD-039 | Device tiers T1–T3 are informative, declared by each runtime |
| OD-038 | Eight slots; `classifier` separate, segmentation inside `layout` |
| OD-037 | No-grant indistinguishability covers content and shape, not timing |
| OD-036 | v0.1 self-certified via signed reports and a repo registry; no certifying body |
| OD-035 | Extraction accuracy reported as metrics only, no threshold |
| OD-034 | Skills: manifest standardized in v0.1; portable WASM sandbox in v0.2 |
| OD-033 | Skill network access only to declared hosts, with owner grant, logged and labelled `network_used` |
| OD-032 | OMDA skills are read-and-report only; actions belong to the product layer |
| OD-031 | `issuer_signed` status added above `confirmed` (ePassport chip, mDL) |
| OD-030 | Predicates (e.g. `age_over_18`) are first-class derived disclosures |
| OD-029 | Owner may disclose `unverified`/`candidate` fields, status-labelled |
| OD-028 | Exchange = VC 2.0 + SD-JWT, signed by an attested runtime key; claims reading and checks, not document authenticity |
| OD-027 | No grant in a domain = indistinguishable from empty; partial grant = `withheld:no_grant` markers |
| OD-026 | Consumers may ingest documents; only the owner edits assertions, statuses, relationships |
| OD-025 | Both `ask` and `query`/`retrieve` exposed to consumers |
| OD-024 | MCP tools are the canonical interface; AppFunctions and App Intents are bindings |
| OD-023 | Portable encrypted store export/import is mandatory; owner decisions and labels survive migration |
| OD-022 | Unlock: MUST for `special`, SHOULD for `identifier` |
| OD-021 | Cloud model slots allowed with per-document-type owner opt-in and `remote` labels |
| OD-020 | `method.kind` adds `derived`; `method.location` added (`device` / `remote`) |
| OD-019 | v0.1 ships the identity profile complete plus a profile template; other domains in v0.2 |
| OD-018 | Photo and signature are region-only `image` assertions, never exported by default |
| OD-017 | As-printed name is primary; structured name parts are derived |
| OD-016 | One generic `national_id` doc type with `jurisdiction`-bound checks |
| OD-015 | Check registry kept as a separate versioned file, outside the spec text |
| OD-014 | `format` and `consistency` passes never lift an assertion to `verified` |
| OD-013 | Fuzzy gate matching allowed via the `matcher` model slot, capped at `candidate` |
| OD-012 | Person identity is out of scope; `subject` is an optional local label with informative guidance only |
| OD-011 | Status enumerations for super documents, segments, entities and relationships |
| OD-010 | Lineage effects on answers apply only after owner confirmation, even with deterministic evidence |
| OD-009 | Three identity levels: super document, segment, document entity |
| OD-008 | Multi-value fields: one assertion per value, linked by `group` |
| OD-007 | Exports omit quote, region and page hash |
| OD-006 | Regions use normalized 0–1 coordinates plus a required page hash |
| OD-005 | Assertion model specified before the runtime: the data format is what adopters depend on |
| OD-004 | Disclose, don't prohibit: gaps labelled with `nonconformance`, never hidden |
| OD-003 | Citations required for generated answers (L3); uncited answers labelled `ungrounded` |
| OD-002 | Models may generate answer values (RAG); grounding is labelled rather than forbidden |
| OD-001 | Name: Open Mobile Document Agent (OMDA) |
