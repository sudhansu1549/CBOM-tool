# CryptoSight CBOM Dashboard

A local, upload-only PCAP dashboard for cryptographic visibility, CBOM generation, policy deviations, compliance-risk indicators, evidence drill-down, and executive reporting.

## What it does

Upload a real `.pcap`, `.pcapng`, or `.cap` file and generate:

- Cryptographic Bill of Materials
- TLS version and cipher inventory
- Legacy TLS / weak cipher / static RSA detection
- Plaintext protocol detection
- SSH algorithm visibility where available from tshark
- DNSSEC, IPsec/IKE, and QUIC observation counts
- Evidence records with flow, frame, timestamp, and PCAP hash
- Compliance defensibility labels
- Recommendations
- JSON, CSV, and executive HTML report exports

## Important limitation

This dashboard analyzes only the traffic present in the uploaded PCAP. It does not prove full organizational, legal, regulatory, or framework compliance.

Compliance labels used:

- Observed
- Inferred
- Risk Indicator
- Requires Manual Validation

## Run locally

First install Wireshark/tshark.

Then:

```bash
pip install -r requirements.txt
streamlit run app.py
```

Open:

```text
http://localhost:8501
```

## Run with Docker

```bash
docker build -t cryptosight-cbom .
docker run --rm -p 8501:8501 cryptosight-cbom
```

Then open:

```text
http://localhost:8501
```

## Production hardening needed before enterprise use

This package is a functional local dashboard. Before enterprise deployment, add:

- OIDC/SAML authentication
- RBAC
- tenant isolation
- persistent PostgreSQL database
- secure object storage
- sandboxed parser containers
- malware scanning/quarantine workflow
- immutable audit logs
- retention and secure deletion
- Kubernetes deployment
- structured observability
- formal parser accuracy validation using known PCAP fixtures
