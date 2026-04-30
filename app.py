import streamlit as st
import pandas as pd
import subprocess, tempfile, hashlib, json, os, shutil, uuid, re
from pathlib import Path
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px

st.set_page_config(page_title="RBI CBOM | Board Quantum Readiness", page_icon="🛡️", layout="wide", initial_sidebar_state="expanded")

st.markdown(r"""
<style>
:root{--bg:#f7fafc;--card:#fff;--ink:#0f172a;--muted:#64748b;--line:#e2e8f0;--blue:#2563eb;--blue2:#eff6ff;--green:#059669;--green2:#ecfdf5;--amber:#d97706;--amber2:#fffbeb;--red:#dc2626;--red2:#fef2f2;--violet:#7c3aed;--violet2:#f5f3ff;--dark:#020617;--shadow:0 16px 40px rgba(15,23,42,.08)}
.main{background:linear-gradient(135deg,#f8fafc,#eef6ff 55%,#f7fafc)}.block-container{max-width:1380px;padding-top:1.4rem;padding-bottom:2.6rem}
.hero{background:rgba(255,255,255,.94);border:1px solid var(--line);border-radius:34px;box-shadow:var(--shadow);overflow:hidden;margin-bottom:22px}.heroTop{padding:34px;background:radial-gradient(circle at top right,#dbeafe,transparent 38%),linear-gradient(135deg,#fff,#f8fafc);border-bottom:1px solid var(--line);display:grid;grid-template-columns:1fr 380px;gap:28px;align-items:center}.hero h1{font-size:46px;line-height:1.02;margin:12px 0;letter-spacing:-1.5px;color:#0f172a;font-weight:950}.sub{font-size:16px;line-height:1.65;color:var(--muted);max-width:860px}.badges{display:flex;gap:8px;flex-wrap:wrap}.badge{display:inline-flex;align-items:center;border-radius:999px;border:1px solid var(--line);padding:7px 11px;font-size:12px;font-weight:850;background:#f8fafc;color:#334155}.bblue{background:var(--blue2);color:#1d4ed8;border-color:#bfdbfe}.bgreen{background:var(--green2);color:#047857;border-color:#a7f3d0}.bamber{background:var(--amber2);color:#b45309;border-color:#fde68a}.bred{background:var(--red2);color:#b91c1c;border-color:#fecaca}.bviolet{background:var(--violet2);color:#6d28d9;border-color:#ddd6fe}.uploadBox{background:white;border:1px solid var(--line);border-radius:26px;padding:18px;box-shadow:0 8px 22px rgba(15,23,42,.06)}
.grid4{display:grid;grid-template-columns:repeat(4,1fr);gap:18px;margin:18px 0}.metric{background:var(--card);border:1px solid var(--line);border-radius:26px;padding:22px;box-shadow:0 6px 18px rgba(15,23,42,.04)}.metric .label{font-size:11px;text-transform:uppercase;letter-spacing:.08em;color:var(--muted);font-weight:900}.metric .val{font-size:24px;font-weight:950;margin-top:8px;word-break:break-word;color:#0f172a}.metric .note{margin-top:12px}.two{display:grid;grid-template-columns:2fr 1fr;gap:18px;margin-top:18px}.card{background:var(--card);border:1px solid var(--line);border-radius:28px;padding:24px;box-shadow:0 8px 22px rgba(15,23,42,.04)}.dark{background:#020617;color:white}.dark p,.dark .muted{color:#cbd5e1}.risk{background:var(--amber2);border-color:#fde68a}.risk h3,.risk p{color:#92400e}.card h3{margin:0 0 10px;font-size:19px}.muted{color:var(--muted)}.kpis{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-top:18px}.kpi{border-radius:18px;background:rgba(255,255,255,.10);padding:14px}.kpi small{display:block;color:#cbd5e1}.kpi strong{display:block;margin-top:5px;color:white}.sectionHead{display:flex;justify-content:space-between;gap:16px;align-items:flex-start;margin:28px 0 16px}.sectionHead h2{font-size:23px;margin:0;letter-spacing:-.4px;color:#0f172a}.desc{margin:7px 0 0;color:var(--muted);line-height:1.6;font-size:14px}.findings{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}.finding{background:white;border:1px solid var(--line);border-radius:24px;padding:18px;min-height:190px}.findingTop{display:flex;justify-content:space-between;gap:10px;margin-bottom:14px}.finding .title{font-size:13px;color:var(--muted);font-weight:900}.finding .value{font-size:18px;font-weight:950;margin-top:5px;color:#0f172a}.finding .detail{font-size:13px;line-height:1.55;color:#475569;margin-top:12px}.foot{display:flex;justify-content:space-between;gap:10px;margin-top:14px;font-size:12px;color:var(--muted)}.flow{background:#f8fafc;border:1px solid var(--line);border-radius:18px;padding:15px;margin-bottom:12px}.flowHead{display:flex;justify-content:space-between;gap:10px}.flow code{font-size:12px;color:#334155}.console{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;background:#020617;color:#d1fae5;border-radius:20px;padding:16px;white-space:pre-wrap;font-size:12px;line-height:1.45;max-height:260px;overflow:auto}.stTabs [data-baseweb="tab-list"]{gap:8px;background:rgba(255,255,255,.72);border:1px solid var(--line);padding:8px;border-radius:18px}.stTabs [data-baseweb="tab"]{border-radius:14px;font-weight:800}div[data-testid="stFileUploader"]{border:2px dashed #cbd5e1;border-radius:22px;padding:18px;background:#f8fafc}div[data-testid="stFileUploader"]:hover{background:#eef6ff;border-color:#93c5fd}@media(max-width:1000px){.heroTop,.two,.grid4,.findings{grid-template-columns:1fr}.hero h1{font-size:34px}.kpis{grid-template-columns:1fr}}
</style>
""", unsafe_allow_html=True)

