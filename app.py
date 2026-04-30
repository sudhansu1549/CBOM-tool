
import streamlit as st
import pandas as pd
import hashlib, tempfile, os, json, uuid, struct
from pathlib import Path
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px

st.set_page_config(page_title="RBI CBOM | Board Report", page_icon="🛡️", layout="wide")

# ---------- Executive styling ----------
st.markdown("""
<style>
:root{--bg:#f7fafc;--card:#ffffff;--ink:#0f172a;--muted:#64748b;--line:#e2e8f0;--blue:#2563eb;--blue2:#eff6ff;--green:#059669;--green2:#ecfdf5;--amber:#d97706;--amber2:#fffbeb;--red:#dc2626;--red2:#fef2f2;--violet:#7c3aed;--violet2:#f5f3ff;--shadow:0 16px 40px rgba(15,23,42,.08)}
.main{background:linear-gradient(135deg,#f8fafc,#eef6ff 55%,#f7fafc)}
.block-container{max-width:1360px;padding-top:1.4rem}
.hero{background:rgba(255,255,255,.94);border:1px solid var(--line);border-radius:34px;box-shadow:var(--shadow);overflow:hidden;margin-bottom:22px}
.heroTop{padding:34px;background:radial-gradient(circle at top right,#dbeafe,transparent 38%),linear-gradient(135deg,#fff,#f8fafc);display:grid;grid-template-columns:1fr 380px;gap:28px;align-items:center}
.hero h1{font-size:46px;line-height:1.02;margin:12px 0;letter-spacing:-1.5px;color:var(--ink);font-weight:950}
.sub{font-size:16px;line-height:1.65;color:var(--muted);max-width:860px}
.badge{display:inline-flex;align-items:center;border-radius:999px;border:1px solid var(--line);padding:7px 11px;font-size:12px;font-weight:850;background:#f8fafc;color:#334155;margin:2px}
.bblue{background:var(--blue2);color:#1d4ed8;border-color:#bfdbfe}.bgreen{background:var(--green2);color:#047857;border-color:#a7f3d0}.bamber{background:var(--amber2);color:#b45309;border-color:#fde68a}.bred{background:var(--red2);color:#b91c1c;border-color:#fecaca}.bviolet{background:var(--violet2);color:#6d28d9;border-color:#ddd6fe}
.uploadBox{background:white;border:1px solid var(--line);border-radius:26px;padding:18px;box-shadow:0 8px 22px rgba(15,23,42,.06)}
.grid4{display:grid;grid-template-columns:repeat(4,1fr);gap:18px;margin:18px 0}.metric{background:white;border:1px solid var(--line);border-radius:26px;padding:22px;box-shadow:0 6px 18px rgba(15,23,42,.04)}.metric .label{font-size:11px;text-transform:uppercase;letter-spacing:.08em;color:var(--muted);font-weight:900}.metric .val{font-size:24px;font-weight:950;margin-top:8px;word-break:break-word;color:var(--ink)}.metric .note{margin-top:12px}
.two{display:grid;grid-template-columns:2fr 1fr;gap:18px;margin-top:18px}.three{display:grid;grid-template-columns:repeat(3,1fr);gap:18px;margin-top:18px}.card{background:white;border:1px solid var(--line);border-radius:28px;padding:24px;box-shadow:0 8px 22px rgba(15,23,42,.04)}.dark{background:#020617;color:white}.dark p,.dark .muted{color:#cbd5e1}.risk{background:var(--amber2);border-color:#fde68a}.risk h3,.risk p{color:#92400e}.warn{background:var(--red2);border-color:#fecaca;color:#991b1b}.card h3{margin:0 0 10px;font-size:19px}.muted{color:var(--muted)}
.kpis{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-top:18px}.kpi{border-radius:18px;background:rgba(255,255,255,.10);padding:14px}.kpi small{display:block;color:#cbd5e1}.kpi strong{display:block;margin-top:5px;color:white}
.sectionHead{display:flex;justify-content:space-between;gap:16px;align-items:flex-start;margin:30px 0 16px}.sectionHead h2{font-size:24px;margin:0;color:var(--ink);letter-spacing:-.4px}.desc{margin:7px 0 0;color:var(--muted);line-height:1.6;font-size:14px}
.findings{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}.finding{background:white;border:1px solid var(--line);border-radius:24px;padding:18px;min-height:190px}.findingTop{display:flex;justify-content:space-between;gap:10px;margin-bottom:14px}.finding .title{font-size:13px;color:var(--muted);font-weight:900}.finding .value{font-size:18px;font-weight:950;margin-top:5px;color:var(--ink)}.finding .detail{font-size:13px;line-height:1.55;color:#475569;margin-top:12px}.foot{display:flex;justify-content:space-between;gap:10px;margin-top:14px;font-size:12px;color:var(--muted)}
.tableCard{border:1px solid var(--line);border-radius:24px;overflow:hidden;background:white;box-shadow:0 8px 22px rgba(15,23,42,.04)}.flow{background:#f8fafc;border:1px solid var(--line);border-radius:18px;padding:15px;margin-bottom:12px}.flow code{font-size:12px;color:#334155}.console{font-family:ui-monospace,Menlo,monospace;background:#020617;color:#d1fae5;border-radius:20px;padding:16px;white-space:pre-wrap;font-size:12px;line-height:1.45;max-height:260px;overflow:auto}
.road{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}.road ul{margin:14px 0 0;padding-left:20px;color:#475569;line-height:1.6;font-size:13px}
div[data-testid="stFileUploader"]{border:2px dashed #cbd5e1;border-radius:22px;padding:18px;background:#f8fafc}
.stTabs [data-baseweb="tab-list"]{gap:8px;background:rgba(255,255,255,.72);border:1px solid var(--line);padding:8px;border-radius:18px}.stTabs [data-baseweb="tab"]{border-radius:14px;font-weight:800}
@media(max-width:1000px){.heroTop,.two,.three,.grid4,.findings,.road{grid-template-columns:1fr}.hero h1{font-size:34px}.kpis{grid-template-columns:1fr}}

.boardSection{
  background:#ffffff;
  border:1px solid #e2e8f0;
  border-radius:30px;
  padding:26px;
  margin:24px 0;
  box-shadow:0 10px 28px rgba(15,23,42,.05);
}
.boardSection h2{
  font-size:24px;
  margin:0;
  color:#0f172a;
  letter-spacing:-.45px;
}
.boardSection .lead{
  margin:8px 0 18px;
  color:#64748b;
  line-height:1.6;
  font-size:14px;
}
.insightGrid{
  display:grid;
  grid-template-columns:repeat(3,1fr);
  gap:14px;
  margin:14px 0 20px;
}
.insight{
  background:#f8fafc;
  border:1px solid #e2e8f0;
  border-radius:20px;
  padding:16px;
}
.insight small{
  display:block;
  color:#64748b;
  text-transform:uppercase;
  letter-spacing:.06em;
  font-weight:900;
  font-size:11px;
}
.insight b{
  display:block;
  margin-top:7px;
  font-size:18px;
  color:#0f172a;
}
.cleanTableWrap{
  border:1px solid #e2e8f0;
  border-radius:22px;
  overflow:hidden;
  background:white;
}
.cleanTableWrap div[data-testid="stDataFrame"]{
  border-radius:22px;
}
.sectionDivider{
  height:1px;
  background:#e2e8f0;
  margin:18px 0;
}
.roadGrid{
  display:grid;
  grid-template-columns:repeat(3,1fr);
  gap:16px;
}
.roadCard{
  background:#ffffff;
  border:1px solid #e2e8f0;
  border-radius:24px;
  padding:20px;
  box-shadow:0 6px 18px rgba(15,23,42,.04);
}
.roadCard h3{
  margin:12px 0 8px;
  color:#0f172a;
}
.roadCard ul{
  margin:10px 0 0;
  padding-left:20px;
  color:#475569;
  line-height:1.55;
  font-size:13px;
}
.tableNote{
  background:#eff6ff;
  border:1px solid #bfdbfe;
  color:#1e3a8a;
  border-radius:16px;
  padding:12px 14px;
  font-size:13px;
  margin-bottom:14px;
}
@media(max-width:1000px){
  .insightGrid,.roadGrid{grid-template-columns:1fr}
}

</style>
""", unsafe_allow_html=True)

