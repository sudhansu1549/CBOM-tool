
import streamlit as st
import pandas as pd
import subprocess, tempfile, hashlib, uuid, json, os, shutil, re
from pathlib import Path
from datetime import datetime

# ============================================================
# RBI CBOM — Executive PCAP Cryptographic & Quantum Readiness Dashboard
# ============================================================

st.set_page_config(
    page_title="RBI CBOM | Executive Quantum Readiness Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -------------------------------
# Executive UI Styling
# -------------------------------
st.markdown("""
<style>
:root {
  --navy:#0B1F44;
  --blue:#1747A6;
  --sky:#EAF2FF;
  --green:#047857;
  --amber:#B45309;
  --orange:#EA580C;
  --red:#B91C1C;
  --slate:#334155;
  --muted:#64748B;
  --border:#E2E8F0;
  --card:#FFFFFF;
  --bg:#F8FAFC;
}
.main {
  background: radial-gradient(circle at top left, #EEF6FF 0, #F8FAFC 32%, #FFFFFF 100%);
}
.block-container { padding-top: 1.1rem; padding-bottom: 2.2rem; }
.hero {
  padding: 26px 30px;
  border-radius: 26px;
  background: linear-gradient(135deg, #071B3A 0%, #0B2F6B 48%, #1747A6 100%);
  color: white;
  margin-bottom: 18px;
  box-shadow: 0 22px 52px rgba(7, 27, 58, .24);
}
.hero h1 { margin: 0; font-size: 36px; font-weight: 950; letter-spacing:-.03em; }
.hero p { margin: 8px 0 0 0; color: #DBEAFE; font-size: 15px; }
.section {
  background: linear-gradient(90deg, #0B2F6B, #1747A6);
  color: white;
  padding: 12px 16px;
  border-radius: 14px;
  font-weight: 900;
  margin: 20px 0 12px;
}
.card {
  background: #FFFFFF;
  border: 1px solid #E2E8F0;
  border-radius: 20px;
  padding: 16px;
  box-shadow: 0 10px 28px rgba(15, 23, 42, .07);
  margin-bottom: 12px;
}
.kpi {
  background: rgba(255,255,255,.96);
  border: 1px solid #E2E8F0;
  border-radius: 20px;
  padding: 16px 12px;
  text-align: center;
  box-shadow: 0 10px 28px rgba(15,23,42,.07);
  min-height: 118px;
}
.kpi small {
  color: #64748B;
  font-size: 11px;
  font-weight: 900;
  text-transform: uppercase;
  letter-spacing: .055em;
}
.kpi b {
  display:block;
  font-size: 26px;
  color: #0F172A;
  margin-top: 8px;
  line-height: 1.1;
}
.badge {
  display:inline-block;
  padding: 5px 10px;
  border-radius: 999px;
  color: white;
  font-size: 12px;
  font-weight: 900;
}
.badge-red { background:#B91C1C; }
.badge-orange { background:#EA580C; }
.badge-amber { background:#B45309; }
.badge-green { background:#047857; }
.badge-blue { background:#1747A6; }
.muted { color:#64748B; font-size:13px; }
.big-number { font-size:34px; font-weight:950; color:#0B1F44; }
.executive-note {
  padding: 14px 16px;
  border-left: 5px solid #1747A6;
  background: #EFF6FF;
  border-radius: 14px;
  color: #0B1F44;
}
.warning-note {
  padding: 14px 16px;
  border-left: 5px solid #EA580C;
  background: #FFF7ED;
  border-radius: 14px;
  color: #7C2D12;
}
.success-note {
  padding: 14px 16px;
  border-left: 5px solid #047857;
  background: #ECFDF5;
  border-radius: 14px;
  color: #064E3B;
}
</style>
""", unsafe_allow_html=True)

# -------------------------------
# Mapping dictionaries
# -------------------------------
TLS_VERSION_MAP = {
    "0x0002": "SSLv2",
    "0x0300": "SSLv3",
    "0x0301": "TLSv1.0",
    "0x0302": "TLSv1.1",
    "0x0303": "TLSv1.2",
    "0x0304": "TLSv1.3",
    "769": "TLSv1.0",
    "770": "TLSv1.1",
    "771": "TLSv1.2",
    "772": "TLSv1.3",
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
    "4865": "TLS_AES_128_GCM_SHA256",
    "4866": "TLS_AES_256_GCM_SHA384",
    "4867": "TLS_CHACHA20_POLY1305_SHA256",
}

NAMED_GROUP_MAP = {
    "0x0017": "secp256r1",
    "0x0018": "secp384r1",
    "0x0019": "secp521r1",
    "0x001d": "x25519",
    "0x001e": "x448",
    "23": "secp256r1",
    "24": "secp384r1",
    "25": "secp521r1",
    "29": "x25519",
    "30": "x448",
    "secp256r1": "secp256r1",
    "prime256v1": "secp256r1",
    "x25519": "x25519",
    "x448": "x448",
    "secp384r1": "secp384r1",
    "secp521r1": "secp521r1",
}

PQC_KEYWORDS = ["ml-kem", "kyber", "mlkem", "ml_dsa", "ml-dsa", "dilithium", "slh-dsa", "sphincs", "hybrid", "pqc"]

PQC_REFERENCE = pd.DataFrame([
    {"Algorithm": "ML-KEM / Kyber", "Type": "Lattice-based KEM", "NIST Status": "FIPS 203 Approved", "Use Case": "Key encapsulation / key exchange"},
    {"Algorithm": "ML-DSA / Dilithium", "Type": "Lattice-based signature", "NIST Status": "FIPS 204 Approved", "Use Case": "Digital signatures"},
    {"Algorithm": "SLH-DSA / SPHINCS+", "Type": "Hash-based signature", "NIST Status": "FIPS 205 Approved", "Use Case": "Stateless signatures"},
    {"Algorithm": "FN-DSA / Falcon", "Type": "Lattice-based signature", "NIST Status": "Pending / Round 4 family", "Use Case": "Compact signatures"},
])

GLOSSARY = pd.DataFrame([
    {"Term": "CBOM", "Definition": "Cryptography Bill of Materials — inventory of cryptographic assets observed or inferred from evidence."},
    {"Term": "PQC", "Definition": "Post-Quantum Cryptography — algorithms designed to resist known quantum attacks."},
    {"Term": "Q-Day", "Definition": "Point at which a cryptographically relevant quantum computer could break widely used public-key cryptography."},
    {"Term": "HNDL", "Definition": "Harvest Now, Decrypt Later — capture encrypted data today and decrypt it later when quantum capability matures."},
    {"Term": "Shor's Algorithm", "Definition": "Quantum algorithm threatening RSA, finite-field DH, ECDH and ECDSA."},
    {"Term": "Grover's Algorithm", "Definition": "Quantum search algorithm reducing effective security margin of symmetric algorithms."},
    {"Term": "Evidence Label", "Definition": "Observed, Inferred, Risk Indicator, or Requires Manual Validation."},
])

# -------------------------------
# Utility functions
# -------------------------------
def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def run_tshark(args, timeout=300):
    if not shutil.which("tshark"):
        return False, "", "tshark not found. Deploy using Docker/Render or install Wireshark/tshark."
    try:
        res = subprocess.run(["tshark"] + args, capture_output=True, text=True, timeout=timeout)
        return res.returncode == 0 or bool(res.stdout.strip()), res.stdout, res.stderr
    except subprocess.TimeoutExpired:
        return False, "", "tshark command timed out."
    except Exception as e:
        return False, "", str(e)

def extract_fields(file_path, display_filter, fields, timeout=300):
    args = ["-r", file_path, "-Y", display_filter, "-T", "fields", "-E", "header=y", "-E", "separator=\t"]
    for field in fields:
        args += ["-e", field]
    ok, out, err = run_tshark(args, timeout)
    if not out.strip():
        return pd.DataFrame(columns=fields), err
    from io import StringIO
    try:
        return pd.read_csv(StringIO(out), sep="\t", dtype=str).fillna(""), err
    except Exception as e:
        return pd.DataFrame(columns=fields), str(e)

def normalize_tls_version(v):
    v = str(v or "").strip()
    if "," in v:
        parts = [p.strip() for p in v.split(",") if p.strip()]
        # choose highest known version when multiple appear
        vals = [TLS_VERSION_MAP.get(p.lower(), TLS_VERSION_MAP.get(p, p)) for p in parts]
        order = {"SSLv2":0, "SSLv3":1, "TLSv1.0":2, "TLSv1.1":3, "TLSv1.2":4, "TLSv1.3":5}
        return sorted(vals, key=lambda x: order.get(x, -1), reverse=True)[0] if vals else "Unknown"
    return TLS_VERSION_MAP.get(v.lower(), TLS_VERSION_MAP.get(v, v or "Unknown"))

def normalize_cipher(c):
    c = str(c or "").strip()
    if "," in c:
        c = c.split(",")[-1].strip()
    return CIPHER_MAP.get(c.lower(), CIPHER_MAP.get(c, c or "Unknown"))

def normalize_group(g):
    g = str(g or "").strip()
    if not g:
        return ""
    if "," in g:
        # ServerHello usually has one key share; choose last populated.
        parts = [p.strip() for p in g.split(",") if p.strip()]
        g = parts[-1] if parts else ""
    return NAMED_GROUP_MAP.get(g.lower(), NAMED_GROUP_MAP.get(g, g))

def infer_cipher_components(cipher, tls_version):
    u = str(cipher).upper()

    if "TLS_AES_" in u or "CHACHA20" in u or tls_version == "TLSv1.3":
        kx_family = "TLS 1.3 key schedule"
    elif "ECDHE" in u:
        kx_family = "ECDHE"
    elif re.search(r"(^|_)DHE(_|$)", u):
        kx_family = "DHE"
    elif "RSA_WITH" in u or u.startswith("TLS_RSA"):
        kx_family = "RSA static key exchange"
    elif "PSK" in u:
        kx_family = "PSK"
    else:
        kx_family = "Unknown"

    if "AES_256_GCM" in u:
        enc = "AES-256-GCM"
    elif "AES_128_GCM" in u:
        enc = "AES-128-GCM"
    elif "AES_256_CBC" in u:
        enc = "AES-256-CBC"
    elif "AES_128_CBC" in u:
        enc = "AES-128-CBC"
    elif "CHACHA20" in u:
        enc = "ChaCha20-Poly1305"
    elif "3DES" in u:
        enc = "3DES"
    elif "DES" in u:
        enc = "DES"
    elif "RC4" in u:
        enc = "RC4"
    elif "NULL" in u:
        enc = "NULL"
    else:
        enc = "Unknown"

    if "SHA384" in u:
        mac = "SHA-384"
    elif "SHA256" in u:
        mac = "SHA-256"
    elif "SHA" in u:
        mac = "SHA-1"
    elif "MD5" in u:
        mac = "MD5"
    else:
        mac = "AEAD / Unknown"

    forward_secrecy = ("ECDHE" in kx_family) or ("DHE" == kx_family) or tls_version == "TLSv1.3"
    return kx_family, enc, mac, forward_secrecy

def classify_quantum_readiness(tls_version, cipher, kx_family, named_group, cert_sig_alg="", cert_pubkey_alg="", cert_pubkey_size=""):
    """
    More accurate model:
    - RSA, ECDH/ECDHE, ECDSA, DHE, DSA are quantum-vulnerable to Shor's algorithm.
    - TLS 1.3 is not automatically quantum safe; standard TLS 1.3 normally uses ECDHE unless hybrid/PQC group is observed.
    - AES-256/SHA-384 have stronger post-quantum margin than AES-128/SHA-256.
    - PQC/hybrid is only marked quantum-safe if explicitly observed in group/algorithm strings.
    """
    observed_text = " ".join([tls_version, cipher, kx_family, named_group, cert_sig_alg, cert_pubkey_alg]).lower()

    if any(k in observed_text for k in PQC_KEYWORDS):
        return {
            "algorithm": named_group or "Hybrid PQC / PQC",
            "category": "Post-Quantum / Hybrid",
            "quantum_status": "Quantum Safe",
            "quantum_safe": True,
            "priority": 4,
            "threat_basis": "PQC / hybrid PQC observed",
            "attack_algorithm": "No known Shor/Grover break for approved PQC family",
            "estimated_break": "No known practical quantum break for approved PQC",
            "migration": "Maintain crypto-agility, implementation assurance, and monitoring.",
            "confidence": 0.88,
            "evidence_label": "Observed",
        }

    # Asymmetric key establishment/signature observed or inferred
    asymmetric_indicators = [
        "ecdhe", "ecdh", "ecdsa", "rsa", "dhe", "diffie", "dsa",
        "secp", "prime256", "x25519", "x448"
    ]
    if any(x in observed_text for x in asymmetric_indicators):
        alg_name = named_group or cert_pubkey_alg or kx_family
        if not alg_name or alg_name == "TLS 1.3 key schedule":
            alg_name = "ECDHE / classical asymmetric key exchange"
        return {
            "algorithm": alg_name,
            "category": "Classical asymmetric cryptography",
            "quantum_status": "Quantum Vulnerable",
            "quantum_safe": False,
            "priority": 2,
            "threat_basis": "Shor’s algorithm at Q-Day",
            "attack_algorithm": "Shor's algorithm",
            "estimated_break": "Q-Day / CRQC dependent",
            "migration": "Plan hybrid/PQC migration. Prefer ML-KEM for key establishment and ML-DSA/SLH-DSA for signatures where supported.",
            "confidence": 0.86 if named_group else 0.78,
            "evidence_label": "Observed" if named_group or "rsa" in observed_text or "ecdhe" in observed_text else "Inferred",
        }

    # Symmetric only view
    if any(x in observed_text for x in ["aes-256", "sha-384", "sha-512"]):
        return {
            "algorithm": "AES-256 / SHA-384+",
            "category": "Symmetric / hash algorithm",
            "quantum_status": "Adequate Post-Quantum Margin",
            "quantum_safe": True,
            "priority": 4,
            "threat_basis": "Grover’s algorithm mitigated by larger security margin",
            "attack_algorithm": "Grover's algorithm",
            "estimated_break": "Adequate post-quantum margin",
            "migration": "Maintain AES-256 and SHA-384/512 preference.",
            "confidence": 0.82,
            "evidence_label": "Observed",
        }

    if any(x in observed_text for x in ["aes-128", "sha-256", "chacha20"]):
        return {
            "algorithm": "AES-128 / SHA-256 / ChaCha20 family",
            "category": "Symmetric / hash algorithm",
            "quantum_status": "Quantum Weakened",
            "quantum_safe": False,
            "priority": 3,
            "threat_basis": "Grover’s algorithm reduces effective security margin",
            "attack_algorithm": "Grover's algorithm",
            "estimated_break": "Post-Q-Day effective margin reduction",
            "migration": "Prefer AES-256 and SHA-384/512 for long-lived sensitive data.",
            "confidence": 0.82,
            "evidence_label": "Risk Indicator",
        }

    return {
        "algorithm": "Unknown / Not enough handshake evidence",
        "category": "Unknown",
        "quantum_status": "Requires Manual Validation",
        "quantum_safe": False,
        "priority": 3,
        "threat_basis": "Insufficient cryptographic metadata in capture",
        "attack_algorithm": "Unknown",
        "estimated_break": "Unknown",
        "migration": "Capture complete handshakes and validate system crypto configuration manually.",
        "confidence": 0.50,
        "evidence_label": "Requires Manual Validation",
    }

def risk_from_record(flags, quantum_priority):
    if "PLAINTEXT_PROTOCOL" in flags or "TLS_LEGACY_VERSION" in flags or "WEAK_CIPHER" in flags:
        return "Critical"
    if "STATIC_RSA_KEY_EXCHANGE" in flags:
        return "High"
    if quantum_priority == 2:
        return "Medium"
    if quantum_priority == 3:
        return "Medium"
    return "Low"

def priority_badge(priority):
    color = {
        "Priority 1": "badge-red",
        "Priority 2": "badge-orange",
        "Priority 3": "badge-amber",
        "Priority 4": "badge-green",
    }.get(priority, "badge-blue")
    return f"<span class='badge {color}'>{priority}</span>"

def score_compliance(cbom):
    has_legacy = any("TLS_LEGACY_VERSION" in r["Policy Flags List"] for r in cbom)
    has_weak = any("WEAK_CIPHER" in r["Policy Flags List"] for r in cbom)
    has_plain = any("PLAINTEXT_PROTOCOL" in r["Policy Flags List"] for r in cbom)
    has_qv = any(r["Quantum Priority"] == "Priority 2" for r in cbom)
    has_unknown = any(r["Evidence Label"] == "Requires Manual Validation" for r in cbom)

    rows = [
        {
            "Standard": "NIST SP 800-52 Rev. 2",
            "Posture": "Non-alignment Indicator" if has_legacy or has_weak else "No direct TLS baseline violation observed",
            "Score": "0%" if has_legacy or has_weak else "80%",
            "Evidence Label": "Observed" if has_legacy or has_weak else "Risk Indicator",
            "Auditor-Safe Statement": "Observed TLS/cipher evidence indicates potential non-alignment with modern TLS baseline expectations." if has_legacy or has_weak else "No legacy TLS or weak cipher was observed in the uploaded capture; this does not prove full environment compliance."
        },
        {
            "Standard": "NIST SP 800-131A",
            "Posture": "Non-alignment Indicator" if has_legacy or has_weak else "Partial Alignment Indicator",
            "Score": "0%" if has_legacy or has_weak else "80%",
            "Evidence Label": "Observed" if has_legacy or has_weak else "Risk Indicator",
            "Auditor-Safe Statement": "Deprecated or weak cryptographic mechanisms are directly observable when present in parsed PCAP evidence."
        },
        {
            "Standard": "CNSA 2.0 / PQC Readiness",
            "Posture": "PQC Migration Required" if has_qv else "No classical asymmetric PQC gap observed",
            "Score": "0%" if has_qv else "70%",
            "Evidence Label": "Risk Indicator",
            "Auditor-Safe Statement": "Classical asymmetric cryptography observed in TLS/PKI is quantum-vulnerable. Formal CNSA 2.0 conformance requires architecture and configuration review."
        },
        {
            "Standard": "PCI DSS",
            "Posture": "Compliance Risk Indicator" if has_legacy or has_weak or has_plain else "Partial Alignment Indicator",
            "Score": "0%" if has_legacy or has_weak or has_plain else "70%",
            "Evidence Label": "Risk Indicator",
            "Auditor-Safe Statement": "PCAP can show weak/plaintext transport indicators, but cardholder-data scope requires manual validation."
        },
        {
            "Standard": "ISO/IEC 27001 / 27002",
            "Posture": "Security Control Risk Indicator" if has_legacy or has_weak or has_plain else "Technical Indicator",
            "Score": "40%" if has_legacy or has_weak or has_plain else "75%",
            "Evidence Label": "Risk Indicator",
            "Auditor-Safe Statement": "Network encryption evidence supports technical control assessment, not full ISMS certification."
        },
        {
            "Standard": "RBI Cybersecurity Expectations",
            "Posture": "Cryptographic Hygiene Risk Indicator" if has_legacy or has_weak or has_plain or has_qv else "Technical Indicator",
            "Score": "40%" if has_legacy or has_weak or has_plain or has_qv else "75%",
            "Evidence Label": "Risk Indicator",
            "Auditor-Safe Statement": "The PCAP provides cryptographic evidence useful for risk review; full RBI compliance requires policy, governance, incident, and control evidence."
        },
        {
            "Standard": "CERT-In Directions",
            "Posture": "Manual Validation Required",
            "Score": "Manual",
            "Evidence Label": "Requires Manual Validation",
            "Auditor-Safe Statement": "PCAP may support incident investigation, but reporting obligations require incident context, timeline, and legal/compliance review."
        },
        {
            "Standard": "DPDP Act, 2023",
            "Posture": "Personal Data Exposure Risk Indicator" if has_plain or has_weak else "Manual Validation Required",
            "Score": "40%" if has_plain or has_weak else "Manual",
            "Evidence Label": "Risk Indicator" if has_plain or has_weak else "Requires Manual Validation",
            "Auditor-Safe Statement": "PCAP alone cannot prove DPDP compliance. Validate whether personal data was present, processed, or exposed."
        },
        {
            "Standard": "FIPS 140-3",
            "Posture": "Algorithm Indicator Only",
            "Score": "Manual",
            "Evidence Label": "Requires Manual Validation",
            "Auditor-Safe Statement": "PCAP may show algorithm use, but FIPS module validation cannot be proven from traffic alone."
        }
    ]
    return rows

def analyze_pcap(path, meta):
    start = datetime.now()
    pcap_hash = sha256_file(path)

    frame_df, _ = extract_fields(path, "frame", ["frame.number"])
    total_packets = len(frame_df)

    # ServerHello gives negotiated version/cipher. KeyShare group improves PQ accuracy for TLS 1.3.
    tls_fields = [
        "frame.number", "frame.time_epoch",
        "ip.src", "tcp.srcport", "ip.dst", "tcp.dstport",
        "ipv6.src", "ipv6.dst",
        "tls.handshake.version",
        "tls.handshake.ciphersuite",
        "tls.handshake.extensions_server_name",
        "tls.handshake.extensions_key_share_group",
        "tls.handshake.extensions_supported_group"
    ]
    tls_df, tls_err = extract_fields(path, "tls.handshake.type == 2", tls_fields)

    # ClientHello can provide SNI and supported groups if ServerHello key share field is unavailable.
    ch_fields = [
        "frame.number", "frame.time_epoch",
        "ip.src", "tcp.srcport", "ip.dst", "tcp.dstport",
        "tls.handshake.extensions_server_name",
        "tls.handshake.extensions_supported_group",
        "tls.handshake.ciphersuite"
    ]
    client_hello_df, _ = extract_fields(path, "tls.handshake.type == 1", ch_fields)

    # Certificate metadata: field availability varies by tshark version, so keep optional.
    cert_fields = [
        "frame.number", "frame.time_epoch",
        "ip.src", "ip.dst",
        "x509af.signature_algorithm",
        "x509af.subjectPublicKeyInfo.algorithm.algorithm",
        "x509af.rsa_modulus",
        "x509sat.printableString",
        "x509sat.uTF8String"
    ]
    cert_df, cert_err = extract_fields(path, "tls.handshake.certificate", cert_fields)

    plaintext_df, plaintext_err = extract_fields(
        path,
        "http or ftp or telnet or smtp or pop or imap or ldap or snmp",
        ["frame.number","frame.time_epoch","ip.src","tcp.srcport","udp.srcport","ip.dst","tcp.dstport","udp.dstport","_ws.col.Protocol"]
    )

    ssh_df, _ = extract_fields(path, "ssh", ["frame.number","frame.time_epoch","ip.src","ip.dst","tcp.dstport","ssh.protocol","ssh.kex_algorithms","ssh.encryption_algorithms_client_to_server","ssh.mac_algorithms_client_to_server","ssh.server_host_key_algorithms"])
    dnssec_df, _ = extract_fields(path, "dns.flags.authenticated == 1 or dns.resp.type == 46 or dns.resp.type == 48 or dns.resp.type == 43", ["frame.number"])
    ipsec_df, _ = extract_fields(path, "isakmp or esp or ah", ["frame.number"])
    quic_df, _ = extract_fields(path, "quic", ["frame.number","frame.time_epoch","ip.src","udp.srcport","ip.dst","udp.dstport","_ws.col.Info"])

    cbom, evidence, findings = [], [], []
    algorithm_map = {}

    # TLS observations
    for i, r in tls_df.iterrows():
        src = r.get("ip.src","") or r.get("ipv6.src","")
        dst = r.get("ip.dst","") or r.get("ipv6.dst","")
        sport = r.get("tcp.srcport","")
        dport = r.get("tcp.dstport","")
        version = normalize_tls_version(r.get("tls.handshake.version",""))
        cipher = normalize_cipher(r.get("tls.handshake.ciphersuite",""))
        keyshare_group = normalize_group(r.get("tls.handshake.extensions_key_share_group",""))
        supported_group = normalize_group(r.get("tls.handshake.extensions_supported_group",""))
        named_group = keyshare_group or supported_group

        # If no group appears in ServerHello, try to infer from ClientHello on the opposite flow.
        if not named_group and not client_hello_df.empty:
            candidate = client_hello_df[
                ((client_hello_df.get("ip.src","") == dst) & (client_hello_df.get("ip.dst","") == src)) |
                ((client_hello_df.get("ip.src","") == src) & (client_hello_df.get("ip.dst","") == dst))
            ]
            if not candidate.empty:
                named_group = normalize_group(candidate.iloc[0].get("tls.handshake.extensions_supported_group",""))

        kx_family, enc, mac, fs = infer_cipher_components(cipher, version)
        cert_sig = ""
        cert_pk_alg = ""
        cert_pk_size = ""

        q = classify_quantum_readiness(version, cipher, kx_family, named_group, cert_sig, cert_pk_alg, cert_pk_size)

        flags = []
        if version in ["SSLv2", "SSLv3", "TLSv1.0", "TLSv1.1"]:
            flags.append("TLS_LEGACY_VERSION")
        if any(x in cipher.upper() for x in ["RC4","3DES","DES","NULL","EXPORT","ANON","MD5"]):
            flags.append("WEAK_CIPHER")
        if kx_family == "RSA static key exchange":
            flags.append("STATIC_RSA_KEY_EXCHANGE")
        if q["priority"] == 2:
            flags.append("QUANTUM_VULNERABLE_ASYMMETRIC")
        elif q["priority"] == 3:
            flags.append("QUANTUM_WEAKENED_SYMMETRIC_OR_HASH")
        if not named_group and version == "TLSv1.3":
            flags.append("KEY_SHARE_GROUP_NOT_EXTRACTED")

        risk = risk_from_record(flags, q["priority"])
        ev_id = f"EVD-TLS-{i+1:04d}"

        cbom_record = {
            "CBOM ID": f"CBOM-{len(cbom)+1:06d}",
            "Asset / Algorithm": q["algorithm"],
            "Category": q["category"],
            "Protocol": "TLS",
            "TLS Version": version,
            "Cipher Suite": cipher,
            "Named Group / KEX Detail": named_group or kx_family,
            "Key Exchange Family": kx_family,
            "Encryption": enc,
            "Hash / MAC": mac,
            "Forward Secrecy": fs,
            "Quantum Status": q["quantum_status"],
            "Quantum Safe": "Yes" if q["quantum_safe"] else "No",
            "Quantum Priority": f"Priority {q['priority']}",
            "Threat Basis": q["threat_basis"],
            "Attack Algorithm": q["attack_algorithm"],
            "Estimated Break": q["estimated_break"],
            "Recommended Migration": q["migration"],
            "Risk": risk,
            "Source IP": src,
            "Source Port": sport,
            "Destination IP": dst,
            "Destination Port": dport,
            "SNI / Hostname": r.get("tls.handshake.extensions_server_name",""),
            "Evidence Label": q["evidence_label"],
            "Confidence": round(q["confidence"], 2),
            "Policy Flags": ", ".join(flags),
            "Policy Flags List": flags,
            "Evidence ID": ev_id,
        }
        cbom.append(cbom_record)

        evidence.append({
            "Evidence ID": ev_id,
            "Frame": r.get("frame.number",""),
            "Timestamp": r.get("frame.time_epoch",""),
            "Source": src,
            "Destination": f"{dst}:{dport}",
            "Protocol": "TLS",
            "Observed Field": "ServerHello: tls.handshake.version / tls.handshake.ciphersuite / key_share_group",
            "Observed Value": f"{version} / {cipher} / {named_group or 'group not extracted'}",
            "Defensibility": q["evidence_label"],
            "Confidence": round(q["confidence"], 2),
            "PCAP SHA256": pcap_hash,
        })

        alg_key = q["algorithm"]
        algorithm_map.setdefault(alg_key, {
            "Algorithm": alg_key,
            "Category": q["category"],
            "Quantum Threat": q["quantum_status"],
            "Priority": f"Priority {q['priority']}",
            "Threat Basis": q["threat_basis"],
            "Attack Algorithm": q["attack_algorithm"],
            "Estimated Break": q["estimated_break"],
            "NIST / PQC Status": "Classical algorithm; PQC migration required" if q["priority"] == 2 else "Adequate margin / monitor" if q["priority"] == 4 else "Post-quantum margin reduction indicator",
            "Recommended Migration": q["migration"],
            "Source IPs": set(),
            "Destination IPs": set(),
            "Connections": 0,
            "Evidence Label": q["evidence_label"],
            "Confidence": round(q["confidence"], 2),
        })
        algorithm_map[alg_key]["Source IPs"].add(src)
        algorithm_map[alg_key]["Destination IPs"].add(dst)
        algorithm_map[alg_key]["Connections"] += 1

    # Certificate metadata observations as separate CBOM entries where fields appear
    for i, r in cert_df.iterrows():
        sig_alg = str(r.get("x509af.signature_algorithm",""))
        pk_alg = str(r.get("x509af.subjectPublicKeyInfo.algorithm.algorithm",""))
        if not sig_alg and not pk_alg:
            continue

        q = classify_quantum_readiness("", "", "", "", sig_alg, pk_alg)
        flags = []
        text = f"{sig_alg} {pk_alg}".lower()
        if "sha1" in text or "md5" in text:
            flags.append("WEAK_CERT_SIGNATURE")
        if "rsa" in text or "ecdsa" in text or "ecpublickey" in text:
            flags.append("QUANTUM_VULNERABLE_CERTIFICATE_ALGORITHM")

        ev_id = f"EVD-CERT-{i+1:04d}"
        src = r.get("ip.src","")
        dst = r.get("ip.dst","")
        cbom.append({
            "CBOM ID": f"CBOM-{len(cbom)+1:06d}",
            "Asset / Algorithm": pk_alg or sig_alg,
            "Category": "Certificate / PKI",
            "Protocol": "TLS Certificate",
            "TLS Version": "N/A",
            "Cipher Suite": "N/A",
            "Named Group / KEX Detail": pk_alg,
            "Key Exchange Family": "Certificate public key",
            "Encryption": "N/A",
            "Hash / MAC": sig_alg,
            "Forward Secrecy": "N/A",
            "Quantum Status": q["quantum_status"],
            "Quantum Safe": "Yes" if q["quantum_safe"] else "No",
            "Quantum Priority": f"Priority {q['priority']}",
            "Threat Basis": q["threat_basis"],
            "Attack Algorithm": q["attack_algorithm"],
            "Estimated Break": q["estimated_break"],
            "Recommended Migration": q["migration"],
            "Risk": risk_from_record(flags, q["priority"]),
            "Source IP": src,
            "Source Port": "",
            "Destination IP": dst,
            "Destination Port": "",
            "SNI / Hostname": "",
            "Evidence Label": q["evidence_label"],
            "Confidence": round(q["confidence"], 2),
            "Policy Flags": ", ".join(flags),
            "Policy Flags List": flags,
            "Evidence ID": ev_id,
        })
        evidence.append({
            "Evidence ID": ev_id,
            "Frame": r.get("frame.number",""),
            "Timestamp": r.get("frame.time_epoch",""),
            "Source": src,
            "Destination": dst,
            "Protocol": "TLS Certificate",
            "Observed Field": "x509 certificate metadata",
            "Observed Value": f"Signature={sig_alg}; PublicKey={pk_alg}",
            "Defensibility": q["evidence_label"],
            "Confidence": round(q["confidence"], 2),
            "PCAP SHA256": pcap_hash,
        })

    # Plaintext protocol observations
    for i, r in plaintext_df.head(1000).iterrows():
        src = r.get("ip.src","")
        dst = r.get("ip.dst","")
        sport = r.get("tcp.srcport","") or r.get("udp.srcport","")
        dport = r.get("tcp.dstport","") or r.get("udp.dstport","")
        proto = r.get("_ws.col.Protocol","Plaintext")
        ev_id = f"EVD-PLAIN-{i+1:04d}"
        flags = ["PLAINTEXT_PROTOCOL"]
        cbom.append({
            "CBOM ID": f"CBOM-{len(cbom)+1:06d}",
            "Asset / Algorithm": "Plaintext Transport",
            "Category": "No transport encryption observed",
            "Protocol": proto,
            "TLS Version": "N/A",
            "Cipher Suite": "None",
            "Named Group / KEX Detail": "None",
            "Key Exchange Family": "None",
            "Encryption": "None",
            "Hash / MAC": "None",
            "Forward Secrecy": False,
            "Quantum Status": "Classical confidentiality risk",
            "Quantum Safe": "N/A",
            "Quantum Priority": "Priority 1",
            "Threat Basis": "No cryptographic protection observed",
            "Attack Algorithm": "No quantum computer required",
            "Estimated Break": "Already exposed if sensitive payload exists",
            "Recommended Migration": "Replace plaintext with TLS/SSH/SFTP/STARTTLS as appropriate.",
            "Risk": "Critical",
            "Source IP": src,
            "Source Port": sport,
            "Destination IP": dst,
            "Destination Port": dport,
            "SNI / Hostname": "",
            "Evidence Label": "Observed",
            "Confidence": 0.90,
            "Policy Flags": ", ".join(flags),
            "Policy Flags List": flags,
            "Evidence ID": ev_id,
        })
        evidence.append({
            "Evidence ID": ev_id,
            "Frame": r.get("frame.number",""),
            "Timestamp": r.get("frame.time_epoch",""),
            "Source": src,
            "Destination": f"{dst}:{dport}",
            "Protocol": proto,
            "Observed Field": "_ws.col.Protocol",
            "Observed Value": proto,
            "Defensibility": "Observed",
            "Confidence": 0.90,
            "PCAP SHA256": pcap_hash,
        })

    # SSH algorithm observations where tshark exposes them
    for i, r in ssh_df.head(1000).iterrows():
        alg_text = " ".join(str(r.get(c,"")) for c in ssh_df.columns)
        alg_low = alg_text.lower()
        flags = []
        weak_terms = ["diffie-hellman-group1-sha1", "ssh-rsa", "hmac-md5", "3des", "arcfour", "cbc"]
        if any(x in alg_low for x in weak_terms):
            flags.append("WEAK_SSH_ALGORITHM")
        if any(x in alg_low for x in ["diffie-hellman", "ecdh", "ssh-rsa", "rsa", "ecdsa"]):
            flags.append("QUANTUM_VULNERABLE_SSH_ASYMMETRIC")
        q_status = "Quantum Vulnerable" if "QUANTUM_VULNERABLE_SSH_ASYMMETRIC" in flags else "Requires Manual Validation"
        q_priority = 2 if q_status == "Quantum Vulnerable" else 3
        ev_id = f"EVD-SSH-{i+1:04d}"
        src = r.get("ip.src","")
        dst = r.get("ip.dst","")
        dport = r.get("tcp.dstport","")
        cbom.append({
            "CBOM ID": f"CBOM-{len(cbom)+1:06d}",
            "Asset / Algorithm": r.get("ssh.kex_algorithms","SSH algorithm set") or "SSH algorithm set",
            "Category": "SSH cryptography",
            "Protocol": "SSH",
            "TLS Version": "N/A",
            "Cipher Suite": "N/A",
            "Named Group / KEX Detail": r.get("ssh.kex_algorithms",""),
            "Key Exchange Family": "SSH KEX",
            "Encryption": r.get("ssh.encryption_algorithms_client_to_server",""),
            "Hash / MAC": r.get("ssh.mac_algorithms_client_to_server",""),
            "Forward Secrecy": "ecdh" in alg_low or "curve25519" in alg_low,
            "Quantum Status": q_status,
            "Quantum Safe": "No",
            "Quantum Priority": f"Priority {q_priority}",
            "Threat Basis": "Shor’s algorithm at Q-Day" if q_priority == 2 else "Insufficient SSH algorithm visibility",
            "Attack Algorithm": "Shor's algorithm" if q_priority == 2 else "Unknown",
            "Estimated Break": "Q-Day / CRQC dependent" if q_priority == 2 else "Unknown",
            "Recommended Migration": "Harden SSH algorithms and plan PQC-ready SSH migration as standards and platform support mature.",
            "Risk": risk_from_record(flags, q_priority),
            "Source IP": src,
            "Source Port": "",
            "Destination IP": dst,
            "Destination Port": dport,
            "SNI / Hostname": "",
            "Evidence Label": "Observed" if r.get("ssh.kex_algorithms","") else "Risk Indicator",
            "Confidence": 0.75,
            "Policy Flags": ", ".join(flags),
            "Policy Flags List": flags,
            "Evidence ID": ev_id,
        })
        evidence.append({
            "Evidence ID": ev_id,
            "Frame": r.get("frame.number",""),
            "Timestamp": r.get("frame.time_epoch",""),
            "Source": src,
            "Destination": f"{dst}:{dport}",
            "Protocol": "SSH",
            "Observed Field": "ssh algorithm fields",
            "Observed Value": alg_text[:1000],
            "Defensibility": "Observed" if r.get("ssh.kex_algorithms","") else "Risk Indicator",
            "Confidence": 0.75,
            "PCAP SHA256": pcap_hash,
        })

    # Findings from policy flags
    for r in cbom:
        for flag in r["Policy Flags List"]:
            finding_title = {
                "TLS_LEGACY_VERSION": "Deprecated TLS/SSL protocol observed",
                "WEAK_CIPHER": "Weak cipher suite observed",
                "STATIC_RSA_KEY_EXCHANGE": "Static RSA key exchange observed",
                "QUANTUM_VULNERABLE_ASYMMETRIC": "Quantum-vulnerable asymmetric cryptography observed",
                "QUANTUM_WEAKENED_SYMMETRIC_OR_HASH": "Symmetric/hash algorithm with reduced post-quantum margin",
                "KEY_SHARE_GROUP_NOT_EXTRACTED": "TLS 1.3 key share group not extracted",
                "WEAK_CERT_SIGNATURE": "Weak certificate signature algorithm observed",
                "QUANTUM_VULNERABLE_CERTIFICATE_ALGORITHM": "Quantum-vulnerable certificate public-key algorithm",
                "PLAINTEXT_PROTOCOL": "Plaintext protocol observed",
                "WEAK_SSH_ALGORITHM": "Weak SSH algorithm observed",
                "QUANTUM_VULNERABLE_SSH_ASYMMETRIC": "Quantum-vulnerable SSH asymmetric cryptography"
            }.get(flag, flag)

            findings.append({
                "Policy": "default_network",
                "Finding": finding_title,
                "Priority": r["Quantum Priority"] if "QUANTUM" in flag else "Priority 1" if flag in ["TLS_LEGACY_VERSION","WEAK_CIPHER","PLAINTEXT_PROTOCOL","WEAK_CERT_SIGNATURE","WEAK_SSH_ALGORITHM"] else "Priority 2",
                "Risk": r["Risk"],
                "Asset / Algorithm": r["Asset / Algorithm"],
                "Endpoint": f"{r['Destination IP']}:{r['Destination Port']}",
                "Evidence ID": r["Evidence ID"],
                "Evidence Label": "Observed" if flag not in ["QUANTUM_VULNERABLE_ASYMMETRIC","QUANTUM_WEAKENED_SYMMETRIC_OR_HASH","QUANTUM_VULNERABLE_SSH_ASYMMETRIC"] else "Risk Indicator",
                "Confidence": r["Confidence"],
                "Executive Meaning": "This finding affects cryptographic assurance, audit readiness, or quantum migration planning."
            })

    # Summary calculations
    total_connections = max(len(cbom), 1)
    encrypted_connections = sum(1 for r in cbom if r["Protocol"] in ["TLS", "SSH", "TLS Certificate"])
    unencrypted_connections = sum(1 for r in cbom if "PLAINTEXT_PROTOCOL" in r["Policy Flags List"])
    weak_protocols = sum(1 for r in cbom if r["Risk"] in ["Critical", "High"])
    quantum_safe = sum(1 for r in cbom if r["Quantum Safe"] == "Yes")
    quantum_vulnerable = sum(1 for r in cbom if r["Quantum Status"] in ["Quantum Vulnerable", "Quantum Weakened", "Classical confidentiality risk"])
    deprecated = sum(1 for r in cbom if any(f in r["Policy Flags List"] for f in ["TLS_LEGACY_VERSION", "WEAK_CIPHER", "WEAK_CERT_SIGNATURE"]))
    unknown_manual = sum(1 for r in cbom if r["Evidence Label"] == "Requires Manual Validation")

    # Quantum readiness: count only cryptographic assets with meaningful quantum classification
    quantum_relevant = [r for r in cbom if r["Quantum Safe"] in ["Yes", "No"]]
    quantum_score = round(100 * sum(1 for r in quantum_relevant if r["Quantum Safe"] == "Yes") / max(len(quantum_relevant), 1), 1)

    encryption_score = round(100 * encrypted_connections / max(encrypted_connections + unencrypted_connections, 1), 1)

    if deprecated or unencrypted_connections:
        overall_priority = "Priority 1"
    elif quantum_vulnerable:
        overall_priority = "Priority 2"
    elif unknown_manual:
        overall_priority = "Priority 3"
    else:
        overall_priority = "Priority 4"

    algorithms = []
    for a in algorithm_map.values():
        algorithms.append({
            **{k:v for k,v in a.items() if k not in ["Source IPs", "Destination IPs"]},
            "Source IPs": ", ".join(sorted(x for x in a["Source IPs"] if x)),
            "Destination IPs": ", ".join(sorted(x for x in a["Destination IPs"] if x)),
        })

    compliance = score_compliance(cbom)

    recommendations = []
    if deprecated:
        recommendations.append({
            "Recommendation": "Eliminate deprecated cryptography",
            "Category": "Immediate Hardening",
            "Timeline": "Immediate",
            "Priority": "Priority 1",
            "Affected": deprecated,
            "Executive Action": "Approve immediate remediation for deprecated TLS, weak cipher, or weak certificate findings.",
            "Technical Action": "Disable SSL/TLS legacy versions and weak ciphers; replace weak signatures and certificate algorithms.",
            "Verification": "Upload a fresh PCAP after remediation and confirm zero deprecated observations."
        })
    if unencrypted_connections:
        recommendations.append({
            "Recommendation": "Remove plaintext protocols",
            "Category": "Transport Security",
            "Timeline": "Immediate to 4 weeks",
            "Priority": "Priority 1",
            "Affected": unencrypted_connections,
            "Executive Action": "Require business owners to migrate plaintext services to encrypted alternatives.",
            "Technical Action": "Replace FTP/Telnet/HTTP-sensitive flows with SFTP/SSH/HTTPS/STARTTLS.",
            "Verification": "Confirm no plaintext protocol observations in a new capture."
        })
    if quantum_vulnerable:
        recommendations.append({
            "Recommendation": "Begin PQC migration planning",
            "Category": "Quantum Readiness",
            "Timeline": "2–6 months",
            "Priority": "Priority 2",
            "Affected": quantum_vulnerable,
            "Executive Action": "Create a crypto-agility and PQC migration program for quantum-vulnerable cryptography.",
            "Technical Action": "Inventory RSA/ECDH/ECDSA/DHE usage, test hybrid TLS/PQC options, and plan ML-KEM/ML-DSA migration.",
            "Verification": "Track reduction of Priority 2 assets and validate hybrid/PQC pilot results."
        })

    recommendations += [
        {
            "Recommendation": "Implement centralized cryptographic inventory",
            "Category": "Governance",
            "Timeline": "2–4 weeks",
            "Priority": "Priority 3",
            "Affected": len(cbom),
            "Executive Action": "Mandate recurring CBOM updates for critical network zones.",
            "Technical Action": "Schedule periodic PCAP-based discovery and integrate output with asset inventory.",
            "Verification": "Monthly CBOM trend report."
        },
        {
            "Recommendation": "Implement crypto-agility framework",
            "Category": "Architecture",
            "Timeline": "3–6 months",
            "Priority": "Priority 3",
            "Affected": len(algorithms),
            "Executive Action": "Approve architecture changes that allow algorithm replacement without major rewrites.",
            "Technical Action": "Abstract cryptographic dependencies and document approved algorithm baselines.",
            "Verification": "Architecture review and migration test."
        }
    ]

    duration = datetime.now() - start

    document = {
        "Document Title": "Network Security Assessment Report",
        "Tool Name": "RBI CBOM",
        "Target Application": meta["target"],
        "Scan Type": "NETWORK / TLS Discovery & Quantum Readiness",
        "Scan ID": str(uuid.uuid4()),
        "Assessment Date": datetime.now().strftime("%B %d, %Y"),
        "Report Generated": datetime.now().strftime("%B %d, %Y"),
        "Classification": meta["classification"],
        "Scanner Version": "RBI CBOM PQC Scanner v2.0",
        "Scan Target": "Uploaded PCAP",
        "Total Packets": total_packets,
        "Packets Analyzed": total_packets,
        "Analysis Duration": str(duration).split(".")[0],
        "Business Unit": meta["business_unit"],
        "Application Criticality": overall_priority,
        "PCAP SHA256": pcap_hash
    }

    summary = {
        "Overall Risk": overall_priority,
        "Total Connections / Assets": total_connections,
        "Encrypted Observations": encrypted_connections,
        "Plaintext Observations": unencrypted_connections,
        "Weak / Critical Observations": weak_protocols,
        "Algorithms Identified": len(algorithms),
        "Quantum Safe": quantum_safe,
        "Quantum Vulnerable / Weakened": quantum_vulnerable,
        "Deprecated": deprecated,
        "Encryption Security Score": encryption_score,
        "Quantum Readiness Score": quantum_score,
        "Manual Validation Items": unknown_manual,
    }

    protocol = {
        "TLS Crypto Assets": sum(1 for r in cbom if r["Protocol"] == "TLS"),
        "Unique Cipher Suites": len(set(r["Cipher Suite"] for r in cbom if r["Cipher Suite"] not in ["", "None", "N/A"])),
        "TLS 1.3 Assets": sum(1 for r in cbom if r["TLS Version"] == "TLSv1.3"),
        "TLS 1.2 Assets": sum(1 for r in cbom if r["TLS Version"] == "TLSv1.2"),
        "SSH Observations": len(ssh_df),
        "DNSSEC Observations": len(dnssec_df),
        "IPsec / IKE Observations": len(ipsec_df),
        "QUIC Observations": len(quic_df),
        "Certificate Metadata Rows": len(cert_df),
    }

    scope = {
        "Target Application": meta["target"],
        "Assessment Type": "PCAP TRAFFIC ANALYSIS",
        "Total Connections / Assets Scanned": total_connections,
        "Encrypted Observations": encrypted_connections,
        "Unencrypted Observations": unencrypted_connections,
        "Algorithms Identified": len(algorithms),
        "Total Packets": total_packets,
        "Packets Analyzed": total_packets,
        "Scan Status": "COMPLETED"
    }

    limitations = [
        "This dashboard analyzes only traffic present in the uploaded PCAP.",
        "TLS 1.3 is not automatically quantum-safe; standard TLS 1.3 using classical ECDHE remains quantum-vulnerable unless hybrid/PQC key exchange is observed.",
        "If the PCAP does not include complete handshakes, certificates, or key-share groups, confidence is reduced and manual validation is required.",
        "Compliance results are evidence-backed indicators, not formal legal or regulatory certification.",
        "Payload contents are not inspected by default; sensitive-data exposure requires legal approval and separate validation.",
        "NAT, proxies, load balancers, and short capture windows may affect endpoint attribution."
    ]

    return {
        "document": document,
        "summary": summary,
        "scope": scope,
        "protocol": protocol,
        "cbom": cbom,
        "algorithms": algorithms,
        "findings": findings,
        "compliance": compliance,
        "recommendations": recommendations,
        "evidence": evidence,
        "pqc_reference": PQC_REFERENCE.to_dict("records"),
        "glossary": GLOSSARY.to_dict("records"),
        "limitations": limitations,
        "parser_notes": {
            "tls": tls_err,
            "certificate": cert_err,
            "plaintext": plaintext_err
        }
    }

def df_from_records(records):
    return pd.DataFrame(records) if records else pd.DataFrame()

def clean_cbom_for_display(cbom):
    df = pd.DataFrame(cbom)
    if df.empty:
        return df
    return df.drop(columns=["Policy Flags List"], errors="ignore")

def html_report(report):
    def table_dict(d):
        return "<table>" + "".join(f"<tr><th>{k}</th><td>{v}</td></tr>" for k,v in d.items()) + "</table>"
    def table_records(records):
        df = pd.DataFrame(records)
        if df.empty:
            return "<p>No records.</p>"
        return df.drop(columns=["Policy Flags List"], errors="ignore").to_html(index=False, escape=False)

    s = report["summary"]
    d = report["document"]
    style = """
    <style>
    body{font-family:Arial, sans-serif;margin:34px;color:#0f172a}
    h1{color:#0B2F6B;font-size:34px;margin-bottom:4px}
    h2{background:#0B2F6B;color:white;padding:11px 14px;border-radius:8px;margin-top:28px}
    h3{color:#0B2F6B;border-left:4px solid #0B2F6B;padding-left:8px}
    table{width:100%;border-collapse:collapse;font-size:12px;margin:12px 0}
    th,td{border:1px solid #dbe3ef;padding:7px;text-align:left;vertical-align:top}
    th{background:#eef2f7;color:#0B2F6B}
    .pill{background:#EA580C;color:white;padding:5px 9px;border-radius:999px;font-weight:bold}
    .kpi{display:inline-block;width:160px;border:1px solid #dbe3ef;border-radius:12px;padding:12px;margin:5px;text-align:center}
    .kpi b{display:block;font-size:22px}
    .note{background:#eff6ff;border-left:5px solid #1747A6;padding:12px;border-radius:8px}
    </style>
    """
    kpis = "".join(f"<div class='kpi'>{k}<b>{v}</b></div>" for k,v in s.items())
    return f"""
    <html><head><meta charset='UTF-8'>{style}</head>
    <body>
    <h1>RBI CBOM — Network Security Assessment Report</h1>
    <h3>TLS Discovery & Quantum Readiness Analysis</h3>
    <p><b>Target Application:</b> {d['Target Application']} | <b>Overall Risk:</b> <span class='pill'>{s['Overall Risk']}</span></p>
    <p><b>Generated:</b> {d['Report Generated']} | <b>Scan ID:</b> {d['Scan ID']}</p>
    <p class='note'>This report is based on PCAP-derived evidence. It does not certify full legal, regulatory, or organizational compliance.</p>

    <h2>1. Executive Summary</h2>
    {kpis}
    <p><b>Board Message:</b> The uploaded capture was assessed for cryptographic exposure, TLS posture, CBOM inventory, and quantum-readiness indicators. Quantum readiness is assessed by separating classical symmetric strength from quantum-vulnerable asymmetric key exchange and certificate algorithms.</p>

    <h2>2. Document Control</h2>
    {table_dict(d)}

    <h2>3. Assessment Scope</h2>
    {table_dict(report['scope'])}

    <h2>4. Protocol & TLS Analysis</h2>
    {table_dict(report['protocol'])}
    <h3>Cryptographic Assets / CBOM</h3>
    {table_records(report['cbom'])}

    <h2>5. Algorithm Security & Quantum Readiness</h2>
    {table_records(report['algorithms'])}

    <h2>6. Compliance & Policy Assessment</h2>
    <p>Each compliance result is labelled as Observed, Risk Indicator, or Requires Manual Validation.</p>
    {table_records(report['compliance'])}
    <h3>Policy Findings</h3>
    {table_records(report['findings'])}

    <h2>7. Recommendations</h2>
    {table_records(report['recommendations'])}

    <h2>8. Remediation Roadmap</h2>
    <table>
    <tr><th>Phase</th><th>Action</th></tr>
    <tr><td>Immediate</td><td>Fix plaintext, weak ciphers, legacy TLS, weak certificates, and critical exposure.</td></tr>
    <tr><td>Short Term</td><td>Identify owners for Priority 2 quantum-vulnerable assets and begin PQC migration planning.</td></tr>
    <tr><td>Medium Term</td><td>Test hybrid/PQC TLS and migrate suitable systems to ML-KEM/ML-DSA-ready architecture.</td></tr>
    <tr><td>Long Term</td><td>Institutionalize crypto-agility and continuous CBOM monitoring.</td></tr>
    </table>

    <h2>9. Evidence Appendix</h2>
    {table_records(report['evidence'])}

    <h2>10. PQC Reference & Glossary</h2>
    <h3>PQC Reference</h3>{table_records(report['pqc_reference'])}
    <h3>Glossary</h3>{table_records(report['glossary'])}

    <h2>11. Limitations</h2>
    <ul>{"".join("<li>"+x+"</li>" for x in report["limitations"])}</ul>
    </body></html>
    """

# -------------------------------
# Sidebar
# -------------------------------
st.sidebar.title("🛡️ RBI CBOM")
st.sidebar.caption("Executive CBOM, TLS discovery, and quantum-readiness assessment from uploaded PCAP.")
target = st.sidebar.text_input("Target Application", "RBI-Website")
business_unit = st.sidebar.text_input("Business Unit", "Network")
classification = st.sidebar.selectbox("Classification", ["CONFIDENTIAL", "INTERNAL", "RESTRICTED", "PUBLIC"], index=0)

st.sidebar.markdown("---")
st.sidebar.markdown("### Accuracy upgrades")
st.sidebar.write("• Separates TLS security from PQC readiness")
st.sidebar.write("• TLS 1.3 ≠ automatically quantum-safe")
st.sidebar.write("• Uses key-share/named-group where visible")
st.sidebar.write("• Flags ECDHE/RSA/DHE as Shor-vulnerable")
st.sidebar.write("• Labels low-confidence cases")

# -------------------------------
# Landing header
# -------------------------------
st.markdown("""
<div class="hero">
  <h1>RBI CBOM</h1>
  <p>Executive Cryptographic Bill of Materials, TLS Discovery, Compliance Indicators, and Quantum Readiness from uploaded PCAP evidence.</p>
</div>
""", unsafe_allow_html=True)

uploaded = st.file_uploader("Upload actual PCAP / PCAPNG / CAP file", type=["pcap", "pcapng", "cap"])

if not uploaded:
    c1, c2, c3 = st.columns(3)
    c1.markdown("<div class='card'><b>Executive Dashboard</b><br><span class='muted'>Modern CISO-facing risk, quantum readiness, and remediation view.</span></div>", unsafe_allow_html=True)
    c2.markdown("<div class='card'><b>Improved Quantum Accuracy</b><br><span class='muted'>Classifies ECDHE/RSA/DHE/ECDSA separately from AES/SHA strength.</span></div>", unsafe_allow_html=True)
    c3.markdown("<div class='card'><b>Defensible Evidence</b><br><span class='muted'>Every finding carries evidence label, confidence, and PCAP hash.</span></div>", unsafe_allow_html=True)
    st.info("Upload a PCAP to generate the executive report.")
    st.stop()

with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded.name).suffix or ".pcap") as tmp:
    tmp.write(uploaded.read())
    tmp_path = tmp.name

