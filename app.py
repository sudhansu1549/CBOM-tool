
import streamlit as st, pandas as pd, subprocess, tempfile, hashlib, uuid, json, os, shutil
from pathlib import Path
from datetime import datetime

st.set_page_config(page_title="RBI CBOM", page_icon="🛡️", layout="wide")

st.markdown("""
<style>
.hero{padding:26px;border-radius:22px;background:linear-gradient(135deg,#0b2f6b,#1747a6);color:white;margin-bottom:18px}
.hero h1{margin:0;font-size:34px;font-weight:900}.hero p{color:#dbeafe}
.sec{background:#173f92;color:white;padding:12px 16px;border-radius:10px;font-weight:800;margin:18px 0 10px}
.card{background:white;border:1px solid #e2e8f0;border-radius:16px;padding:14px;box-shadow:0 8px 24px rgba(15,23,42,.07)}
.kpi{background:white;border:1px solid #e2e8f0;border-radius:16px;padding:14px;text-align:center}
.kpi small{color:#64748b;font-weight:800}.kpi b{display:block;font-size:28px;color:#0f172a}
.pill{padding:4px 9px;border-radius:999px;color:white;background:#f97316;font-weight:900}
</style>
""", unsafe_allow_html=True)

TLS_VERSION_MAP={"0x0300":"SSLv3","0x0301":"TLSv1.0","0x0302":"TLSv1.1","0x0303":"TLSv1.2","0x0304":"TLSv1.3"}
CIPHER_MAP={"0x0004":"TLS_RSA_WITH_RC4_128_MD5","0x0005":"TLS_RSA_WITH_RC4_128_SHA","0x000a":"TLS_RSA_WITH_3DES_EDE_CBC_SHA","0x002f":"TLS_RSA_WITH_AES_128_CBC_SHA","0x0035":"TLS_RSA_WITH_AES_256_CBC_SHA","0x009c":"TLS_RSA_WITH_AES_128_GCM_SHA256","0x009d":"TLS_RSA_WITH_AES_256_GCM_SHA384","0xc02f":"TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256","0xc030":"TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384","0x1301":"TLS_AES_128_GCM_SHA256","0x1302":"TLS_AES_256_GCM_SHA384","0x1303":"TLS_CHACHA20_POLY1305_SHA256"}
PQC_REF=pd.DataFrame([
{"Algorithm":"ML-KEM (Kyber)","Type":"Lattice-based KEM","NIST Status":"FIPS 203 Approved","Use Case":"Key Encapsulation"},
{"Algorithm":"ML-DSA (Dilithium)","Type":"Lattice-based Signature","NIST Status":"FIPS 204 Approved","Use Case":"Digital Signatures"},
{"Algorithm":"SLH-DSA (SPHINCS+)","Type":"Hash-based Signature","NIST Status":"FIPS 205 Approved","Use Case":"Stateless Signatures"},
{"Algorithm":"FN-DSA (Falcon)","Type":"Lattice-based Signature","NIST Status":"Round 4 / Pending","Use Case":"Compact Signatures"}])
GLOSSARY=pd.DataFrame([
{"Term":"CBOM","Definition":"Cryptography Bill of Materials — inventory of cryptographic assets."},
{"Term":"PQC","Definition":"Post-Quantum Cryptography — algorithms resistant to quantum attacks."},
{"Term":"HNDL","Definition":"Harvest Now, Decrypt Later — capture encrypted data now for future quantum decryption."},
{"Term":"OPA","Definition":"Open Policy Agent — policy engine for compliance and security rules."},
{"Term":"CNSA 2.0","Definition":"NSA Commercial National Security Algorithm Suite 2.0."}])

def sha256_file(p):
    h=hashlib.sha256()
    with open(p,"rb") as f:
        for c in iter(lambda:f.read(1048576),b""): h.update(c)
    return h.hexdigest()

