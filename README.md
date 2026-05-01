# RBI QuBOM v9 — Stable Priority + Home Page PCAP/SBOM/CBOM

## Fixes
- Stable quantum priority model: Priority 1/2/3/4 are explicitly defined and used everywhere.
- PCAP-based CBOM and Source-code SBOM/CBOM are both available on the home page.
- Source parsing has defensive error handling for ZIP/TAR/single-file uploads.
- Source SBOM supports common manifests: package.json, requirements.txt, pyproject.toml, pom.xml, go.mod, Cargo.toml.
- Source CBOM detects common crypto APIs and algorithms.

## Priority model
- Priority 1: Broken/deprecated today.
- Priority 2: Quantum migration required due to classical asymmetric crypto.
- Priority 3: Validation or crypto-agility required.
- Priority 4: PQC/hybrid ready or strong post-quantum symmetric margin.

## Run
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Docker
```bash
docker build -t rbi-qubom .
docker run --rm -p 8501:8501 rbi-qubom
```


## v10 board-report patch
- Restored PCAP Board HTML report to the earlier executive board-meeting format.
- Added matching Source Code SBOM/CBOM Board HTML report export.


## Branding update
The tool has been renamed from RBI CBOM to **RBI QuBOM**. Core CBOM/SBOM capabilities are unchanged.


## v11 source vulnerability analysis
RBI QuBOM now analyzes source code for vulnerability patterns and provides remediation recommendations.

Detected categories include:
- SQL injection
- OS command injection
- Dynamic code execution
- Hardcoded secrets
- Weak hashes and weak crypto
- Insecure TLS versions
- Unsafe deserialization
- Path traversal
- XSS sinks
- JWT verification issues
- Debug mode enabled
- Overly permissive CORS
- Disabled certificate verification

Exports added:
- Source Vulnerabilities CSV
- Source Vulnerability Roadmap CSV
- Vulnerabilities included in Standard BOM JSON
