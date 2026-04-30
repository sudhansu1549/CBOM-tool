import streamlit as st
import pandas as pd
import subprocess, tempfile, hashlib, uuid, json, os, shutil, re
from pathlib import Path
from datetime import datetime

st.set_page_config(page_title="RBI CBOM | Board Quantum Readiness Dashboard", page_icon="🛡️", layout="wide")

st.markdown('''
<style>
:root{--bg:#f7fafc;--card:#fff;--ink:#0f172a;--muted:#64748b;--line:#e2e8f0;--blue:#2563eb;--blue2:#eff6ff;--green2:#ecfdf5;--amber2:#fffbeb;--red2:#fef2f2;--violet2:#f5f3ff;--shadow:0 16px 40px rgba(15,23,42,.08)}
.main{background:linear-gradient(135deg,#f8fafc,#eef6ff 55%,#f7fafc)}.block-container{max-width:1320px;padding-top:1.4rem}.hero{background:rgba(255,255,255,.94);border:1px solid var(--line);border-radius:34px;box-shadow:var(--shadow);overflow:hidden;margin-bottom:22px}.heroTop{padding:34px;background:radial-gradient(circle at top right,#dbeafe,transparent 38%),linear-gradient(135deg,#fff,#f8fafc);border-bottom:1px solid var(--line);display:grid;grid-template-columns:1fr 360px;gap:28px;align-items:center}.hero h1{font-size:46px;line-height:1.02;margin:12px 0;letter-spacing:-1.5px;color:#0f172a;font-weight:950}.sub{font-size:16px;line-height:1.65;color:var(--muted);max-width:850px}.badge{display:inline-flex;align-items:center;border-radius:999px;border:1px solid var(--line);padding:7px 11px;font-size:12px;font-weight:800;background:#f8fafc;color:#334155}.bblue{background:#eff6ff;color:#1d4ed8;border-color:#bfdbfe}.bgreen{background:#ecfdf5;color:#047857;border-color:#a7f3d0}.bamber{background:#fffbeb;color:#b45309;border-color:#fde68a}.bred{background:#fef2f2;color:#b91c1c;border-color:#fecaca}.bviolet{background:#f5f3ff;color:#6d28d9;border-color:#ddd6fe}.uploadBox{background:white;border:1px solid var(--line);border-radius:26px;padding:18px;box-shadow:0 8px 22px rgba(15,23,42,.06)}.grid4{display:grid;grid-template-columns:repeat(4,1fr);gap:18px;padding:28px}.metric{background:var(--card);border:1px solid var(--line);border-radius:26px;padding:22px;box-shadow:0 6px 18px rgba(15,23,42,.04)}.metric .label{font-size:11px;text-transform:uppercase;letter-spacing:.08em;color:var(--muted);font-weight:900}.metric .val{font-size:24px;font-weight:950;margin-top:8px;word-break:break-word;color:#0f172a}.section{padding:0 28px 28px}.section h2{font-size:23px;margin:0 0 8px;color:#0f172a}.desc{margin:7px 0 16px;color:var(--muted);line-height:1.6;font-size:14px}.two{display:grid;grid-template-columns:2fr 1fr;gap:18px}.card{background:var(--card);border:1px solid var(--line);border-radius:28px;padding:24px;box-shadow:0 8px 22px rgba(15,23,42,.04)}.dark{background:#020617;color:white}.dark p,.dark .muted{color:#cbd5e1}.risk{background:#fffbeb;border-color:#fde68a}.risk h3,.risk p{color:#92400e}.card h3{margin:0 0 10px;font-size:19px}.muted{color:var(--muted)}.kpis{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-top:18px}.kpi{border-radius:18px;background:rgba(255,255,255,.10);padding:14px}.kpi small{display:block;color:#cbd5e1}.kpi strong{display:block;margin-top:5px;color:white}.findings{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}.finding{background:white;border:1px solid var(--line);border-radius:24px;padding:18px;min-height:190px}.findingTop{display:flex;justify-content:space-between;gap:10px;margin-bottom:14px}.finding .title{font-size:13px;color:var(--muted);font-weight:900}.finding .value{font-size:18px;font-weight:950;margin-top:5px;color:#0f172a}.finding .detail{font-size:13px;line-height:1.55;color:#475569;margin-top:12px}.foot{display:flex;justify-content:space-between;gap:10px;margin-top:14px;font-size:12px;color:var(--muted)}.console{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;background:#020617;color:#d1fae5;border-radius:20px;padding:16px;white-space:pre-wrap;font-size:12px;line-height:1.45;max-height:240px;overflow:auto}.road{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}.road .card ul{margin:14px 0 0;padding-left:20px;color:#475569;line-height:1.6;font-size:13px}div[data-testid="stFileUploader"]{border:2px dashed #cbd5e1;border-radius:22px;padding:18px;background:#f8fafc}.stTabs [data-baseweb="tab-list"]{gap:8px;background:rgba(255,255,255,.72);border:1px solid var(--line);padding:8px;border-radius:18px}.stTabs [data-baseweb="tab"]{border-radius:14px;font-weight:800}@media(max-width:1000px){.heroTop,.two,.grid4,.findings,.road{grid-template-columns:1fr}.hero h1{font-size:34px}.section,.heroTop,.grid4{padding:20px}.kpis{grid-template-columns:1fr}}
</style>
''', unsafe_allow_html=True)

