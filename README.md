# RBI CBOM v2 — Executive Quantum Readiness Dashboard

This version improves the dashboard in three ways:

1. **Better quantum-readiness accuracy**
   - TLS 1.3 is not automatically treated as quantum-safe.
   - Classical ECDHE / X25519 / secp256r1 / RSA / DHE / ECDSA are treated as Shor-vulnerable.
   - AES-256 and SHA-384/512 are treated as having better post-quantum margin.
   - AES-128 and SHA-256 are treated as quantum-weakened indicators.
   - PQC-safe status is assigned only where hybrid/PQC algorithms are actually observed.
   - Missing key-share or incomplete handshakes are clearly labelled as lower-confidence or requiring validation.

2. **Removed Table of Contents**
   - The dashboard now uses modern executive tabs instead of a report-like TOC page.

3. **Modern executive UI**
   - Executive risk overview
   - Quantum readiness panel
   - Protocol and TLS analysis
   - CBOM inventory
   - Compliance and policy assessment
   - Recommendations and remediation roadmap
   - Evidence explorer
   - Downloadable HTML, JSON, CSV reports

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
