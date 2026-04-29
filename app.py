
import streamlit as st
import pandas as pd
import subprocess
import tempfile
import json
import hashlib
import os
import shutil
import re
from datetime import datetime, timezone
from pathlib import Path

st.set_page_config(
    page_title="CryptoSight CBOM | PCAP Crypto Risk Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -------------------------------
# Styling
# -------------------------------
st.markdown("""
<style>
    .main {
        background: linear-gradient(180deg, #f8fafc 0%, #ffffff 100%);
    }
    .block-container {
        padding-top: 1.4rem;
        padding-bottom: 2rem;
    }
    .metric-card {
        padding: 1rem;
        border-radius: 18px;
        background: #ffffff;
        box-shadow: 0 10px 30px rgba(15, 23, 42, 0.08);
        border: 1px solid #e2e8f0;
    }
    .risk-critical {color:#b91c1c; font-weight:800;}
    .risk-high {color:#c2410c; font-weight:800;}
    .risk-medium {color:#b45309; font-weight:800;}
    .risk-low {color:#047857; font-weight:800;}
    .small-muted {color:#64748b; font-size:0.88rem;}
    .headline {
        font-size: 2rem;
        font-weight: 850;
        color: #0f172a;
        margin-bottom: 0.2rem;
    }
    .subheadline {
        color:#475569;
        font-size:1rem;
        margin-bottom:1rem;
    }
    .pill {
        display:inline-block;
        padding:0.25rem 0.65rem;
        border-radius:999px;
        background:#e2e8f0;
        color:#0f172a;
        font-size:0.8rem;
        font-weight:700;
        margin-right:0.25rem;
    }
</style>
""", unsafe_allow_html=True)

# -------------------------------
# Constants and policy baseline
# -------------------------------
TLS_VERSION_MAP = {
    "0x0002": "SSLv2",
    "0x0300": "SSLv3",
    "0x0301": "TLS 1.0",
    "0x0302": "TLS 1.1",
    "0x0303": "TLS 1.2",
    "0x0304": "TLS 1.3",
}

CIPHER_MAP = {
    "0x0004": "TLS_RSA_WITH_RC4_128_MD5",
    "0x0005": "TLS_RSA_WITH_RC4_128_SHA",
    "0x0009": "TLS_RSA_WITH_DES_CBC_SHA",
    "0x000a": "TLS_RSA_WITH_3DES_EDE_CBC_SHA",
    "0x002f": "TLS_RSA_WITH_AES_128_CBC_SHA",
    "0x0035": "TLS_RSA_WITH_AES_256_CBC_SHA",
    "0x003c": "TLS_RSA_WITH_AES_128_CBC_SHA256",
    "0x003d": "TLS_RSA_WITH_AES_256_CBC_SHA256",
    "0x009c": "TLS_RSA_WITH_AES_128_GCM_SHA256",
    "0x009d": "TLS_RSA_WITH_AES_256_GCM_SHA384",
    "0xc009": "TLS_ECDHE_ECDSA_WITH_AES_128_CBC_SHA",
    "0xc00a": "TLS_ECDHE_ECDSA_WITH_AES_256_CBC_SHA",
    "0xc013": "TLS_ECDHE_RSA_WITH_AES_128_CBC_SHA",
    "0xc014": "TLS_ECDHE_RSA_WITH_AES_256_CBC_SHA",
    "0xc02f": "TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256",
    "0xc030": "TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384",
    "0xc02b": "TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256",
    "0xc02c": "TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384",
    "0x1301": "TLS_AES_128_GCM_SHA256",
    "0x1302": "TLS_AES_256_GCM_SHA384",
    "0x1303": "TLS_CHACHA20_POLY1305_SHA256",
}

WEAK_KEYWORDS = ["RC4", "3DES", "DES", "NULL", "EXPORT", "anon", "MD5", "SHA1", "_SHA"]
PLAINTEXT_FILTER = "http or ftp or telnet or smtp or pop or imap or ldap or snmp"
PLAINTEXT_PROTOCOLS = {
    "http": "HTTP",
    "ftp": "FTP",
    "telnet": "Telnet",
    "smtp": "SMTP",
    "pop": "POP3",
    "imap": "IMAP",
    "ldap": "LDAP",
    "snmp": "SNMP",
}

COMPLIANCE_FRAMEWORKS = [
    "NIST CSF",
    "NIST SP 800-52 Rev. 2",
    "NIST SP 800-57",
    "NIST SP 800-131A",
    "ISO/IEC 27001",
    "ISO/IEC 27002",
    "PCI DSS",
    "GDPR",
    "HIPAA Security Rule",
    "RBI Cybersecurity Guidelines",
    "CERT-In Directions",
    "DPDP Act, 2023",
    "MeitY Security Best Practices",
]

# -------------------------------
# Utility functions
# -------------------------------
def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def run_tshark(args, timeout=180):
    if not shutil.which("tshark"):
        return False, "tshark not found. Install Wireshark/tshark or run the Docker image.", ""
    try:
        result = subprocess.run(
            ["tshark"] + args,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "tshark command timed out."
    except Exception as e:
        return False, "", str(e)

def field_extract(file_path, display_filter, fields, timeout=180):
    args = ["-r", file_path, "-Y", display_filter, "-T", "fields", "-E", "header=y", "-E", "separator=\t"]
    for f in fields:
        args += ["-e", f]
    ok, out, err = run_tshark(args, timeout=timeout)
    if not ok and not out.strip():
        return pd.DataFrame(), err
    if not out.strip():
        return pd.DataFrame(columns=fields), err
    from io import StringIO
    try:
        df = pd.read_csv(StringIO(out), sep="\t", dtype=str).fillna("")
    except Exception:
        df = pd.DataFrame(columns=fields)
    return df, err

def normalize_tls_version(v):
    if not v:
        return "Unknown"
    v = str(v).strip()
    return TLS_VERSION_MAP.get(v.lower(), TLS_VERSION_MAP.get(v, v))

def normalize_cipher(c):
    if not c:
        return "Unknown"
    c = str(c).strip()
    return CIPHER_MAP.get(c.lower(), CIPHER_MAP.get(c, c))

def infer_algorithms(cipher):
    cipher_upper = str(cipher).upper()
    if "TLS_AES_" in cipher_upper or "CHACHA20" in cipher_upper:
        kx = "TLS 1.3 key schedule"
    elif "ECDHE" in cipher_upper:
        kx = "ECDHE"
    elif "DHE" in cipher_upper:
        kx = "DHE"
    elif "RSA" in cipher_upper:
        kx = "RSA/static RSA"
    elif "PSK" in cipher_upper:
        kx = "PSK"
    else:
        kx = "Unknown"

    if "CHACHA20" in cipher_upper:
        enc = "ChaCha20-Poly1305"
    elif "AES_256_GCM" in cipher_upper:
        enc = "AES-256-GCM"
    elif "AES_128_GCM" in cipher_upper:
        enc = "AES-128-GCM"
    elif "AES_256_CBC" in cipher_upper:
        enc = "AES-256-CBC"
    elif "AES_128_CBC" in cipher_upper:
        enc = "AES-128-CBC"
    elif "3DES" in cipher_upper:
        enc = "3DES"
    elif "DES" in cipher_upper:
        enc = "DES"
    elif "RC4" in cipher_upper:
        enc = "RC4"
    else:
        enc = "Unknown"

    if "SHA384" in cipher_upper:
        mac = "SHA-384"
    elif "SHA256" in cipher_upper:
        mac = "SHA-256"
    elif "SHA" in cipher_upper:
        mac = "SHA-1"
    elif "MD5" in cipher_upper:
        mac = "MD5"
    else:
        mac = "AEAD/Unknown"

    fs = kx in ["ECDHE", "DHE"] or "TLS 1.3" in kx
    return kx, enc, mac, fs

def severity_from_score(score):
    if score >= 90:
        return "Critical"
    if score >= 70:
        return "High"
    if score >= 40:
        return "Medium"
    if score >= 20:
        return "Low"
    return "Informational"

def score_tls_record(version, cipher, forward_secrecy):
    score = 10
    version = str(version)
    cipher_u = str(cipher).upper()

    if version in ["SSLv2", "SSLv3"]:
        score += 85
    elif version in ["TLS 1.0", "TLS 1.1"]:
        score += 75
    elif version == "TLS 1.2":
        score += 20
    elif version == "TLS 1.3":
        score += 0
    else:
        score += 25

    if any(k in cipher_u for k in ["RC4", "3DES", "DES", "NULL", "EXPORT", "ANON"]):
        score += 30
    if "MD5" in cipher_u or "SHA1" in cipher_u:
        score += 20
    if "RSA_WITH" in cipher_u or (("RSA" in cipher_u) and ("ECDHE" not in cipher_u) and ("DHE" not in cipher_u) and ("TLS_AES" not in cipher_u)):
        score += 20
    if not forward_secrecy and version != "TLS 1.3":
        score += 10

    return min(score, 100)

def build_compliance_mappings(issue_type, label):
    mappings = []
    if issue_type in ["Legacy TLS", "Weak Cipher", "Static RSA"]:
        relevant = [
            "NIST SP 800-52 Rev. 2",
            "NIST SP 800-131A",
            "ISO/IEC 27002",
            "PCI DSS",
            "RBI Cybersecurity Guidelines",
        ]
    elif issue_type == "Plaintext Protocol":
        relevant = [
            "ISO/IEC 27002",
            "PCI DSS",
            "GDPR",
            "HIPAA Security Rule",
            "RBI Cybersecurity Guidelines",
            "DPDP Act, 2023",
        ]
    elif issue_type == "Certificate Issue":
        relevant = [
            "NIST SP 800-57",
            "NIST SP 800-131A",
            "ISO/IEC 27002",
            "PCI DSS",
        ]
    else:
        relevant = COMPLIANCE_FRAMEWORKS[:4]

    for fw in relevant:
        if fw in ["GDPR", "HIPAA Security Rule", "DPDP Act, 2023"]:
            mappings.append({
                "framework": fw,
                "defensibility_label": "Risk Indicator",
                "statement": f"{issue_type} was detected in network evidence. This may indicate exposure where regulated or sensitive data is involved, but formal compliance impact requires manual validation."
            })
        else:
            mappings.append({
                "framework": fw,
                "defensibility_label": label,
                "statement": f"{issue_type} was detected from PCAP-derived evidence and may indicate non-alignment with modern cryptographic baseline expectations."
            })
    return mappings

def make_recommendation(issue_type):
    recs = {
        "Legacy TLS": {
            "recommendation_id": "REC-TLS-001",
            "executive": "Eliminate legacy encryption protocols from observed traffic.",
            "technical": "Disable SSLv2, SSLv3, TLS 1.0 and TLS 1.1. Enforce TLS 1.2 with strong suites and prefer TLS 1.3.",
            "verification": "Capture a fresh PCAP after remediation and confirm no legacy TLS negotiation remains.",
            "owner": "Infrastructure Security / Application Owner"
        },
        "Weak Cipher": {
            "recommendation_id": "REC-CIPHER-001",
            "executive": "Remove weak cipher suites from exposed services.",
            "technical": "Disable RC4, DES, 3DES, NULL, EXPORT and anonymous cipher suites. Prefer AEAD suites such as AES-GCM or ChaCha20-Poly1305.",
            "verification": "Re-test traffic and confirm only approved cipher suites are negotiated.",
            "owner": "Infrastructure Security"
        },
        "Static RSA": {
            "recommendation_id": "REC-FS-001",
            "executive": "Improve forward secrecy for encrypted sessions.",
            "technical": "Prioritize ECDHE/DHE suites or TLS 1.3. Remove static RSA key exchange where possible.",
            "verification": "Confirm negotiated suites include forward secrecy.",
            "owner": "Application / Platform Owner"
        },
        "Plaintext Protocol": {
            "recommendation_id": "REC-PLAIN-001",
            "executive": "Reduce exposure from unencrypted network protocols.",
            "technical": "Replace Telnet/FTP with SSH/SFTP. Enforce HTTPS and TLS/STARTTLS for mail and directory protocols.",
            "verification": "Confirm plaintext protocols no longer appear in post-remediation PCAPs.",
            "owner": "Network Security / Application Owner"
        },
        "Certificate Issue": {
            "recommendation_id": "REC-CERT-001",
            "executive": "Improve certificate lifecycle and trust posture.",
            "technical": "Replace expired, weak, self-signed or SHA-1/MD5 certificates. Use RSA >= 2048-bit or approved ECC curves.",
            "verification": "Inspect new certificate metadata and validate trust chain.",
            "owner": "PKI / Infrastructure Security"
        }
    }
    return recs.get(issue_type, {
        "recommendation_id": "REC-GEN-001",
        "executive": "Review cryptographic exposure.",
        "technical": "Validate configuration against approved security baseline.",
        "verification": "Re-run PCAP analysis after remediation.",
        "owner": "Security Engineering"
    })

def analyze_pcap(file_path):
    analysis_time = datetime.now(timezone.utc).isoformat()
    pcap_hash = sha256_file(file_path)

    # Basic file info from capinfos if available
    capinfos = {}
    if shutil.which("capinfos"):
        try:
            res = subprocess.run(["capinfos", "-Tm", file_path], capture_output=True, text=True, timeout=60)
            capinfos["raw"] = res.stdout
        except Exception as e:
            capinfos["error"] = str(e)

    # TLS ServerHello negotiated versions/ciphers
    tls_fields = [
        "frame.number", "frame.time_epoch",
        "ip.src", "tcp.srcport", "ip.dst", "tcp.dstport",
        "ipv6.src", "ipv6.dst",
        "tls.handshake.version",
        "tls.handshake.ciphersuite",
        "tls.handshake.extensions_server_name"
    ]
    tls_df, tls_err = field_extract(file_path, "tls.handshake.type == 2", tls_fields)

    cbom_records = []
    findings = []
    evidence_records = []

    for idx, row in tls_df.iterrows():
        src_ip = row.get("ip.src", "") or row.get("ipv6.src", "")
        dst_ip = row.get("ip.dst", "") or row.get("ipv6.dst", "")
        version = normalize_tls_version(row.get("tls.handshake.version", ""))
        cipher = normalize_cipher(row.get("tls.handshake.ciphersuite", ""))
        kx, enc, mac, fs = infer_algorithms(cipher)
        score = score_tls_record(version, cipher, fs)
        severity = severity_from_score(score)
        flow_id = f"flow-tls-{idx+1}"
        evidence_id = f"evd-tls-{idx+1}"

        labels = []
        issue_types = []
        if version in ["SSLv2", "SSLv3", "TLS 1.0", "TLS 1.1"]:
            labels.append("TLS_LEGACY_VERSION")
            issue_types.append("Legacy TLS")
        if any(k in cipher.upper() for k in ["RC4", "3DES", "DES", "NULL", "EXPORT", "ANON"]):
            labels.append("WEAK_CIPHER")
            issue_types.append("Weak Cipher")
        if "RSA" in kx and not fs:
            labels.append("STATIC_RSA_KEY_EXCHANGE")
            issue_types.append("Static RSA")
        if not issue_types:
            issue_types = ["Cryptographic Observation"]

        cbom_records.append({
            "cbom_id": f"cbom-{idx+1:06d}",
            "flow_id": flow_id,
            "timestamp_observed": row.get("frame.time_epoch", ""),
            "source_ip": src_ip,
            "source_port": row.get("tcp.srcport", ""),
            "destination_ip": dst_ip,
            "destination_port": row.get("tcp.dstport", ""),
            "transport_protocol": "TCP",
            "application_protocol": "TLS",
            "crypto_protocol": "TLS",
            "crypto_version": version,
            "cipher_suite": cipher,
            "encryption_algorithm": enc,
            "key_exchange_algorithm": kx,
            "hash_or_mac_algorithm": mac,
            "forward_secrecy": fs,
            "risk_score": score,
            "risk_level": severity,
            "confidence_score": 0.94 if version != "Unknown" else 0.70,
            "evidence_classification": "Observed",
            "policy_deviation_flags": labels,
            "evidence_id": evidence_id,
            "pcap_sha256": pcap_hash,
        })

        evidence_records.append({
            "evidence_id": evidence_id,
            "flow_id": flow_id,
            "frame_number": row.get("frame.number", ""),
            "timestamp": row.get("frame.time_epoch", ""),
            "source_ip": src_ip,
            "destination_ip": dst_ip,
            "destination_port": row.get("tcp.dstport", ""),
            "protocol": "TLS",
            "observed_field": "tls.handshake.version / tls.handshake.ciphersuite",
            "observed_value": f"{version} / {cipher}",
            "parser": "tshark",
            "pcap_sha256": pcap_hash,
            "defensibility_label": "Observed",
            "confidence_score": 0.94
        })

        for issue in sorted(set(issue_types)):
            if issue != "Cryptographic Observation":
                findings.append({
                    "finding_id": f"find-{len(findings)+1:06d}",
                    "title": issue,
                    "severity": severity,
                    "risk_score": score,
                    "affected_endpoint": f"{dst_ip}:{row.get('tcp.dstport', '')}",
                    "evidence_id": evidence_id,
                    "defensibility_label": "Observed",
                    "confidence_score": 0.94,
                    "business_impact": "Potential confidentiality, audit-readiness, downgrade, or interception risk depending on service criticality.",
                    "compliance_mappings": build_compliance_mappings(issue, "Observed"),
                    "recommendation": make_recommendation(issue),
                })

    # Plaintext protocols
    plain_fields = [
        "frame.number", "frame.time_epoch",
        "ip.src", "tcp.srcport", "udp.srcport",
        "ip.dst", "tcp.dstport", "udp.dstport",
        "ipv6.src", "ipv6.dst",
        "_ws.col.Protocol"
    ]
    plain_df, plain_err = field_extract(file_path, PLAINTEXT_FILTER, plain_fields)
    if not plain_df.empty:
        # keep one row per protocol/endpoint pair to avoid flooding UI
        for idx, row in plain_df.head(500).iterrows():
            proto = row.get("_ws.col.Protocol", "") or "Plaintext"
            src_ip = row.get("ip.src", "") or row.get("ipv6.src", "")
            dst_ip = row.get("ip.dst", "") or row.get("ipv6.dst", "")
            dst_port = row.get("tcp.dstport", "") or row.get("udp.dstport", "")
            flow_id = f"flow-plain-{idx+1}"
            evidence_id = f"evd-plain-{idx+1}"

            cbom_records.append({
                "cbom_id": f"cbom-{len(cbom_records)+1:06d}",
                "flow_id": flow_id,
                "timestamp_observed": row.get("frame.time_epoch", ""),
                "source_ip": src_ip,
                "source_port": row.get("tcp.srcport", "") or row.get("udp.srcport", ""),
                "destination_ip": dst_ip,
                "destination_port": dst_port,
                "transport_protocol": "TCP/UDP",
                "application_protocol": proto,
                "crypto_protocol": "None observed",
                "crypto_version": "Plaintext",
                "cipher_suite": "None",
                "encryption_algorithm": "None",
                "key_exchange_algorithm": "None",
                "hash_or_mac_algorithm": "None",
                "forward_secrecy": False,
                "risk_score": 65,
                "risk_level": "Medium",
                "confidence_score": 0.90,
                "evidence_classification": "Observed",
                "policy_deviation_flags": ["PLAINTEXT_PROTOCOL"],
                "evidence_id": evidence_id,
                "pcap_sha256": pcap_hash,
            })

            evidence_records.append({
                "evidence_id": evidence_id,
                "flow_id": flow_id,
                "frame_number": row.get("frame.number", ""),
                "timestamp": row.get("frame.time_epoch", ""),
                "source_ip": src_ip,
                "destination_ip": dst_ip,
                "destination_port": dst_port,
                "protocol": proto,
                "observed_field": "_ws.col.Protocol",
                "observed_value": proto,
                "parser": "tshark",
                "pcap_sha256": pcap_hash,
                "defensibility_label": "Observed",
                "confidence_score": 0.90
            })

            findings.append({
                "finding_id": f"find-{len(findings)+1:06d}",
                "title": "Plaintext Protocol",
                "severity": "Medium",
                "risk_score": 65,
                "affected_endpoint": f"{dst_ip}:{dst_port}",
                "evidence_id": evidence_id,
                "defensibility_label": "Observed",
                "confidence_score": 0.90,
                "business_impact": "Plaintext traffic may expose credentials, personal data, or business-sensitive information if sensitive payloads are present.",
                "compliance_mappings": build_compliance_mappings("Plaintext Protocol", "Observed"),
                "recommendation": make_recommendation("Plaintext Protocol"),
            })

    # SSH visibility
    ssh_fields = [
        "frame.number", "frame.time_epoch", "ip.src", "tcp.srcport", "ip.dst", "tcp.dstport",
        "ssh.protocol", "ssh.message_code", "ssh.kex_algorithms", "ssh.encryption_algorithms_client_to_server",
        "ssh.encryption_algorithms_server_to_client", "ssh.mac_algorithms_client_to_server",
        "ssh.server_host_key_algorithms"
    ]
    ssh_df, ssh_err = field_extract(file_path, "ssh", ssh_fields)

    for idx, row in ssh_df.head(300).iterrows():
        algs = " ".join([str(row.get(c, "")) for c in ssh_df.columns]).lower()
        weak = any(k in algs for k in ["diffie-hellman-group1-sha1", "ssh-rsa", "hmac-md5", "3des", "arcfour", "cbc"])
        score = 75 if weak else 25
        flow_id = f"flow-ssh-{idx+1}"
        evidence_id = f"evd-ssh-{idx+1}"
        src_ip = row.get("ip.src", "")
        dst_ip = row.get("ip.dst", "")
        cbom_records.append({
            "cbom_id": f"cbom-{len(cbom_records)+1:06d}",
            "flow_id": flow_id,
            "timestamp_observed": row.get("frame.time_epoch", ""),
            "source_ip": src_ip,
            "source_port": row.get("tcp.srcport", ""),
            "destination_ip": dst_ip,
            "destination_port": row.get("tcp.dstport", ""),
            "transport_protocol": "TCP",
            "application_protocol": "SSH",
            "crypto_protocol": "SSH",
            "crypto_version": row.get("ssh.protocol", "SSH"),
            "cipher_suite": "See SSH algorithms",
            "encryption_algorithm": row.get("ssh.encryption_algorithms_client_to_server", ""),
            "key_exchange_algorithm": row.get("ssh.kex_algorithms", ""),
            "hash_or_mac_algorithm": row.get("ssh.mac_algorithms_client_to_server", ""),
            "forward_secrecy": "curve25519" in algs or "ecdh" in algs,
            "risk_score": score,
            "risk_level": severity_from_score(score),
            "confidence_score": 0.75,
            "evidence_classification": "Observed" if row.get("ssh.kex_algorithms", "") else "Risk Indicator",
            "policy_deviation_flags": ["WEAK_SSH_ALGORITHM"] if weak else [],
            "evidence_id": evidence_id,
            "pcap_sha256": pcap_hash,
        })
        if weak:
            findings.append({
                "finding_id": f"find-{len(findings)+1:06d}",
                "title": "Weak SSH Algorithm",
                "severity": severity_from_score(score),
                "risk_score": score,
                "affected_endpoint": f"{dst_ip}:{row.get('tcp.dstport', '')}",
                "evidence_id": evidence_id,
                "defensibility_label": "Observed",
                "confidence_score": 0.75,
                "business_impact": "Weak SSH algorithms may reduce the security of administrative access channels.",
                "compliance_mappings": build_compliance_mappings("Weak SSH Algorithm", "Observed"),
                "recommendation": {
                    "recommendation_id": "REC-SSH-001",
                    "executive": "Harden SSH administrative channels.",
                    "technical": "Disable diffie-hellman-group1-sha1, ssh-rsa/SHA-1, CBC mode ciphers, arcfour, and hmac-md5. Prefer curve25519, ecdh-sha2, chacha20-poly1305, AES-GCM, and SHA-2 MACs.",
                    "verification": "Capture SSH handshake after remediation and confirm only approved algorithms remain.",
                    "owner": "Infrastructure Security"
                },
            })

    # DNSSEC / IPsec / QUIC visibility
    dnssec_df, _ = field_extract(file_path, "dns.flags.authenticated == 1 or dns.resp.type == 46 or dns.resp.type == 48 or dns.resp.type == 43", 
                                 ["frame.number", "frame.time_epoch", "ip.src", "ip.dst", "_ws.col.Info"])
    ipsec_df, _ = field_extract(file_path, "isakmp or esp or ah", 
                                ["frame.number", "frame.time_epoch", "ip.src", "ip.dst", "_ws.col.Protocol", "_ws.col.Info"])
    quic_df, _ = field_extract(file_path, "quic", 
                               ["frame.number", "frame.time_epoch", "ip.src", "udp.srcport", "ip.dst", "udp.dstport", "_ws.col.Info"])

    observations = {
        "dnssec_observations": len(dnssec_df),
        "ipsec_ike_observations": len(ipsec_df),
        "quic_observations": len(quic_df),
        "tls_serverhello_records": len(tls_df),
        "plaintext_records_sampled": len(plain_df),
        "ssh_records_sampled": len(ssh_df)
    }

    report = {
        "analysis_time": analysis_time,
        "pcap_sha256": pcap_hash,
        "capinfos": capinfos,
        "observations": observations,
        "cbom": cbom_records,
        "findings": findings,
        "evidence": evidence_records,
        "limitations": [
            "This analysis only covers traffic present in the uploaded PCAP.",
            "Full legal, regulatory, or organizational compliance cannot be proven from PCAP alone.",
            "Encrypted payload contents are not visible unless payload inspection/decryption is separately authorized and configured.",
            "Short or incomplete captures may miss handshakes, certificates, or endpoint behavior.",
            "NAT, proxies, and load balancers may affect asset attribution.",
            "Compliance mappings are evidence-backed indicators, not certifications."
        ],
        "parser_errors": {
            "tls": tls_err,
            "plaintext": plain_err,
            "ssh": ssh_err
        }
    }
    return report

def make_html_report(report):
    findings = report["findings"]
    cbom = report["cbom"]
    critical = sum(1 for f in findings if f["severity"] == "Critical")
    high = sum(1 for f in findings if f["severity"] == "High")
    medium = sum(1 for f in findings if f["severity"] == "Medium")
    risk_score = max([f["risk_score"] for f in findings], default=0)
    rows = ""
    for f in findings[:50]:
        rows += f"""
        <tr>
            <td>{f['finding_id']}</td>
            <td>{f['title']}</td>
            <td>{f['severity']}</td>
            <td>{f['risk_score']}</td>
            <td>{f['affected_endpoint']}</td>
            <td>{f['defensibility_label']}</td>
        </tr>
        """

    return f"""
    <html>
    <head>
        <title>CryptoSight CBOM Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; color: #0f172a; }}
            h1 {{ color: #0f172a; }}
            .card {{ border:1px solid #e2e8f0; border-radius:16px; padding:18px; margin:14px 0; box-shadow:0 6px 20px rgba(15,23,42,.06); }}
            table {{ width:100%; border-collapse:collapse; margin-top:16px; }}
            th, td {{ border-bottom:1px solid #e2e8f0; padding:9px; text-align:left; font-size:13px; }}
            th {{ background:#f8fafc; }}
        </style>
    </head>
    <body>
        <h1>CryptoSight CBOM Executive Report</h1>
        <p><b>Analysis time:</b> {report['analysis_time']}</p>
        <p><b>PCAP SHA256:</b> {report['pcap_sha256']}</p>
        <div class="card">
            <h2>Executive Summary</h2>
            <p>The uploaded PCAP produced {len(cbom)} CBOM observations and {len(findings)} risk findings. The highest observed risk score is {risk_score}. These findings are based on PCAP-derived evidence and do not constitute full legal or regulatory compliance certification.</p>
            <p><b>Critical:</b> {critical} &nbsp; <b>High:</b> {high} &nbsp; <b>Medium:</b> {medium}</p>
        </div>
        <div class="card">
            <h2>Top Findings</h2>
            <table>
                <tr><th>ID</th><th>Finding</th><th>Severity</th><th>Score</th><th>Endpoint</th><th>Label</th></tr>
                {rows}
            </table>
        </div>
        <div class="card">
            <h2>Limitations</h2>
            <ul>
                {''.join('<li>'+x+'</li>' for x in report['limitations'])}
            </ul>
        </div>
    </body>
    </html>
    """

# -------------------------------
# Sidebar
# -------------------------------
st.sidebar.title("🛡️ CryptoSight CBOM")
st.sidebar.caption("PCAP-based cryptographic visibility, policy deviation, and compliance-risk intelligence.")

st.sidebar.markdown("### Analysis Settings")
payload_inspection = st.sidebar.toggle(
    "Payload inspection mode",
    value=False,
    help="Disabled by default. This dashboard focuses on metadata/handshake evidence. Enable only where legally approved."
)
policy_mode = st.sidebar.selectbox(
    "Policy baseline",
    ["Enterprise secure baseline", "Strict regulated environment", "Legacy tolerant mode"]
)
st.sidebar.markdown("---")
st.sidebar.markdown("### Defensibility Rules")
st.sidebar.write("✅ No full compliance claims")
st.sidebar.write("✅ PCAP evidence only")
st.sidebar.write("✅ Labels: Observed / Inferred / Risk Indicator / Manual Validation")
st.sidebar.write("✅ Confidence scores included")

# -------------------------------
# Header
# -------------------------------
st.markdown('<div class="headline">CryptoSight CBOM Dashboard</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subheadline">Upload a real PCAP/PCAPNG file to generate a Cryptographic Bill of Materials, policy deviations, compliance-risk indicators, and executive recommendations.</div>',
    unsafe_allow_html=True,
)

with st.expander("Important limitation", expanded=False):
    st.warning(
        "This tool analyzes only the traffic present in the uploaded PCAP. "
        "It does not prove full organizational, legal, regulatory, or framework compliance. "
        "Compliance statements are evidence-backed indicators and must be manually validated for formal audits."
    )

uploaded = st.file_uploader(
    "Upload PCAP / PCAPNG",
    type=["pcap", "pcapng", "cap"],
    help="Upload-only analysis. Files are processed locally in this Streamlit session."
)

if not uploaded:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("CBOM Records", "—")
    c2.metric("Findings", "—")
    c3.metric("Highest Risk", "—")
    c4.metric("Evidence Confidence", "—")
    st.info("Upload a `.pcap` or `.pcapng` file to begin analysis.")
    st.stop()

suffix = Path(uploaded.name).suffix or ".pcap"
with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
    tmp.write(uploaded.read())
    tmp_path = tmp.name

try:
    with st.spinner("Analyzing PCAP with tshark. Large files may take longer..."):
        report = analyze_pcap(tmp_path)
finally:
    try:
        os.remove(tmp_path)
    except Exception:
        pass

cbom_df = pd.DataFrame(report["cbom"])
findings_df = pd.DataFrame(report["findings"])
evidence_df = pd.DataFrame(report["evidence"])

# -------------------------------
# Executive overview
# -------------------------------
max_risk = int(findings_df["risk_score"].max()) if not findings_df.empty else 0
risk_label = severity_from_score(max_risk)
critical_count = int((findings_df["severity"] == "Critical").sum()) if not findings_df.empty else 0
high_count = int((findings_df["severity"] == "High").sum()) if not findings_df.empty else 0
medium_count = int((findings_df["severity"] == "Medium").sum()) if not findings_df.empty else 0
avg_conf = round(float(evidence_df["confidence_score"].mean()), 2) if not evidence_df.empty else 0

m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Overall Risk", risk_label, f"{max_risk}/100")
m2.metric("CBOM Records", len(cbom_df))
m3.metric("Findings", len(findings_df))
m4.metric("Critical / High", f"{critical_count} / {high_count}")
m5.metric("Avg Confidence", avg_conf)

st.markdown("## Executive Overview")

if findings_df.empty:
    st.success("No high-risk cryptographic deviations were identified in the parsed evidence. This does not prove full compliance; it only reflects the uploaded capture.")
else:
    top = findings_df.sort_values("risk_score", ascending=False).head(5)
    st.markdown("### Top 5 Decisions Required")
    for _, row in top.iterrows():
        st.markdown(
            f"""
            <div class="metric-card">
            <b>{row['severity']}:</b> {row['title']} on <b>{row['affected_endpoint']}</b><br>
            <span class="small-muted">Defensibility: {row['defensibility_label']} | Confidence: {row['confidence_score']} | Evidence: {row['evidence_id']}</span><br>
            <b>Action:</b> {row['recommendation']['executive']}
            </div>
            """,
            unsafe_allow_html=True
        )

# -------------------------------
# Tabs
# -------------------------------
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📦 CBOM Inventory",
    "⚠️ Policy Deviations",
    "📜 Compliance Posture",
    "🔎 Evidence Explorer",
    "🛠️ Recommendations",
    "⬇️ Exports"
])