TLS_VERSION_MAP={"0x0002":"SSLv2","0x0300":"SSLv3","0x0301":"TLS 1.0","0x0302":"TLS 1.1","0x0303":"TLS 1.2","0x0304":"TLS 1.3","769":"TLS 1.0","770":"TLS 1.1","771":"TLS 1.2","772":"TLS 1.3"}
CIPHER_MAP={"0x0004":"TLS_RSA_WITH_RC4_128_MD5","0x0005":"TLS_RSA_WITH_RC4_128_SHA","0x0009":"TLS_RSA_WITH_DES_CBC_SHA","0x000a":"TLS_RSA_WITH_3DES_EDE_CBC_SHA","0x002f":"TLS_RSA_WITH_AES_128_CBC_SHA","0x0035":"TLS_RSA_WITH_AES_256_CBC_SHA","0x009c":"TLS_RSA_WITH_AES_128_GCM_SHA256","0x009d":"TLS_RSA_WITH_AES_256_GCM_SHA384","0xc02f":"TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256","0xc030":"TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384","0xc02b":"TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256","0xc02c":"TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384","0x1301":"TLS_AES_128_GCM_SHA256","0x1302":"TLS_AES_256_GCM_SHA384","0x1303":"TLS_CHACHA20_POLY1305_SHA256","4865":"TLS_AES_128_GCM_SHA256","4866":"TLS_AES_256_GCM_SHA384","4867":"TLS_CHACHA20_POLY1305_SHA256"}
GROUP_MAP={"0x0017":"secp256r1 / P-256","0x0018":"secp384r1 / P-384","0x0019":"secp521r1 / P-521","0x001d":"x25519","0x001e":"x448","0x11ec":"X25519 + ML-KEM-768 / Kyber-768 hybrid","0x6399":"X25519 + ML-KEM/Kyber hybrid draft","23":"secp256r1 / P-256","24":"secp384r1 / P-384","25":"secp521r1 / P-521","29":"x25519","30":"x448","secp256r1":"secp256r1 / P-256","prime256v1":"secp256r1 / P-256","x25519":"x25519","x448":"x448","secp384r1":"secp384r1 / P-384"}
PQC_KEYWORDS=["ml-kem","kyber","mlkem","ml_dsa","ml-dsa","dilithium","slh-dsa","sphincs","hybrid","pqc"]
PQC_REFERENCE=pd.DataFrame([{"Algorithm":"ML-KEM / Kyber","Type":"Lattice-based KEM","NIST Status":"FIPS 203 Approved","Use Case":"Key encapsulation / key exchange"},{"Algorithm":"ML-DSA / Dilithium","Type":"Lattice-based signature","NIST Status":"FIPS 204 Approved","Use Case":"Digital signatures"},{"Algorithm":"SLH-DSA / SPHINCS+","Type":"Hash-based signature","NIST Status":"FIPS 205 Approved","Use Case":"Stateless signatures"}])
GLOSSARY=pd.DataFrame([{"Term":"CBOM","Definition":"Cryptography Bill of Materials — inventory of cryptographic assets observed or inferred from evidence."},{"Term":"PQC","Definition":"Post-Quantum Cryptography — algorithms designed to resist known quantum attacks."},{"Term":"HNDL","Definition":"Harvest Now, Decrypt Later — capture encrypted data today and decrypt it later when quantum capability matures."},{"Term":"Evidence Label","Definition":"Observed, Inferred, Risk Indicator, or Requires Manual Validation."}])

def sha256_file(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""): h.update(chunk)
    return h.hexdigest()

def run_tshark(args,timeout=300):
    if not shutil.which("tshark"): return False,"","tshark not found. Deploy using Docker/Render or install Wireshark/tshark."
    try:
        r=subprocess.run(["tshark"]+args,capture_output=True,text=True,timeout=timeout)
        return r.returncode==0 or bool(r.stdout.strip()),r.stdout,r.stderr
    except subprocess.TimeoutExpired: return False,"","tshark command timed out."
    except Exception as e: return False,"",str(e)

def extract_fields(path,filt,fields,timeout=300):
    args=["-r",path,"-Y",filt,"-T","fields","-E","header=y","-E","separator=\t"]
    for field in fields: args += ["-e",field]
    ok,out,err=run_tshark(args,timeout)
    if not out.strip(): return pd.DataFrame(columns=fields),err
    from io import StringIO
    try: return pd.read_csv(StringIO(out),sep="\t",dtype=str).fillna(""),err
    except Exception as e: return pd.DataFrame(columns=fields),str(e)

def normver(v):
    v=str(v or "").strip()
    if "," in v:
        parts=[p.strip() for p in v.split(",") if p.strip()]
        vals=[TLS_VERSION_MAP.get(p.lower(),TLS_VERSION_MAP.get(p,p)) for p in parts]
        order={"SSLv2":0,"SSLv3":1,"TLS 1.0":2,"TLS 1.1":3,"TLS 1.2":4,"TLS 1.3":5}
        return sorted(vals,key=lambda x:order.get(x,-1),reverse=True)[0] if vals else "Not observable"
    return TLS_VERSION_MAP.get(v.lower(),TLS_VERSION_MAP.get(v,v or "Not observable"))

def normcipher(c):
    c=str(c or "").strip()
    if "," in c: c=c.split(",")[-1].strip()
    return CIPHER_MAP.get(c.lower(),CIPHER_MAP.get(c,c or "Not observable"))

def normgroup(g):
    g=str(g or "").strip()
    if not g: return ""
    if "," in g:
        parts=[p.strip() for p in g.split(",") if p.strip()]
        g=parts[-1] if parts else ""
    return GROUP_MAP.get(g.lower(),GROUP_MAP.get(g,g))

def components(cipher,ver):
    u=str(cipher).upper()
    if "TLS_AES" in u or "CHACHA20" in u or ver=="TLS 1.3": kx="TLS 1.3 key schedule"
    elif "ECDHE" in u: kx="ECDHE"
    elif re.search(r"(^|_)DHE(_|$)",u): kx="DHE"
    elif "RSA_WITH" in u or u.startswith("TLS_RSA"): kx="RSA static key exchange"
    elif "PSK" in u: kx="PSK"
    else: kx="Unknown"
    if "AES_256_GCM" in u: enc="AES-256-GCM"
    elif "AES_128_GCM" in u: enc="AES-128-GCM"
    elif "AES_256_CBC" in u: enc="AES-256-CBC"
    elif "AES_128_CBC" in u: enc="AES-128-CBC"
    elif "CHACHA20" in u: enc="ChaCha20-Poly1305"
    elif "3DES" in u: enc="3DES"
    elif "DES" in u: enc="DES"
    elif "RC4" in u: enc="RC4"
    elif "NULL" in u: enc="NULL"
    else: enc="Unknown"
    if "SHA384" in u: mac="SHA-384"
    elif "SHA256" in u: mac="SHA-256"
    elif "SHA" in u: mac="SHA-1"
    elif "MD5" in u: mac="MD5"
    else: mac="AEAD / Unknown"
    fs=("ECDHE" in kx) or (kx=="DHE") or ver=="TLS 1.3"
    return kx,enc,mac,fs