TLSVER={0x0301:"TLS 1.0",0x0302:"TLS 1.1",0x0303:"TLS 1.2",0x0304:"TLS 1.3"}
CIPH={0x1301:"TLS_AES_128_GCM_SHA256",0x1302:"TLS_AES_256_GCM_SHA384",0x1303:"TLS_CHACHA20_POLY1305_SHA256",0x1304:"TLS_AES_128_CCM_SHA256",0x1305:"TLS_AES_128_CCM_8_SHA256",0xC02F:"TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256",0xC030:"TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384",0xC02B:"TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256",0xC02C:"TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384",0x009C:"TLS_RSA_WITH_AES_128_GCM_SHA256",0x009D:"TLS_RSA_WITH_AES_256_GCM_SHA384",0x000A:"TLS_RSA_WITH_3DES_EDE_CBC_SHA",0x0005:"TLS_RSA_WITH_RC4_128_SHA"}
GROUP={0x001D:"x25519",0x0017:"secp256r1 / P-256",0x0018:"secp384r1 / P-384",0x0019:"secp521r1 / P-521",0x001E:"x448",0x11EC:"X25519 + ML-KEM-768 / Kyber-768 hybrid",0x6399:"X25519 + ML-KEM/Kyber hybrid draft",0x2F39:"ML-KEM-768 draft / experimental hybrid indicator"}

def bclass(v):
    v=str(v).lower()
    if "critical" in v or "priority 1" in v or "not quantum" in v or "deprecated" in v: return "bred"
    if "vulnerable" in v or "priority 2" in v or "medium" in v or "partial" in v or "risk" in v or "gap" in v: return "bamber"
    if "manual" in v or "unknown" in v or "priority 3" in v: return "bviolet"
    if "safe" in v or "ready" in v or "observed" in v or "low" in v or "strong" in v: return "bgreen"
    return "bblue"
def badge(v): return f"<span class='badge {bclass(v)}'>{v}</span>"
def u16(b,o,le=False): return b[o]|(b[o+1]<<8) if le else (b[o]<<8)|b[o+1]
def u32(b,o,le=False): return (b[o]|(b[o+1]<<8)|(b[o+2]<<16)|(b[o+3]<<24))&0xffffffff if le else ((b[o]<<24)|(b[o+1]<<16)|(b[o+2]<<8)|b[o+3])&0xffffffff
def ip4(b,o): return f"{b[o]}.{b[o+1]}.{b[o+2]}.{b[o+3]}"
def sha256_bytes(data): return hashlib.sha256(data).hexdigest()

def parse_pcap_packets(data):
    packets=[]; logs=[]
    if len(data)<24: return packets,["File too small."]
    magic_be=u32(data,0,False); magic_le=u32(data,0,True)
    if magic_be==0x0a0d0d0a:
        off=0
        while off+12<=len(data):
            bt=u32(data,off,False); bl=u32(data,off+4,False)
            if bl<12 or off+bl>len(data): break
            if bt==0x00000006 and off+28<=len(data):
                caplen=u32(data,off+20,False); po=off+28
                if po+caplen<=off+bl: packets.append(data[po:po+caplen])
            off+=bl
        logs.append(f"Parsed PCAPNG enhanced packet blocks: {len(packets)}")
        return packets,logs
    if magic_be==0xa1b2c3d4: le=False
    elif magic_be==0xd4c3b2a1 or magic_le==0xa1b2c3d4: le=True
    else: return packets,[f"Unsupported capture magic: 0x{magic_be:x}"]
    off=24
    while off+16<=len(data):
        incl=u32(data,off+8,le); off+=16
        if off+incl>len(data): break
        packets.append(data[off:off+incl]); off+=incl
    logs.append(f"Parsed PCAP packets: {len(packets)}")
    return packets,logs

def parse_client_hello(b):
    try:
        if len(b)<42: return None
        o=0; legacy=u16(b,o); o+=2+32
        sid=b[o]; o+=1+sid
        if o+2>len(b): return None
        cslen=u16(b,o); o+=2+cslen
        if o>=len(b): return None
        comp=b[o]; o+=1+comp
        if o+2>len(b): return {"legacy":TLSVER.get(legacy,f"0x{legacy:04x}"),"sni":"","groups":[],"pq_offer":False,"supported_versions":[]}
        extlen=u16(b,o); o+=2; end=min(o+extlen,len(b))
        sni=""; groups=[]; pq=False; versions=[]
        while o+4<=end:
            et=u16(b,o); el=u16(b,o+2); o+=4; e=min(o+el,end)
            if et==0 and o+2<=e:
                p=o+2
                while p+3<=e:
                    nt=b[p]; nl=u16(b,p+1); p+=3
                    if p+nl>e: break
                    if nt==0: sni=b[p:p+nl].decode("utf-8","ignore")
                    p+=nl
            elif et==10 and o+2<=e:
                gl=u16(b,o); p=o+2; limit=min(o+2+gl,e)
                while p+2<=limit:
                    g=u16(b,p); groups.append(GROUP.get(g,f"group 0x{g:04x}")); p+=2
            elif et==43 and o<e:
                l=b[o]; p=o+1; limit=min(o+1+l,e)
                while p+2<=limit:
                    v=u16(b,p); versions.append(TLSVER.get(v,f"0x{v:04x}")); p+=2
            elif et==51 and o+2<=e:
                kl=u16(b,o); p=o+2; limit=min(o+2+kl,e)
                while p+4<=limit:
                    g=u16(b,p); klen=u16(b,p+2); name=GROUP.get(g,f"group 0x{g:04x}")
                    groups.append(name)
                    if "ML-KEM" in name or "Kyber" in name or "hybrid" in name or klen>1000: pq=True
                    p+=4+klen
            o=e
        if any("ML-KEM" in g or "Kyber" in g or "hybrid" in g for g in groups): pq=True
        return {"legacy":TLSVER.get(legacy,f"0x{legacy:04x}"),"sni":sni,"groups":groups,"pq_offer":pq,"supported_versions":versions}
    except Exception:
        return None

def parse_server_hello(b):
    try:
        if len(b)<38: return None
        o=0; legacy=u16(b,o); o+=2+32
        sid=b[o]; o+=1+sid
        if o+2>len(b): return None
        cipher=u16(b,o); o+=2
        if o>=len(b): return None
        o+=1
        final=TLSVER.get(legacy,f"0x{legacy:04x}"); src="legacy_version field"; group=""
        if o+2<=len(b):
            extlen=u16(b,o); o+=2; end=min(o+extlen,len(b))
            while o+4<=end:
                et=u16(b,o); el=u16(b,o+2); o+=4; e=min(o+el,end)
                if et==43 and el>=2:
                    v=u16(b,o); final=TLSVER.get(v,f"0x{v:04x}"); src="ServerHello supported_versions extension"
                elif et==51 and el>=4:
                    g=u16(b,o); group=GROUP.get(g,f"group 0x{g:04x}")
                o=e
        return {"legacy":TLSVER.get(legacy,f"0x{legacy:04x}"),"tls_version":final,"version_evidence":src,"cipher":CIPH.get(cipher,f"0x{cipher:04x}"),"group":group}
    except Exception:
        return None