TLS_VER={"0x0002":"SSLv2","0x0300":"SSLv3","0x0301":"TLS 1.0","0x0302":"TLS 1.1","0x0303":"TLS 1.2","0x0304":"TLS 1.3","769":"TLS 1.0","770":"TLS 1.1","771":"TLS 1.2","772":"TLS 1.3","0301":"TLS 1.0","0302":"TLS 1.1","0303":"TLS 1.2","0304":"TLS 1.3"}
CIPHER={"0x0004":"TLS_RSA_WITH_RC4_128_MD5","0x0005":"TLS_RSA_WITH_RC4_128_SHA","0x0009":"TLS_RSA_WITH_DES_CBC_SHA","0x000a":"TLS_RSA_WITH_3DES_EDE_CBC_SHA","0x002f":"TLS_RSA_WITH_AES_128_CBC_SHA","0x0035":"TLS_RSA_WITH_AES_256_CBC_SHA","0x009c":"TLS_RSA_WITH_AES_128_GCM_SHA256","0x009d":"TLS_RSA_WITH_AES_256_GCM_SHA384","0xc02f":"TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256","0xc030":"TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384","0xc02b":"TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256","0xc02c":"TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384","0x1301":"TLS_AES_128_GCM_SHA256","0x1302":"TLS_AES_256_GCM_SHA384","0x1303":"TLS_CHACHA20_POLY1305_SHA256","4865":"TLS_AES_128_GCM_SHA256","4866":"TLS_AES_256_GCM_SHA384","4867":"TLS_CHACHA20_POLY1305_SHA256"}
GROUP={"0x0017":"secp256r1 / P-256","0x0018":"secp384r1 / P-384","0x0019":"secp521r1 / P-521","0x001d":"x25519","0x001e":"x448","0x11ec":"X25519 + ML-KEM-768 / Kyber-768 hybrid","0x6399":"X25519 + ML-KEM/Kyber hybrid draft","0x2f39":"ML-KEM-768 draft / experimental hybrid indicator","23":"secp256r1 / P-256","24":"secp384r1 / P-384","25":"secp521r1 / P-521","29":"x25519","30":"x448","secp256r1":"secp256r1 / P-256","prime256v1":"secp256r1 / P-256","x25519":"x25519","x448":"x448","secp384r1":"secp384r1 / P-384","secp521r1":"secp521r1 / P-521"}
PQC_WORDS=["ml-kem","kyber","mlkem","ml_dsa","ml-dsa","dilithium","slh-dsa","sphincs","hybrid","pqc"]

def badge_class(v):
    v=str(v).lower()
    if any(x in v for x in ["critical","priority 1","not quantum","deprecated"]): return "bred"
    if any(x in v for x in ["vulnerable","priority 2","medium","partial","risk"]): return "bamber"
    if any(x in v for x in ["manual","unknown","priority 3"]): return "bviolet"
    if any(x in v for x in ["safe","ready","observed","low","strong"]): return "bgreen"
    return "bblue"