def tshark(args, timeout=220):
    if not shutil.which("tshark"): return False,"","tshark not found"
    try:
        r=subprocess.run(["tshark"]+args,capture_output=True,text=True,timeout=timeout)
        return r.returncode==0 or bool(r.stdout.strip()),r.stdout,r.stderr
    except Exception as e: return False,"",str(e)

def fields(p, filt, fs):
    args=["-r",p,"-Y",filt,"-T","fields","-E","header=y","-E","separator=\t"]
    for f in fs: args+=["-e",f]
    ok,out,err=tshark(args)
    if not out.strip(): return pd.DataFrame(columns=fs),err
    from io import StringIO
    try: return pd.read_csv(StringIO(out),sep="\t",dtype=str).fillna(""),err
    except Exception as e: return pd.DataFrame(columns=fs),str(e)

def norm_ver(v): return TLS_VERSION_MAP.get(str(v).strip().lower(), TLS_VERSION_MAP.get(str(v).strip(), str(v).strip() or "Unknown"))
def norm_cipher(c): return CIPHER_MAP.get(str(c).strip().lower(), CIPHER_MAP.get(str(c).strip(), str(c).strip() or "Unknown"))

def algs(cipher):
    u=str(cipher).upper()
    if "TLS_AES" in u or "CHACHA20" in u: kx="TLS 1.3 / ECDHE"
    elif "ECDHE" in u: kx="ECDHE"
    elif "DHE" in u: kx="DHE"
    elif "RSA" in u: kx="RSA"
    else: kx="Unknown"
    enc="AES-256-GCM" if "AES_256_GCM" in u else "AES-128-GCM" if "AES_128_GCM" in u else "ChaCha20-Poly1305" if "CHACHA20" in u else "3DES" if "3DES" in u else "DES" if "DES" in u else "RC4" if "RC4" in u else "Unknown"
    mac="SHA-384" if "SHA384" in u else "SHA-256" if "SHA256" in u else "SHA-1" if "SHA" in u else "MD5" if "MD5" in u else "AEAD/Unknown"
    fs=("ECDHE" in kx) or ("TLS 1.3" in kx)
    return kx,enc,mac,fs

def pq(kx,enc,mac):
    t=f"{kx} {enc} {mac}".lower()
    if any(x in t for x in ["ecdh","ecdhe","rsa","dhe"]):
        return ("secp256r1/ECDHE or RSA/DH","Elliptic Curve / Asymmetric","⚠️ Vulnerable","Priority 2","Shor's algorithm","ML-KEM-768 for key exchange; ML-DSA-65 for signatures")
    if any(x in t for x in ["aes-128","sha-256","chacha20"]):
        return (enc if enc!="Unknown" else mac,"Symmetric / Hash","⚠️ Weakened","Priority 3","Grover's algorithm","Prefer AES-256 and SHA-384/512 for long-term confidentiality")
    if any(x in t for x in ["aes-256","sha-384","sha-512"]):
        return (enc if enc!="Unknown" else mac,"Symmetric / Hash","✅ Adequate Margin","Priority 4","Grover mitigated by key length","Maintain monitoring")
    return ("Unknown","Unknown","Requires Manual Validation","Priority 3","Unknown","Validate manually")

def priority_num(p):
    try: return int(str(p).split()[-1])
    except: return 3

