# RBI CBOM v5 — Fixed Parser

This version fixes the issue where the dashboard identifies nothing by using a built-in PCAP/TLS parser for core TLS detection.

## Key fixes

- No dependency on tshark for core TLS detection.
- Parses PCAP and PCAPNG directly.
- Parses TLS ClientHello and ServerHello directly.
- Correctly identifies TLS 1.3 from ServerHello supported_versions extension.
- Does not mislabel TLS 1.3 as TLS 1.2 due to legacy_version.
- Extracts cipher suite, SNI, key exchange group where visible.
- Detects client PQ/hybrid offers and server negotiated PQ/hybrid groups.
- Presents board-ready executive dashboard.

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