def qclass(ver,cipher,kx,group,cert_alg=""):
    obs=" ".join([ver,cipher,kx,group,cert_alg]).lower()
    if any(k in obs for k in PQC_KEYWORDS):
        return dict(status="Quantum Ready / Hybrid Observed",safe="Yes",priority="Priority 4",risk="Low",asset=group or "Hybrid PQC / PQC",category="Post-Quantum / Hybrid",basis="PQC or hybrid key exchange observed",attack="No known Shor/Grover break for approved PQC family",migration="Maintain crypto-agility and monitor implementation maturity.",confidence=.88,label="Observed")
    if any(x in obs for x in ["ecdhe","ecdh","ecdsa","rsa","dhe","diffie","dsa","secp","prime256","x25519","x448"]):
        asset=group or cert_alg or kx or "Classical asymmetric key exchange"
        return dict(status="Quantum Vulnerable",safe="No",priority="Priority 2",risk="Medium",asset=asset,category="Classical asymmetric cryptography",basis="Shor’s algorithm at Q-Day",attack="Shor's algorithm",migration="Plan hybrid/PQC migration. Prefer ML-KEM for key establishment and ML-DSA/SLH-DSA for signatures where supported.",confidence=.86 if group else .78,label="Observed" if group or "rsa" in obs or "ecdhe" in obs else "Inferred")
    if any(x in obs for x in ["aes-256","sha-384","sha-512"]):
        return dict(status="Adequate Post-Quantum Symmetric Margin",safe="Yes",priority="Priority 4",risk="Low",asset="AES-256 / SHA-384+",category="Symmetric / hash algorithm",basis="Grover’s algorithm mitigated by larger security margin",attack="Grover's algorithm",migration="Maintain AES-256 and SHA-384/512 preference.",confidence=.82,label="Inferred")
    if any(x in obs for x in ["aes-128","sha-256","chacha20"]):
        return dict(status="Quantum Weakened",safe="No",priority="Priority 3",risk="Medium",asset="AES-128 / SHA-256 / ChaCha20 family",category="Symmetric / hash algorithm",basis="Grover’s algorithm reduces effective security margin",attack="Grover's algorithm",migration="Prefer AES-256 and SHA-384/512 for long-lived sensitive data.",confidence=.82,label="Risk Indicator")
    return dict(status="Requires Manual Validation",safe="No",priority="Priority 3",risk="Unknown",asset="Unknown / not enough handshake evidence",category="Unknown",basis="Insufficient cryptographic metadata in capture",attack="Unknown",migration="Capture complete handshakes and validate server configuration manually.",confidence=.50,label="Requires Manual Validation")

def bclass(v):
    v=str(v).lower()
    if any(x in v for x in ["priority 1","critical","not quantum","non","gap"]): return "bred"
    if any(x in v for x in ["priority 2","medium","partial","risk","vulnerable"]): return "bamber"
    if any(x in v for x in ["priority 3","manual","unknown"]): return "bviolet"
    if any(x in v for x in ["safe","ready","strong","observed","low"]): return "bgreen"
    return "bblue"

def badge(text): return f"<span class='badge {bclass(text)}'>{text}</span>"