def analyze(path, meta):
    h=sha256_file(path)
    frame_df,_=fields(path,"frame",["frame.number"])
    total_packets=len(frame_df)
    tls,te=fields(path,"tls.handshake.type == 2",["frame.number","frame.time_epoch","ip.src","tcp.srcport","ip.dst","tcp.dstport","ipv6.src","ipv6.dst","tls.handshake.version","tls.handshake.ciphersuite","tls.handshake.extensions_server_name"])
    plain,pe=fields(path,"http or ftp or telnet or smtp or pop or imap or ldap or snmp",["frame.number","frame.time_epoch","ip.src","tcp.srcport","udp.srcport","ip.dst","tcp.dstport","udp.dstport","_ws.col.Protocol"])
    ssh,_=fields(path,"ssh",["frame.number"])
    dnssec,_=fields(path,"dns.flags.authenticated == 1 or dns.resp.type == 46 or dns.resp.type == 48 or dns.resp.type == 43",["frame.number"])
    ipsec,_=fields(path,"isakmp or esp or ah",["frame.number"])
    quic,_=fields(path,"quic",["frame.number"])

    cbom=[]; evidence=[]; algmap={}
    for i,r in tls.iterrows():
        ver=norm_ver(r.get("tls.handshake.version","")); cipher=norm_cipher(r.get("tls.handshake.ciphersuite",""))
        kx,enc,mac,fs=algs(cipher); an,cat,qth,prio,attack,mig=pq(kx,enc,mac)
        src=r.get("ip.src","") or r.get("ipv6.src",""); dst=r.get("ip.dst","") or r.get("ipv6.dst",""); port=r.get("tcp.dstport","")
        flags=[]
        if ver in ["SSLv3","TLSv1.0","TLSv1.1"]: flags.append("TLS_LEGACY_VERSION")
        if any(x in cipher.upper() for x in ["RC4","3DES","DES","NULL","EXPORT","ANON","MD5"]): flags.append("WEAK_CIPHER")
        if priority_num(prio)==2: flags.append("QUANTUM_VULNERABLE")
        risk="HIGH" if flags and ("TLS_LEGACY_VERSION" in flags or "WEAK_CIPHER" in flags) else "MEDIUM" if priority_num(prio) in [2,3] else "LOW"
        ev=f"EVD-TLS-{i+1:04d}"
        cbom.append({"ASSET / ENDPOINT":an,"PROTOCOL TYPE":"TLS","TLS VERSION":ver,"CIPHER SUITE":cipher,"KEY EXCHANGE":kx,"QUANTUM SAFE":"✅ SAFE" if priority_num(prio)==4 else "⚠️ VULN","RISK":risk,"SRC IPS":src,"DST IPS":dst,"DST PORT":port,"ENCRYPTION":enc,"HASH/MAC":mac,"FORWARD SECRECY":fs,"QUANTUM THREAT":qth,"PRIORITY":prio,"POLICY FLAGS":", ".join(flags),"EVIDENCE LABEL":"Observed","CONFIDENCE":0.94,"EVIDENCE ID":ev})
        evidence.append({"Evidence ID":ev,"Frame":r.get("frame.number",""),"Timestamp":r.get("frame.time_epoch",""),"Source":src,"Destination":f"{dst}:{port}","Protocol":"TLS","Observed Value":f"{ver} / {cipher}","Defensibility":"Observed","Confidence":0.94,"PCAP SHA256":h})
        algmap.setdefault(an,{"ALGORITHM":an,"CATEGORY":cat,"QUANTUM THREAT":qth,"NIST STATUS":"Classically approved depending on implementation; PQC readiness requires validation","RECOMMENDED MIGRATION":mig,"ATTACK ALGORITHM":attack,"PRIORITY":prio,"SRC IPS":set(),"DST IPS":set(),"CONNECTIONS":0})
        algmap[an]["SRC IPS"].add(src); algmap[an]["DST IPS"].add(dst); algmap[an]["CONNECTIONS"]+=1

    for i,r in plain.head(500).iterrows():
        src=r.get("ip.src",""); dst=r.get("ip.dst",""); port=r.get("tcp.dstport","") or r.get("udp.dstport",""); proto=r.get("_ws.col.Protocol","Plaintext")
        ev=f"EVD-PLAIN-{i+1:04d}"
        cbom.append({"ASSET / ENDPOINT":"Plaintext Transport","PROTOCOL TYPE":proto,"TLS VERSION":"N/A","CIPHER SUITE":"None","KEY EXCHANGE":"None","QUANTUM SAFE":"N/A","RISK":"HIGH","SRC IPS":src,"DST IPS":dst,"DST PORT":port,"ENCRYPTION":"None","HASH/MAC":"None","FORWARD SECRECY":False,"QUANTUM THREAT":"Classical confidentiality risk","PRIORITY":"Priority 1","POLICY FLAGS":"PLAINTEXT_PROTOCOL","EVIDENCE LABEL":"Observed","CONFIDENCE":0.90,"EVIDENCE ID":ev})
        evidence.append({"Evidence ID":ev,"Frame":r.get("frame.number",""),"Timestamp":r.get("frame.time_epoch",""),"Source":src,"Destination":f"{dst}:{port}","Protocol":proto,"Observed Value":proto,"Defensibility":"Observed","Confidence":0.90,"PCAP SHA256":h})

    encrypted=sum(1 for x in cbom if x["PROTOCOL TYPE"]=="TLS")
    unencrypted=sum(1 for x in cbom if "PLAINTEXT_PROTOCOL" in x["POLICY FLAGS"])
    weak=sum(1 for x in cbom if x["RISK"] in ["HIGH"])
    qv=sum(1 for x in cbom if x["QUANTUM SAFE"]=="⚠️ VULN")
    qs=sum(1 for x in cbom if x["QUANTUM SAFE"]=="✅ SAFE")
    deprecated=sum(1 for x in cbom if "TLS_LEGACY_VERSION" in x["POLICY FLAGS"] or "WEAK_CIPHER" in x["POLICY FLAGS"])
    total=max(len(cbom),1)
    overall="Priority 1" if deprecated or unencrypted else "Priority 2" if qv else "Priority 4"
    algorithms=[{**{k:v for k,v in a.items() if k not in ["SRC IPS","DST IPS"]},"SRC IPS":", ".join(a["SRC IPS"]),"DST IPS":", ".join(a["DST IPS"])} for a in algmap.values()]
    findings=[]
    for x in cbom:
        for flag in [f for f in x["POLICY FLAGS"].split(", ") if f]:
            findings.append({"POLICY":"default_network","VIOLATION":flag,"PRIORITY":x["PRIORITY"],"RISK":x["RISK"],"ASSET":x["ASSET / ENDPOINT"],"ENDPOINT":f"{x['DST IPS']}:{x['DST PORT']}","DEFENSIBILITY":"Observed" if flag!="QUANTUM_VULNERABLE" else "Risk Indicator","EVIDENCE ID":x["EVIDENCE ID"]})
    comp=pd.DataFrame([
        {"STANDARD":"PCI_DSS","SCORE":"0%" if deprecated or unencrypted else "70%","STATUS":"NON-COMPLIANT INDICATOR" if deprecated or unencrypted else "PARTIAL ALIGNMENT","DEFENSIBILITY":"Risk Indicator"},
        {"STANDARD":"FIPS_140_2","SCORE":"100%" if not deprecated else "50%","STATUS":"INDICATOR","DEFENSIBILITY":"Requires Manual Validation"},
        {"STANDARD":"FIPS_140_3","SCORE":"100%" if not deprecated else "50%","STATUS":"INDICATOR","DEFENSIBILITY":"Requires Manual Validation"},
        {"STANDARD":"NIST_SP_800_131A","SCORE":"0%" if deprecated else "80%","STATUS":"NON-ALIGNED INDICATOR" if deprecated else "PARTIAL ALIGNMENT","DEFENSIBILITY":"Observed" if deprecated else "Risk Indicator"},
        {"STANDARD":"RBI","SCORE":"40%" if deprecated or unencrypted else "75%","STATUS":"RISK INDICATOR","DEFENSIBILITY":"Risk Indicator"},
        {"STANDARD":"CERT_IN","SCORE":"Manual","STATUS":"MANUAL VALIDATION","DEFENSIBILITY":"Requires Manual Validation"},
        {"STANDARD":"DPDP_ACT","SCORE":"40%" if unencrypted else "70%","STATUS":"RISK INDICATOR","DEFENSIBILITY":"Risk Indicator"},
        {"STANDARD":"CNSA_2_0","SCORE":"0%" if qv else "80%","STATUS":"NON-COMPLIANT INDICATOR" if qv else "PARTIAL ALIGNMENT","DEFENSIBILITY":"Risk Indicator"}])
    recs=pd.DataFrame([
        {"RECOMMENDATION":"Address critical vulnerabilities: deprecated protocols, weak ciphers and plaintext protocols.","CATEGORY":"Immediate Hardening","TIMELINE":"Immediate","PRIORITY":"Priority 1","AFFECTED":deprecated+unencrypted},
        {"RECOMMENDATION":"Migrate quantum-vulnerable key exchange and authentication algorithms; begin PQC/hybrid TLS planning.","CATEGORY":"Quantum Readiness","TIMELINE":"2-6 months","PRIORITY":"Priority 2","AFFECTED":qv},
        {"RECOMMENDATION":"Implement centralized key management system with lifecycle, rotation and audit trails.","CATEGORY":"Key Management","TIMELINE":"2-4 months","PRIORITY":"Priority 2","AFFECTED":0},
        {"RECOMMENDATION":"Implement crypto-agility framework for rapid algorithm replacement.","CATEGORY":"Architecture","TIMELINE":"3-6 months","PRIORITY":"Priority 3","AFFECTED":0},
        {"RECOMMENDATION":"Establish continuous cryptographic inventory management.","CATEGORY":"Governance","TIMELINE":"2-4 weeks","PRIORITY":"Priority 3","AFFECTED":0}])
    doc={"Document Title":"Network Security Assessment Report","Target Application":meta["target"],"Scan Type":"NETWORK / TLS Discovery Analysis","Scan ID":str(uuid.uuid4()),"Assessment Date":datetime.now().strftime("%B %d, %Y"),"Report Generated":datetime.now().strftime("%B %d, %Y"),"Classification":meta["class"],"Scanner Version":"RBI CBOM PQC Scanner v1.0","Scan Target":"Network Traffic","Total Packets":total_packets,"Packets Analyzed":total_packets,"Description":"PCAP","Technology Stack":"PCAP + tshark","Business Unit":meta["unit"],"Application Criticality":overall,"PCAP SHA256":h}
    summary={"OVERALL RISK":overall,"TOTAL CONNECTIONS":total,"SECURE PROTOCOLS":encrypted,"WEAK PROTOCOLS":weak,"TOTAL ALGORITHMS":len(algorithms),"QUANTUM SAFE":qs,"QUANTUM VULNERABLE":qv,"DEPRECATED":deprecated,"Encryption Security Score":round(encrypted/total*100,1),"Quantum Readiness Score":round(qs/max(qs+qv,1)*100,1)}
    scope={"Target Application":meta["target"],"Assessment Type":"PCAP TRAFFIC ANALYSIS","Total Connections Scanned":total,"Encrypted Connections":encrypted,"Unencrypted Connections":unencrypted,"Algorithms Identified":len(algorithms),"Total Packets":total_packets,"Packets Analyzed":total_packets,"Scan Status":"COMPLETED"}
    proto={"TLS Crypto Assets":encrypted,"Unique Cipher Suites":len(set(x["CIPHER SUITE"] for x in cbom if x["CIPHER SUITE"]!="None")),"TLS 1.3 Assets":sum(1 for x in cbom if x["TLS VERSION"]=="TLSv1.3"),"TLS 1.2 Assets":sum(1 for x in cbom if x["TLS VERSION"]=="TLSv1.2"),"SSH Observations":len(ssh),"DNSSEC Observations":len(dnssec),"IPsec/IKE Observations":len(ipsec),"QUIC Observations":len(quic)}
    return {"document":doc,"summary":summary,"scope":scope,"protocol":proto,"cbom":cbom,"algorithms":algorithms,"findings":findings,"compliance":comp.to_dict("records"),"recommendations":recs.to_dict("records"),"evidence":evidence,"pqc_reference":PQC_REF.to_dict("records"),"glossary":GLOSSARY.to_dict("records"),"limitations":["PCAP-only analysis cannot prove full legal/regulatory compliance.","Quantum readiness is inferred from observed algorithms and requires validation.","Short captures, NAT, proxies and missing handshakes can reduce accuracy.","Payload inspection is not performed by default."]}

