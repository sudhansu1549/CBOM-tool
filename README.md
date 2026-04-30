# RBI CBOM v7 — Board Sections UI

This version removes the cluttered charts and replaces tabs with a board-ready report page.

## Changes

- Removed Quantum Readiness Score chart
- Removed Evidence Labels chart
- Removed CBOM Evidence Types chart
- Removed odd tab layout
- Added stacked executive sections:
  - Report CBOM
  - Observed TLS Flows
  - Compliance Mapping
  - Quantum Remediation Roadmap
  - Evidence + Logs
  - Exports
- Improved table readability with selected columns, clearer headings, and board-level notes.
- Retains built-in PCAP/TLS parser and TLS 1.3 supported_versions correction.

## Run

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Docker

```bash
docker build -t rbi-cbom .
docker run --rm -p 8501:8501 rbi-cbom
```