def parse_tls_records(payload, flow):
    o=0
    while o+5<=len(payload):
        ctype=payload[o]; ln=u16(payload,o+3)
        if ctype not in [20,21,22,23] or ln<=0 or o+5+ln>len(payload): break
        if ctype==22:
            p=o+5; end=o+5+ln
            while p+4<=end:
                htype=payload[p]; hlen=(payload[p+1]<<16)|(payload[p+2]<<8)|payload[p+3]
                hp=p+4; he=hp+hlen
                if hlen<0 or he>end: break
                if htype==1:
                    ch=parse_client_hello(payload[hp:he])
                    if ch: flow["client_hellos"].append(ch)
                elif htype==2:
                    sh=parse_server_hello(payload[hp:he])
                    if sh: flow["server_hellos"].append(sh)
                p=he
        o+=5+ln

def conn_key(src,sp,dst,dp):
    # canonicalize client/server by port 443 when possible
    if sp==443: return (dst,dp,src,sp)
    if dp==443: return (src,sp,dst,dp)
    return tuple(sorted([(src,sp),(dst,dp)]))

def parse_packets_to_connections(packets):
    conns={}
    for p in packets:
        if len(p)<34: continue
        eth=u16(p,12); ipoff=14
        if eth==0x8100 and len(p)>=18:
            eth=u16(p,16); ipoff=18
        if eth not in [0x0800] and len(p)>=16 and u16(p,14)==0x0800:
            eth=0x0800; ipoff=16
        if eth!=0x0800 or ipoff+20>len(p): continue
        ihl=(p[ipoff]&0xf)*4; proto=p[ipoff+9]
        if proto!=6: continue
        src=ip4(p,ipoff+12); dst=ip4(p,ipoff+16)
        toff=ipoff+ihl
        if toff+20>len(p): continue
        sp=u16(p,toff); dp=u16(p,toff+2)
        doff=((p[toff+12]>>4)&0xf)*4; po=toff+doff
        if po>=len(p): continue
        key=conn_key(src,sp,dst,dp)
        if key not in conns:
            if sp==443: conns[key]={"client_ip":dst,"client_port":dp,"server_ip":src,"server_port":sp,"client_hellos":[],"server_hellos":[]}
            else: conns[key]={"client_ip":src,"client_port":sp,"server_ip":dst,"server_port":dp,"client_hellos":[],"server_hellos":[]}
        parse_tls_records(p[po:], conns[key])
    return conns

def cipher_parts(cipher, ver):
    u=str(cipher).upper()
    kx="TLS 1.3 key schedule" if ver=="TLS 1.3" or "TLS_AES" in u or "CHACHA20" in u else "ECDHE" if "ECDHE" in u else "DHE" if "_DHE_" in u else "RSA static key exchange" if u.startswith("TLS_RSA") else "Unknown"
    enc="AES-256-GCM" if "AES_256_GCM" in u else "AES-128-GCM" if "AES_128_GCM" in u else "ChaCha20-Poly1305" if "CHACHA20" in u else "3DES" if "3DES" in u else "DES" if "DES" in u else "RC4" if "RC4" in u else "Unknown"
    mac="SHA-384" if "SHA384" in u else "SHA-256" if "SHA256" in u else "SHA-1" if "SHA" in u else "MD5" if "MD5" in u else "AEAD/Unknown"
    return kx,enc,mac,(ver=="TLS 1.3" or kx in ["ECDHE","DHE"])

def qclass(ver,cipher,kx,group,client_pq):
    text=" ".join([ver,cipher,kx,group]).lower()
    if any(x in text for x in ["ml-kem","kyber","hybrid","pqc"]):
        return {"asset":group or "Hybrid PQC","qr":"Quantum Ready / Hybrid Observed","safe":"Yes","priority":"Priority 4","risk":"Low","etype":"Observed","conf":"High","conf_score":0.90,"note":"Hybrid/PQC key exchange was negotiated."}
    classical=any(x in text for x in ["ecdhe","ecdh","rsa","dhe","diffie","ecdsa","secp","x25519","x448"]) or ver=="TLS 1.3"
    if classical:
        note="Final selected key exchange is classical or not PQ-observable; vulnerable to Shor's algorithm at Q-Day."
        if client_pq: note+=" Client offered PQ/hybrid, but the final server selection did not show PQ/hybrid."
        return {"asset":group or kx,"qr":"Quantum Vulnerable","safe":"No","priority":"Priority 2","risk":"Medium","etype":"Observed" if group else "Risk Indicator","conf":"High" if group else "Medium","conf_score":0.88 if group else 0.72,"note":note}
    return {"asset":"Unknown","qr":"Requires Manual Validation","safe":"No","priority":"Priority 3","risk":"Unknown","etype":"Requires Manual Validation","conf":"Low","conf_score":0.50,"note":"Incomplete handshake evidence."}