def html(report):
    def dict_table(d): return "<table>"+''.join(f"<tr><th>{k}</th><td>{v}</td></tr>" for k,v in d.items())+"</table>"
    def df(x): return pd.DataFrame(x).to_html(index=False,escape=False) if x else "<p>No records.</p>"
    s=report["summary"]; d=report["document"]
    style="<style>body{font-family:Arial;margin:36px;color:#0f172a}h1{color:#173f92}h2{background:#173f92;color:white;padding:10px;border-radius:8px}table{width:100%;border-collapse:collapse;font-size:12px}th,td{border:1px solid #dbe3ef;padding:7px}th{background:#eef2f7;color:#173f92}.pill{background:#f97316;color:white;padding:5px 9px;border-radius:999px;font-weight:bold}</style>"
    kpis=''.join(f"<td><b>{k}</b><br>{v}</td>" for k,v in s.items())
    return f"<html><head>{style}</head><body><h1>NETWORK SECURITY ASSESSMENT REPORT</h1><h3>TLS Discovery & Quantum Readiness Analysis</h3><p><b>Target:</b> {d['Target Application']} | <b>Risk:</b> <span class='pill'>{s['OVERALL RISK']}</span></p><h2>1 Document Control</h2>{dict_table(d)}<h2>2 Table of Contents</h2><ol><li>Document Control</li><li>Executive Summary</li><li>Assessment Scope</li><li>Protocol Analysis</li><li>Algorithm Security Analysis</li><li>Compliance & Policy Assessment</li><li>Recommendations</li><li>Remediation Timeline</li><li>Appendices</li></ol><h2>3 Executive Summary</h2><table><tr>{kpis}</tr></table><p><b>Business Impact:</b> Quantum-vulnerable cryptography may create HNDL exposure for long-lived sensitive data.</p><h2>4 Assessment Scope</h2>{dict_table(report['scope'])}<h2>5 Protocol Analysis</h2>{dict_table(report['protocol'])}<h3>Network Cryptographic Assets</h3>{df(report['cbom'])}<h2>6 Algorithm Security Analysis</h2>{df(report['algorithms'])}<h2>7 Compliance & Policy Assessment</h2>{df(report['compliance'])}<h3>OPA-style Policy Violations</h3>{df(report['findings'])}<h2>8 Recommendations</h2>{df(report['recommendations'])}<h2>9 Remediation Timeline</h2><table><tr><th>Phase</th><th>Action</th></tr><tr><td>Phase 1 — Immediate</td><td>Fix deprecated protocols, weak ciphers, plaintext protocols.</td></tr><tr><td>Phase 2 — Short Term</td><td>Begin PQC transition planning.</td></tr><tr><td>Phase 3 — Medium Term</td><td>Adopt ML-KEM, ML-DSA, SLH-DSA or hybrid approaches.</td></tr><tr><td>Phase 4 — Long Term</td><td>Continuous crypto monitoring and formal validation.</td></tr></table><h2>10 Appendices</h2><h3>PQC Reference</h3>{df(report['pqc_reference'])}<h3>Glossary</h3>{df(report['glossary'])}<h3>Evidence</h3>{df(report['evidence'])}<h3>Disclaimer</h3><ul>{''.join('<li>'+x+'</li>' for x in report['limitations'])}</ul></body></html>"

