# Publishing checklist (v0.1.0)

1. **Domain** — buy `openmobiledocumentagent.org` on Cloudflare Registrar (confirm availability first).
2. **GitHub org** — create `open-mobile-document-agent` at https://github.com/account/organizations/new (Free plan).
3. **Repo** — create `open-mobile-document-agent/open-mobile-document-agent`, then:
   ```bash
   git remote add origin https://github.com/open-mobile-document-agent/open-mobile-document-agent.git
   git push -u origin main
   ```
4. **Checks (local, no CI)** — `cd tools && pip install -e ".[test]" && pytest && omda-validate --all-examples`
5. **Release** — tag `v0.1.0`, create a GitHub release with notes from `spec/DECISIONS.md`.
6. **Zenodo** — enable the repo at https://zenodo.org/account/settings/github/ before tagging; `.zenodo.json` supplies metadata and the release mints the DOI. Add the DOI badge to `README.md`.
7. **PyPI** — `cd tools && python sync_data.py && python -m build && twine upload dist/*` (package `omda-tools`).
8. **W3C Community Group** — submit `docs/w3c-community-group-proposal.md`.
9. **Announce** — LinkedIn post from `docs/announcement-linkedin.md`.