def analyze_bytes(data, filename, meta):
    packets,logs=parse_pcap_packets(data)
    conns=parse_packets_to_connections(packets)
    pcap_hash=sha256_bytes(data)
    cbom=[]; flows=[]; findings=[]; evidence=[]; algos={}
    for key,c in conns.items():
        if not c["server_hellos"]: continue
        # choose best serverhello: prefer one with selected group, then TLS 1.3
        sh=sorted(c["server_hellos"], key=lambda x:(1 if x.get("group") else 0, 1 if x.get("tls_version")=="TLS 1.3" else 0), reverse=True)[0]
        ch=c["client_hellos"][-1] if c["client_hellos"] else {}
        client_pq=bool(ch.get("pq_offer"))
        group=sh.get("group","")
        kx,enc,mac,fs=cipher_parts(sh["cipher"], sh["tls_version"])
        q=qclass(sh["tls_version"], sh["cipher"], kx, group, client_pq)
        flags=[]
        if q["priority"]=="Priority 2": flags.append("QUANTUM_VULNERABLE_ASYMMETRIC")
        if client_pq and not any(x in group.lower() for x in ["ml-kem","kyber","hybrid"]): flags.append("CLIENT_PQ_OFFER_SERVER_NOT_PQ")
        if sh["tls_version"]=="TLS 1.3" and not group: flags.append("KEY_SHARE_GROUP_NOT_EXTRACTED")
        ev=f"EVD-TLS-{len(evidence)+1:04d}"
        rec={"CBOM ID":f"CBOM-{len(cbom)+1:06d}","Asset":q["asset"],"Protocol":"TLS","TLS Version":sh["tls_version"],"TLS Version Evidence":sh["version_evidence"],"Cipher Suite":sh["cipher"],"Symmetric Encryption":enc,"Hash / KDF":mac,"Key Exchange":group or kx,"Client Offered PQ Hybrid":"Yes - hybrid key share indicator observed" if client_pq else "No visible PQ offer","Client Offered Groups":", ".join(ch.get("groups",[])[:8]),"Server Selected PQ Hybrid":"Yes" if "hybrid" in group.lower() or "ML-KEM" in group else "No","Forward Secrecy":fs,"Quantum Readiness":q["qr"],"Quantum Safe":q["safe"],"Priority":q["priority"],"Risk":q["risk"],"Source":f"{c['client_ip']}:{c['client_port']}","Destination":f"{c['server_ip']}:{c['server_port']}","SNI":ch.get("sni",""),"Evidence Type":q["etype"],"Confidence":q["conf"],"Confidence Score":q["conf_score"],"Executive Note":q["note"],"Recommended Migration":"Plan hybrid/PQC migration using ML-KEM for key establishment and ML-DSA/SLH-DSA for signatures where supported." if q["priority"]=="Priority 2" else "Maintain monitoring.","Policy Flags":", ".join(flags),"Evidence ID":ev}
        cbom.append(rec)
        flows.append({"Source":rec["Source"],"Destination":rec["Destination"],"SNI":rec["SNI"],"TLS":rec["TLS Version"],"Cipher":rec["Cipher Suite"],"KEX":rec["Key Exchange"],"Quantum":rec["Quantum Readiness"]})
        evidence.append({"Evidence ID":ev,"Source":rec["Source"],"Destination":rec["Destination"],"Protocol":"TLS","Observed Value":f"{rec['TLS Version']} via {rec['TLS Version Evidence']} / {rec['Cipher Suite']} / {rec['Key Exchange']}","Defensibility":rec["Evidence Type"],"Confidence":rec["Confidence"],"PCAP SHA256":pcap_hash})
        algos.setdefault(q["asset"],{"Algorithm":q["asset"],"Quantum Threat":q["qr"],"Priority":q["priority"],"Attack Algorithm":"Shor's algorithm" if q["priority"]=="Priority 2" else "N/A / Grover context","Recommended Migration":rec["Recommended Migration"],"Connections":0,"Evidence Type":q["etype"],"Confidence":q["conf"]})
        algos[q["asset"]]["Connections"]+=1
        for flag in flags:
            title={"QUANTUM_VULNERABLE_ASYMMETRIC":"Quantum-vulnerable asymmetric cryptography","CLIENT_PQ_OFFER_SERVER_NOT_PQ":"Client PQ offer seen, but server did not negotiate PQ/hybrid","KEY_SHARE_GROUP_NOT_EXTRACTED":"TLS 1.3 key-share group not extracted"}.get(flag,flag)
            findings.append({"Finding":title,"Value":rec["Asset"],"Status":rec["Risk"],"Evidence Type":"Risk Indicator" if flag!="KEY_SHARE_GROUP_NOT_EXTRACTED" else "Requires Manual Validation","Confidence":rec["Confidence"],"Detail":rec["Executive Note"],"Evidence ID":ev,"Endpoint":rec["Destination"],"Policy":"default_network"})
    # Add fixed report-grade findings and CBOM capabilities if TLS found
    if cbom:
        primary=cbom[0]
        fixed_findings=[
            {"Finding":"TLS Version Negotiated","Value":primary["TLS Version"],"Status":"Strong","Evidence Type":"Observed","Confidence":"High","Detail":"Supported_versions extension or ServerHello evidence confirms negotiated TLS version.","Evidence ID":primary["Evidence ID"],"Endpoint":primary["Destination"],"Policy":"evidence"},
            {"Finding":"Cipher Suite","Value":primary["Cipher Suite"],"Status":"Strong/Review","Evidence Type":"Observed","Confidence":"High","Detail":"Selected ServerHello cipher suite.","Evidence ID":primary["Evidence ID"],"Endpoint":primary["Destination"],"Policy":"evidence"},
            {"Finding":"Final Key Exchange","Value":primary["Key Exchange"],"Status":"Classical or PQ Review","Evidence Type":"Observed" if primary["Key Exchange"]!="TLS 1.3 key schedule" else "Risk Indicator","Confidence":primary["Confidence"],"Detail":"Final selected key share group determines PQ readiness.","Evidence ID":primary["Evidence ID"],"Endpoint":primary["Destination"],"Policy":"evidence"},
            {"Finding":"Client PQ Capability","Value":primary["Client Offered PQ Hybrid"],"Status":"Indicator","Evidence Type":"Observed / Strongly Inferred" if primary["Client Offered PQ Hybrid"].startswith("Yes") else "Observed","Confidence":"Medium-High" if primary["Client Offered PQ Hybrid"].startswith("Yes") else "Medium","Detail":"Client offer alone does not mean the session is PQ-safe.","Evidence ID":primary["Evidence ID"],"Endpoint":primary["Destination"],"Policy":"evidence"},
            {"Finding":"Server PQ Negotiation","Value":"Negotiated" if primary["Server Selected PQ Hybrid"]=="Yes" else "Not negotiated","Status":"Gap/Status" if primary["Server Selected PQ Hybrid"]!="Yes" else "Positive","Evidence Type":"Observed","Confidence":"High","Detail":"Server selection determines final TLS session posture.","Evidence ID":primary["Evidence ID"],"Endpoint":primary["Destination"],"Policy":"evidence"},
            {"Finding":"Certificate Visibility","Value":"Encrypted or not captured","Status":"Manual Validation Needed","Evidence Type":"Requires Manual Validation","Confidence":"High","Detail":"TLS 1.3 certificate details usually require TLS key logs or external certificate scan.","Evidence ID":"EVD-CERT-MANUAL","Endpoint":primary["Destination"],"Policy":"manual_validation"}
        ]
        # prepend fixed findings
        findings=fixed_findings+findings
        report_cbom=[
            {"Asset":"File","Value":filename,"Evidence Type":"Observed","Confidence":"High","Executive Note":"Input analyzed by RBI CBOM parser"},
            {"Asset":"Protocol","Value":primary["TLS Version"],"Evidence Type":"Observed","Confidence":"High","Executive Note":"TLS version from ServerHello supported_versions/visible handshake evidence"},
            {"Asset":"SNI","Value":primary["SNI"] or "Not visible","Evidence Type":"Observed" if primary["SNI"] else "Requires Manual Validation","Confidence":"High" if primary["SNI"] else "Low","Executive Note":"Server Name Indication from ClientHello"},
            {"Asset":"Server IP","Value":primary["Destination"].split(":")[0],"Evidence Type":"Observed","Confidence":"High","Executive Note":"Destination endpoint in capture"},
            {"Asset":"Cipher Suite","Value":primary["Cipher Suite"],"Evidence Type":"Observed","Confidence":"High","Executive Note":"Selected by ServerHello"},
            {"Asset":"Symmetric Encryption","Value":primary["Symmetric Encryption"],"Evidence Type":"Inferred from cipher","Confidence":"High","Executive Note":"Symmetric crypto remains more quantum-resilient than public-key crypto"},
            {"Asset":"Hash / KDF","Value":primary["Hash / KDF"],"Evidence Type":"Inferred from cipher","Confidence":"High","Executive Note":"Hash family inferred from TLS cipher suite"},
            {"Asset":"Key Exchange","Value":primary["Key Exchange"],"Evidence Type":"Observed" if primary["Key Exchange"]!="TLS 1.3 key schedule" else "Risk Indicator","Confidence":primary["Confidence"],"Executive Note":"Classical ECC is not PQ-safe unless hybrid/PQ is negotiated"},
            {"Asset":"Client Offered PQ Hybrid","Value":primary["Client Offered PQ Hybrid"],"Evidence Type":"Observed / Strongly Inferred" if primary["Client Offered PQ Hybrid"].startswith("Yes") else "Observed","Confidence":"Medium-High" if primary["Client Offered PQ Hybrid"].startswith("Yes") else "Medium","Executive Note":"Client-side transition signal only; does not prove final PQ security"},
            {"Asset":"Server Selected PQ Hybrid","Value":primary["Server Selected PQ Hybrid"],"Evidence Type":"Observed","Confidence":"High","Executive Note":"Final negotiated key exchange determines session quantum-readiness"},
            {"Asset":"Certificate Chain","Value":"Not visible from encrypted TLS 1.3 handshake","Evidence Type":"Requires Manual Validation","Confidence":"High","Executive Note":"Use TLS key logs or external certificate scan for certificate assurance"}
        ]
    else:
        primary={}
        report_cbom=[]
    qsafe=sum(1 for r in cbom if r["Quantum Safe"]=="Yes")
    qv=sum(1 for r in cbom if r["Quantum Safe"]=="No")
    score=round(100*qsafe/max(qsafe+qv,1),1)
    readiness="Quantum Ready" if score==100 and cbom else "Partially Ready" if primary and primary.get("Client Offered PQ Hybrid","").startswith("Yes") else "Not Quantum Ready"
    overall="Priority 2" if qv else "Priority 4"
    compliance=[
        {"Framework":"NIST PQC Migration","Status":"Partial / Gap" if qv else "Positive Indicator","Evidence Type":"Risk Indicator","Executive Note":"Classical ECC remains exposed to future quantum attacks unless hybrid/PQ is negotiated."},
        {"Framework":"CNSA 2.0 Direction","Status":"Gap" if qv else "Monitor","Evidence Type":"Risk Indicator","Executive Note":"Hybrid/PQ transition should be planned and piloted."},
        {"Framework":"ISO 27001 / 27002","Status":"Needs Crypto Inventory","Evidence Type":"Observed + Inferred","Executive Note":"Maintain CBOM evidence for cryptographic asset governance."},
        {"Framework":"PCI DSS","Status":"TLS Baseline Review","Evidence Type":"Observed","Executive Note":"TLS 1.2+ and strong cipher posture should be evidenced."},
        {"Framework":"RBI / Financial Sector Cyber Resilience","Status":"Needs PQ Roadmap" if qv else "Technical Indicator","Evidence Type":"Risk Indicator","Executive Note":"Quantum-readiness roadmap should be documented for critical banking-facing endpoints."},
        {"Framework":"CERT-In / Incident Readiness","Status":"Evidence Pack Needed","Evidence Type":"Requires Manual Validation","Executive Note":"Retain packet-level evidence and periodic crypto scan records."},
        {"Framework":"DPDP / GDPR Confidentiality","Status":"HNDL Risk Present" if qv else "Manual Validation","Evidence Type":"Inferred","Executive Note":"Classical ECDHE may expose long-lived sensitive data to harvest-now-decrypt-later risk."}
    ]
    roadmap=[
        {"Phase":"0–30 Days","Title":"Evidence Baseline","Actions":"Run repeated PCAP scans from multiple clients and networks; add TLS key-log supported certificate validation for controlled tests; create endpoint-level CBOM inventory for RBI-facing domains."},
        {"Phase":"30–90 Days","Title":"Crypto-Agility Readiness","Actions":"Track RSA, ECDSA, ECDHE, P-256, P-384, X25519, ML-KEM, and hybrid usage; define internal policy for PQ transition readiness; add server-side support checks for hybrid TLS key exchange."},
        {"Phase":"90–180 Days","Title":"Hybrid PQ Pilot","Actions":"Pilot X25519 + ML-KEM-768 hybrid key exchange in controlled environments; measure latency, compatibility and failure rates; prepare board-level quantum-risk reporting and exception workflows."}
    ]
    return {"document":{"Tool Name":"RBI CBOM","Target Application":meta["target"],"Scan ID":str(uuid.uuid4()),"Assessment Date":datetime.now().strftime("%B %d, %Y"),"Classification":meta["classification"],"Scanner Version":"RBI CBOM PQC Scanner v6.0","Total Packets":len(packets),"PCAP SHA256":pcap_hash},"summary":{"Quantum Readiness":readiness,"Overall Risk":overall,"TLS Version":primary.get("TLS Version","Not observable"),"Cipher Suite":primary.get("Cipher Suite","Not observable"),"Key Exchange":primary.get("Key Exchange","Not observable"),"Server IP":primary.get("Destination","").split(":")[0] if primary else "Not observable","Target":primary.get("SNI",meta["target"]) if primary else meta["target"],"TLS Sessions":len(cbom),"Quantum Readiness Score":score,"Total Assets":len(report_cbom),"Quantum Vulnerable / Weakened":qv},"cbom":cbom,"report_cbom":report_cbom,"findings":findings,"flows":flows,"evidence":evidence,"algorithms":list(algos.values()),"compliance":compliance,"roadmap":roadmap,"parser_logs":logs+[f"TLS sessions identified: {len(cbom)}","TLS 1.3 accuracy rule: ServerHello supported_versions overrides legacy_version."],"limitations":["Certificate chain, certificate expiry, SAN validation, issuer, signature algorithm, and weak certificate checks are not directly visible when TLS 1.3 encrypts certificate messages. Add TLS key-log ingestion or external certificate scan integration for complete certificate assurance.","This dashboard analyzes only traffic present in the uploaded PCAP.","Compliance results are evidence indicators, not formal certification."]}