st.sidebar.title("🛡️ RBI CBOM")
target=st.sidebar.text_input("Target Application","RBI-Website")
unit=st.sidebar.text_input("Business Unit","Network")
klass=st.sidebar.selectbox("Classification",["CONFIDENTIAL","INTERNAL","RESTRICTED","PUBLIC"])
st.sidebar.caption("QDrishti-style report layout with PCAP-only evidence labels.")

st.markdown('<div class="hero"><h1>NETWORK SECURITY ASSESSMENT REPORT</h1><p>TLS Discovery & Quantum Readiness Analysis — upload PCAP to generate CBOM, policy, compliance and executive report.</p></div>', unsafe_allow_html=True)
up=st.file_uploader("Upload actual PCAP / PCAPNG / CAP file",type=["pcap","pcapng","cap"])

if not up:
    st.info("Upload a PCAP to generate a QDrishti-style dashboard.")
    st.stop()

with tempfile.NamedTemporaryFile(delete=False,suffix=Path(up.name).suffix or ".pcap") as tmp:
    tmp.write(up.read()); p=tmp.name
try:
    with st.spinner("Analyzing PCAP with tshark..."):
        report=analyze(p,{"target":target,"unit":unit,"class":klass})
finally:
    try: os.remove(p)
    except: pass