with tab1:
    st.subheader("Cryptographic Bill of Materials")
    if cbom_df.empty:
        st.info("No cryptographic or plaintext protocol observations were extracted.")
    else:
        show_cols = [
            "cbom_id", "source_ip", "destination_ip", "destination_port",
            "application_protocol", "crypto_version", "cipher_suite",
            "encryption_algorithm", "key_exchange_algorithm", "forward_secrecy",
            "risk_level", "risk_score", "evidence_classification", "confidence_score"
        ]
        st.dataframe(cbom_df[[c for c in show_cols if c in cbom_df.columns]], use_container_width=True)

        st.markdown("### TLS Version Distribution")
        if "crypto_version" in cbom_df:
            st.bar_chart(cbom_df["crypto_version"].value_counts())

        st.markdown("### Protocol Distribution")
        if "application_protocol" in cbom_df:
            st.bar_chart(cbom_df["application_protocol"].value_counts())

with tab2:
    st.subheader("Policy Deviations")
    if findings_df.empty:
        st.success("No policy deviations were identified from parsed evidence.")
    else:
        cols = ["finding_id", "title", "severity", "risk_score", "affected_endpoint", "defensibility_label", "confidence_score", "evidence_id"]
        st.dataframe(findings_df[[c for c in cols if c in findings_df.columns]], use_container_width=True)

        st.markdown("### Severity Breakdown")
        st.bar_chart(findings_df["severity"].value_counts())