def analyze(path,meta):
    start=datetime.now(); h=sha256_file(path)
    frames,_=extract_fields(path,"frame",["frame.number"]); total_packets=len(frames)
    tls,tls_err=extract_fields(path,"tls.handshake.type == 2",["frame.number","frame.time_epoch","ip.src","tcp.srcport","ip.dst","tcp.dstport","ipv6.src","ipv6.dst","tls.handshake.version","tls.handshake.ciphersuite","tls.handshake.extensions_server_name","tls.handshake.extensions_key_share_group","tls.handshake.extensions_supported_group"])
    ch,_=extract_fields(path,"tls.handshake.type == 1",["frame.number","frame.time_epoch","ip.src","tcp.srcport","ip.dst","tcp.dstport","tls.handshake.extensions_server_name","tls.handshake.extensions_supported_group","tls.handshake.extensions_key_share_group"])
    cert,cert_err=extract_fields(path,"tls.handshake.certificate",["frame.number","frame.time_epoch","ip.src","ip.dst","x509af.signature_algorithm","x509af.subjectPublicKeyInfo.algorithm.algorithm"])
    plain,plain_err=extract_fields(path,"http or ftp or telnet or smtp or pop or imap or ldap or snmp",["frame.number","frame.time_epoch","ip.src","tcp.srcport","udp.srcport","ip.dst","tcp.dstport","udp.dstport","_ws.col.Protocol"])
    ssh,_=extract_fields(path,"ssh",["frame.number"]); dnssec,_=extract_fields(path,"dns.flags.authenticated == 1 or dns.resp.type == 46 or dns.resp.type == 48 or dns.resp.type == 43",["frame.number"]); ipsec,_=extract_fields(path,"isakmp or esp or ah",["frame.number"]); quic,_=extract_fields(path,"quic",["frame.number"])
    cbom=[]; evidence=[]; findings=[]; algomap={}; logs=[f"Packets observed: {total_packets}",f"TLS ServerHello rows extracted: {len(tls)}",f"TLS Certificate rows extracted: {len(cert)}",f"Plaintext protocol rows sampled: {len(plain)}"]
    for i,r in tls.iterrows():
        src=r.get("ip.src","") or r.get("ipv6.src",""); dst=r.get("ip.dst","") or r.get("ipv6.dst",""); sport=r.get("tcp.srcport",""); dport=r.get("tcp.dstport","")
        ver=normver(r.get("tls.handshake.version","")); cipher=normcipher(r.get("tls.handshake.ciphersuite","")); group=normgroup(r.get("tls.handshake.extensions_key_share_group","")) or normgroup(r.get("tls.handshake.extensions_supported_group","")); sni=r.get("tls.handshake.extensions_server_name","")
        if not group and not ch.empty:
            cand=ch[((ch.get("ip.src","")==dst)&(ch.get("ip.dst","")==src)) | ((ch.get("ip.src","")==src)&(ch.get("ip.dst","")==dst))]
            if not cand.empty:
                group=normgroup(cand.iloc[0].get("tls.handshake.extensions_key_share_group","")) or normgroup(cand.iloc[0].get("tls.handshake.extensions_supported_group",""))
                if not sni: sni=cand.iloc[0].get("tls.handshake.extensions_server_name","")
        kx,enc,mac,fs=components(cipher,ver); q=qclass(ver,cipher,kx,group)
        flags=[]
        if ver in ["SSLv2","SSLv3","TLS 1.0","TLS 1.1"]: flags.append("TLS_LEGACY_VERSION")
        if any(x in cipher.upper() for x in ["RC4","3DES","DES","NULL","EXPORT","ANON","MD5"]): flags.append("WEAK_CIPHER")
        if kx=="RSA static key exchange": flags.append("STATIC_RSA_KEY_EXCHANGE")
        if q["priority"]=="Priority 2": flags.append("QUANTUM_VULNERABLE_ASYMMETRIC")
        elif q["priority"]=="Priority 3": flags.append("QUANTUM_WEAKENED_OR_UNKNOWN")
        if ver=="TLS 1.3" and not group: flags.append("KEY_SHARE_GROUP_NOT_EXTRACTED")
        risk="Critical" if any(f in flags for f in ["TLS_LEGACY_VERSION","WEAK_CIPHER"]) else "High" if "STATIC_RSA_KEY_EXCHANGE" in flags else q["risk"]
        ev=f"EVD-TLS-{i+1:04d}"
        rec={"CBOM ID":f"CBOM-{len(cbom)+1:06d}","Asset":q["asset"],"Protocol":"TLS","TLS Version":ver,"Cipher Suite":cipher,"Symmetric Encryption":enc,"Hash / KDF":mac,"Key Exchange":group or kx,"Forward Secrecy":fs,"Quantum Readiness":q["status"],"Quantum Safe":q["safe"],"Priority":q["priority"],"Risk":risk,"Source":f"{src}:{sport}","Destination":f"{dst}:{dport}","SNI":sni,"Evidence Type":q["label"],"Confidence":q["confidence"],"Executive Note":q["basis"],"Recommended Migration":q["migration"],"Policy Flags":", ".join(flags),"Evidence ID":ev}
        cbom.append(rec); evidence.append({"Evidence ID":ev,"Frame":r.get("frame.number",""),"Timestamp":r.get("frame.time_epoch",""),"Source":rec["Source"],"Destination":rec["Destination"],"Protocol":"TLS","Observed Value":f"{ver} / {cipher} / {group or kx}","Defensibility":q["label"],"Confidence":q["confidence"],"PCAP SHA256":h})
        algomap.setdefault(q["asset"],{"Algorithm":q["asset"],"Category":q["category"],"Quantum Threat":q["status"],"Priority":q["priority"],"Attack Algorithm":q["attack"],"NIST / PQC Status":"PQC migration required" if q["priority"]=="Priority 2" else "Adequate / monitor","Recommended Migration":q["migration"],"Source IPs":set(),"Destination IPs":set(),"Connections":0,"Evidence Type":q["label"],"Confidence":q["confidence"]})
        algomap[q["asset"]]["Source IPs"].add(src); algomap[q["asset"]]["Destination IPs"].add(dst); algomap[q["asset"]]["Connections"]+=1
    for i,r in plain.head(1000).iterrows():
        src=r.get("ip.src",""); dst=r.get("ip.dst",""); sport=r.get("tcp.srcport","") or r.get("udp.srcport",""); dport=r.get("tcp.dstport","") or r.get("udp.dstport",""); proto=r.get("_ws.col.Protocol","Plaintext"); ev=f"EVD-PLAIN-{i+1:04d}"
        cbom.append({"CBOM ID":f"CBOM-{len(cbom)+1:06d}","Asset":"Plaintext Transport","Protocol":proto,"TLS Version":"N/A","Cipher Suite":"None","Symmetric Encryption":"None","Hash / KDF":"None","Key Exchange":"None","Forward Secrecy":False,"Quantum Readiness":"Classical confidentiality risk","Quantum Safe":"N/A","Priority":"Priority 1","Risk":"Critical","Source":f"{src}:{sport}","Destination":f"{dst}:{dport}","SNI":"","Evidence Type":"Observed","Confidence":.90,"Executive Note":"No cryptographic protection observed","Recommended Migration":"Replace plaintext with TLS/SSH/SFTP/STARTTLS as appropriate.","Policy Flags":"PLAINTEXT_PROTOCOL","Evidence ID":ev})
        evidence.append({"Evidence ID":ev,"Frame":r.get("frame.number",""),"Timestamp":r.get("frame.time_epoch",""),"Source":f"{src}:{sport}","Destination":f"{dst}:{dport}","Protocol":proto,"Observed Value":proto,"Defensibility":"Observed","Confidence":.90,"PCAP SHA256":h})
    for rec in cbom:
        flags=[x.strip() for x in rec.get("Policy Flags","").split(",") if x.strip()]
        for flag in flags:
            title={"TLS_LEGACY_VERSION":"Deprecated TLS/SSL protocol observed","WEAK_CIPHER":"Weak cipher suite observed","STATIC_RSA_KEY_EXCHANGE":"Static RSA key exchange observed","QUANTUM_VULNERABLE_ASYMMETRIC":"Quantum-vulnerable asymmetric cryptography","QUANTUM_WEAKENED_OR_UNKNOWN":"Quantum-weakened or low-confidence cryptographic evidence","KEY_SHARE_GROUP_NOT_EXTRACTED":"TLS key-share group not extracted","PLAINTEXT_PROTOCOL":"Plaintext protocol observed"}.get(flag,flag)
            findings.append({"Finding":title,"Value":rec["Asset"],"Status":rec["Risk"],"Evidence Type":rec["Evidence Type"],"Confidence":rec["Confidence"],"Detail":rec["Executive Note"],"Evidence ID":rec["Evidence ID"],"Endpoint":rec["Destination"],"Policy":"default_network"})
    encrypted=sum(1 for r in cbom if r["Protocol"] in ["TLS","SSH","TLS Certificate"]); plaintext=sum(1 for r in cbom if "PLAINTEXT_PROTOCOL" in r.get("Policy Flags","")); qsafe=sum(1 for r in cbom if r["Quantum Safe"]=="Yes"); qv=sum(1 for r in cbom if r["Quantum Safe"]=="No"); deprecated=sum(1 for r in cbom if any(x in r.get("Policy Flags","") for x in ["TLS_LEGACY_VERSION","WEAK_CIPHER","WEAK_CERT_SIGNATURE"])); manual=sum(1 for r in cbom if r["Evidence Type"]=="Requires Manual Validation")
    qrel=[r for r in cbom if r["Quantum Safe"] in ["Yes","No"]]; qscore=round(100*sum(1 for r in qrel if r["Quantum Safe"]=="Yes")/max(len(qrel),1),1); escore=round(100*encrypted/max(encrypted+plaintext,1),1)
    overall="Priority 1" if deprecated or plaintext else "Priority 2" if qv else "Priority 3" if manual else "Priority 4"
    algorithms=[{**{k:v for k,v in a.items() if k not in ["Source IPs","Destination IPs"]},"Source IPs":", ".join(sorted(x for x in a["Source IPs"] if x)),"Destination IPs":", ".join(sorted(x for x in a["Destination IPs"] if x))} for a in algomap.values()]
    compliance=[{"Framework":"NIST PQC Migration","Status":"Gap" if qv else "Positive Indicator","Evidence Type":"Risk Indicator","Executive Note":"Classical ECC/RSA/DHE are Shor-vulnerable unless hybrid/PQ is negotiated."},{"Framework":"CNSA 2.0 Direction","Status":"PQC Migration Required" if qv else "Monitor","Evidence Type":"Risk Indicator","Executive Note":"Plan hybrid/PQC transition for critical endpoints."},{"Framework":"ISO 27001 / 27002","Status":"Crypto Inventory Required","Evidence Type":"Observed + Inferred","Executive Note":"Maintain CBOM evidence for cryptographic asset governance."},{"Framework":"PCI DSS","Status":"TLS Baseline Review","Evidence Type":"Risk Indicator","Executive Note":"Weak/plaintext transport may affect regulated data scope; validate manually."},{"Framework":"RBI / Financial Sector Cyber Resilience","Status":"PQC Roadmap Required" if qv else "Technical Indicator","Evidence Type":"Risk Indicator","Executive Note":"Board-level quantum-risk roadmap should be documented for critical banking-facing endpoints."},{"Framework":"CERT-In / Incident Readiness","Status":"Evidence Pack Needed","Evidence Type":"Requires Manual Validation","Executive Note":"Retain packet-level evidence and event timelines where incident obligations may apply."},{"Framework":"DPDP / GDPR Confidentiality","Status":"HNDL Risk Present" if qv else "Manual Validation","Evidence Type":"Inferred","Executive Note":"Classical public-key crypto may expose long-lived sensitive data to harvest-now-decrypt-later risk."}]
    recs=[]
    if deprecated: recs.append({"Recommendation":"Eliminate deprecated cryptography","Category":"Immediate Hardening","Timeline":"0–30 Days","Priority":"Priority 1","Affected":deprecated,"Executive Action":"Approve immediate remediation for deprecated TLS, weak cipher, or weak certificate findings.","Technical Action":"Disable legacy TLS and weak ciphers; replace weak signatures and algorithms.","Verification":"Fresh PCAP shows zero deprecated observations."})
    if plaintext: recs.append({"Recommendation":"Remove plaintext protocols","Category":"Transport Security","Timeline":"0–30 Days","Priority":"Priority 1","Affected":plaintext,"Executive Action":"Require business owners to migrate plaintext services.","Technical Action":"Replace FTP/Telnet/HTTP-sensitive flows with SFTP/SSH/HTTPS/STARTTLS.","Verification":"Fresh PCAP shows zero plaintext flows."})
    if qv: recs.append({"Recommendation":"Begin PQC migration planning","Category":"Quantum Readiness","Timeline":"30–90 Days","Priority":"Priority 2","Affected":qv,"Executive Action":"Create a crypto-agility and PQC migration program.","Technical Action":"Inventory RSA/ECDH/ECDSA/DHE usage, test hybrid TLS/PQC options, and plan ML-KEM/ML-DSA migration.","Verification":"Track reduction of Priority 2 assets and validate hybrid/PQC pilot results."})
    recs += [{"Recommendation":"Establish continuous CBOM inventory","Category":"Governance","Timeline":"2–4 Weeks","Priority":"Priority 3","Affected":len(cbom),"Executive Action":"Mandate recurring CBOM updates for critical network zones.","Technical Action":"Schedule periodic PCAP-based discovery and integrate with asset inventory.","Verification":"Monthly CBOM trend report."},{"Recommendation":"Implement crypto-agility framework","Category":"Architecture","Timeline":"3–6 Months","Priority":"Priority 3","Affected":len(algorithms),"Executive Action":"Approve architecture changes for rapid algorithm replacement.","Technical Action":"Abstract cryptographic dependencies and document approved algorithm baselines.","Verification":"Architecture review and migration test."}]
    flows=[{"Source":r["Source"],"Destination":r["Destination"],"SNI":r["SNI"],"TLS":r["TLS Version"],"Cipher":r["Cipher Suite"],"KEX":r["Key Exchange"]} for r in cbom if r["Protocol"]=="TLS"]
    doc={"Document Title":"RBI CBOM Quantum Readiness Dashboard","Tool Name":"RBI CBOM","Target Application":meta["target"],"Scan Type":"NETWORK / TLS Discovery & Quantum Readiness","Scan ID":str(uuid.uuid4()),"Assessment Date":datetime.now().strftime("%B %d, %Y"),"Classification":meta["classification"],"Scanner Version":"RBI CBOM PQC Scanner v3.0","Scan Target":"Uploaded PCAP","Total Packets":total_packets,"Analysis Duration":str(datetime.now()-start).split(".")[0],"Business Unit":meta["business_unit"],"Application Criticality":overall,"PCAP SHA256":h}
    summary={"Quantum Readiness":"Quantum Ready" if qscore==100 else "Partially Ready" if qscore>0 else "Not Quantum Ready","Overall Risk":overall,"TLS Version":cbom[0]["TLS Version"] if cbom else "Not observable","Cipher Suite":cbom[0]["Cipher Suite"] if cbom else "Not observable","Key Exchange":cbom[0]["Key Exchange"] if cbom else "Not observable","Quantum Readiness Score":qscore,"Encryption Security Score":escore,"Total Assets":len(cbom),"Quantum Safe":qsafe,"Quantum Vulnerable / Weakened":qv,"Deprecated":deprecated,"Manual Validation Items":manual}
    limitations=["This dashboard analyzes only traffic present in the uploaded PCAP.","TLS 1.3 is not automatically quantum-safe; standard TLS 1.3 using classical ECDHE remains quantum-vulnerable unless hybrid/PQC key exchange is observed.","If TLS 1.3 encrypts certificate messages, full certificate assurance may require TLS key logs or external certificate scanning.","Compliance results are evidence-backed indicators, not formal legal or regulatory certification.","Payload contents are not inspected by default."]
    return {"document":doc,"summary":summary,"protocol":{"TLS Crypto Assets":sum(1 for r in cbom if r["Protocol"]=="TLS"),"Unique Cipher Suites":len(set(r["Cipher Suite"] for r in cbom if r["Cipher Suite"] not in ["","None","N/A"])),"TLS 1.3 Assets":sum(1 for r in cbom if r["TLS Version"]=="TLS 1.3"),"TLS 1.2 Assets":sum(1 for r in cbom if r["TLS Version"]=="TLS 1.2"),"SSH Observations":len(ssh),"DNSSEC Observations":len(dnssec),"IPsec / IKE Observations":len(ipsec),"QUIC Observations":len(quic),"Certificate Metadata Rows":len(cert)},"cbom":cbom,"algorithms":algorithms,"findings":findings,"compliance":compliance,"recommendations":recs,"evidence":evidence,"flows":flows,"pqc_reference":PQC_REFERENCE.to_dict("records"),"glossary":GLOSSARY.to_dict("records"),"limitations":limitations,"parser_logs":logs+[f"TLS parser note: {tls_err}" if tls_err else "TLS parser completed.", f"Certificate parser note: {cert_err}" if cert_err else "Certificate parser completed.", f"Plaintext parser note: {plain_err}" if plain_err else "Plaintext parser completed."]}

