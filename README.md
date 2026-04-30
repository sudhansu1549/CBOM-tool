# RBI CBOM v6 — Report-Grade Board Dashboard

This version adds the report capabilities shown in the attached RBI CBOM PDF:

- Report-style KPI cards: Quantum Readiness, TLS Version, Cipher Suite, Key Exchange
- Executive Assessment and Board-Level Risk narrative
- Evidence-backed findings section
- Board-style CBOM table
- Observed TLS flows
- Compliance mapping
- Quantum remediation roadmap
- "What this PCAP cannot prove alone" section
- Parser log
- Board-ready HTML export

## Parser capabilities

- Built-in PCAP and PCAPNG parser
- TLS ClientHello and ServerHello parser
- TLS 1.3 detection from ServerHello supported_versions
- Server-selected key share detection
- Client PQ/hybrid offer detection
- Report-grade CBOM and technical CBOM

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