try:
    with st.spinner("Analyzing PCAP with improved quantum-readiness model..."):
        report = analyze_pcap(tmp_path, {
            "target": target,
            "business_unit": business_unit,
            "classification": classification
        })
finally:
    try:
        os.remove(tmp_path)
    except Exception:
        pass

summary = report["summary"]

# -------------------------------
# Executive summary top panel
# -------------------------------
st.markdown('<div class="section">Executive Risk Overview</div>', unsafe_allow_html=True)

cols = st.columns(6)
main_metrics = [
    ("Overall Risk", summary["Overall Risk"]),
    ("Quantum Readiness", f"{summary['Quantum Readiness Score']}%"),
    ("TLS Security", f"{summary['Encryption Security Score']}%"),
    ("Q-Vulnerable", summary["Quantum Vulnerable / Weakened"]),
    ("Deprecated", summary["Deprecated"]),
    ("Manual Validation", summary["Manual Validation Items"]),
]
for c, (label, value) in zip(cols, main_metrics):
    c.markdown(f"<div class='kpi'><small>{label}</small><b>{value}</b></div>", unsafe_allow_html=True)

if summary["Quantum Vulnerable / Weakened"] > 0:
    st.markdown("""
    <div class="warning-note">
    <b>Executive Interpretation:</b> The capture contains cryptographic assets that are either quantum-vulnerable or weakened in a post-quantum scenario.
    Standard TLS 1.3 is treated as classically strong but not automatically quantum-safe unless a hybrid/PQC key exchange is actually observed.
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <div class="success-note">
    <b>Executive Interpretation:</b> No quantum-vulnerable cryptographic asset was identified from the parsed evidence. This does not prove full enterprise PQC readiness.
    </div>
    """, unsafe_allow_html=True)