s=report["summary"]
st.markdown('<div class="sec">3 Executive Summary</div>', unsafe_allow_html=True)
cols=st.columns(8)
for c,(k,v) in zip(cols,s.items()):
    c.markdown(f"<div class='kpi'><small>{k}</small><b>{v}</b></div>", unsafe_allow_html=True)

tabs=st.tabs(["1 Document Control","2 Table of Contents","3 Executive Summary","4 Assessment Scope","5 Protocol Analysis","6 Algorithm Security","7 Compliance & Policy","8 Recommendations","9 Remediation Timeline","10 Appendices","Exports"])

with tabs[0]:
    st.markdown('<div class="sec">1 Document Control</div>', unsafe_allow_html=True)
    st.dataframe(pd.DataFrame(report["document"].items(),columns=["Field","Value"]),use_container_width=True)
with tabs[1]:
    st.markdown('<div class="sec">2 Table of Contents</div>', unsafe_allow_html=True)
    for x in ["1. Document Control","2. Table of Contents","3. Executive Summary","3.1 Risk Overview","3.2 TLS Security Posture","3.3 Quantum Readiness Assessment","4. Assessment Scope","5. Protocol Analysis","5.1 Protocol Distribution","5.2 TLS Handshake Analysis","5.5 Network Cryptographic Assets","6. Algorithm Security Analysis","7. Compliance & Policy Assessment","8. Recommendations","9. Remediation Timeline","10. Appendices"]:
        st.write(x)