def render_html_table(records, cols=None):
    if not records: return "<p class='muted'>No records.</p>"
    if cols is None: cols=list(records[0].keys())
    head="".join(f"<th>{c}</th>" for c in cols); body=""
    for r in records:
        body += "<tr>" + "".join(f"<td>{badge(r.get(c,'')) if c in ['Evidence Type','Priority','Risk','Status','Quantum Readiness','Quantum Safe'] else str(r.get(c,''))}</td>" for c in cols) + "</tr>"
    return f"<div class='tableWrap'><table class='board'><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>"

def html_report(report):
    s=report['summary']; d=report['document']
    # reuse the Streamlit CSS-compatible markup for the downloaded HTML
    css = '''<style>body{margin:0;background:linear-gradient(135deg,#f8fafc,#eef6ff 55%,#f7fafc);font-family:Inter,Arial,sans-serif;color:#0f172a}.wrap{max-width:1320px;margin:auto;padding:28px}.hero{background:rgba(255,255,255,.92);border:1px solid #e2e8f0;border-radius:34px;box-shadow:0 16px 40px rgba(15,23,42,.08);overflow:hidden}.heroTop{padding:34px;background:radial-gradient(circle at top right,#dbeafe,transparent 38%),linear-gradient(135deg,#fff,#f8fafc);border-bottom:1px solid #e2e8f0}h1{font-size:46px;line-height:1.02;margin:12px 0;letter-spacing:-1.5px}.sub{font-size:16px;line-height:1.65;color:#64748b}.badge{display:inline-flex;align-items:center;border-radius:999px;border:1px solid #e2e8f0;padding:7px 11px;font-size:12px;font-weight:800;background:#f8fafc;color:#334155}.bblue{background:#eff6ff;color:#1d4ed8;border-color:#bfdbfe}.bgreen{background:#ecfdf5;color:#047857;border-color:#a7f3d0}.bamber{background:#fffbeb;color:#b45309;border-color:#fde68a}.bred{background:#fef2f2;color:#b91c1c;border-color:#fecaca}.bviolet{background:#f5f3ff;color:#6d28d9;border-color:#ddd6fe}.grid4{display:grid;grid-template-columns:repeat(4,1fr);gap:18px;padding:28px}.metric{background:#fff;border:1px solid #e2e8f0;border-radius:26px;padding:22px;box-shadow:0 6px 18px rgba(15,23,42,.04)}.label{font-size:11px;text-transform:uppercase;letter-spacing:.08em;color:#64748b;font-weight:900}.val{font-size:24px;font-weight:950;margin-top:8px}.section{padding:0 28px 28px}.two{display:grid;grid-template-columns:2fr 1fr;gap:18px}.card{background:#fff;border:1px solid #e2e8f0;border-radius:28px;padding:24px;box-shadow:0 8px 22px rgba(15,23,42,.04)}.dark{background:#020617;color:white}.dark p{color:#cbd5e1}.risk{background:#fffbeb;border-color:#fde68a}.risk h3,.risk p{color:#92400e}.findings{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}.finding{background:white;border:1px solid #e2e8f0;border-radius:24px;padding:18px}.findingTop{display:flex;justify-content:space-between;gap:10px;margin-bottom:14px}.title{font-size:13px;color:#64748b;font-weight:900}.value{font-size:18px;font-weight:950;margin-top:5px}.detail{font-size:13px;line-height:1.55;color:#475569;margin-top:12px}.foot{display:flex;justify-content:space-between;gap:10px;margin-top:14px;font-size:12px;color:#64748b}table{width:100%;border-collapse:collapse;background:white}th{background:#f1f5f9;color:#475569;text-align:left;font-size:11px;text-transform:uppercase;letter-spacing:.08em;padding:15px}td{border-top:1px solid #f1f5f9;padding:15px;font-size:13px;vertical-align:top}.tableWrap{border:1px solid #e2e8f0;border-radius:24px;overflow:auto;background:white;box-shadow:0 8px 22px rgba(15,23,42,.04)}.road{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}.console{font-family:monospace;background:#020617;color:#d1fae5;border-radius:20px;padding:16px;white-space:pre-wrap;font-size:12px}</style>'''
    findings=''.join([f"<div class='finding'><div class='findingTop'>{badge(f.get('Evidence Type',''))}{badge(f.get('Confidence',''))}</div><div class='title'>{f.get('Finding','')}</div><div class='value'>{f.get('Value','')}</div><div class='detail'>{f.get('Detail','')}</div><div class='foot'><span>Status: {f.get('Status','')}</span><span>{f.get('Evidence ID','')}</span></div></div>" for f in report['findings'][:6]]) or "<p>No findings.</p>"
    road=''.join([f"<div class='card'>{badge(r['Timeline'])}<h3>{r['Recommendation']}</h3><p>{r['Executive Action']}</p><ul><li>{r['Technical Action']}</li><li>{r['Verification']}</li></ul></div>" for r in report['recommendations'][:3]])
    flows=''.join([f"<p><b>{fl['Source']} → {fl['Destination']}</b><br>SNI: {fl['SNI']} · TLS: {fl['TLS']} · Cipher: {fl['Cipher']} · KEX: {fl['KEX']}</p>" for fl in report['flows']]) or "<p>No TLS flows parsed.</p>"
    return f"<!doctype html><html><head><meta charset='utf-8'><title>RBI CBOM Board Report</title>{css}</head><body><div class='wrap'><main class='hero'><div class='heroTop'><span class='badge bblue'>RBI CBOM</span> <span class='badge bviolet'>Quantum Readiness</span> <span class='badge'>PCAP Evidence Mode</span><h1>RBI CBOM Quantum Readiness Dashboard</h1><p class='sub'>Executive board-ready report for TLS detection, CBOM inventory, compliance mapping and harvest-now-decrypt-later quantum-risk assessment.</p></div><div class='grid4'><div class='metric'><div class='label'>Quantum Readiness</div><div class='val'>{s['Quantum Readiness']}</div>{badge(s['Overall Risk'])}</div><div class='metric'><div class='label'>TLS Version</div><div class='val'>{s['TLS Version']}</div>{badge('Observed')}</div><div class='metric'><div class='label'>Cipher Suite</div><div class='val' style='font-size:17px'>{s['Cipher Suite']}</div>{badge('Review')}</div><div class='metric'><div class='label'>Key Exchange</div><div class='val'>{s['Key Exchange']}</div>{badge('Classical / PQ Review')}</div></div><section class='section'><div class='two'><div class='card dark'><h3>Executive Assessment</h3><p>RBI CBOM analyzed the uploaded PCAP for cryptographic exposure, TLS posture, CBOM inventory and quantum-readiness. TLS 1.3 is treated as modern but not automatically quantum-safe unless hybrid/PQC key exchange is observed.</p></div><div class='card risk'><h3>Board-Level Risk</h3><p>Overall risk is {s['Overall Risk']}. Quantum readiness score is {s['Quantum Readiness Score']}%.</p>{badge(s['Quantum Readiness'])}</div></div></section><section class='section'><h2>Evidence-Backed Findings</h2><div class='findings'>{findings}</div></section><section class='section'><h2>Cryptographic Bill of Materials</h2>{render_html_table(report['cbom'], ['Asset','Protocol','TLS Version','Cipher Suite','Key Exchange','Quantum Readiness','Priority','Risk','Evidence Type','Confidence','Executive Note'])}</section><section class='section'><div class='two'><div class='card'><h3>Observed TLS Flows</h3>{flows}</div><div class='card'><h3>Compliance Mapping</h3>{render_html_table(report['compliance'], ['Framework','Status','Evidence Type','Executive Note'])}</div></div></section><section class='section'><h2>Quantum Remediation Roadmap</h2><div class='road'>{road}</div></section><section class='section'><h2>Evidence Appendix</h2>{render_html_table(report['evidence'])}</section><section class='section'><h2>Document Control</h2>{render_html_table([d])}<h2>Parser Log</h2><div class='console'>{chr(10).join(report['parser_logs'])}</div><h2>Limitations</h2><ul>{''.join('<li>'+x+'</li>' for x in report['limitations'])}</ul></section></main></div></body></html>"