def html_report(r):
    """Generate board-ready HTML without using an f-string.

    This avoids Python SyntaxError caused by backslashes inside f-string
    expression blocks. All dynamic values are assembled before formatting.
    """
    import html as _html

    def esc(x):
        return _html.escape(str(x if x is not None else ""))

    def table(rows, columns=None):
        if not rows:
            return "<p class='muted'>No records.</p>"
        if columns is None:
            columns = list(rows[0].keys())
        head = "".join("<th>{}</th>".format(esc(c)) for c in columns)
        body_rows = []
        for row in rows:
            cells = "".join("<td>{}</td>".format(esc(row.get(c, ""))) for c in columns)
            body_rows.append("<tr>{}</tr>".format(cells))
        return "<div class='tableWrap'><table><thead><tr>{}</tr></thead><tbody>{}</tbody></table></div>".format(
            head, "".join(body_rows)
        )

    summary = r.get("summary", {})
    doc = r.get("document", {})
    parser_log = "\n".join(str(x) for x in r.get("parser_logs", []))
    limitations = "".join("<li>{}</li>".format(esc(x)) for x in r.get("limitations", []))

    cbom_cols = [
        "Asset", "Value", "Evidence Type", "Confidence", "Executive Note"
    ]
    technical_cols = [
        "CBOM ID", "Asset", "Protocol", "TLS Version", "Cipher Suite",
        "Key Exchange", "Quantum Readiness", "Quantum Safe", "Priority",
        "Risk", "Evidence Type", "Confidence"
    ]
    flow_cols = ["Source", "Destination", "SNI", "TLS", "Cipher", "KEX", "Quantum"]
    comp_cols = ["Framework", "Status", "Evidence Type", "Executive Note"]
    rec_cols = ["Timeline", "Recommendation", "Executive Action", "Technical Action", "Verification"]

    css = """
    <style>
    body{margin:0;background:#f7fafc;font-family:Inter,Arial,sans-serif;color:#0f172a}
    .wrap{max-width:1120px;margin:auto;padding:34px}
    .hero{background:#fff;border:1px solid #e2e8f0;border-radius:34px;padding:34px;box-shadow:0 16px 40px rgba(15,23,42,.08)}
    h1{font-size:42px;line-height:1.05;margin:14px 0;letter-spacing:-1.3px}
    h2{font-size:25px;margin-top:36px}
    h3{font-size:20px;margin:0 0 12px}
    p{line-height:1.58}
    .sub{color:#64748b;font-size:16px}
    .badge{display:inline-flex;border-radius:999px;border:1px solid #e2e8f0;padding:7px 11px;font-size:12px;font-weight:800;background:#f8fafc;color:#334155;margin:2px}
    .bblue{background:#eff6ff;color:#1d4ed8;border-color:#bfdbfe}
    .bgreen{background:#ecfdf5;color:#047857;border-color:#a7f3d0}
    .bamber{background:#fffbeb;color:#b45309;border-color:#fde68a}
    .grid{display:grid;grid-template-columns:repeat(4,1fr);gap:18px;margin:28px 0}
    .metric{background:#fff;border:1px solid #e2e8f0;border-radius:26px;padding:22px;box-shadow:0 6px 18px rgba(15,23,42,.04)}
    .metric small{display:block;font-size:11px;text-transform:uppercase;letter-spacing:.08em;color:#64748b;font-weight:900}
    .metric b{display:block;font-size:24px;margin-top:8px}
    .card{background:white;border:1px solid #e2e8f0;border-radius:28px;padding:24px;box-shadow:0 8px 22px rgba(15,23,42,.04);margin:18px 0}
    .risk{background:#fffbeb;border-color:#fde68a;color:#92400e}
    .warn{background:#fef2f2;border-color:#fecaca;color:#991b1b}
    .tableWrap{border:1px solid #e2e8f0;border-radius:24px;overflow:auto;background:white;box-shadow:0 8px 22px rgba(15,23,42,.04)}
    table{width:100%;border-collapse:collapse;background:white;font-size:12px}
    th{background:#f1f5f9;color:#475569;text-align:left;text-transform:uppercase;font-size:11px;letter-spacing:.08em;padding:14px}
    td{border-top:1px solid #f1f5f9;padding:13px;vertical-align:top}
    .console{font-family:monospace;background:#020617;color:#d1fae5;border-radius:20px;padding:16px;white-space:pre-wrap;font-size:12px;line-height:1.45}
    .muted{color:#64748b}
    @media print{body{background:white}.wrap{padding:0}.hero,.card,.metric{box-shadow:none}}
    </style>
    """

    html_doc = """
    <!doctype html>
    <html>
    <head>
      <meta charset="utf-8">
      <title>RBI CBOM Board Report</title>
      {css}
    </head>
    <body>
      <div class="wrap">
        <div class="hero">
          <span class="badge bblue">RBI CBOM</span>
          <span class="badge">Quantum Readiness</span>
          <span class="badge">PCAP Evidence Mode</span>
          <h1>RBI CBOM Quantum Readiness Dashboard</h1>
          <p class="sub">Standalone executive dashboard for TLS version detection, cryptographic bill of materials, evidence-backed compliance mapping, and harvest-now-decrypt-later quantum-risk assessment from uploaded PCAP files.</p>

          <div class="grid">
            <div class="metric"><small>Quantum Readiness</small><b>{quantum_readiness}</b><span class="badge bamber">{overall_risk}</span></div>
            <div class="metric"><small>TLS Version</small><b>{tls_version}</b><span class="badge bgreen">Observed</span></div>
            <div class="metric"><small>Cipher Suite</small><b style="font-size:16px">{cipher_suite}</b><span class="badge bgreen">Strong</span></div>
            <div class="metric"><small>Key Exchange</small><b>{key_exchange}</b><span class="badge bamber">Classical ECC</span></div>
          </div>

          <div class="card">
            <h3>Executive Assessment</h3>
            <p>{executive_assessment}</p>
          </div>

          <div class="card risk">
            <h3>Board-Level Risk</h3>
            <p>{board_risk}</p>
            <span class="badge bamber">Harvest-now-decrypt-later risk present</span>
          </div>

          <h2>Evidence-Backed Findings</h2>
          {findings_table}

          <h2>Cryptographic Bill of Materials</h2>
          {report_cbom_table}

          <h2>Technical CBOM Inventory</h2>
          {technical_cbom_table}

          <h2>Observed TLS Flows</h2>
          {flows_table}

          <h2>Compliance Mapping</h2>
          {compliance_table}

          <h2>Quantum Remediation Roadmap</h2>
          {recommendations_table}

          <div class="card warn">
            <h3>What This PCAP Cannot Prove Alone</h3>
            <p>Certificate chain, certificate expiry, SAN validation, issuer, signature algorithm, and weak certificate checks may not be directly visible when TLS 1.3 encrypts certificate messages. Add TLS key-log ingestion or external certificate scan integration for complete certificate assurance.</p>
          </div>

          <h2>Evidence Appendix</h2>
          {evidence_table}

          <h2>Document Control</h2>
          {doc_table}

          <h2>Parser Log</h2>
          <div class="console">{parser_log}</div>

          <h2>Limitations</h2>
          <ul>{limitations}</ul>

          <p style="color:#64748b;font-size:12px">RBI CBOM Dashboard · Use results as evidence indicators. Certificate validation and full compliance sign-off may require TLS secrets, external certificate scans, endpoint configuration review, and manual validation.</p>
        </div>
      </div>
    </body>
    </html>
    """.format(
        css=css,
        quantum_readiness=esc(summary.get("Quantum Readiness", "Unknown")),
        overall_risk=esc(summary.get("Overall Risk", "Unknown")),
        tls_version=esc(summary.get("TLS Version", "Not observable")),
        cipher_suite=esc(summary.get("Cipher Suite", "Not observable")),
        key_exchange=esc(summary.get("Key Exchange", "Not observable")),
        executive_assessment=esc(
            summary.get(
                "Executive Assessment",
                "TLS posture and quantum readiness are assessed from visible PCAP handshake evidence."
            )
        ),
        board_risk=esc(
            summary.get(
                "Board Risk",
                "Classical key exchange may expose long-lived sensitive data to harvest-now-decrypt-later risk unless hybrid/PQC is negotiated."
            )
        ),
        findings_table=table(r.get("findings", [])),
        report_cbom_table=table(r.get("report_cbom", []), cbom_cols) if r.get("report_cbom") else table(r.get("cbom", [])),
        technical_cbom_table=table(r.get("cbom", []), technical_cols if r.get("cbom") and all(c in r["cbom"][0] for c in technical_cols) else None),
        flows_table=table(r.get("flows", []), flow_cols if r.get("flows") and all(c in r["flows"][0] for c in flow_cols) else None),
        compliance_table=table(r.get("compliance", []), comp_cols if r.get("compliance") and all(c in r["compliance"][0] for c in comp_cols) else None),
        recommendations_table=table(r.get("recommendations", []), rec_cols if r.get("recommendations") and all(c in r["recommendations"][0] for c in rec_cols) else None),
        evidence_table=table(r.get("evidence", [])),
        doc_table=table([doc]) if doc else "<p>No document metadata.</p>",
        parser_log=esc(parser_log),
        limitations=limitations
    )
    return html_doc