# -------------------------------
# Modern report tabs without Table of Contents
# -------------------------------
tabs = st.tabs([
    "Executive Summary",
    "Document Control",
    "Assessment Scope",
    "Protocol & TLS Analysis",
    "Quantum Readiness",
    "CBOM Inventory",
    "Compliance & Policy",
    "Recommendations",
    "Evidence Explorer",
    "Exports"
])

with tabs[0]:
    st.markdown('<div class="section">1. Executive Summary</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="card">
    <b>Board-ready summary:</b><br>
    RBI CBOM analyzed the uploaded PCAP for cryptographic exposure, TLS posture, weak/deprecated protocols, plaintext traffic, certificate/PKI indicators, and quantum-readiness.
    The current overall risk is <b>{summary['Overall Risk']}</b>. Quantum readiness score is <b>{summary['Quantum Readiness Score']}%</b>.
    </div>
    """, unsafe_allow_html=True)

    s_df = pd.DataFrame(summary.items(), columns=["Metric", "Value"])
    st.dataframe(s_df, use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### TLS / Encryption Security")
        st.progress(min(float(summary["Encryption Security Score"]) / 100, 1.0))
        st.write(f"**Encryption Security Score:** {summary['Encryption Security Score']}%")
    with c2:
        st.markdown("### Quantum Readiness")
        st.progress(min(float(summary["Quantum Readiness Score"]) / 100, 1.0))
        st.write(f"**Quantum Readiness Score:** {summary['Quantum Readiness Score']}%")

    st.markdown("### Top Executive Actions")
    rec_df = pd.DataFrame(report["recommendations"])
    st.dataframe(rec_df[["Priority", "Recommendation", "Timeline", "Executive Action"]], use_container_width=True)

with tabs[1]:
    st.markdown('<div class="section">2. Document Control</div>', unsafe_allow_html=True)
    st.dataframe(pd.DataFrame(report["document"].items(), columns=["Field", "Value"]), use_container_width=True)

with tabs[2]:
    st.markdown('<div class="section">3. Assessment Scope</div>', unsafe_allow_html=True)
    st.dataframe(pd.DataFrame(report["scope"].items(), columns=["Scope Item", "Value"]), use_container_width=True)
    st.markdown("### Analysis Limitations")
    for item in report["limitations"]:
        st.write("- " + item)

with tabs[3]:
    st.markdown('<div class="section">4. Protocol & TLS Analysis</div>', unsafe_allow_html=True)
    st.dataframe(pd.DataFrame(report["protocol"].items(), columns=["Metric", "Value"]), use_container_width=True)

    cbom_df = clean_cbom_for_display(report["cbom"])
    if not cbom_df.empty:
        st.markdown("### TLS Version Distribution")
        st.bar_chart(cbom_df["TLS Version"].value_counts())

        st.markdown("### Protocol Distribution")
        st.bar_chart(cbom_df["Protocol"].value_counts())

        st.markdown("### Cipher Suites Observed")
        tls_cipher_df = cbom_df[cbom_df["Protocol"].isin(["TLS", "TLS Certificate"])]
        if not tls_cipher_df.empty:
            st.dataframe(
                tls_cipher_df[[
                    "Protocol", "TLS Version", "Cipher Suite", "Named Group / KEX Detail",
                    "Encryption", "Hash / MAC", "Forward Secrecy", "Risk", "Evidence Label", "Confidence"
                ]],
                use_container_width=True
            )
        else:
            st.info("No TLS cipher suite observations were extracted.")

with tabs[4]:
    st.markdown('<div class="section">5. Quantum Readiness</div>', unsafe_allow_html=True)
    algo_df = pd.DataFrame(report["algorithms"])
    if algo_df.empty:
        st.info("No cryptographic algorithms were confidently identified from complete handshake evidence.")
    else:
        st.markdown("""
        <div class="executive-note">
        <b>Accuracy note:</b> TLS 1.3 with AES-256 is classically strong, but the session is not considered quantum-safe if it still uses classical ECDHE/X25519/secp256r1 key exchange.
        PQC-safe status is assigned only when hybrid/PQC algorithms are actually observed.
        </div>
        """, unsafe_allow_html=True)
        st.dataframe(algo_df, use_container_width=True)

        st.markdown("### Quantum Threat Distribution")
        st.bar_chart(algo_df["Quantum Threat"].value_counts())

        st.markdown("### Algorithm Details")
        for _, row in algo_df.iterrows():
            with st.expander(f"{row['Algorithm']} — {row['Priority']} — {row['Quantum Threat']}"):
                st.write("**Category:**", row["Category"])
                st.write("**Threat Basis:**", row["Threat Basis"])
                st.write("**Attack Algorithm:**", row["Attack Algorithm"])
                st.write("**Estimated Break:**", row["Estimated Break"])
                st.write("**Recommended Migration:**", row["Recommended Migration"])
                st.write("**Source IPs:**", row["Source IPs"])
                st.write("**Destination IPs:**", row["Destination IPs"])
                st.write("**Evidence Label:**", row["Evidence Label"])
                st.write("**Confidence:**", row["Confidence"])

with tabs[5]:
    st.markdown('<div class="section">6. Cryptographic Bill of Materials</div>', unsafe_allow_html=True)
    cbom_df = clean_cbom_for_display(report["cbom"])
    if cbom_df.empty:
        st.warning("No CBOM records were generated. Ensure the PCAP contains complete handshakes or plaintext protocol traffic.")
    else:
        st.dataframe(cbom_df, use_container_width=True)

with tabs[6]:
    st.markdown('<div class="section">7. Compliance & Policy Assessment</div>', unsafe_allow_html=True)
    st.caption("Compliance results are evidence-backed indicators, not legal or regulatory certification.")
    comp_df = pd.DataFrame(report["compliance"])
    st.dataframe(comp_df, use_container_width=True)

    st.markdown("### Policy Findings")
    findings_df = pd.DataFrame(report["findings"])
    if findings_df.empty:
        st.success("No policy findings were generated from the parsed evidence.")
    else:
        st.dataframe(findings_df, use_container_width=True)

with tabs[7]:
    st.markdown('<div class="section">8. Recommendations & Remediation Roadmap</div>', unsafe_allow_html=True)
    rec_df = pd.DataFrame(report["recommendations"])
    st.dataframe(rec_df, use_container_width=True)

    st.markdown("### Remediation Timeline")
    roadmap = pd.DataFrame([
        {"Phase": "Immediate", "Action": "Fix plaintext protocols, weak ciphers, legacy TLS, weak certificate signatures, and critical exposures."},
        {"Phase": "Short Term", "Action": "Assign owners for Priority 2 quantum-vulnerable assets and begin PQC/hybrid readiness planning."},
        {"Phase": "Medium Term", "Action": "Pilot hybrid/PQC key exchange where supported; align migration with vendor/application roadmaps."},
        {"Phase": "Long Term", "Action": "Institutionalize crypto-agility, continuous CBOM monitoring, and formal audit validation."},
    ])
    st.dataframe(roadmap, use_container_width=True)

with tabs[8]:
    st.markdown('<div class="section">9. Evidence Explorer</div>', unsafe_allow_html=True)
    evidence_df = pd.DataFrame(report["evidence"])
    if evidence_df.empty:
        st.info("No evidence records were generated.")
    else:
        st.dataframe(evidence_df, use_container_width=True)

    with st.expander("Parser Notes"):
        st.json(report.get("parser_notes", {}))

    st.markdown("### PQC Reference")
    st.dataframe(pd.DataFrame(report["pqc_reference"]), use_container_width=True)
    st.markdown("### Glossary")
    st.dataframe(pd.DataFrame(report["glossary"]), use_container_width=True)

with tabs[9]:
    st.markdown('<div class="section">10. Exports</div>', unsafe_allow_html=True)
    st.download_button(
        "Download Full JSON Report",
        data=json.dumps(report, indent=2),
        file_name="rbi_cbom_quantum_readiness_report.json",
        mime="application/json"
    )
    st.download_button(
        "Download Executive HTML Report",
        data=html_report(report),
        file_name="rbi_cbom_executive_report.html",
        mime="text/html"
    )
    st.download_button(
        "Download CBOM CSV",
        data=clean_cbom_for_display(report["cbom"]).to_csv(index=False),
        file_name="rbi_cbom_inventory.csv",
        mime="text/csv"
    )
    st.download_button(
        "Download Compliance CSV",
        data=pd.DataFrame(report["compliance"]).to_csv(index=False),
        file_name="rbi_cbom_compliance.csv",
        mime="text/csv"
    )

st.caption("RBI CBOM | PCAP-derived evidence only. Quantum readiness and compliance conclusions require manual validation before audit or regulatory use.")
