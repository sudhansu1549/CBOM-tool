# RBI CBOM v4 — Accurate Board-Ready Quantum Readiness Dashboard

This version fixes inaccurate TLS version detection, especially the common issue where TLS 1.3 sessions are incorrectly shown as TLS 1.2.

## Accuracy improvements

- Uses `tshark -T json` instead of only flat field extraction.
- Reads negotiated TLS 1.3 from the ServerHello `supported_versions` extension.
- Treats `tls.handshake.version` as a legacy compatibility field, not final negotiated TLS version.
- Extracts key-share / named-group data when visible.
- Detects PQ/hybrid indicators such as ML-KEM / Kyber / hybrid key-share groups.
- Treats classical ECDHE / X25519 / P-256 / RSA / DHE / ECDSA as Shor-vulnerable.
- Separates TLS security from quantum readiness.
- Labels low-confidence and incomplete-handshake cases.

## Board-ready UI

- Executive KPI cards
- Quantum readiness gauge
- Quantum posture donut chart
- Protocol distribution chart
- Evidence-backed findings cards
- Executive CBOM table
- TLS evidence table
- Compliance mapping
- Recommendations
- Parser log and limitations
- Board-ready HTML export

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
