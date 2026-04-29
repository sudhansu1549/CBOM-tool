# RBI CBOM — QDrishti-Style Dashboard

This dashboard accepts PCAP/PCAPNG/CAP uploads and presents a Network Security Assessment report layout similar to the provided sample:

1. Document Control
2. Table of Contents
3. Executive Summary
4. Assessment Scope
5. Protocol Analysis
6. Algorithm Security Analysis
7. Compliance & Policy Assessment
8. Recommendations
9. Remediation Timeline
10. Appendices

## Run with Docker

```bash
docker build -t rbi-cbom .
docker run --rm -p 8501:8501 rbi-cbom
```

Then open:

```text
http://localhost:8501
```

## Deploy Online

Upload this folder to GitHub and deploy to Render as a Docker Web Service.

Suggested Render service name:

```text
rbi-cbom
```

## Note

This is PCAP-only evidence. It does not certify legal/regulatory compliance.