st.sidebar.title("🛡️ RBI CBOM")
target=st.sidebar.text_input("Target Application","RBI-Website")
unit=st.sidebar.text_input("Business Unit","Network")
classification=st.sidebar.selectbox("Classification",["CONFIDENTIAL","INTERNAL","RESTRICTED","PUBLIC"],0)
st.sidebar.markdown("### Capabilities")
st.sidebar.write("• TLS 1.3 supported_versions parser")
st.sidebar.write("• Server selected key share")
st.sidebar.write("• Client PQ/hybrid offer detection")
st.sidebar.write("• Report-grade CBOM")
st.sidebar.write("• Board-ready HTML export")

st.markdown("""<div class="hero"><div class="heroTop"><div><span class="badge bblue">RBI CBOM</span><span class="badge bviolet">Quantum Readiness</span><span class="badge">PCAP Evidence Mode</span><h1>RBI CBOM Quantum Readiness Dashboard</h1><p class="sub">Standalone executive dashboard for TLS version detection, cryptographic bill of materials, evidence-backed compliance mapping, and harvest-now-decrypt-later quantum-risk assessment from uploaded PCAP files.</p></div><div class="uploadBox"><b>Upload PCAP / PCAPNG</b><p class="muted">Built-in parser reads TLS ClientHello/ServerHello and final TLS 1.3 supported_versions.</p>""", unsafe_allow_html=True)
up=st.file_uploader("Upload PCAP / PCAPNG / CAP",type=["pcap","pcapng","cap"],label_visibility="collapsed")
st.markdown("</div></div></div>", unsafe_allow_html=True)
if not up:
    st.info("Upload a PCAP to generate the RBI CBOM report.")
    st.stop()
data=up.read()
report=analyze_bytes(data, up.name, {"target":target,"business_unit":unit,"classification":classification})
s=report["summary"]