# Sidebar
st.sidebar.title("🛡️ RBI CBOM")
st.sidebar.caption("Board-ready CBOM, TLS discovery, compliance indicators, and quantum-readiness from PCAP evidence.")
target=st.sidebar.text_input("Target Application","RBI-Website")
business_unit=st.sidebar.text_input("Business Unit","Network")
classification=st.sidebar.selectbox("Classification",["CONFIDENTIAL","INTERNAL","RESTRICTED","PUBLIC"],index=0)
st.sidebar.markdown("---")
st.sidebar.write("• Executive hero dashboard")
st.sidebar.write("• Board-level risk narrative")
st.sidebar.write("• Evidence-backed findings")
st.sidebar.write("• CBOM and compliance tables")
st.sidebar.write("• Quantum remediation roadmap")

st.markdown('''<div class="hero"><div class="heroTop"><div><span class="badge bblue">RBI CBOM</span> <span class="badge bviolet">Quantum Readiness</span> <span class="badge">PCAP Evidence Mode</span><h1>RBI CBOM Quantum Readiness Dashboard</h1><p class="sub">Executive dashboard for TLS version detection, cryptographic bill of materials, evidence-backed compliance mapping, and harvest-now-decrypt-later quantum-risk assessment from uploaded PCAP files.</p></div><div class="uploadBox"><b>Upload PCAP / PCAPNG</b><p class="muted">Runs in the app backend using tshark. Use private deployment for sensitive captures.</p>''', unsafe_allow_html=True)
uploaded=st.file_uploader("Upload PCAP / PCAPNG / CAP", type=["pcap","pcapng","cap"], label_visibility="collapsed")
st.markdown("</div></div></div>", unsafe_allow_html=True)