def badge(v): return f"<span class='badge {badge_class(v)}'>{v}</span>"
def sha256_file(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for c in iter(lambda:f.read(1024*1024), b""): h.update(c)
    return h.hexdigest()
def run_cmd(cmd, timeout=300):
    try:
        r=subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode==0 or bool(r.stdout.strip()), r.stdout, r.stderr
    except Exception as e: return False, "", str(e)
def tshark_json(path, filt):
    if not shutil.which("tshark"): return [], "tshark not found. Use Docker/Render deployment."
    ok,out,err=run_cmd(["tshark","-r",path,"-Y",filt,"-T","json"], timeout=300)
    if not out.strip(): return [], err
    try: return json.loads(out), err
    except Exception as e: return [], f"JSON parse error: {e}; tshark error: {err}"
def tshark_fields(path, filt, fields):
    if not shutil.which("tshark"): return pd.DataFrame(columns=fields), "tshark not found"
    args=["tshark","-r",path,"-Y",filt,"-T","fields","-E","header=y","-E","separator=\t"]
    for f in fields: args += ["-e", f]
    ok,out,err=run_cmd(args, timeout=300)
    if not out.strip(): return pd.DataFrame(columns=fields), err
    from io import StringIO
    try: return pd.read_csv(StringIO(out), sep="\t", dtype=str).fillna(""), err
    except Exception as e: return pd.DataFrame(columns=fields), f"{e}; {err}"
def count_packets(path):
    df,_=tshark_fields(path,"frame",["frame.number"]); return len(df)
def flatten(obj, prefix=""):
    items={}
    if isinstance(obj,dict):
        for k,v in obj.items():
            key=f"{prefix}.{k}" if prefix else k
            items.update(flatten(v,key))
    elif isinstance(obj,list):
        for i,v in enumerate(obj): items.update(flatten(v,f"{prefix}.{i}"))
    else: items[prefix]=obj
    return items
def get_any(flat, contains):
    vals=[]
    for k,v in flat.items():
        lk=k.lower()
        if all(c.lower() in lk for c in contains):
            vals.extend(v if isinstance(v,list) else [v])
    return [str(x) for x in vals if str(x) not in ["","None"]]
def norm_version(v):
    if not v: return "Not observable"
    if isinstance(v,list): v=v[-1] if v else ""
    v=str(v).strip()
    if "," in v:
        parts=[p.strip() for p in v.split(",") if p.strip()]
        mapped=[TLS_VER.get(p.lower(),TLS_VER.get(p,p)) for p in parts]
        order={"SSLv2":0,"SSLv3":1,"TLS 1.0":2,"TLS 1.1":3,"TLS 1.2":4,"TLS 1.3":5}
        return sorted(mapped,key=lambda x:order.get(x,-1),reverse=True)[0] if mapped else "Not observable"
    return TLS_VER.get(v.lower(),TLS_VER.get(v,v))
def norm_cipher(v):
    if not v: return "Not observable"
    if isinstance(v,list): v=v[-1] if v else ""
    v=str(v).strip()
    if "," in v: v=v.split(",")[-1].strip()
    return CIPHER.get(v.lower(), CIPHER.get(v, v))
def norm_group(v):
    if not v: return ""
    if isinstance(v,list): v=v[-1] if v else ""
    v=str(v).strip()
    if "," in v:
        parts=[p.strip() for p in v.split(",") if p.strip()]
        v=parts[-1] if parts else ""
    return GROUP.get(v.lower(), GROUP.get(v, v))
def extract_serverhello(pkt):
    layers=pkt.get("_source",{}).get("layers",{})
    flat=flatten(layers); ip=layers.get("ip",{}); ipv6=layers.get("ipv6",{}); tcp=layers.get("tcp",{}); frame=layers.get("frame",{})
    src=ip.get("ip.src","") or ipv6.get("ipv6.src",""); dst=ip.get("ip.dst","") or ipv6.get("ipv6.dst","")
    sport=tcp.get("tcp.srcport",""); dport=tcp.get("tcp.dstport","")
    supported_candidates=get_any(flat,["supported_version"])+get_any(flat,["supported_versions"])+get_any(flat,["tls.handshake.extensions.supported_version"])
    legacy_candidates=get_any(flat,["tls.handshake.version"])
    mapped=[norm_version(x) for x in supported_candidates]
    if "TLS 1.3" in mapped: final_version="TLS 1.3"; version_source="ServerHello supported_versions extension"
    elif mapped: final_version=mapped[-1]; version_source="ServerHello supported_versions extension"
    elif legacy_candidates: final_version=norm_version(legacy_candidates[-1]); version_source="Legacy handshake version field"
    else: final_version="Not observable"; version_source="Not observable"
    cipher=norm_cipher((get_any(flat,["ciphersuite"])+get_any(flat,["cipher_suite"]))[-1] if (get_any(flat,["ciphersuite"])+get_any(flat,["cipher_suite"])) else "")
    group_candidates=get_any(flat,["key_share_group"])+get_any(flat,["supported_group"])+get_any(flat,["group"])
    named_group=""
    for g in group_candidates:
        ng=norm_group(g)
        if ng and "length" not in ng.lower() and "list" not in ng.lower(): named_group=ng
    sni_candidates=get_any(flat,["server_name"])
    return {"frame":frame.get("frame.number",""),"timestamp":frame.get("frame.time_epoch",""),"src":src,"dst":dst,"sport":sport,"dport":dport,"tls_version":final_version,"version_source":version_source,"cipher":cipher,"named_group":named_group,"sni":sni_candidates[-1] if sni_candidates else ""}
def extract_clienthello(pkt):
    layers=pkt.get("_source",{}).get("layers",{}); flat=flatten(layers); ip=layers.get("ip",{}); tcp=layers.get("tcp",{})
    groups=get_any(flat,["supported_group"])+get_any(flat,["key_share_group"])+get_any(flat,["group"])
    norm=[norm_group(g) for g in groups if norm_group(g)]
    sni=get_any(flat,["server_name"])
    return {"src":ip.get("ip.src",""),"dst":ip.get("ip.dst",""),"sport":tcp.get("tcp.srcport",""),"dport":tcp.get("tcp.dstport",""),"sni":sni[-1] if sni else "","groups":norm,"pq_offer":any(any(w in g.lower() for w in PQC_WORDS) for g in norm)}
def cipher_components(cipher,version):
    u=str(cipher).upper()
    if version=="TLS 1.3" or "TLS_AES_" in u or "CHACHA20" in u: kx="TLS 1.3 key schedule"
    elif "ECDHE" in u: kx="ECDHE"
    elif re.search(r"(^|_)DHE(_|$)",u): kx="DHE"
    elif u.startswith("TLS_RSA") or "RSA_WITH" in u: kx="RSA static key exchange"
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
    return kx,enc,mac,(version=="TLS 1.3" or kx in ["ECDHE","DHE"])
def quantum_classify(version,cipher,kx,named_group,client_pq_offer=False,cert_alg=""):
    observed=" ".join([version,cipher,kx,named_group,cert_alg]).lower()
    if any(w in observed for w in PQC_WORDS):
        return dict(asset=named_group or "Hybrid PQC / PQC",status="Quantum Ready / Hybrid Observed",safe="Yes",priority="Priority 4",risk="Low",category="Post-Quantum / Hybrid",basis="Hybrid/PQC key exchange was observed in the negotiated session.",attack="No known Shor/Grover break for approved PQC family",migration="Maintain crypto-agility and compatibility monitoring.",confidence=0.90,label="Observed")
    classical=any(x in observed for x in ["ecdhe","ecdh","ecdsa","rsa","dhe","diffie","dsa","secp","prime256","x25519","x448"])
    tls13_no_group=version=="TLS 1.3" and not named_group
    if classical or tls13_no_group:
        if named_group: asset=named_group; label="Observed"; conf=0.88; basis="Classical asymmetric key exchange is visible and is vulnerable to Shor's algorithm at Q-Day."
        elif tls13_no_group: asset="TLS 1.3 key exchange group not extracted"; label="Risk Indicator"; conf=0.72; basis="TLS 1.3 was negotiated, but the key-share group was not extracted. Standard TLS 1.3 commonly uses classical ECDHE unless hybrid/PQC is observed."
        else: asset=kx or cert_alg or "Classical asymmetric cryptography"; label="Inferred"; conf=0.76; basis="Classical asymmetric cryptography is inferred from cipher/certificate metadata."
        if client_pq_offer: basis += " Client-side PQ/hybrid capability may be present, but final server negotiation remains decisive."
        return dict(asset=asset,status="Quantum Vulnerable",safe="No",priority="Priority 2",risk="Medium",category="Classical asymmetric cryptography",basis=basis,attack="Shor's algorithm",migration="Plan hybrid/PQC migration. Prefer ML-KEM for key establishment and ML-DSA/SLH-DSA for signatures where supported.",confidence=conf,label=label)
    if any(x in observed for x in ["aes-256","sha-384","sha-512"]):
        return dict(asset="AES-256 / SHA-384+",status="Adequate Post-Quantum Symmetric Margin",safe="Yes",priority="Priority 4",risk="Low",category="Symmetric / hash algorithm",basis="Symmetric/hash strength has stronger post-quantum margin against Grover-style reduction.",attack="Grover's algorithm",migration="Maintain AES-256 and SHA-384/512 preference.",confidence=0.82,label="Inferred")
    if any(x in observed for x in ["aes-128","sha-256","chacha20"]):
        return dict(asset="AES-128 / SHA-256 / ChaCha20 family",status="Quantum Weakened",safe="No",priority="Priority 3",risk="Medium",category="Symmetric / hash algorithm",basis="Grover's algorithm may reduce effective security margin for long-lived sensitive data.",attack="Grover's algorithm",migration="Prefer AES-256 and SHA-384/512 for long-lived sensitive data.",confidence=0.82,label="Risk Indicator")
    return dict(asset="Unknown / incomplete handshake evidence",status="Requires Manual Validation",safe="No",priority="Priority 3",risk="Unknown",category="Unknown",basis="Insufficient cryptographic metadata in capture.",attack="Unknown",migration="Capture complete handshakes and validate endpoint configuration manually.",confidence=0.50,label="Requires Manual Validation")

def analyze(path,meta):
    start=datetime.now(); pcap_hash=sha256_file(path); total_packets=count_packets(path)
    server_json,tls_err=tshark_json(path,"tls.handshake.type == 2"); client_json,ch_err=tshark_json(path,"tls.handshake.type == 1")
    cert_df,cert_err=tshark_fields(path,"tls.handshake.certificate",["frame.number","frame.time_epoch","ip.src","ip.dst","x509af.signature_algorithm","x509af.subjectPublicKeyInfo.algorithm.algorithm"])
    plain_df,plain_err=tshark_fields(path,"http or ftp or telnet or smtp or pop or imap or ldap or snmp",["frame.number","frame.time_epoch","ip.src","tcp.srcport","udp.srcport","ip.dst","tcp.dstport","udp.dstport","_ws.col.Protocol"])
    ssh_df,ssh_err=tshark_fields(path,"ssh",["frame.number","frame.time_epoch","ip.src","ip.dst","tcp.dstport","ssh.kex_algorithms","ssh.encryption_algorithms_client_to_server","ssh.mac_algorithms_client_to_server","ssh.server_host_key_algorithms"])
    dnssec_df,_=tshark_fields(path,"dns.flags.authenticated == 1 or dns.resp.type == 46 or dns.resp.type == 48 or dns.resp.type == 43",["frame.number"])
    ipsec_df,_=tshark_fields(path,"isakmp or esp or ah",["frame.number"]); quic_df,_=tshark_fields(path,"quic",["frame.number","frame.time_epoch","ip.src","udp.srcport","ip.dst","udp.dstport","_ws.col.Info"])
    clients=[extract_clienthello(p) for p in client_json]; cbom=[]; evidence=[]; findings=[]; flows=[]; algomap={}
    logs=[f"Packets analyzed: {total_packets}",f"ClientHello records parsed: {len(clients)}",f"ServerHello records parsed: {len(server_json)}","TLS version accuracy rule: ServerHello supported_versions extension overrides tls.handshake.version legacy field."]
    for idx,p in enumerate(server_json):
        sh=extract_serverhello(p); matched=[ch for ch in clients if (ch['src']==sh['dst'] and ch['dst']==sh['src']) or (ch['src']==sh['src'] and ch['dst']==sh['dst'])]
        client_pq=any(ch['pq_offer'] for ch in matched)
        if not sh['sni'] and matched: sh['sni']=next((ch['sni'] for ch in matched if ch['sni']),"")
        if not sh['named_group'] and matched:
            allg=[]
            for ch in matched: allg.extend(ch['groups'])
            pqg=[g for g in allg if any(w in g.lower() for w in PQC_WORDS)]
            sh['client_group_indicator']=(pqg[-1] if pqg else allg[-1]) if allg else ""
        else: sh['client_group_indicator']=""
        kx,enc,mac,fs=cipher_components(sh['cipher'],sh['tls_version']); q=quantum_classify(sh['tls_version'],sh['cipher'],kx,sh['named_group'],client_pq)
        flags=[]
        if sh['tls_version'] in ["SSLv2","SSLv3","TLS 1.0","TLS 1.1"]: flags.append("TLS_LEGACY_VERSION")
        if any(x in sh['cipher'].upper() for x in ["RC4","3DES","DES","NULL","EXPORT","ANON","MD5"]): flags.append("WEAK_CIPHER")
        if kx=="RSA static key exchange": flags.append("STATIC_RSA_KEY_EXCHANGE")
        if q['priority']=="Priority 2": flags.append("QUANTUM_VULNERABLE_ASYMMETRIC")
        elif q['priority']=="Priority 3": flags.append("QUANTUM_WEAKENED_OR_UNKNOWN")
        if sh['tls_version']=="TLS 1.3" and not sh['named_group']: flags.append("KEY_SHARE_GROUP_NOT_EXTRACTED")
        if client_pq and not any(w in (sh['named_group'] or '').lower() for w in PQC_WORDS): flags.append("CLIENT_PQ_OFFER_SERVER_SELECTED_CLASSICAL_OR_UNKNOWN")
        risk="Critical" if any(f in flags for f in ["TLS_LEGACY_VERSION","WEAK_CIPHER"]) else "High" if "STATIC_RSA_KEY_EXCHANGE" in flags else q['risk']
        ev=f"EVD-TLS-{idx+1:04d}"; rec={"CBOM ID":f"CBOM-{len(cbom)+1:06d}","Asset":q['asset'],"Protocol":"TLS","TLS Version":sh['tls_version'],"TLS Version Evidence":sh['version_source'],"Cipher Suite":sh['cipher'],"Symmetric Encryption":enc,"Hash / KDF":mac,"Key Exchange":sh['named_group'] or kx,"Client Offered PQ/Hybrid":"Yes" if client_pq else "No","Client Offered Group Indicator":sh.get('client_group_indicator',''),"Forward Secrecy":fs,"Quantum Readiness":q['status'],"Quantum Safe":q['safe'],"Priority":q['priority'],"Risk":risk,"Source":f"{sh['src']}:{sh['sport']}","Destination":f"{sh['dst']}:{sh['dport']}","SNI":sh['sni'],"Evidence Type":q['label'],"Confidence":q['confidence'],"Executive Note":q['basis'],"Recommended Migration":q['migration'],"Policy Flags":", ".join(flags),"Evidence ID":ev}
        cbom.append(rec); evidence.append({"Evidence ID":ev,"Frame":sh['frame'],"Timestamp":sh['timestamp'],"Source":rec['Source'],"Destination":rec['Destination'],"Protocol":"TLS","Observed Value":f"{sh['tls_version']} via {sh['version_source']} / {sh['cipher']} / {sh['named_group'] or kx}","Defensibility":q['label'],"Confidence":q['confidence'],"PCAP SHA256":pcap_hash}); flows.append({"Source":rec['Source'],"Destination":rec['Destination'],"SNI":sh['sni'],"TLS":sh['tls_version'],"Version Evidence":sh['version_source'],"Cipher":sh['cipher'],"KEX":sh['named_group'] or kx,"Quantum":q['status']})
        algomap.setdefault(q['asset'],{"Algorithm":q['asset'],"Category":q['category'],"Quantum Threat":q['status'],"Priority":q['priority'],"Attack Algorithm":q['attack'],"NIST / PQC Status":"PQC migration required" if q['priority']=="Priority 2" else "Adequate / monitor","Recommended Migration":q['migration'],"Source IPs":set(),"Destination IPs":set(),"Connections":0,"Evidence Type":q['label'],"Confidence":q['confidence']})
        algomap[q['asset']]['Source IPs'].add(sh['src']); algomap[q['asset']]['Destination IPs'].add(sh['dst']); algomap[q['asset']]['Connections']+=1
    for i,r in plain_df.head(1000).iterrows():
        src=r.get('ip.src',''); dst=r.get('ip.dst',''); sport=r.get('tcp.srcport','') or r.get('udp.srcport',''); dport=r.get('tcp.dstport','') or r.get('udp.dstport',''); proto=r.get('_ws.col.Protocol','Plaintext'); ev=f"EVD-PLAIN-{i+1:04d}"
        cbom.append({"CBOM ID":f"CBOM-{len(cbom)+1:06d}","Asset":"Plaintext Transport","Protocol":proto,"TLS Version":"N/A","TLS Version Evidence":"Plaintext protocol","Cipher Suite":"None","Symmetric Encryption":"None","Hash / KDF":"None","Key Exchange":"None","Client Offered PQ/Hybrid":"N/A","Client Offered Group Indicator":"","Forward Secrecy":False,"Quantum Readiness":"Classical confidentiality risk","Quantum Safe":"N/A","Priority":"Priority 1","Risk":"Critical","Source":f"{src}:{sport}","Destination":f"{dst}:{dport}","SNI":"","Evidence Type":"Observed","Confidence":0.90,"Executive Note":"No cryptographic protection observed.","Recommended Migration":"Replace plaintext with TLS/SSH/SFTP/STARTTLS as appropriate.","Policy Flags":"PLAINTEXT_PROTOCOL","Evidence ID":ev})
    title_map={"TLS_LEGACY_VERSION":"Deprecated TLS/SSL protocol observed","WEAK_CIPHER":"Weak cipher suite observed","STATIC_RSA_KEY_EXCHANGE":"Static RSA key exchange observed","QUANTUM_VULNERABLE_ASYMMETRIC":"Quantum-vulnerable asymmetric cryptography","QUANTUM_WEAKENED_OR_UNKNOWN":"Quantum-weakened or low-confidence cryptographic evidence","KEY_SHARE_GROUP_NOT_EXTRACTED":"TLS 1.3 key-share group not extracted","CLIENT_PQ_OFFER_SERVER_SELECTED_CLASSICAL_OR_UNKNOWN":"Client PQ offer seen, but server did not negotiate PQ/hybrid","PLAINTEXT_PROTOCOL":"Plaintext protocol observed"}
    for r in cbom:
        for flag in [x.strip() for x in r.get('Policy Flags','').split(',') if x.strip()]: findings.append({"Finding":title_map.get(flag,flag),"Value":r['Asset'],"Status":r['Risk'],"Evidence Type":"Risk Indicator" if flag.startswith('QUANTUM') or flag.startswith('CLIENT_PQ') else r['Evidence Type'],"Confidence":r['Confidence'],"Detail":r['Executive Note'],"Evidence ID":r['Evidence ID'],"Endpoint":r['Destination'],"Policy":"default_network"})
    encrypted=sum(1 for r in cbom if r['Protocol'] in ['TLS','SSH','TLS Certificate']); plaintext=sum(1 for r in cbom if 'PLAINTEXT_PROTOCOL' in r.get('Policy Flags','')); qsafe=sum(1 for r in cbom if r['Quantum Safe']=='Yes'); qv=sum(1 for r in cbom if r['Quantum Safe']=='No' and r['Priority'] in ['Priority 2','Priority 3']); deprecated=sum(1 for r in cbom if any(x in r.get('Policy Flags','') for x in ['TLS_LEGACY_VERSION','WEAK_CIPHER','WEAK_CERT_SIGNATURE'])); manual=sum(1 for r in cbom if r['Evidence Type']=='Requires Manual Validation')
    quantum_relevant=[r for r in cbom if r['Quantum Safe'] in ['Yes','No']]; quantum_score=round(100*sum(1 for r in quantum_relevant if r['Quantum Safe']=='Yes')/max(len(quantum_relevant),1),1); encryption_score=round(100*encrypted/max(encrypted+plaintext,1),1); overall='Priority 1' if deprecated or plaintext else 'Priority 2' if qv else 'Priority 3' if manual else 'Priority 4'
    algorithms=[{**{k:v for k,v in a.items() if k not in ['Source IPs','Destination IPs']},'Source IPs':', '.join(sorted(x for x in a['Source IPs'] if x)),'Destination IPs':', '.join(sorted(x for x in a['Destination IPs'] if x))} for a in algomap.values()]
    compliance=[{"Framework":"NIST PQC Migration","Status":"Gap" if qv else "Positive Indicator","Evidence Type":"Risk Indicator","Executive Note":"Classical ECC/RSA/DHE are Shor-vulnerable unless hybrid/PQ is negotiated."},{"Framework":"CNSA 2.0 Direction","Status":"PQC Migration Required" if qv else "Monitor","Evidence Type":"Risk Indicator","Executive Note":"Plan hybrid/PQC transition for critical endpoints."},{"Framework":"ISO 27001 / 27002","Status":"Crypto Inventory Required","Evidence Type":"Observed + Inferred","Executive Note":"Maintain CBOM evidence for cryptographic asset governance."},{"Framework":"PCI DSS","Status":"TLS Baseline Review","Evidence Type":"Risk Indicator","Executive Note":"Weak/plaintext transport may affect regulated data scope; validate manually."},{"Framework":"RBI / Financial Sector Cyber Resilience","Status":"PQC Roadmap Required" if qv else "Technical Indicator","Evidence Type":"Risk Indicator","Executive Note":"Board-level quantum-risk roadmap should be documented for critical banking-facing endpoints."},{"Framework":"CERT-In / Incident Readiness","Status":"Evidence Pack Needed","Evidence Type":"Requires Manual Validation","Executive Note":"Retain packet-level evidence and event timelines where incident obligations may apply."},{"Framework":"DPDP / GDPR Confidentiality","Status":"HNDL Risk Present" if qv else "Manual Validation","Evidence Type":"Inferred","Executive Note":"Classical public-key crypto may expose long-lived sensitive data to harvest-now-decrypt-later risk."}]
    recommendations=[]
    if deprecated: recommendations.append({"Recommendation":"Eliminate deprecated cryptography","Category":"Immediate Hardening","Timeline":"0-30 Days","Priority":"Priority 1","Affected":deprecated,"Executive Action":"Approve immediate remediation for deprecated TLS, weak cipher, or weak certificate findings.","Technical Action":"Disable legacy TLS and weak ciphers; replace weak signatures and algorithms.","Verification":"Fresh PCAP shows zero deprecated observations."})
    if plaintext: recommendations.append({"Recommendation":"Remove plaintext protocols","Category":"Transport Security","Timeline":"0-30 Days","Priority":"Priority 1","Affected":plaintext,"Executive Action":"Require business owners to migrate plaintext services.","Technical Action":"Replace FTP/Telnet/HTTP-sensitive flows with SFTP/SSH/HTTPS/STARTTLS.","Verification":"Fresh PCAP shows zero plaintext flows."})
    if qv: recommendations.append({"Recommendation":"Begin PQC migration planning","Category":"Quantum Readiness","Timeline":"30-90 Days","Priority":"Priority 2","Affected":qv,"Executive Action":"Create a crypto-agility and PQC migration program.","Technical Action":"Inventory RSA/ECDH/ECDSA/DHE usage, test hybrid TLS/PQC options, and plan ML-KEM/ML-DSA migration.","Verification":"Track reduction of Priority 2 assets and validate hybrid/PQC pilot results."})
    recommendations += [{"Recommendation":"Establish continuous CBOM inventory","Category":"Governance","Timeline":"2-4 Weeks","Priority":"Priority 3","Affected":len(cbom),"Executive Action":"Mandate recurring CBOM updates for critical network zones.","Technical Action":"Schedule periodic PCAP-based discovery and integrate with asset inventory.","Verification":"Monthly CBOM trend report."},{"Recommendation":"Implement crypto-agility framework","Category":"Architecture","Timeline":"3-6 Months","Priority":"Priority 3","Affected":len(algorithms),"Executive Action":"Approve architecture changes for rapid algorithm replacement.","Technical Action":"Abstract cryptographic dependencies and document approved algorithm baselines.","Verification":"Architecture review and migration test."}]
    primary=next((r for r in cbom if r['Protocol']=='TLS'),{})
    summary={"Quantum Readiness":"Quantum Ready" if quantum_score==100 else "Partially Ready" if quantum_score>0 else "Not Quantum Ready","Overall Risk":overall,"TLS Version":primary.get('TLS Version','Not observable'),"TLS Version Evidence":primary.get('TLS Version Evidence','Not observable'),"Cipher Suite":primary.get('Cipher Suite','Not observable'),"Key Exchange":primary.get('Key Exchange','Not observable'),"Quantum Readiness Score":quantum_score,"Encryption Security Score":encryption_score,"Total Assets":len(cbom),"Quantum Safe":qsafe,"Quantum Vulnerable / Weakened":qv,"Deprecated":deprecated,"Manual Validation Items":manual}
    doc={"Document Title":"RBI CBOM Quantum Readiness Dashboard","Tool Name":"RBI CBOM","Target Application":meta['target'],"Scan Type":"NETWORK / TLS Discovery & Quantum Readiness","Scan ID":str(uuid.uuid4()),"Assessment Date":datetime.now().strftime('%B %d, %Y'),"Classification":meta['classification'],"Scanner Version":"RBI CBOM PQC Scanner v4.0","Parser Engine":"tshark JSON + supported_versions negotiation parser","Scan Target":"Uploaded PCAP","Total Packets":total_packets,"Analysis Duration":str(datetime.now()-start).split('.')[0],"Business Unit":meta['business_unit'],"Application Criticality":overall,"PCAP SHA256":pcap_hash}
    limitations=["This dashboard analyzes only traffic present in the uploaded PCAP.","TLS 1.3 must be detected through the ServerHello supported_versions extension; tls.handshake.version alone may show TLS 1.2 as a legacy compatibility field.","TLS 1.3 is not automatically quantum-safe; standard TLS 1.3 using classical ECDHE remains quantum-vulnerable unless hybrid/PQC key exchange is observed.","If TLS 1.3 encrypts certificate messages, full certificate assurance may require TLS key logs or external certificate scanning.","Compliance results are evidence-backed indicators, not formal legal or regulatory certification.","NAT, proxies, load balancers, and short capture windows may affect endpoint attribution."]
    parser_logs=logs+[f"Certificate rows extracted: {len(cert_df)}",f"Plaintext rows sampled: {len(plain_df)}",f"SSH rows sampled: {len(ssh_df)}",f"DNSSEC observations: {len(dnssec_df)}",f"IPsec/IKE observations: {len(ipsec_df)}",f"QUIC observations: {len(quic_df)}",f"TLS parser note: {tls_err}" if tls_err else "TLS JSON parser completed.",f"ClientHello parser note: {ch_err}" if ch_err else "ClientHello JSON parser completed.",f"Certificate parser note: {cert_err}" if cert_err else "Certificate parser completed.",f"Plaintext parser note: {plain_err}" if plain_err else "Plaintext parser completed.",f"SSH parser note: {ssh_err}" if ssh_err else "SSH parser completed."]
    return {"document":doc,"summary":summary,"protocol":{"TLS Crypto Assets":sum(1 for r in cbom if r['Protocol']=='TLS'),"Unique Cipher Suites":len(set(r['Cipher Suite'] for r in cbom if r['Cipher Suite'] not in ['', 'None','N/A','Not observable'])),"TLS 1.3 Assets":sum(1 for r in cbom if r['TLS Version']=='TLS 1.3'),"TLS 1.2 Assets":sum(1 for r in cbom if r['TLS Version']=='TLS 1.2'),"SSH Observations":len(ssh_df),"DNSSEC Observations":len(dnssec_df),"IPsec / IKE Observations":len(ipsec_df),"QUIC Observations":len(quic_df),"Certificate Metadata Rows":len(cert_df)},"cbom":cbom,"algorithms":algorithms,"findings":findings,"compliance":compliance,"recommendations":recommendations,"evidence":evidence,"flows":flows,"limitations":limitations,"parser_logs":parser_logs}

def html_report(report):
    s=report['summary']; d=report['document']
    def table(records): return pd.DataFrame(records).to_html(index=False, escape=False) if records else '<p>No records.</p>'
    return f"""<!doctype html><html><head><meta charset='utf-8'><title>RBI CBOM Board Report</title><style>body{{font-family:Inter,Arial,sans-serif;margin:0;background:linear-gradient(135deg,#f8fafc,#eef6ff 55%,#f7fafc);color:#0f172a}}.wrap{{max-width:1320px;margin:auto;padding:28px}}.hero{{background:white;border:1px solid #e2e8f0;border-radius:34px;box-shadow:0 16px 40px rgba(15,23,42,.08);overflow:hidden}}.top{{padding:34px;background:radial-gradient(circle at top right,#dbeafe,transparent 38%),linear-gradient(135deg,#fff,#f8fafc);border-bottom:1px solid #e2e8f0}}h1{{font-size:46px;line-height:1.02;margin:12px 0;letter-spacing:-1.5px}}.sub{{font-size:16px;line-height:1.65;color:#64748b;max-width:850px}}.badge{{display:inline-flex;border-radius:999px;border:1px solid #e2e8f0;padding:7px 11px;font-size:12px;font-weight:800;background:#eff6ff;color:#1d4ed8;margin:2px}}.grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:18px;padding:28px}}.metric{{background:white;border:1px solid #e2e8f0;border-radius:26px;padding:22px;box-shadow:0 6px 18px rgba(15,23,42,.04)}}.metric small{{font-size:11px;text-transform:uppercase;color:#64748b;font-weight:900}}.metric b{{display:block;font-size:24px;margin-top:8px}}.section{{padding:0 28px 28px}}.card{{background:white;border:1px solid #e2e8f0;border-radius:28px;padding:24px;margin-bottom:18px}}table{{width:100%;border-collapse:collapse;background:white;font-size:12px}}th{{background:#f1f5f9;color:#475569;text-align:left;text-transform:uppercase;font-size:11px;padding:12px}}td{{border-top:1px solid #f1f5f9;padding:10px;vertical-align:top}}</style></head><body><div class='wrap'><main class='hero'><div class='top'><span class='badge'>RBI CBOM</span><span class='badge'>Quantum Readiness</span><span class='badge'>PCAP Evidence Mode</span><h1>RBI CBOM Quantum Readiness Dashboard</h1><p class='sub'>Executive board-ready report for TLS version detection, CBOM inventory, compliance indicators, and quantum-readiness.</p></div><div class='grid'><div class='metric'><small>Quantum Readiness</small><b>{s['Quantum Readiness']}</b></div><div class='metric'><small>TLS Version</small><b>{s['TLS Version']}</b><p>{s['TLS Version Evidence']}</p></div><div class='metric'><small>Cipher Suite</small><b style='font-size:16px'>{s['Cipher Suite']}</b></div><div class='metric'><small>Key Exchange</small><b>{s['Key Exchange']}</b></div></div><section class='section'><div class='card'><h2>Executive Assessment</h2><p>Overall risk is <b>{s['Overall Risk']}</b>. Quantum readiness score is <b>{s['Quantum Readiness Score']}%</b>. TLS 1.3 is not treated as quantum-safe unless hybrid/PQC key exchange is observed.</p></div></section><section class='section'><h2>CBOM</h2>{table(report['cbom'])}</section><section class='section'><h2>Findings</h2>{table(report['findings'])}</section><section class='section'><h2>Compliance Mapping</h2>{table(report['compliance'])}</section><section class='section'><h2>Recommendations</h2>{table(report['recommendations'])}</section><section class='section'><h2>Evidence</h2>{table(report['evidence'])}</section><section class='section'><h2>Document Control</h2>{table([d])}</section><section class='section'><h2>Limitations</h2><ul>{''.join('<li>'+x+'</li>' for x in report['limitations'])}</ul></section></main></div></body></html>"""

st.sidebar.title('🛡️ RBI CBOM'); st.sidebar.caption('Accurate board-ready CBOM, TLS discovery, and quantum-readiness from PCAP evidence.')
target=st.sidebar.text_input('Target Application','RBI-Website'); business_unit=st.sidebar.text_input('Business Unit','Network'); classification=st.sidebar.selectbox('Classification',['CONFIDENTIAL','INTERNAL','RESTRICTED','PUBLIC'],index=0)
st.sidebar.markdown('---'); st.sidebar.markdown('### Accuracy engine'); st.sidebar.write('• tshark JSON parser'); st.sidebar.write('• ServerHello supported_versions'); st.sidebar.write('• TLS 1.3 legacy-version correction'); st.sidebar.write('• Key-share / named-group extraction'); st.sidebar.write('• PQC/hybrid detection')

st.markdown("""<div class="hero"><div class="heroTop"><div><div class="badges"><span class="badge bblue">RBI CBOM</span><span class="badge bviolet">Quantum Readiness</span><span class="badge">PCAP Evidence Mode</span></div><h1>RBI CBOM Quantum Readiness Dashboard</h1><p class="sub">Executive board-level dashboard for TLS version detection, cryptographic bill of materials, evidence-backed compliance mapping, and harvest-now-decrypt-later quantum-risk assessment from uploaded PCAP files.</p></div><div class="uploadBox"><b>Upload PCAP / PCAPNG</b><p class="muted">Uses tshark JSON parsing. TLS 1.3 is detected from ServerHello supported_versions, avoiding false TLS 1.2 legacy-version results.</p>""", unsafe_allow_html=True)
uploaded=st.file_uploader('Upload PCAP / PCAPNG / CAP',type=['pcap','pcapng','cap'],label_visibility='collapsed')
st.markdown('</div></div></div>', unsafe_allow_html=True)
if not uploaded:
    st.markdown("""<div class="grid4"><div class="metric"><div class="label">Quantum Readiness</div><div class="val">Awaiting PCAP</div><div class="note"><span class="badge bviolet">No input</span></div></div><div class="metric"><div class="label">TLS Version</div><div class="val">—</div><div class="note"><span class="badge">Pending</span></div></div><div class="metric"><div class="label">Cipher Suite</div><div class="val">—</div><div class="note"><span class="badge">Pending</span></div></div><div class="metric"><div class="label">Key Exchange</div><div class="val">—</div><div class="note"><span class="badge">Pending</span></div></div></div><div class="two"><div class="card dark"><h3>Executive Assessment</h3><p>Upload a PCAP to generate a board-ready RBI CBOM quantum-readiness assessment.</p></div><div class="card risk"><h3>Board-Level Risk</h3><p>No assessment has been run yet.</p><span class="badge bviolet">Awaiting evidence</span></div></div>""", unsafe_allow_html=True); st.stop()
with tempfile.NamedTemporaryFile(delete=False,suffix=Path(uploaded.name).suffix or '.pcap') as tmp:
    tmp.write(uploaded.read()); tmp_path=tmp.name
try:
    with st.spinner('Generating accurate RBI CBOM assessment...'):
        report=analyze(tmp_path, {'target':target,'business_unit':business_unit,'classification':classification})
finally:
    try: os.remove(tmp_path)
    except Exception: pass
s=report['summary']
st.markdown(f"""<div class="grid4"><div class="metric"><div class="label">Quantum Readiness</div><div class="val">{s['Quantum Readiness']}</div><div class="note">{badge(s['Overall Risk'])}</div></div><div class="metric"><div class="label">TLS Version</div><div class="val">{s['TLS Version']}</div><div class="note">{badge(s['TLS Version Evidence'])}</div></div><div class="metric"><div class="label">Cipher Suite</div><div class="val" style="font-size:17px">{s['Cipher Suite']}</div><div class="note">{badge('Strong / Review' if 'AES' in s['Cipher Suite'] or 'CHACHA' in s['Cipher Suite'] else 'Review')}</div></div><div class="metric"><div class="label">Key Exchange</div><div class="val">{s['Key Exchange']}</div><div class="note">{badge('Classical / PQ Review')}</div></div></div>""", unsafe_allow_html=True)
assessment=f"RBI CBOM analyzed the uploaded PCAP and identified {s['Total Assets']} cryptographic assets/observations. The negotiated TLS version is reported as {s['TLS Version']} using: {s['TLS Version Evidence']}. The current quantum-readiness state is {s['Quantum Readiness']} with overall risk {s['Overall Risk']}. TLS 1.3 is treated as classically modern, but not automatically quantum-safe unless hybrid/PQC key exchange is observed."
board_risk="The endpoint may be secure by current classical TLS standards, but remains exposed to harvest-now-decrypt-later risk where classical asymmetric key exchange or certificate algorithms are used. Board oversight should focus on crypto-agility, PQC migration planning, and continuous CBOM monitoring." if s['Quantum Vulnerable / Weakened']>0 else "No quantum-vulnerable cryptographic asset was identified in parsed evidence. This does not prove full organizational PQC readiness."
st.markdown(f"""<div class="two"><div class="card dark"><h3>Executive Assessment</h3><p>{assessment}</p><div class="kpis"><div class="kpi"><small>Target</small><strong>{target}</strong></div><div class="kpi"><small>Assets</small><strong>{s['Total Assets']}</strong></div><div class="kpi"><small>Quantum Score</small><strong>{s['Quantum Readiness Score']}%</strong></div></div></div><div class="card risk"><h3>Board-Level Risk</h3><p>{board_risk}</p>{badge('Harvest-now-decrypt-later risk present' if s['Quantum Vulnerable / Weakened']>0 else 'No PQC gap observed')}</div></div>""", unsafe_allow_html=True)
st.markdown('<div class="sectionHead"><div><h2>Board Metrics</h2><p class="desc">Executive summary charts optimized for board and risk committee discussion.</p></div></div>', unsafe_allow_html=True)
g1,g2,g3=st.columns(3); cbom_df=pd.DataFrame(report['cbom'])
with g1:
    fig=go.Figure(go.Indicator(mode='gauge+number',value=s['Quantum Readiness Score'],title={'text':'Quantum Readiness Score'},gauge={'axis':{'range':[0,100]},'bar':{'color':'#2563eb'},'steps':[{'range':[0,40],'color':'#fef2f2'},{'range':[40,75],'color':'#fffbeb'},{'range':[75,100],'color':'#ecfdf5'}]})); fig.update_layout(height=310, margin=dict(l=20,r=20,t=50,b=20), paper_bgcolor='rgba(0,0,0,0)'); st.plotly_chart(fig,use_container_width=True)
with g2:
    if not cbom_df.empty:
        dist=cbom_df['Quantum Readiness'].value_counts().reset_index(); dist.columns=['Quantum Readiness','Count']; fig=px.pie(dist,names='Quantum Readiness',values='Count',hole=0.58,title='Quantum Posture Mix'); fig.update_layout(height=310,margin=dict(l=20,r=20,t=50,b=20),paper_bgcolor='rgba(0,0,0,0)'); st.plotly_chart(fig,use_container_width=True)
with g3:
    if not cbom_df.empty:
        dist=cbom_df['Protocol'].value_counts().reset_index(); dist.columns=['Protocol','Count']; fig=px.bar(dist,x='Protocol',y='Count',title='Protocol Observations',text='Count'); fig.update_layout(height=310,margin=dict(l=20,r=20,t=50,b=20),paper_bgcolor='rgba(0,0,0,0)'); st.plotly_chart(fig,use_container_width=True)
st.markdown('<div class="sectionHead"><div><h2>Evidence-Backed Findings</h2><p class="desc">Every claim is labelled as Observed, Inferred, Risk Indicator, or Requires Manual Validation.</p></div></div>', unsafe_allow_html=True)
finding_html=''
for f in report['findings'][:6]:
    finding_html += f"""<div class="finding"><div class="findingTop">{badge(f.get('Evidence Type',''))}{badge(str(f.get('Confidence','')))}</div><div class="title">{f.get('Finding','')}</div><div class="value">{f.get('Value','')}</div><div class="detail">{f.get('Detail','')}</div><div class="foot"><span>Status: {f.get('Status','')}</span><span>{f.get('Evidence ID','')}</span></div></div>"""
if not finding_html: finding_html="<div class='card'><b>No high-risk findings generated from parsed evidence.</b><p class='muted'>This does not prove full compliance or full PQC readiness.</p></div>"
st.markdown(f"<div class='findings'>{finding_html}</div>", unsafe_allow_html=True)
tabs=st.tabs(['Executive CBOM','TLS Evidence','Compliance','Roadmap','Evidence Explorer','Exports'])
with tabs[0]:
    st.markdown('### Cryptographic Bill of Materials')
    cols=['Asset','Protocol','TLS Version','TLS Version Evidence','Cipher Suite','Key Exchange','Client Offered PQ/Hybrid','Quantum Readiness','Quantum Safe','Priority','Risk','Evidence Type','Confidence','Executive Note']
    st.dataframe(cbom_df[cols] if not cbom_df.empty else cbom_df, use_container_width=True, hide_index=True)
    st.markdown('### Algorithm Security Analysis'); st.dataframe(pd.DataFrame(report['algorithms']),use_container_width=True,hide_index=True)
with tabs[1]:
    st.markdown('### Observed TLS Flows')
    if report['flows']:
        st.dataframe(pd.DataFrame(report['flows']),use_container_width=True,hide_index=True)
    else: st.info('No TLS flows parsed. Capture may not include visible ClientHello/ServerHello records.')
with tabs[2]:
    st.markdown('### Compliance Mapping'); st.caption('Evidence-backed indicators, not formal certification.'); st.dataframe(pd.DataFrame(report['compliance']),use_container_width=True,hide_index=True); st.markdown('### Policy Findings'); st.dataframe(pd.DataFrame(report['findings']),use_container_width=True,hide_index=True)
with tabs[3]:
    st.markdown('### Quantum Remediation Roadmap'); rec_df=pd.DataFrame(report['recommendations'])
    if not rec_df.empty:
        st.dataframe(rec_df,use_container_width=True,hide_index=True)
with tabs[4]:
    c1,c2=st.columns([2,1])
    with c1: st.markdown('### Evidence Explorer'); st.dataframe(pd.DataFrame(report['evidence']),use_container_width=True,hide_index=True)
    with c2: st.markdown('### Parser Log'); st.markdown(f"<div class='console'>{chr(10).join(report['parser_logs'])}</div>", unsafe_allow_html=True); st.markdown('### Limitations'); [st.write('- '+x) for x in report['limitations']]
with tabs[5]:
    html=html_report(report); st.download_button('Download Board-Ready HTML Report',html,'rbi_cbom_board_report.html','text/html'); st.download_button('Download Full JSON Report',json.dumps(report,indent=2),'rbi_cbom_report.json','application/json'); st.download_button('Download CBOM CSV',cbom_df.to_csv(index=False),'rbi_cbom.csv','text/csv'); st.download_button('Download Compliance CSV',pd.DataFrame(report['compliance']).to_csv(index=False),'rbi_cbom_compliance.csv','text/csv')
st.caption('RBI CBOM Dashboard · tshark JSON parser · TLS 1.3 supported_versions correction · PCAP evidence mode · Not standalone legal/regulatory certification.')
