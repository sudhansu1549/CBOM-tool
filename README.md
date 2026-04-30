# RBI CBOM v3 — Board-Ready Quantum Readiness Dashboard

This version modifies RBI CBOM to present reports in the executive style of the attached HTML dashboard.

## Executive/board features

- Large board-ready hero section
- Executive KPI cards
- Board-level risk narrative
- Evidence-backed findings cards
- CBOM inventory table
- Observed TLS flows
- Compliance mapping for CISO/audit discussion
- Quantum remediation roadmap
- Parser log and limitations section
- Board-ready downloadable HTML report
- JSON, CBOM CSV, and Compliance CSV exports

## Accuracy model

- TLS 1.3 is not automatically treated as quantum-safe.
- Classical ECDHE / X25519 / secp256r1 / RSA / DHE / ECDSA are treated as Shor-vulnerable.
- AES-256 / SHA-384+ are treated as having stronger post-quantum symmetric margin.
- PQC-safe status is assigned only where hybrid/PQC algorithms are actually observed.
- Missing key-share or incomplete handshakes are labelled with lower confidence or manual validation.

## Run with Docker

```bash
docker build -t rbi-cbom .
docker run --rm -p 8501:8501 rbi-cbom
```

Then open:

```text
http://localhost:8501
```

## Deploy Online on Render

1. Upload this folder to GitHub.
2. Go to Render.com.
3. Create a new Web Service.
4. Select Docker environment.
5. Deploy.

## Important

This is PCAP-only evidence. It does not certify full legal/regulatory compliance.