with tab3:
    st.subheader("Compliance Posture")
    st.caption("Compliance posture is evidence-backed but not a full legal or regulatory compliance determination.")

    if findings_df.empty:
        st.info("No compliance risk indicators were generated from findings.")
    else:
        records = []
        for _, f in findings_df.iterrows():
            for m in f["compliance_mappings"]:
                records.append({
                    "finding_id": f["finding_id"],
                    "framework": m["framework"],
                    "defensibility_label": m["defensibility_label"],
                    "statement": m["statement"],
                    "manual_validation_required": m["defensibility_label"] in ["Risk Indicator", "Requires Manual Validation"]
                })
        comp_df = pd.DataFrame(records)
        st.dataframe(comp_df, use_container_width=True)

        st.markdown("### Defensibility Breakdown")
        st.bar_chart(comp_df["defensibility_label"].value_counts())

        st.markdown("### Manual Validation Checklist")
        st.write("- Confirm asset criticality and business owner.")
        st.write("- Confirm whether sensitive, regulated, personal, health, or payment data was transmitted.")
        st.write("- Review encryption policy and approved exception records.")
        st.write("- Review compensating controls for legacy systems.")
        st.write("- Validate formal legal/regulatory interpretation with compliance/legal teams.")

with tab4:
    st.subheader("Evidence Explorer")
    if evidence_df.empty:
        st.info("No evidence records were produced.")
    else:
        st.dataframe(evidence_df, use_container_width=True)