if not uploaded:
    st.markdown('''<div class="grid4"><div class="metric"><div class="label">Quantum Readiness</div><div class="val">Awaiting PCAP</div><span class="badge bviolet">No input</span></div><div class="metric"><div class="label">TLS Version</div><div class="val">—</div><span class="badge">Pending</span></div><div class="metric"><div class="label">Cipher Suite</div><div class="val">—</div><span class="badge">Pending</span></div><div class="metric"><div class="label">Key Exchange</div><div class="val">—</div><span class="badge">Pending</span></div></div><section class="section"><div class="two"><div class="card dark"><h3>Executive Assessment</h3><p>Upload a PCAP to generate the RBI CBOM board-ready quantum-readiness report.</p></div><div class="card risk"><h3>Board-Level Risk</h3><p>No assessment has been run yet.</p><span class="badge bviolet">Awaiting evidence</span></div></div></section>''', unsafe_allow_html=True)
    st.stop()

with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded.name).suffix or ".pcap") as tmp:
    tmp.write(uploaded.read()); tmp_path=tmp.name
try:
    with st.spinner("Generating RBI CBOM board-ready assessment..."):
        report=analyze(tmp_path,{"target":target,"business_unit":business_unit,"classification":classification})
finally:
    try: os.remove(tmp_path)
    except Exception: pass
