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


## Final board cleanup

Removed from dashboard and exported report:
- Quantum Readiness Score
- Evidence labels / Evidence Type fields
- Evidence labels chart
- CBOM evidence types chart


# RBI CBOM v8 — Comprehensive PCAP + Source Code SBOM/CBOM

## Removed
All CycloneDX branding/mentions have been removed.

## New capabilities
RBI CBOM now supports PCAP CBOM, source-code SBOM, and source-code CBOM.

### Source Code SBOM manifests
- package.json
- requirements.txt
- pyproject.toml
- pom.xml
- go.mod
- Cargo.toml
- composer.json
- Gemfile

### Source Code CBOM crypto detection
- RSA, DSA, ECDSA/ECDH, Diffie-Hellman
- AES, DES/3DES, RC4
- MD5, SHA-1, SHA-256, SHA-384/SHA-512
- TLS 1.0/1.1/1.2/1.3
- OpenSSL, Java crypto, Python crypto, Node crypto
- PQC/hybrid indicators

### Exports
- Standard BOM JSON
- SPDX-like JSON
- SBOM CSV
- Source CBOM CSV
- BOM integrity manifest

## Note
For full enterprise parity with leading SBOM platforms, connect RBI CBOM to NVD, OSV, GHSA, EPSS, KEV, package registries, license databases, and internal asset inventories.