with tab5:
    st.subheader("Recommendations")
    if findings_df.empty:
        st.info("No recommendations generated because no findings were identified.")
    else:
        seen = set()
        for _, row in findings_df.sort_values("risk_score", ascending=False).iterrows():
            rec = row["recommendation"]
            key = rec["recommendation_id"] + row["affected_endpoint"]
            if key in seen:
                continue
            seen.add(key)
            with st.expander(f"{row['severity']} | {row['title']} | {row['affected_endpoint']}", expanded=False):
                st.write("**Executive action:**", rec["executive"])
                st.write("**Technical remediation:**", rec["technical"])
                st.write("**Suggested owner:**", rec["owner"])
                st.write("**Verification method:**", rec["verification"])
                st.write("**Residual risk guidance:** Document exceptions with owner, expiry date, compensating controls, and risk acceptance approval.")

with tab6:
    st.subheader("Exports")
    report_json = json.dumps(report, indent=2)
    st.download_button(
        "Download Full JSON Report",
        data=report_json,
        file_name="cryptosight_cbom_report.json",
        mime="application/json",
    )

    if not cbom_df.empty:
        st.download_button(
            "Download CBOM CSV",
            data=cbom_df.to_csv(index=False),
            file_name="cbom_inventory.csv",
            mime="text/csv",
        )

    if not findings_df.empty:
        export_findings = findings_df.drop(columns=["compliance_mappings", "recommendation"], errors="ignore")
        st.download_button(
            "Download Findings CSV",
            data=export_findings.to_csv(index=False),
            file_name="policy_deviations.csv",
            mime="text/csv",
        )

    html_report = make_html_report(report)
    st.download_button(
        "Download Executive HTML Report",
        data=html_report,
        file_name="executive_cbom_report.html",
        mime="text/html",
    )

    st.markdown("### PCAP Integrity")
    st.code(report["pcap_sha256"])

st.markdown("---")
st.caption("CryptoSight CBOM | PCAP-derived evidence only. Do not use this output as a standalone legal or regulatory compliance certification.")