s=report["summary"]
st.markdown(f"""<div class="grid4"><div class="metric"><div class="label">Quantum Readiness</div><div class="val">{s['Quantum Readiness']}</div>{badge(s['Overall Risk'])}</div><div class="metric"><div class="label">TLS Version</div><div class="val">{s['TLS Version']}</div>{badge('Observed' if s['TLS Version']!='Not observable' else 'Requires Manual Validation')}</div><div class="metric"><div class="label">Cipher Suite</div><div class="val" style="font-size:17px">{s['Cipher Suite']}</div>{badge('Strong / Review' if 'AES' in s['Cipher Suite'] or 'CHACHA' in s['Cipher Suite'] else 'Review')}</div><div class="metric"><div class="label">Key Exchange</div><div class="val">{s['Key Exchange']}</div>{badge('Classical ECC' if any(x in s['Key Exchange'].lower() for x in ['secp','x25519','x448']) else 'Review')}</div></div>""", unsafe_allow_html=True)
assessment=f"RBI CBOM analyzed the uploaded PCAP and identified {s['Total Assets']} cryptographic assets/observations. The current quantum-readiness state is {s['Quantum Readiness']} with an overall risk of {s['Overall Risk']}. TLS 1.3 is treated as classically modern, but not automatically quantum-safe unless hybrid/PQC key exchange is observed."
board_risk="The endpoint may be secure by current classical TLS standards, but remains exposed to harvest-now-decrypt-later risk where classical asymmetric key exchange or certificate algorithms are used. Board oversight should focus on crypto-agility, PQC migration planning, and continuous CBOM monitoring." if s["Quantum Vulnerable / Weakened"]>0 else "No quantum-vulnerable cryptographic asset was identified in parsed evidence. This does not prove full organizational PQC readiness."
st.markdown(f"""<section class="section"><div class="two"><div class="card dark"><h3>Executive Assessment</h3><p>{assessment}</p><div class="kpis"><div class="kpi"><small>Target</small><strong>{target}</strong></div><div class="kpi"><small>Assets</small><strong>{s['Total Assets']}</strong></div><div class="kpi"><small>Quantum Score</small><strong>{s['Quantum Readiness Score']}%</strong></div></div></div><div class="card risk"><h3>Board-Level Risk</h3><p>{board_risk}</p>{badge('Harvest-now-decrypt-later risk present' if s['Quantum Vulnerable / Weakened']>0 else 'No PQC gap observed')}</div></div></section>""", unsafe_allow_html=True)
finding_html="".join([f"<div class='finding'><div class='findingTop'>{badge(f.get('Evidence Type',''))}{badge(str(f.get('Confidence','')))}</div><div class='title'>{f.get('Finding','')}</div><div class='value'>{f.get('Value','')}</div><div class='detail'>{f.get('Detail','')}</div><div class='foot'><span>Status: {f.get('Status','')}</span><span>{f.get('Evidence ID','')}</span></div></div>" for f in report["findings"][:6]]) or "<div class='card'><b>No high-risk findings generated from parsed evidence.</b><p class='muted'>This does not prove full compliance or full PQC readiness.</p></div>"
st.markdown(f"<section class='section'><h2>Evidence-Backed Findings</h2><p class='desc'>Every claim is labelled as Observed, Inferred, Risk Indicator, or Requires Manual Validation.</p><div class='findings'>{finding_html}</div></section>", unsafe_allow_html=True)

tabs=st.tabs(["CBOM", "TLS Flows", "Compliance", "Roadmap", "Evidence", "Exports"])
with tabs[0]:
    st.markdown("### Cryptographic Bill of Materials")
    st.dataframe(pd.DataFrame(report["cbom"]), use_container_width=True)
    df=pd.DataFrame(report["cbom"])
    if not df.empty:
        c1,c2=st.columns(2)
        with c1: st.bar_chart(df["Quantum Readiness"].value_counts())
        with c2: st.bar_chart(df["Protocol"].value_counts())
with tabs[1]:
    st.markdown("### Observed TLS Flows")
    if report["flows"]:
        for i,fl in enumerate(report["flows"],1):
            st.markdown(f"<div class='card'><b>Flow {i}</b> {badge(fl.get('TLS','TLS observed'))}<p><code>{fl.get('Source','?')} → {fl.get('Destination','?')}</code></p><p class='muted'>SNI: <b>{fl.get('SNI','')}</b> · Cipher: <b>{fl.get('Cipher','')}</b> · KEX: <b>{fl.get('KEX','')}</b></p></div>", unsafe_allow_html=True)
    else: st.info("No TLS flows parsed. Capture may not include visible ClientHello/ServerHello records.")
with tabs[2]:
    st.markdown("### Compliance Mapping")
    st.caption("CISO, audit, and regulatory conversation view. These are evidence-backed indicators, not formal certification.")
    st.dataframe(pd.DataFrame(report["compliance"]), use_container_width=True)
    st.markdown("### Policy Findings")
    st.dataframe(pd.DataFrame(report["findings"]), use_container_width=True)
with tabs[3]:
    st.markdown("### Quantum Remediation Roadmap")
    road_html="".join([f"<div class='card'>{badge(r['Timeline'])}<h3 style='margin-top:14px'>{r['Recommendation']}</h3><p class='muted'>{r['Executive Action']}</p><ul><li>{r['Technical Action']}</li><li>{r['Verification']}</li></ul></div>" for r in report["recommendations"][:3]])
    st.markdown(f"<div class='road'>{road_html}</div>", unsafe_allow_html=True)
    st.dataframe(pd.DataFrame(report["recommendations"]), use_container_width=True)
with tabs[4]:
    c1,c2=st.columns([2,1])
    with c1:
        st.markdown("### Evidence Explorer")
        st.dataframe(pd.DataFrame(report["evidence"]), use_container_width=True)
    with c2:
        st.markdown("### Parser Log")
        st.markdown(f"<div class='console'>{chr(10).join(report['parser_logs'])}</div>", unsafe_allow_html=True)
        st.markdown("### Limitations")
        for item in report["limitations"]: st.write("- "+item)
    st.markdown("### PQC Reference")
    st.dataframe(PQC_REFERENCE, use_container_width=True)
    st.markdown("### Glossary")
    st.dataframe(GLOSSARY, use_container_width=True)
with tabs[5]:
    html=html_report(report)
    st.download_button("Download Board-Ready HTML Report", html, "rbi_cbom_board_report.html", "text/html")
    st.download_button("Download Full JSON Report", json.dumps(report, indent=2), "rbi_cbom_report.json", "application/json")
    st.download_button("Download CBOM CSV", pd.DataFrame(report["cbom"]).to_csv(index=False), "rbi_cbom.csv", "text/csv")
    st.download_button("Download Compliance CSV", pd.DataFrame(report["compliance"]).to_csv(index=False), "rbi_cbom_compliance.csv", "text/csv")

st.caption("RBI CBOM Dashboard · PCAP evidence mode · Use results as defensible indicators, not standalone legal/regulatory certification.")
