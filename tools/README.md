# omda-tools

Reference checks and schema validator for the [OMDA specification](../spec/omda-v0.1.md).

```bash
pip install -e ".[test]"
omda-validate --all-examples
omda-validate assertion file.json
pytest
```

`omda_tools.checks` implements the core check registry: Luhn, Verhoeff, ISO 7064 mod 97, ICAO 9303 TD3 MRZ (parse + all check digits), MRZ-vs-printed cross check, issue-before-expiry, ISO 3166 alpha-3 format.