with tabs[2]:
    st.markdown("### 3.1 Risk Overview"); st.dataframe(pd.DataFrame(s.items(),columns=["Metric","Value"]),use_container_width=True)
    st.markdown("### 3.2 TLS Security Posture"); st.progress(min(float(s["Encryption Security Score"])/100,1.0)); st.write(f"Encryption Security Score: **{s['Encryption Security Score']}%**")
    st.markdown("### 3.3 Quantum Readiness Assessment"); st.progress(min(float(s["Quantum Readiness Score"])/100,1.0)); st.write(f"Quantum Readiness Score: **{s['Quantum Readiness Score']}%**")
with tabs[3]:
    st.markdown('<div class="sec">4 Assessment Scope</div>', unsafe_allow_html=True); st.dataframe(pd.DataFrame(report["scope"].items(),columns=["Scope Item","Value"]),use_container_width=True)
with tabs[4]:
    st.markdown('<div class="sec">5 Protocol Analysis</div>', unsafe_allow_html=True)
    st.dataframe(pd.DataFrame(report["protocol"].items(),columns=["Metric","Value"]),use_container_width=True)
    cb=pd.DataFrame(report["cbom"])
    if not cb.empty:
        st.markdown("### Protocol / Algorithm Distribution"); st.bar_chart(cb["ASSET / ENDPOINT"].value_counts())
        st.markdown("### TLS Protocol Version Distribution"); st.bar_chart(cb["TLS VERSION"].value_counts())
        st.markdown("### Network Cryptographic Assets"); st.dataframe(cb,use_container_width=True)