st.markdown(f"""<div class="grid4"><div class="metric"><div class="label">Quantum Readiness</div><div class="val">{s['Quantum Readiness']}</div><div class="note">{badge('Transition stage' if s['Quantum Readiness']=='Partially Ready' else s['Overall Risk'])}</div></div><div class="metric"><div class="label">TLS Version</div><div class="val">{s['TLS Version']}</div><div class="note">{badge('Observed')}</div></div><div class="metric"><div class="label">Cipher Suite</div><div class="val" style="font-size:17px">{s['Cipher Suite']}</div><div class="note">{badge('Strong')}</div></div><div class="metric"><div class="label">Key Exchange</div><div class="val">{s['Key Exchange'].replace('secp256r1 / ','')}</div><div class="note">{badge('Classical ECC')}</div></div></div>""", unsafe_allow_html=True)
st.markdown(f"""<div class="two"><div class="card dark"><h3>Executive Assessment</h3><p>TLS 1.3 is used with modern protocol security. The selected cipher suite is {s['Cipher Suite']}. The final negotiated key exchange is {s['Key Exchange']}. The client appears to offer a hybrid post-quantum key share, but the final session does not show post-quantum or hybrid key exchange. Therefore, the endpoint should not be treated as fully quantum-safe based on this PCAP.</p><div class="kpis"><div class="kpi"><small>Target</small><strong>{s['Target']}</strong></div><div class="kpi"><small>Server IP</small><strong>{s['Server IP']}</strong></div><div class="kpi"><small>TLS Sessions</small><strong>{s['TLS Sessions']}</strong></div></div></div><div class="card risk"><h3>Board-Level Risk</h3><p>The endpoint may be secure by current classical TLS standards, but it is not fully quantum-safe because the final negotiated key exchange is classical or not PQ-observable.</p>{badge('Harvest-now-decrypt-later risk present')}</div></div>""", unsafe_allow_html=True)

# Visuals

# Board-style sections without chart clutter or tab layout

def first_existing_cols(df, cols):
    return [c for c in cols if c in df.columns]

cbom_df = pd.DataFrame(report.get("cbom", []))
findings_df = pd.DataFrame(report.get("findings", []))
flows_df = pd.DataFrame(report.get("flows", []))
compliance_df = pd.DataFrame(report.get("compliance", []))
recommendations_df = pd.DataFrame(report.get("recommendations", []))
evidence_df = pd.DataFrame(report.get("evidence", []))

# -------------------------
# Evidence-backed findings
# -------------------------
st.markdown('<div class="sectionHead"><div><h2>Evidence-Backed Findings</h2><p class="desc">Board-level findings with evidence type, confidence, business relevance, and remediation context.</p></div></div>', unsafe_allow_html=True)

cards = ""
if not findings_df.empty:
    for _, f in findings_df.head(6).iterrows():
        cards += f"""
        <div class='finding'>
          <div class='findingTop'>{badge(f.get('Evidence Type',''))}{badge(f.get('Confidence',''))}</div>
          <div class='title'>{f.get('Finding','')}</div>
          <div class='value'>{f.get('Value','')}</div>
          <div class='detail'>{f.get('Detail','')}</div>
          <div class='foot'><span>{f.get('Status','')}</span><span>{f.get('Evidence ID','')}</span></div>
        </div>
        """
else:
    cards = "<div class='card'><b>No high-risk findings from parsed evidence.</b><p class='muted'>This does not prove full compliance or full PQC readiness.</p></div>"
st.markdown(f"<div class='findings'>{cards}</div>", unsafe_allow_html=True)

# -------------------------
# Report CBOM
# -------------------------
st.markdown("""
<div class="boardSection">
  <h2>Report CBOM</h2>
  <p class="lead">Executive-friendly Cryptographic Bill of Materials showing only the most decision-relevant evidence from the PCAP.</p>
  <div class="insightGrid">
    <div class="insight"><small>Primary TLS Version</small><b>{tls}</b></div>
    <div class="insight"><small>Primary Cipher Suite</small><b>{cipher}</b></div>
    <div class="insight"><small>Final Key Exchange</small><b>{kex}</b></div>
  </div>
</div>
""".format(
    tls=s.get("TLS Version", "Not observable"),
    cipher=s.get("Cipher Suite", "Not observable"),
    kex=s.get("Key Exchange", "Not observable"),
), unsafe_allow_html=True)

# Prefer report_cbom if available; otherwise generate an executive CBOM from technical cbom
if "report_cbom" in report and report["report_cbom"]:
    report_cbom_df = pd.DataFrame(report["report_cbom"])
else:
    rows = []
    if not cbom_df.empty:
        primary = cbom_df.iloc[0].to_dict()
        rows = [
            {"Asset": "Protocol", "Value": primary.get("TLS Version", "Not observable"), "Evidence Type": primary.get("Evidence Type", "Observed"), "Confidence": primary.get("Confidence", ""), "Executive Note": "TLS version from visible handshake evidence."},
            {"Asset": "SNI", "Value": primary.get("SNI", "Not visible"), "Evidence Type": "Observed" if primary.get("SNI") else "Requires Manual Validation", "Confidence": "High" if primary.get("SNI") else "Low", "Executive Note": "Server name indication from ClientHello where visible."},
            {"Asset": "Server IP", "Value": str(primary.get("Destination", "")).split(":")[0], "Evidence Type": "Observed", "Confidence": "High", "Executive Note": "Destination endpoint in capture."},
            {"Asset": "Cipher Suite", "Value": primary.get("Cipher Suite", "Not observable"), "Evidence Type": "Observed", "Confidence": primary.get("Confidence", ""), "Executive Note": "Selected by ServerHello."},
            {"Asset": "Symmetric Encryption", "Value": primary.get("Symmetric Encryption", "Not observable"), "Evidence Type": "Inferred from cipher", "Confidence": "High", "Executive Note": "Symmetric encryption inferred from TLS cipher suite."},
            {"Asset": "Hash / KDF", "Value": primary.get("Hash / KDF", "Not observable"), "Evidence Type": "Inferred from cipher", "Confidence": "High", "Executive Note": "Hash/KDF family inferred from TLS cipher suite."},
            {"Asset": "Key Exchange", "Value": primary.get("Key Exchange", "Not observable"), "Evidence Type": primary.get("Evidence Type", "Observed"), "Confidence": primary.get("Confidence", ""), "Executive Note": "Final key exchange determines quantum readiness."},
            {"Asset": "Client Offered PQ Hybrid", "Value": primary.get("Client Offered PQ/Hybrid", "No"), "Evidence Type": "Observed / Strongly Inferred" if primary.get("Client Offered PQ/Hybrid") == "Yes" else "Observed", "Confidence": "Medium-High", "Executive Note": "Client offer alone does not prove final PQ security."},
            {"Asset": "Server Selected PQ Hybrid", "Value": "Yes" if "Hybrid" in str(primary.get("Quantum Readiness", "")) else "No", "Evidence Type": "Observed", "Confidence": "High", "Executive Note": "Final negotiated key exchange determines session quantum-readiness."},
            {"Asset": "Certificate Chain", "Value": "Not visible from encrypted TLS 1.3 handshake", "Evidence Type": "Requires Manual Validation", "Confidence": "High", "Executive Note": "Use TLS key logs or external certificate scan for certificate assurance."},
        ]
    report_cbom_df = pd.DataFrame(rows)

st.markdown('<div class="tableNote">Readable board table: sorted by asset, evidence type, confidence, and executive note. Technical packet details are kept in the Evidence section.</div>', unsafe_allow_html=True)
st.dataframe(
    report_cbom_df,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Asset": st.column_config.TextColumn("Asset", width="medium"),
        "Value": st.column_config.TextColumn("Value", width="medium"),
        "Evidence Type": st.column_config.TextColumn("Evidence Type", width="small"),
        "Confidence": st.column_config.TextColumn("Confidence", width="small"),
        "Executive Note": st.column_config.TextColumn("Executive Note", width="large"),
    }
)

# -------------------------
# Observed TLS Flows
# -------------------------
st.markdown("""
<div class="boardSection">
  <h2>Observed TLS Flows</h2>
  <p class="lead">Handshake-level view of HTTPS sessions visible in the PCAP. This is the evidence base for TLS version, cipher suite, SNI, and key-exchange claims.</p>
</div>
""", unsafe_allow_html=True)