with tabs[5]:
    st.markdown('<div class="sec">6 Algorithm Security Analysis</div>', unsafe_allow_html=True); st.dataframe(pd.DataFrame(report["algorithms"]),use_container_width=True)
with tabs[6]:
    st.markdown('<div class="sec">7 Compliance & Policy Assessment</div>', unsafe_allow_html=True)
    st.caption("Compliance results are evidence-backed indicators, not legal certification.")
    st.dataframe(pd.DataFrame(report["compliance"]),use_container_width=True)
    st.markdown("### OPA-style Policy Violations"); st.dataframe(pd.DataFrame(report["findings"]),use_container_width=True)
with tabs[7]:
    st.markdown('<div class="sec">8 Recommendations</div>', unsafe_allow_html=True); st.dataframe(pd.DataFrame(report["recommendations"]),use_container_width=True)
with tabs[8]:
    st.markdown('<div class="sec">9 Remediation Timeline</div>', unsafe_allow_html=True)
    st.dataframe(pd.DataFrame([{"Phase":"Phase 1 — Immediate","Action":"Address deprecated algorithms, broken ciphers, weak TLS protocols, insecure cipher suites and plaintext services."},{"Phase":"Phase 2 — Short Term","Action":"Migrate quantum-vulnerable key exchange and authentication algorithms; begin PQC transition planning."},{"Phase":"Phase 3 — Medium Term","Action":"Implement ML-KEM, ML-DSA, SLH-DSA or hybrid approaches."},{"Phase":"Phase 4 — Long Term","Action":"Complete PQC transition and establish continuous cryptographic monitoring."}]),use_container_width=True)
with tabs[9]:
    st.markdown('<div class="sec">10 Appendices</div>', unsafe_allow_html=True)
    st.markdown("### Priority Classification — Quantum Threat Taxonomy")
    st.dataframe(pd.DataFrame([{"Priority":"Priority 1","Threat Basis":"No CRQC required","Definition":"Broken today by classical computers: SSLv3, TLS 1.0/1.1, RC4, DES, MD5, NULL/EXPORT."},{"Priority":"Priority 2","Threat Basis":"Shor’s Algorithm at Q-Day","Definition":"RSA, ECDSA, ECDH, DHE, DSA. HNDL threat active."},{"Priority":"Priority 3","Threat Basis":"Grover’s Algorithm at Q-Day","Definition":"AES-128, SHA-256, HMAC-SHA-256 weakened post-Q-Day."},{"Priority":"Priority 4","Threat Basis":"Quantum-Resistant","Definition":"AES-256, SHA-384/512, SHA3-384/512, NIST PQC."}]),use_container_width=True)
    st.markdown("### PQC Reference"); st.dataframe(pd.DataFrame(report["pqc_reference"]),use_container_width=True)
    st.markdown("### Evidence Explorer"); st.dataframe(pd.DataFrame(report["evidence"]),use_container_width=True)
    st.markdown("### Glossary"); st.dataframe(pd.DataFrame(report["glossary"]),use_container_width=True)
    st.markdown("### Disclaimer"); [st.write("- "+x) for x in report["limitations"]]
with tabs[10]:
    st.download_button("Download Full JSON Report",json.dumps(report,indent=2),"network_security_assessment.json","application/json")
    st.download_button("Download Executive HTML Report",html(report),"network_security_assessment.html","text/html")
    st.download_button("Download CBOM CSV",pd.DataFrame(report["cbom"]).to_csv(index=False),"cbom.csv","text/csv")
    st.download_button("Download Compliance CSV",pd.DataFrame(report["compliance"]).to_csv(index=False),"compliance.csv","text/csv")

st.caption("RBI CBOM | PCAP-only evidence. Compliance and quantum-readiness outputs require manual validation before formal audit use.")