if not flows_df.empty:
    flow_cols = first_existing_cols(flows_df, ["Source", "Destination", "SNI", "TLS", "Version Evidence", "Cipher", "KEX", "Quantum"])
    st.dataframe(
        flows_df[flow_cols],
        use_container_width=True,
        hide_index=True,
        column_config={
            "Source": st.column_config.TextColumn("Source", width="medium"),
            "Destination": st.column_config.TextColumn("Destination", width="medium"),
            "SNI": st.column_config.TextColumn("SNI", width="medium"),
            "TLS": st.column_config.TextColumn("TLS", width="small"),
            "Version Evidence": st.column_config.TextColumn("Version Evidence", width="large"),
            "Cipher": st.column_config.TextColumn("Cipher", width="large"),
            "KEX": st.column_config.TextColumn("KEX", width="medium"),
            "Quantum": st.column_config.TextColumn("Quantum", width="medium"),
        }
    )
else:
    st.info("No TLS flows parsed. Capture may not include visible ClientHello/ServerHello records.")

# -------------------------
# Compliance Mapping
# -------------------------
st.markdown("""
<div class="boardSection">
  <h2>Compliance Mapping</h2>
  <p class="lead">CISO, audit, and regulatory conversation view. These are evidence-backed indicators, not formal certification.</p>
</div>
""", unsafe_allow_html=True)

if not compliance_df.empty:
    comp_cols = first_existing_cols(compliance_df, ["Framework", "Status", "Evidence Type", "Executive Note"])
    st.dataframe(
        compliance_df[comp_cols],
        use_container_width=True,
        hide_index=True,
        column_config={
            "Framework": st.column_config.TextColumn("Framework", width="medium"),
            "Status": st.column_config.TextColumn("Status", width="medium"),
            "Evidence Type": st.column_config.TextColumn("Evidence Type", width="small"),
            "Executive Note": st.column_config.TextColumn("Executive Note", width="large"),
        }
    )

if not findings_df.empty:
    st.markdown("#### Policy Findings")
    finding_cols = first_existing_cols(findings_df, ["Finding", "Value", "Status", "Evidence Type", "Confidence", "Detail", "Endpoint"])
    st.dataframe(
        findings_df[finding_cols],
        use_container_width=True,
        hide_index=True,
        column_config={
            "Finding": st.column_config.TextColumn("Finding", width="medium"),
            "Value": st.column_config.TextColumn("Value", width="medium"),
            "Status": st.column_config.TextColumn("Status", width="small"),
            "Evidence Type": st.column_config.TextColumn("Evidence Type", width="small"),
            "Confidence": st.column_config.TextColumn("Confidence", width="small"),
            "Detail": st.column_config.TextColumn("Detail", width="large"),
            "Endpoint": st.column_config.TextColumn("Endpoint", width="medium"),
        }
    )

# -------------------------
# Roadmap
# -------------------------
st.markdown("""
<div class="boardSection">
  <h2>Quantum Remediation Roadmap</h2>
  <p class="lead">Staged roadmap for moving from classical TLS readiness to hybrid/PQ transition readiness.</p>
</div>
""", unsafe_allow_html=True)

road_cards = """
<div class="roadGrid">
  <div class="roadCard">
    <span class="badge bblue">0–30 Days</span>
    <h3>Evidence Baseline</h3>
    <ul>
      <li>Run repeated PCAP scans from multiple clients and networks.</li>
      <li>Add TLS key-log supported certificate validation for controlled tests.</li>
      <li>Create endpoint-level CBOM inventory for RBI-facing domains.</li>
    </ul>
  </div>
  <div class="roadCard">
    <span class="badge bblue">30–90 Days</span>
    <h3>Crypto-Agility Readiness</h3>
    <ul>
      <li>Track RSA, ECDSA, ECDHE, P-256, P-384, X25519, ML-KEM, and hybrid usage.</li>
      <li>Define internal policy for post-quantum transition readiness.</li>
      <li>Add server-side support checks for hybrid TLS key exchange.</li>
    </ul>
  </div>
  <div class="roadCard">
    <span class="badge bblue">90–180 Days</span>
    <h3>Hybrid PQ Pilot</h3>
    <ul>
      <li>Pilot X25519 + ML-KEM-768 hybrid key exchange in controlled environments.</li>
      <li>Measure latency, compatibility, and failure rates.</li>
      <li>Prepare board-level quantum-risk reporting and exception workflows.</li>
    </ul>
  </div>
</div>
"""
st.markdown(road_cards, unsafe_allow_html=True)

if not recommendations_df.empty:
    st.markdown("#### Action Register")
    rec_cols = first_existing_cols(recommendations_df, ["Timeline", "Priority", "Recommendation", "Executive Action", "Technical Action", "Verification"])
    st.dataframe(
        recommendations_df[rec_cols],
        use_container_width=True,
        hide_index=True,
        column_config={
            "Timeline": st.column_config.TextColumn("Timeline", width="small"),
            "Priority": st.column_config.TextColumn("Priority", width="small"),
            "Recommendation": st.column_config.TextColumn("Recommendation", width="medium"),
            "Executive Action": st.column_config.TextColumn("Executive Action", width="large"),
            "Technical Action": st.column_config.TextColumn("Technical Action", width="large"),
            "Verification": st.column_config.TextColumn("Verification", width="large"),
        }
    )

# -------------------------
# Evidence + Logs
# -------------------------
st.markdown("""
<div class="boardSection">
  <h2>Evidence + Logs</h2>
  <p class="lead">Technical evidence, parser notes, and limitations for validation. Keep this section for audit support and engineering follow-up.</p>
</div>
""", unsafe_allow_html=True)

ev_col, log_col = st.columns([2, 1])
with ev_col:
    if not evidence_df.empty:
        ev_cols = first_existing_cols(evidence_df, ["Evidence ID", "Source", "Destination", "Protocol", "Observed Value", "Defensibility", "Confidence", "PCAP SHA256"])
        st.dataframe(
            evidence_df[ev_cols],
            use_container_width=True,
            hide_index=True,
            column_config={
                "Evidence ID": st.column_config.TextColumn("Evidence ID", width="small"),
                "Source": st.column_config.TextColumn("Source", width="medium"),
                "Destination": st.column_config.TextColumn("Destination", width="medium"),
                "Protocol": st.column_config.TextColumn("Protocol", width="small"),
                "Observed Value": st.column_config.TextColumn("Observed Value", width="large"),
                "Defensibility": st.column_config.TextColumn("Defensibility", width="small"),
                "Confidence": st.column_config.TextColumn("Confidence", width="small"),
                "PCAP SHA256": st.column_config.TextColumn("PCAP SHA256", width="large"),
            }
        )
    else:
        st.info("No evidence records generated.")
with log_col:
    st.markdown("#### Parser Log")
    st.markdown(f"<div class='console'>{chr(10).join(report.get('parser_logs', []))}</div>", unsafe_allow_html=True)

    st.markdown("#### What This PCAP Cannot Prove Alone")
    for item in report.get("limitations", []):
        st.write("- " + item)

# -------------------------
# Exports
# -------------------------
st.markdown("""
<div class="boardSection">
  <h2>Exports</h2>
  <p class="lead">Download the board-ready report or machine-readable evidence for audit, governance, and technical follow-up.</p>
</div>
""", unsafe_allow_html=True)

html = html_report(report)
e1, e2, e3, e4 = st.columns(4)
with e1:
    st.download_button("Board HTML Report", html, "rbi_cbom_board_report.html", "text/html", use_container_width=True)
with e2:
    st.download_button("Full JSON", json.dumps(report, indent=2), "rbi_cbom_report.json", "application/json", use_container_width=True)
with e3:
    st.download_button("Report CBOM CSV", report_cbom_df.to_csv(index=False), "rbi_cbom_report.csv", "text/csv", use_container_width=True)
with e4:
    st.download_button("Technical CBOM CSV", cbom_df.to_csv(index=False), "rbi_cbom_technical.csv", "text/csv", use_container_width=True)



st.caption("RBI CBOM Dashboard · Built-in PCAP analysis · Use results as evidence indicators. Certificate validation and full compliance sign-off may require TLS secrets, external certificate scans, endpoint configuration review, and manual validation.")
