
import streamlit as st
import pandas as pd
import plotly.express as px
import struct, hashlib, json, uuid, re, io, tarfile, zipfile as zf
from pathlib import Path
from datetime import datetime
import xml.etree.ElementTree as ET

st.set_page_config(page_title="RBI QuBOM | Board Dashboard", page_icon="🛡️", layout="wide")

st.markdown("""
<style>
:root{--line:#e2e8f0;--muted:#64748b;--ink:#0f172a;--blue2:#eff6ff;--green2:#ecfdf5;--amber2:#fffbeb;--red2:#fef2f2;--violet2:#f5f3ff}
.main{background:linear-gradient(135deg,#f8fafc,#eef6ff 55%,#f7fafc)}
.block-container{max-width:1380px;padding-top:1.4rem}.hero{background:rgba(255,255,255,.96);border:1px solid var(--line);border-radius:34px;box-shadow:0 16px 40px rgba(15,23,42,.08);overflow:hidden;margin-bottom:20px}.heroTop{padding:34px;background:radial-gradient(circle at top right,#dbeafe,transparent 38%),linear-gradient(135deg,#fff,#f8fafc);display:grid;grid-template-columns:1fr 380px;gap:28px;align-items:center}.hero h1{font-size:46px;line-height:1.02;margin:12px 0;letter-spacing:-1.5px;color:#0f172a;font-weight:950}.sub{font-size:16px;line-height:1.65;color:#64748b;max-width:860px}.badge{display:inline-flex;align-items:center;border-radius:999px;border:1px solid var(--line);padding:7px 11px;font-size:12px;font-weight:850;background:#f8fafc;color:#334155;margin:2px}.bblue{background:#eff6ff;color:#1d4ed8;border-color:#bfdbfe}.bgreen{background:#ecfdf5;color:#047857;border-color:#a7f3d0}.bamber{background:#fffbeb;color:#b45309;border-color:#fde68a}.bred{background:#fef2f2;color:#b91c1c;border-color:#fecaca}.bviolet{background:#f5f3ff;color:#6d28d9;border-color:#ddd6fe}.uploadBox{background:white;border:1px solid var(--line);border-radius:26px;padding:18px;box-shadow:0 8px 22px rgba(15,23,42,.06)}.grid4{display:grid;grid-template-columns:repeat(4,1fr);gap:18px;margin:18px 0}.metric{background:white;border:1px solid var(--line);border-radius:26px;padding:22px;box-shadow:0 6px 18px rgba(15,23,42,.04)}.metric .label{font-size:11px;text-transform:uppercase;letter-spacing:.08em;color:#64748b;font-weight:900}.metric .val{font-size:24px;font-weight:950;margin-top:8px;word-break:break-word;color:#0f172a}.metric .note{margin-top:12px}.two{display:grid;grid-template-columns:2fr 1fr;gap:18px;margin-top:18px}.card{background:white;border:1px solid var(--line);border-radius:28px;padding:24px;box-shadow:0 8px 22px rgba(15,23,42,.04);margin-bottom:14px}.dark{background:#020617;color:white}.dark p,.dark .muted{color:#cbd5e1}.risk{background:#fffbeb;border-color:#fde68a}.risk h3,.risk p{color:#92400e}.kpis{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-top:18px}.kpi{border-radius:18px;background:rgba(255,255,255,.10);padding:14px}.kpi small{display:block;color:#cbd5e1}.kpi strong{display:block;margin-top:5px;color:white}.muted{color:#64748b}.sectionHead{display:flex;justify-content:space-between;gap:16px;align-items:flex-start;margin:28px 0 16px}.sectionHead h2{font-size:23px;margin:0;color:#0f172a}.desc{margin:7px 0 0;color:#64748b;line-height:1.6;font-size:14px}.console{font-family:monospace;background:#020617;color:#d1fae5;border-radius:20px;padding:16px;white-space:pre-wrap;font-size:12px;line-height:1.45;max-height:260px;overflow:auto}div[data-testid="stFileUploader"]{border:2px dashed #cbd5e1;border-radius:22px;padding:18px;background:#f8fafc}@media(max-width:1000px){.heroTop,.two,.grid4{grid-template-columns:1fr}.hero h1{font-size:34px}.kpis{grid-template-columns:1fr}}
</style>
""", unsafe_allow_html=True)

TLSVER={0x0300:'SSLv3',0x0301:'TLS 1.0',0x0302:'TLS 1.1',0x0303:'TLS 1.2',0x0304:'TLS 1.3'}
CIPH={0x1301:'TLS_AES_128_GCM_SHA256',0x1302:'TLS_AES_256_GCM_SHA384',0x1303:'TLS_CHACHA20_POLY1305_SHA256',0xC02F:'TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256',0xC030:'TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384',0xC02B:'TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256',0xC02C:'TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384',0x009C:'TLS_RSA_WITH_AES_128_GCM_SHA256',0x009D:'TLS_RSA_WITH_AES_256_GCM_SHA384',0x000A:'TLS_RSA_WITH_3DES_EDE_CBC_SHA',0x0005:'TLS_RSA_WITH_RC4_128_SHA'}
GROUP={0x001D:'x25519',0x0017:'secp256r1 / P-256',0x0018:'secp384r1 / P-384',0x0019:'secp521r1 / P-521',0x001E:'x448',0x11EC:'X25519 + ML-KEM-768 / Kyber-768 hybrid',0x6399:'X25519 + ML-KEM/Kyber hybrid draft',0x2F39:'ML-KEM-768 draft / experimental hybrid indicator'}
PQC_WORDS=['ml-kem','kyber','mlkem','dilithium','ml-dsa','slh-dsa','sphincs','hybrid','pqc']

def bclass(v):
    v=str(v).lower()
    if 'priority 1' in v or 'critical' in v or 'deprecated' in v or 'broken' in v: return 'bred'
    if 'priority 2' in v or 'vulnerable' in v or 'migration' in v or 'medium' in v: return 'bamber'
    if 'priority 3' in v or 'manual' in v or 'unknown' in v or 'validation' in v: return 'bviolet'
    if 'priority 4' in v or 'ready' in v or 'safe' in v or 'low' in v: return 'bgreen'
    return 'bblue'
def badge(v): return f"<span class='badge {bclass(v)}'>{v}</span>"
def sha256_bytes(b): return hashlib.sha256(b).hexdigest()
def u16(b,o,le=False): return b[o]|(b[o+1]<<8) if le else (b[o]<<8)|b[o+1]
def u32(b,o,le=False): return (b[o]|(b[o+1]<<8)|(b[o+2]<<16)|(b[o+3]<<24))&0xffffffff if le else ((b[o]<<24)|(b[o+1]<<16)|(b[o+2]<<8)|b[o+3])&0xffffffff
def ip4(b,o): return f'{b[o]}.{b[o+1]}.{b[o+2]}.{b[o+3]}'

def priority_definition():
    return pd.DataFrame([
        {'Priority':'Priority 1','Meaning':'Broken or deprecated today','Trigger':'Plaintext, SSL/TLS < 1.2, RC4, DES/3DES, MD5, SHA-1, DSA','Board Action':'Immediate remediation'},
        {'Priority':'Priority 2','Meaning':'Quantum migration required','Trigger':'Final negotiated classical asymmetric crypto: ECDHE, X25519, P-256/P-384, RSA, DHE, ECDSA','Board Action':'PQC migration and crypto-agility roadmap'},
        {'Priority':'Priority 3','Meaning':'Validation or crypto-agility required','Trigger':'Incomplete handshake, unknown selected group, symmetric-only review, client PQ offer not server-selected','Board Action':'Manual validation and configuration scan'},
        {'Priority':'Priority 4','Meaning':'PQC/hybrid ready or strong post-quantum symmetric margin','Trigger':'Server-selected ML-KEM/Kyber/hybrid PQC, or approved strong symmetric/hash context','Board Action':'Monitor and maintain evidence'}
    ])

# PCAP parser
def parse_pcap_packets(data):
    packets=[]; logs=[]
    if len(data)<24: return packets,['File too small']
    mbe=u32(data,0,False); mle=u32(data,0,True)
    if mbe==0x0a0d0d0a:
        off=0
        while off+12<=len(data):
            bt=u32(data,off,False); bl=u32(data,off+4,False)
            if bl<12 or off+bl>len(data): break
            if bt==0x00000006 and off+28<=len(data):
                caplen=u32(data,off+20,False); po=off+28
                if po+caplen<=off+bl: packets.append(data[po:po+caplen])
            off+=bl
        return packets,[f'Parsed PCAPNG enhanced packet blocks: {len(packets)}']
    if mbe==0xa1b2c3d4: le=False
    elif mbe==0xd4c3b2a1 or mle==0xa1b2c3d4: le=True
    else: return packets,[f'Unsupported capture format magic: 0x{mbe:x}']
    off=24
    while off+16<=len(data):
        incl=u32(data,off+8,le); off+=16
        if incl<=0 or off+incl>len(data): break
        packets.append(data[off:off+incl]); off+=incl
    return packets,[f'Parsed PCAP packets: {len(packets)}']

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
                if he>end: break
                body=payload[hp:he]
                if htype==1:
                    ch=parse_client_hello(body)
                    if ch: flow['client_hellos'].append(ch)
                elif htype==2:
                    sh=parse_server_hello(body)
                    if sh: flow['server_hellos'].append(sh)
                p=he
        o+=5+ln

def parse_client_hello(b):
    try:
        if len(b)<42: return None
        o=0; legacy=u16(b,o); o+=2+32
        sid_len=b[o]; o+=1+sid_len
        cs_len=u16(b,o); o+=2+cs_len
        comp_len=b[o]; o+=1+comp_len
        if o+2>len(b): return {'legacy':TLSVER.get(legacy,f'0x{legacy:04x}')}
        ext_len=u16(b,o); o+=2; end=min(o+ext_len,len(b))
        sni=''; groups=[]; pq_offer=False
        while o+4<=end:
            et=u16(b,o); el=u16(b,o+2); o+=4; e=min(o+el,end)
            if et==0 and o+2<=e:
                p=o+2
                while p+3<=e:
                    nt=b[p]; nl=u16(b,p+1); p+=3
                    if p+nl<=e and nt==0: sni=b[p:p+nl].decode('utf-8','ignore')
                    p+=nl
            elif et==10 and o+2<=e:
                gl=u16(b,o); p=o+2
                while p+2<=o+2+gl and p+2<=e:
                    g=u16(b,p); groups.append(GROUP.get(g,f'group 0x{g:04x}')); p+=2
            elif et==51 and o+2<=e:
                kl=u16(b,o); p=o+2
                while p+4<=e and p<o+2+kl:
                    g=u16(b,p); klen=u16(b,p+2); name=GROUP.get(g,f'group 0x{g:04x}')
                    groups.append(name)
                    if any(x in name.lower() for x in PQC_WORDS) or klen>1000: pq_offer=True
                    p+=4+klen
            o=e
        if any(any(x in g.lower() for x in PQC_WORDS) for g in groups): pq_offer=True
        return {'legacy':TLSVER.get(legacy,f'0x{legacy:04x}'),'sni':sni,'groups':groups,'pq_offer':pq_offer}
    except Exception: return None

def parse_server_hello(b):
    try:
        if len(b)<38: return None
        o=0; legacy=u16(b,o); o+=2+32
        sid_len=b[o]; o+=1+sid_len
        cipher=u16(b,o); o+=2; o+=1
        final_ver=TLSVER.get(legacy,f'0x{legacy:04x}'); evidence='legacy_version field'; group=''
        if o+2<=len(b):
            ext_len=u16(b,o); o+=2; end=min(o+ext_len,len(b))
            while o+4<=end:
                et=u16(b,o); el=u16(b,o+2); o+=4; e=min(o+el,end)
                if et==43 and el>=2:
                    v=u16(b,o); final_ver=TLSVER.get(v,f'0x{v:04x}'); evidence='ServerHello supported_versions extension'
                elif et==51 and el>=4:
                    g=u16(b,o); group=GROUP.get(g,f'group 0x{g:04x}')
                o=e
        return {'legacy_version':TLSVER.get(legacy,f'0x{legacy:04x}'),'tls_version':final_ver,'version_evidence':evidence,'cipher':CIPH.get(cipher,f'0x{cipher:04x}'),'group':group}
    except Exception: return None

def conn_key(src,sp,dst,dp): return tuple(sorted([(src,sp),(dst,dp)]))
def parse_packets_to_connections(packets):
    conns={}
    for p in packets:
        if len(p)<34: continue
        eth=u16(p,12); ipoff=14
        if eth==0x8100 and len(p)>=18: eth=u16(p,16); ipoff=18
        if eth!=0x0800 and len(p)>=16 and u16(p,14)==0x0800: eth=0x0800; ipoff=16
        if eth!=0x0800 or ipoff+20>len(p): continue
        ihl=(p[ipoff]&0xf)*4
        if p[ipoff+9]!=6: continue
        src=ip4(p,ipoff+12); dst=ip4(p,ipoff+16); toff=ipoff+ihl
        if toff+20>len(p): continue
        sp=u16(p,toff); dp=u16(p,toff+2); doff=((p[toff+12]>>4)&0xf)*4; po=toff+doff
        if po>=len(p): continue
        key=conn_key(src,sp,dst,dp)
        if key not in conns:
            if sp==443: conns[key]={'client_ip':dst,'client_port':dp,'server_ip':src,'server_port':sp,'client_hellos':[],'server_hellos':[]}
            else: conns[key]={'client_ip':src,'client_port':sp,'server_ip':dst,'server_port':dp,'client_hellos':[],'server_hellos':[]}
        parse_tls_records(p[po:], conns[key])
    return conns

def cipher_parts(cipher, ver):
    u=str(cipher).upper()
    kx='TLS 1.3 key schedule' if ver=='TLS 1.3' or 'TLS_AES' in u or 'CHACHA20' in u else 'ECDHE' if 'ECDHE' in u else 'DHE' if '_DHE_' in u else 'RSA static key exchange' if u.startswith('TLS_RSA') else 'Unknown'
    enc='AES-256-GCM' if 'AES_256_GCM' in u else 'AES-128-GCM' if 'AES_128_GCM' in u else 'ChaCha20-Poly1305' if 'CHACHA20' in u else '3DES' if '3DES' in u else 'DES' if 'DES' in u else 'RC4' if 'RC4' in u else 'Unknown'
    mac='SHA-384' if 'SHA384' in u else 'SHA-256' if 'SHA256' in u else 'SHA-1' if 'SHA' in u else 'MD5' if 'MD5' in u else 'AEAD/Unknown'
    return kx,enc,mac,(ver=='TLS 1.3' or kx in ['ECDHE','DHE'])

def priority_class(ver,cipher,kx,group,client_pq=False):
    text=' '.join([str(ver),str(cipher),str(kx),str(group)]).lower()
    if any(x in text for x in ['rc4','3des','des','md5','ssl','tls 1.0','tls 1.1']):
        return {'priority':'Priority 1','posture':'Broken / Deprecated','safe':'No','risk':'Critical','asset':group or kx or cipher,'note':'Cryptography is deprecated or classically weak today. Immediate remediation required.'}
    if any(x in text for x in PQC_WORDS):
        return {'priority':'Priority 4','posture':'PQC/Hybrid Ready','safe':'Yes','risk':'Low','asset':group or 'Hybrid PQC','note':'Server-selected hybrid/PQC key exchange was observed.'}
    if group or ver=='TLS 1.3' or any(x in text for x in ['ecdhe','ecdh','x25519','x448','secp','p-256','p-384','rsa','dhe','diffie','ecdsa']):
        if ver=='TLS 1.3' and not group:
            return {'priority':'Priority 3','posture':'Validation Required','safe':'No','risk':'Unknown','asset':kx,'note':'TLS 1.3 is confirmed, but server-selected key-share group is not visible. Validate endpoint configuration; do not claim PQC readiness.'}
        return {'priority':'Priority 2','posture':'Quantum Migration Required','safe':'No','risk':'Medium','asset':group or kx,'note':'Final negotiated key exchange is classical asymmetric cryptography, which is vulnerable to Shor’s algorithm at Q-Day.' + (' Client offered PQ/hybrid, but server did not select it.' if client_pq else '')}
    return {'priority':'Priority 3','posture':'Validation Required','safe':'No','risk':'Unknown','asset':kx or 'Unknown','note':'Insufficient handshake evidence to classify the final cryptographic posture.'}

def analyze_pcap_bytes(data, filename, meta):
    packets,logs=parse_pcap_packets(data); conns=parse_packets_to_connections(packets); pcap_hash=sha256_bytes(data)
    cbom=[]; flows=[]; findings=[]; evidence=[]; algos={}
    for key,c in conns.items():
        if not c['server_hellos']: continue
        sh=sorted(c['server_hellos'], key=lambda x:(1 if x.get('group') else 0, 1 if x.get('tls_version')=='TLS 1.3' else 0), reverse=True)[0]
        ch=c['client_hellos'][-1] if c['client_hellos'] else {}; client_pq=bool(ch.get('pq_offer')); group=sh.get('group','')
        kx,enc,mac,fs=cipher_parts(sh['cipher'], sh['tls_version']); q=priority_class(sh['tls_version'],sh['cipher'],kx,group,client_pq)
        flags=[]
        if q['priority']=='Priority 1': flags.append('DEPRECATED_OR_BROKEN_CRYPTO')
        if q['priority']=='Priority 2': flags.append('QUANTUM_VULNERABLE_ASYMMETRIC')
        if q['priority']=='Priority 3': flags.append('MANUAL_VALIDATION_REQUIRED')
        if client_pq and not any(x in group.lower() for x in PQC_WORDS): flags.append('CLIENT_PQ_OFFER_SERVER_NOT_PQ')
        ev=f'EVD-TLS-{len(evidence)+1:04d}'
        rec={'CBOM ID':f'CBOM-{len(cbom)+1:06d}','Asset':q['asset'],'Protocol':'TLS','TLS Version':sh['tls_version'],'TLS Version Evidence':sh['version_evidence'],'Cipher Suite':sh['cipher'],'Symmetric Encryption':enc,'Hash / KDF':mac,'Key Exchange':group or kx,'Client Offered PQ Hybrid':'Yes' if client_pq else 'No','Client Offered Groups':', '.join(ch.get('groups',[])[:8]),'Server Selected PQ Hybrid':'Yes' if any(x in group.lower() for x in PQC_WORDS) else 'No','Forward Secrecy':fs,'Quantum Posture':q['posture'],'Quantum Safe':q['safe'],'Priority':q['priority'],'Risk':q['risk'],'Source':f"{c['client_ip']}:{c['client_port']}",'Destination':f"{c['server_ip']}:{c['server_port']}",'SNI':ch.get('sni',''),'Confidence':'High' if group else 'Medium','Executive Note':q['note'],'Recommended Migration':'Plan hybrid/PQC migration using ML-KEM for key establishment and ML-DSA/SLH-DSA for signatures where supported.' if q['priority']=='Priority 2' else 'Validate configuration and maintain crypto-agility.' if q['priority']=='Priority 3' else 'Maintain monitoring.','Policy Flags':', '.join(flags),'Evidence ID':ev}
        cbom.append(rec); flows.append({'Source':rec['Source'],'Destination':rec['Destination'],'SNI':rec['SNI'],'TLS':rec['TLS Version'],'Cipher':rec['Cipher Suite'],'KEX':rec['Key Exchange'],'Priority':rec['Priority'],'Quantum Posture':rec['Quantum Posture']})
        evidence.append({'Evidence ID':ev,'Source':rec['Source'],'Destination':rec['Destination'],'Protocol':'TLS','Observed Value':f"{rec['TLS Version']} via {rec['TLS Version Evidence']} / {rec['Cipher Suite']} / {rec['Key Exchange']}",'Confidence':rec['Confidence'],'PCAP SHA256':pcap_hash})
        algos.setdefault(q['asset'],{'Algorithm':q['asset'],'Quantum Posture':q['posture'],'Priority':q['priority'],'Recommended Migration':rec['Recommended Migration'],'Connections':0,'Confidence':rec['Confidence']})['Connections']+=1
        for flag in flags:
            title={'QUANTUM_VULNERABLE_ASYMMETRIC':'Quantum-vulnerable asymmetric cryptography','CLIENT_PQ_OFFER_SERVER_NOT_PQ':'Client PQ offer seen, but server did not negotiate PQ/hybrid','MANUAL_VALIDATION_REQUIRED':'Manual validation required for final key exchange','DEPRECATED_OR_BROKEN_CRYPTO':'Deprecated or broken cryptography observed'}.get(flag,flag)
            findings.append({'Finding':title,'Value':rec['Asset'],'Status':rec['Risk'],'Confidence':rec['Confidence'],'Detail':rec['Executive Note'],'Endpoint':rec['Destination'],'Priority':rec['Priority']})
    report_cbom=[]
    if cbom:
        p=cbom[0]
        findings=[{'Finding':'TLS Version Negotiated','Value':p['TLS Version'],'Status':'Observed','Confidence':'High','Detail':'TLS version is taken from final ServerHello evidence; TLS 1.3 supported_versions overrides legacy version.','Endpoint':p['Destination'],'Priority':p['Priority']},{'Finding':'Final Key Exchange','Value':p['Key Exchange'],'Status':p['Quantum Posture'],'Confidence':p['Confidence'],'Detail':'Final server-selected key exchange determines quantum readiness.','Endpoint':p['Destination'],'Priority':p['Priority']},{'Finding':'Server PQ Negotiation','Value':p['Server Selected PQ Hybrid'],'Status':'Negotiated' if p['Server Selected PQ Hybrid']=='Yes' else 'Not negotiated','Confidence':'High','Detail':'Client PQ offer does not make the session quantum-safe unless server selected hybrid/PQC.','Endpoint':p['Destination'],'Priority':p['Priority']}]+findings
        report_cbom=[{'Asset':'File','Value':filename,'Confidence':'High','Executive Note':'Input analyzed by RBI QuBOM parser'},{'Asset':'Protocol','Value':p['TLS Version'],'Confidence':'High','Executive Note':'Final negotiated TLS version from ServerHello evidence'},{'Asset':'SNI','Value':p['SNI'] or 'Not visible','Confidence':'High' if p['SNI'] else 'Low','Executive Note':'Server Name Indication from ClientHello'},{'Asset':'Server IP','Value':p['Destination'].split(':')[0],'Confidence':'High','Executive Note':'Destination endpoint in capture'},{'Asset':'Cipher Suite','Value':p['Cipher Suite'],'Confidence':'High','Executive Note':'Final selected cipher suite from ServerHello'},{'Asset':'Key Exchange','Value':p['Key Exchange'],'Confidence':p['Confidence'],'Executive Note':'Final server-selected key exchange, not client offer'},{'Asset':'Client Offered PQ Hybrid','Value':p['Client Offered PQ Hybrid'],'Confidence':'Medium','Executive Note':'Client capability indicator only'},{'Asset':'Server Selected PQ Hybrid','Value':p['Server Selected PQ Hybrid'],'Confidence':'High','Executive Note':'Determines whether the session is PQC/hybrid ready'}]
    qv=sum(1 for r in cbom if r['Priority']=='Priority 2'); p1=sum(1 for r in cbom if r['Priority']=='Priority 1'); p3=sum(1 for r in cbom if r['Priority']=='Priority 3'); p4=sum(1 for r in cbom if r['Priority']=='Priority 4')
    overall='Priority 1' if p1 else 'Priority 2' if qv else 'Priority 3' if p3 or not cbom else 'Priority 4'
    posture='Broken/Deprecated' if p1 else 'Quantum Migration Required' if qv else 'Validation Required' if p3 or not cbom else 'PQC/Hybrid Ready'
    primary=cbom[0] if cbom else {}
    roadmap=[{'Phase':'0–30 Days','Title':'Evidence Baseline','Actions':'Repeat PCAP scans; validate TLS and certificate configuration; establish endpoint CBOM ownership'},{'Phase':'30–90 Days','Title':'Crypto-Agility Readiness','Actions':'Inventory classical asymmetric algorithms; define PQC transition policy; identify vendor/application support for hybrid TLS'},{'Phase':'90–180 Days','Title':'Hybrid PQ Pilot','Actions':'Pilot X25519 + ML-KEM-768 or equivalent hybrid key exchange; measure compatibility and performance'}]
    return {'document':{'Tool Name':'RBI QuBOM','Target Application':meta.get('target','Application'),'Scan ID':str(uuid.uuid4()),'Assessment Date':datetime.now().strftime('%B %d, %Y'),'Scanner Version':'RBI QuBOM v9','Total Packets':len(packets),'PCAP SHA256':pcap_hash},'summary':{'Quantum Posture':posture,'Overall Priority':overall,'TLS Version':primary.get('TLS Version','Not observable'),'Cipher Suite':primary.get('Cipher Suite','Not observable'),'Key Exchange':primary.get('Key Exchange','Not observable'),'Target':primary.get('SNI',meta.get('target','Application')) if primary else meta.get('target','Application'),'TLS Sessions':len(cbom),'Priority 1':p1,'Priority 2':qv,'Priority 3':p3,'Priority 4':p4},'cbom':cbom,'report_cbom':report_cbom,'findings':findings,'flows':flows,'evidence':evidence,'algorithms':list(algos.values()),'compliance':[{'Framework':'NIST PQC Migration','Status':'PQC migration required' if qv else 'Monitor','Executive Note':'Classical ECC/RSA/DHE are Shor-vulnerable unless hybrid/PQ is negotiated.'},{'Framework':'RBI / Financial Sector Cyber Resilience','Status':'Board roadmap required' if qv else 'Technical indicator','Executive Note':'Board-level quantum-risk roadmap should be documented for critical endpoints.'},{'Framework':'ISO 27001 / 27002','Status':'Crypto inventory required','Executive Note':'Maintain CBOM evidence for cryptographic asset governance.'}],'roadmap':roadmap,'parser_logs':logs+[f'TLS sessions identified: {len(cbom)}','Stable priority model applied: P1 broken/deprecated, P2 Shor-vulnerable classical asymmetric, P3 validation required, P4 PQC/hybrid ready.'],'limitations':['Certificate chain, certificate expiry, SAN validation, issuer, signature algorithm, and weak certificate checks may require TLS key logs or external certificate scan integration.','This dashboard analyzes only visible traffic in the uploaded PCAP.','Compliance results are evidence indicators, not formal certification.']}

# Source code
SOURCE_EXTENSIONS={'.py','.js','.jsx','.ts','.tsx','.java','.go','.rs','.cs','.cpp','.c','.h','.hpp','.php','.rb','.kt','.swift','.scala','.sh','.ps1','.yml','.yaml','.json','.xml','.toml','.gradle','.properties','.conf','.ini','.env','.lock','.txt','.md'}
MANIFESTS={'package.json','package-lock.json','yarn.lock','pnpm-lock.yaml','requirements.txt','pyproject.toml','poetry.lock','Pipfile','Pipfile.lock','pom.xml','build.gradle','build.gradle.kts','gradle.lockfile','go.mod','go.sum','Cargo.toml','Cargo.lock','composer.json','composer.lock','Gemfile','Gemfile.lock','packages.config','Directory.Packages.props'}
CRYPTO_PATTERNS=[('RSA',r'\bRSA\b|RS256|RS384|RS512|generate_private_key|PKCS1|PKCS8'),('DSA',r'\bDSA\b|dsa\.'),('ECDSA/ECDH',r'\bECDSA\b|\bECDH\b|secp256r1|prime256v1|P-256|secp384r1|P-384|secp521r1|P-521|x25519|x448|elliptic|ecdh|ecdsa'),('Diffie-Hellman',r'DiffieHellman|Diffie-Hellman|DHParameter|DHE|dhparam'),('AES',r'\bAES\b|AESGCM|AES-CBC|AES_128|AES_256|createCipheriv'),('3DES/DES',r'\bDES\b|3DES|DESede|TripleDES'),('RC4',r'\bRC4\b|ARC4'),('MD5',r'\bMD5\b|md5\('),('SHA-1',r'SHA1|SHA-1|sha1\('),('SHA-256',r'SHA256|SHA-256|sha256\('),('SHA-384/512',r'SHA384|SHA-384|SHA512|SHA-512|sha384|sha512'),('TLS 1.0/1.1',r'TLSv1\.0|TLSv1\.1|PROTOCOL_TLSv1\b|PROTOCOL_TLSv1_1'),('TLS 1.2',r'TLSv1\.2|PROTOCOL_TLSv1_2'),('TLS 1.3',r'TLSv1\.3|PROTOCOL_TLSv1_3'),('OpenSSL',r'openssl|OpenSSL|libssl'),('Java Crypto',r'javax\.crypto|java\.security|Cipher\.getInstance|KeyPairGenerator|MessageDigest'),('Python cryptography',r'cryptography\.|Crypto\.|hashlib|ssl\.|PyCryptodome'),('Node crypto',r"require\(['\"]crypto['\"]\)|from ['\"]crypto['\"]|crypto\.subtle|webcrypto"),('PQC/Hybrid',r'ML-KEM|Kyber|Dilithium|ML-DSA|SLH-DSA|SPHINCS|Falcon|post-quantum|pqc|hybrid')]
def safe_text(data,limit=2_000_000):
    try: return data[:limit].decode('utf-8','ignore') if isinstance(data,bytes) else str(data)[:limit]
    except Exception: return ''
def archive_files(uploaded):
    name=uploaded.name; raw=uploaded.getvalue(); lower=name.lower(); files=[]; errors=[]
    try:
        if lower.endswith('.zip'):
            with zf.ZipFile(io.BytesIO(raw),'r') as z:
                for info in z.infolist():
                    if info.is_dir() or info.file_size>3_000_000: continue
                    files.append((info.filename,z.read(info.filename)))
        elif lower.endswith(('.tar','.tar.gz','.tgz','.gz')):
            mode='r:gz' if lower.endswith(('.tar.gz','.tgz','.gz')) else 'r:'
            with tarfile.open(fileobj=io.BytesIO(raw),mode=mode) as t:
                for m in t.getmembers():
                    if not m.isfile() or m.size>3_000_000: continue
                    f=t.extractfile(m)
                    if f: files.append((m.name,f.read()))
        else: files.append((name,raw))
    except Exception as e:
        errors.append(f'Archive parse error: {e}. If this is not an archive, upload a ZIP/TAR or single manifest/source file.')
        files.append((name,raw))
    return files,errors
def is_manifest(path):
    base=path.split('/')[-1]
    return base in MANIFESTS or base.endswith('.csproj')
def parse_pkg_json(path,text):
    rows=[]
    try:
        data=json.loads(text)
        for scope in ['dependencies','devDependencies','peerDependencies','optionalDependencies']:
            for name,ver in (data.get(scope,{}) or {}).items(): rows.append({'Component':name,'Version':str(ver),'Ecosystem':'npm','Scope':scope,'Source File':path,'purl-like ID':f'pkg:npm/{name}@{ver}'})
    except Exception: pass
    return rows
def parse_req(path,text):
    rows=[]
    for line in text.splitlines():
        s=line.strip()
        if not s or s.startswith('#') or s.startswith('-'): continue
        m=re.match(r'([A-Za-z0-9_.\-]+)\s*(==|>=|<=|~=|>|<)?\s*([^;#\s]+)?',s)
        if m:
            name=m.group(1); ver=m.group(3) or 'unspecified'; rows.append({'Component':name,'Version':ver,'Ecosystem':'PyPI','Scope':'runtime','Source File':path,'purl-like ID':f'pkg:pypi/{name}@{ver}'})
    return rows
def parse_pom(path,text):
    rows=[]
    try:
        root=ET.fromstring(text)
        for dep in root.findall('.//{*}dependency'):
            gid=dep.findtext('{*}groupId') or ''; aid=dep.findtext('{*}artifactId') or ''; ver=dep.findtext('{*}version') or 'unspecified'; scope=dep.findtext('{*}scope') or 'runtime'
            if aid: rows.append({'Component':f'{gid}:{aid}' if gid else aid,'Version':ver,'Ecosystem':'Maven','Scope':scope,'Source File':path,'purl-like ID':f'pkg:maven/{gid}/{aid}@{ver}'})
    except Exception: pass
    return rows
def parse_go(path,text):
    rows=[]
    for line in text.splitlines():
        s=line.strip()
        if not s or s.startswith('//') or s in ['require (',')']: continue
        if s.startswith('require '): s=s.replace('require ','',1).strip()
        parts=s.split()
        if len(parts)>=2 and '.' in parts[0]: rows.append({'Component':parts[0],'Version':parts[1],'Ecosystem':'Go','Scope':'runtime','Source File':path,'purl-like ID':f'pkg:golang/{parts[0]}@{parts[1]}'})
    return rows
def parse_cargo(path,text):
    rows=[]; indep=False; scope='runtime'
    for line in text.splitlines():
        s=line.strip()
        if s.startswith('['): indep=s in ['[dependencies]','[dev-dependencies]','[build-dependencies]']; scope=s.strip('[]'); continue
        if indep and '=' in s and not s.startswith('#'):
            name,ver=s.split('=',1); name=name.strip(); ver=ver.strip().strip('"').strip("'")
            if name: rows.append({'Component':name,'Version':ver,'Ecosystem':'Cargo','Scope':scope,'Source File':path,'purl-like ID':f'pkg:cargo/{name}@{ver}'})
    return rows
def parse_manifest(path,text):
    base=path.split('/')[-1]
    if base=='package.json': return parse_pkg_json(path,text)
    if base=='requirements.txt': return parse_req(path,text)
    if base=='pom.xml': return parse_pom(path,text)
    if base=='go.mod': return parse_go(path,text)
    if base=='Cargo.toml': return parse_cargo(path,text)
    if base=='pyproject.toml': return parse_req(path,'\n'.join(re.findall(r'["\']([A-Za-z0-9_.\-]+[<>=!~]*[^"\']*)["\']',text)))
    return []
def crypto_status(name):
    if name in {'MD5','SHA-1','RC4','3DES/DES','TLS 1.0/1.1','DSA'}: return 'Deprecated / Critical','Priority 1'
    if name in {'RSA','ECDSA/ECDH','Diffie-Hellman'}: return 'Quantum Vulnerable','Priority 2'
    if name=='PQC/Hybrid': return 'PQC / Hybrid Indicator','Priority 4'
    return 'Modern / Review Required','Priority 3'
def source_cbom(files):
    rows=[]; findings=[]
    for path,raw in files:
        ext=Path(path).suffix.lower()
        if ext not in SOURCE_EXTENSIONS and not is_manifest(path): continue
        text=safe_text(raw)
        for algo,pattern in CRYPTO_PATTERNS:
            matches=list(re.finditer(pattern,text,flags=re.IGNORECASE))
            if not matches: continue
            status,priority=crypto_status(algo); lines=[text[:m.start()].count('\n')+1 for m in matches[:5]]
            action='Replace deprecated algorithm immediately.' if priority=='Priority 1' else 'Plan PQC/hybrid migration and crypto-agility.' if priority=='Priority 2' else 'Validate implementation and approved configuration.'
            rows.append({'Crypto Asset':algo,'Status':status,'Priority':priority,'Source File':path,'Occurrences':len(matches),'Line Hints':', '.join(map(str,lines)),'Recommended Action':action})
            findings.append({'Finding':f'{algo} detected in source','Status':status,'Priority':priority,'File':path,'Action':action})
    return rows,findings
def analyze_source(uploaded,target):
    files,errors=archive_files(uploaded); sbom=[]; manifests=[]
    for path,raw in files:
        if is_manifest(path): manifests.append(path); sbom.extend(parse_manifest(path,safe_text(raw)))
    seen=set(); dedup=[]
    for r in sbom:
        key=(r.get('Component'),r.get('Version'),r.get('Ecosystem'),r.get('Source File'))
        if key not in seen: seen.add(key); dedup.append(r)
    sbom=dedup; scbom,findings=source_cbom(files)
    summary={'Target':target,'Files Scanned':len(files),'Manifest Files Found':len(manifests),'SBOM Components':len(sbom),'Source CBOM Findings':len(scbom),'Critical Crypto Findings':sum(1 for r in scbom if r['Priority']=='Priority 1'),'Quantum-Vulnerable Findings':sum(1 for r in scbom if r['Priority']=='Priority 2'),'Parsing Notes':'; '.join(errors) if errors else 'No parsing errors'}
    integrity={'Tool':'RBI QuBOM','Generated At':datetime.now().isoformat(),'Source Filename':uploaded.name,'Archive SHA256':hashlib.sha256(uploaded.getvalue()).hexdigest(),'SBOM Components':len(sbom),'CBOM Findings':len(scbom)}
    standard={'bomFormat':'RBI-QuBOM-Standard','specVersion':'1.0','serialNumber':'urn:uuid:'+str(uuid.uuid4()),'metadata':{'timestamp':datetime.now().isoformat(),'tool':'RBI QuBOM','component':{'name':target,'type':'application'}},'components':[{'type':'library','name':r['Component'],'version':r['Version'],'ecosystem':r['Ecosystem'],'scope':r['Scope'],'purl':r['purl-like ID'],'evidence':{'source':r['Source File']}} for r in sbom],'cryptography':scbom}
    spdx={'spdxVersion':'SPDX-2.3-like','name':target,'documentNamespace':'https://rbi-qubom.local/spdx/'+str(uuid.uuid4()),'creationInfo':{'created':datetime.now().isoformat(),'creators':['Tool: RBI QuBOM']},'packages':[{'name':r['Component'],'versionInfo':r['Version'],'supplier':'NOASSERTION','downloadLocation':'NOASSERTION','externalRefs':[{'referenceType':'purl','referenceLocator':r['purl-like ID']}],'sourceFile':r['Source File']} for r in sbom]}
    return {'summary':summary,'manifests':manifests,'sbom':sbom,'source_cbom':scbom,'source_findings':findings,'integrity':integrity,'standard_bom_json':standard,'spdx_like_json':spdx}


def _html_escape(x):
    import html
    return html.escape(str(x if x is not None else ""))

def _board_table(rows, columns=None):
    if not rows:
        return "<p class='muted'>No records.</p>"
    if isinstance(rows, dict):
        rows = [rows]
    if columns is None:
        columns = list(rows[0].keys())
    head = "".join("<th>{}</th>".format(_html_escape(c)) for c in columns)
    body = []
    for r in rows:
        cells = "".join("<td>{}</td>".format(_html_escape(r.get(c, ""))) for c in columns)
        body.append("<tr>{}</tr>".format(cells))
    return "<div class='tableWrap'><table><thead><tr>{}</tr></thead><tbody>{}</tbody></table></div>".format(head, "".join(body))

def _board_css():
    return """
    <style>
    :root{--bg:#f7fafc;--card:#fff;--ink:#0f172a;--muted:#64748b;--line:#e2e8f0;--blue:#2563eb;--blue2:#eff6ff;--green2:#ecfdf5;--amber2:#fffbeb;--red2:#fef2f2;--violet2:#f5f3ff;--shadow:0 16px 40px rgba(15,23,42,.08)}
    body{margin:0;background:linear-gradient(135deg,#f8fafc,#eef6ff 55%,#f7fafc);font-family:Inter,Arial,sans-serif;color:var(--ink)}
    .wrap{max-width:1220px;margin:auto;padding:28px}
    .hero{background:rgba(255,255,255,.94);border:1px solid var(--line);border-radius:34px;box-shadow:var(--shadow);overflow:hidden}
    .heroTop{padding:34px;background:radial-gradient(circle at top right,#dbeafe,transparent 38%),linear-gradient(135deg,#fff,#f8fafc);border-bottom:1px solid var(--line)}
    h1{font-size:46px;line-height:1.02;margin:12px 0;letter-spacing:-1.5px}
    h2{font-size:25px;margin:34px 0 14px;letter-spacing:-.5px}
    h3{font-size:20px;margin:0 0 12px}
    p{line-height:1.58}
    .sub{font-size:16px;line-height:1.65;color:var(--muted);max-width:900px}
    .badge{display:inline-flex;border-radius:999px;border:1px solid var(--line);padding:7px 11px;font-size:12px;font-weight:800;background:#f8fafc;color:#334155;margin:2px}
    .bblue{background:#eff6ff;color:#1d4ed8;border-color:#bfdbfe}.bgreen{background:#ecfdf5;color:#047857;border-color:#a7f3d0}.bamber{background:#fffbeb;color:#b45309;border-color:#fde68a}.bred{background:#fef2f2;color:#b91c1c;border-color:#fecaca}.bviolet{background:#f5f3ff;color:#6d28d9;border-color:#ddd6fe}
    .grid4{display:grid;grid-template-columns:repeat(4,1fr);gap:18px;padding:28px}
    .metric{background:white;border:1px solid var(--line);border-radius:26px;padding:22px;box-shadow:0 6px 18px rgba(15,23,42,.04)}
    .metric small{display:block;font-size:11px;text-transform:uppercase;letter-spacing:.08em;color:#64748b;font-weight:900}
    .metric b{display:block;font-size:23px;margin-top:8px;word-break:break-word}
    .section{padding:0 28px 28px}
    .two{display:grid;grid-template-columns:2fr 1fr;gap:18px}
    .three{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}
    .card{background:white;border:1px solid var(--line);border-radius:28px;padding:24px;box-shadow:0 8px 22px rgba(15,23,42,.04);margin-bottom:18px}
    .dark{background:#020617;color:white}.dark p{color:#cbd5e1}
    .risk{background:#fffbeb;border-color:#fde68a;color:#92400e}
    .warn{background:#fef2f2;border-color:#fecaca;color:#991b1b}
    .finding{background:white;border:1px solid var(--line);border-radius:24px;padding:18px;min-height:155px}
    .title{font-size:13px;color:#64748b;font-weight:900}.value{font-size:18px;font-weight:950;margin-top:6px;color:#0f172a}.detail{font-size:13px;line-height:1.55;color:#475569;margin-top:12px}
    .tableWrap{border:1px solid var(--line);border-radius:24px;overflow:auto;background:white;box-shadow:0 8px 22px rgba(15,23,42,.04)}
    table{width:100%;border-collapse:collapse;background:white;font-size:12px}
    th{background:#f1f5f9;color:#475569;text-align:left;text-transform:uppercase;font-size:11px;letter-spacing:.08em;padding:14px}
    td{border-top:1px solid #f1f5f9;padding:13px;vertical-align:top}
    .console{font-family:monospace;background:#020617;color:#d1fae5;border-radius:20px;padding:16px;white-space:pre-wrap;font-size:12px;line-height:1.45}
    .muted{color:#64748b}
    @media print{body{background:white}.wrap{padding:0}.hero,.card,.metric,.finding{box-shadow:none}.section{break-inside:avoid}}
    @media(max-width:900px){.grid4,.two,.three{grid-template-columns:1fr}h1{font-size:34px}}
    </style>
    """

def html_report(report):
    s = report.get("summary", {})
    doc = report.get("document", {})
    parser_log = "\n".join(str(x) for x in report.get("parser_logs", []))
    limitations = "".join("<li>{}</li>".format(_html_escape(x)) for x in report.get("limitations", []))

    priority = s.get("Overall Priority", s.get("Overall Risk", "Unknown"))
    posture = s.get("Quantum Posture", s.get("Quantum Readiness", "Unknown"))
    tls_version = s.get("TLS Version", "Not observable")
    cipher = s.get("Cipher Suite", "Not observable")
    kex = s.get("Key Exchange", "Not observable")

    findings = report.get("findings", [])[:6]
    if findings:
        finding_cards = "".join(
            "<div class='finding'><span class='badge bamber'>{priority}</span><div class='title'>{finding}</div><div class='value'>{value}</div><div class='detail'>{detail}</div></div>".format(
                priority=_html_escape(f.get("Priority", f.get("Status", ""))),
                finding=_html_escape(f.get("Finding", "")),
                value=_html_escape(f.get("Value", "")),
                detail=_html_escape(f.get("Detail", f.get("Action", "")))
            )
            for f in findings
        )
    else:
        finding_cards = "<div class='card'><b>No high-risk findings generated from parsed evidence.</b><p class='muted'>This does not prove full compliance or full PQC readiness.</p></div>"

    html_doc = """
    <!doctype html><html><head><meta charset="utf-8"><title>RBI QuBOM Board Report</title>{css}</head>
    <body><div class="wrap"><main class="hero">
      <div class="heroTop">
        <span class="badge bblue">RBI QuBOM</span><span class="badge bviolet">Board Report</span><span class="badge">PCAP Evidence Mode</span>
        <h1>RBI QuBOM Quantum Readiness Dashboard</h1>
        <p class="sub">Executive board-ready report for TLS discovery, cryptographic bill of materials, compliance mapping, and harvest-now-decrypt-later quantum-risk assessment from uploaded PCAP files.</p>
      </div>

      <div class="grid4">
        <div class="metric"><small>Quantum Posture</small><b>{posture}</b><span class="badge bamber">{priority}</span></div>
        <div class="metric"><small>TLS Version</small><b>{tls_version}</b><span class="badge bgreen">Observed</span></div>
        <div class="metric"><small>Cipher Suite</small><b style="font-size:16px">{cipher}</b><span class="badge bgreen">Selected by Server</span></div>
        <div class="metric"><small>Key Exchange</small><b>{kex}</b><span class="badge bamber">Final KEX</span></div>
      </div>

      <section class="section">
        <div class="two">
          <div class="card dark">
            <h3>Executive Assessment</h3>
            <p>RBI QuBOM analyzed the uploaded PCAP and identified {tls_sessions} TLS session(s). The final posture is <b>{posture}</b> with <b>{priority}</b>. Priority is based on final selected cryptographic evidence, not a changing score.</p>
          </div>
          <div class="card risk">
            <h3>Board-Level Risk</h3>
            <p>Classical ECDHE, X25519, P-256, RSA, DHE, and ECDSA remain quantum-vulnerable unless the server actually negotiates hybrid/PQC key exchange.</p>
            <span class="badge bamber">Harvest-now-decrypt-later risk review</span>
          </div>
        </div>

        <h2>Quantum Priority Definition</h2>
        {priority_table}

        <h2>Evidence-Backed Findings</h2>
        <div class="three">{finding_cards}</div>

        <h2>Cryptographic Bill of Materials</h2>
        {report_cbom_table}

        <h2>Technical CBOM Inventory</h2>
        {technical_cbom_table}

        <h2>Observed TLS Flows</h2>
        {flows_table}

        <h2>Compliance Mapping</h2>
        {compliance_table}

        <h2>Quantum Remediation Roadmap</h2>
        {roadmap_table}

        <div class="card warn">
          <h3>What This PCAP Cannot Prove Alone</h3>
          <p>Certificate chain, certificate expiry, SAN validation, issuer, signature algorithm, and weak certificate checks may require TLS key logs or external certificate scan integration.</p>
        </div>

        <h2>Evidence Appendix</h2>
        {evidence_table}

        <h2>Document Control</h2>
        {doc_table}

        <h2>Parser Log</h2>
        <div class="console">{parser_log}</div>

        <h2>Limitations</h2>
        <ul>{limitations}</ul>

        <p class="muted" style="font-size:12px">RBI QuBOM Dashboard · Use results as evidence indicators. Full compliance sign-off may require TLS secrets, external certificate scans, endpoint configuration review, and manual validation.</p>
      </section>
    </main></div></body></html>
    """.format(
        css=_board_css(),
        posture=_html_escape(posture),
        priority=_html_escape(priority),
        tls_version=_html_escape(tls_version),
        cipher=_html_escape(cipher),
        kex=_html_escape(kex),
        tls_sessions=_html_escape(s.get("TLS Sessions", len(report.get("cbom", [])))),
        priority_table=priority_definition().to_html(index=False, escape=False),
        finding_cards=finding_cards,
        report_cbom_table=_board_table(report.get("report_cbom") or report.get("cbom", [])),
        technical_cbom_table=_board_table(report.get("cbom", [])),
        flows_table=_board_table(report.get("flows", [])),
        compliance_table=_board_table(report.get("compliance", [])),
        roadmap_table=_board_table(report.get("roadmap", [])),
        evidence_table=_board_table(report.get("evidence", [])),
        doc_table=_board_table([doc]) if doc else "<p>No document control data.</p>",
        parser_log=_html_escape(parser_log),
        limitations=limitations
    )
    return html_doc

def source_html_report(source_report):
    s = source_report.get("summary", {})
    target = s.get("Target", "Source Repository")
    critical = s.get("Critical Crypto Findings", 0)
    qv = s.get("Quantum-Vulnerable Findings", 0)
    posture = "High Crypto Risk" if critical else "Quantum Migration Required" if qv else "Review / Monitor"

    finding_rows = source_report.get("source_findings", [])[:6]
    if finding_rows:
        finding_cards = "".join(
            "<div class='finding'><span class='badge bamber'>{priority}</span><div class='title'>{finding}</div><div class='value'>{status}</div><div class='detail'>{file}<br>{action}</div></div>".format(
                priority=_html_escape(f.get("Priority", "")),
                finding=_html_escape(f.get("Finding", "")),
                status=_html_escape(f.get("Status", "")),
                file=_html_escape(f.get("File", "")),
                action=_html_escape(f.get("Action", ""))
            )
            for f in finding_rows
        )
    else:
        finding_cards = "<div class='card'><b>No crypto findings were detected from source scanning.</b><p class='muted'>This does not prove the codebase is free from cryptographic usage.</p></div>"

    manifest_rows = [{"Manifest": x} for x in source_report.get("manifests", [])]
    parser_note = s.get("Parsing Notes", "")

    html_doc = """
    <!doctype html><html><head><meta charset="utf-8"><title>RBI QuBOM Source Board Report</title>{css}</head>
    <body><div class="wrap"><main class="hero">
      <div class="heroTop">
        <span class="badge bblue">RBI QuBOM</span><span class="badge bviolet">Source SBOM + CBOM</span><span class="badge">Board Report</span>
        <h1>RBI QuBOM Source Code SBOM & CBOM Report</h1>
        <p class="sub">Executive board-ready report for dependency SBOM, source-code cryptography CBOM, crypto-risk prioritization, and remediation planning.</p>
      </div>

      <div class="grid4">
        <div class="metric"><small>Source Posture</small><b>{posture}</b><span class="badge bamber">Board Review</span></div>
        <div class="metric"><small>Files Scanned</small><b>{files}</b><span class="badge bblue">Source</span></div>
        <div class="metric"><small>SBOM Components</small><b>{components}</b><span class="badge bgreen">Dependencies</span></div>
        <div class="metric"><small>Source CBOM Findings</small><b>{cbom_findings}</b><span class="badge bamber">Crypto</span></div>
      </div>

      <section class="section">
        <div class="two">
          <div class="card dark">
            <h3>Executive Assessment</h3>
            <p>RBI QuBOM scanned <b>{files}</b> source file(s), identified <b>{components}</b> SBOM component(s), and found <b>{cbom_findings}</b> source-code cryptography finding(s) for <b>{target}</b>.</p>
          </div>
          <div class="card risk">
            <h3>Board-Level Risk</h3>
            <p>Deprecated algorithms require immediate remediation. Classical asymmetric cryptography such as RSA, ECDH, ECDSA, and Diffie-Hellman should be tracked for PQC migration readiness.</p>
            <span class="badge bamber">{posture}</span>
          </div>
        </div>

        <h2>Quantum Priority Definition</h2>
        {priority_table}

        <h2>Source Findings</h2>
        <div class="three">{finding_cards}</div>

        <h2>Source-Code SBOM</h2>
        {sbom_table}

        <h2>Source-Code CBOM</h2>
        {source_cbom_table}

        <h2>Manifest Files Detected</h2>
        {manifest_table}

        <h2>Source Remediation Roadmap</h2>
        {roadmap_table}

        <h2>BOM Integrity Manifest</h2>
        {integrity_table}

        <h2>Parser Notes</h2>
        <div class="console">{parser_note}</div>

        <p class="muted" style="font-size:12px">RBI QuBOM Source Report · Static source analysis can miss dynamically generated dependencies, vendored binaries, encrypted files, and runtime-resolved cryptography.</p>
      </section>
    </main></div></body></html>
    """.format(
        css=_board_css(),
        posture=_html_escape(posture),
        files=_html_escape(s.get("Files Scanned", 0)),
        components=_html_escape(s.get("SBOM Components", 0)),
        cbom_findings=_html_escape(s.get("Source CBOM Findings", 0)),
        target=_html_escape(target),
        priority_table=priority_definition().to_html(index=False, escape=False),
        finding_cards=finding_cards,
        sbom_table=_board_table(source_report.get("sbom", [])),
        source_cbom_table=_board_table(source_report.get("source_cbom", [])),
        manifest_table=_board_table(manifest_rows),
        roadmap_table=_board_table([
            {"Phase": "0–30 Days", "Title": "Dependency Baseline", "Actions": "Validate manifests, generate SBOM, assign ownership for critical packages."},
            {"Phase": "30–90 Days", "Title": "Crypto Inventory", "Actions": "Review source-code CBOM, remove deprecated algorithms, identify PQC migration candidates."},
            {"Phase": "90–180 Days", "Title": "Secure Build Governance", "Actions": "Integrate SBOM/CBOM generation into CI/CD and attach integrity manifests to releases."}
        ]),
        integrity_table=_board_table([source_report.get("integrity", {})]),
        parser_note=_html_escape(parser_note)
    )
    return html_doc

# UI
st.sidebar.title('🛡️ RBI QuBOM')
st.sidebar.caption('PCAP CBOM + Source-code SBOM/CBOM with stable quantum priority model.')
target=st.sidebar.text_input('Target Application','RBI-Website')
unit=st.sidebar.text_input('Business Unit','Network')
classification=st.sidebar.selectbox('Classification',['CONFIDENTIAL','INTERNAL','RESTRICTED','PUBLIC'],0)

st.markdown("""<div class="hero"><div class="heroTop"><div><span class="badge bblue">RBI QuBOM</span><span class="badge bviolet">PCAP + Source Code</span><span class="badge">Stable Priority Model</span><h1>RBI QuBOM Board Dashboard</h1><p class="sub">Generate PCAP-based cryptographic CBOM, source-code cryptography CBOM, and source-code SBOM from one home page. Quantum priority is defined below.</p></div><div class="uploadBox"><b>Choose analysis type below</b><p class="muted">PCAP CBOM and Source SBOM/CBOM are both available on the home page.</p></div></div></div>""", unsafe_allow_html=True)

st.markdown('<div class="sectionHead"><div><h2>Quantum Priority Definition</h2></div></div>', unsafe_allow_html=True)
st.dataframe(priority_definition(), use_container_width=True, hide_index=True)

home_tabs=st.tabs(['PCAP-based CBOM','Source-code SBOM & CBOM'])
with home_tabs[0]:
    up=st.file_uploader('Upload PCAP / PCAPNG / CAP',type=['pcap','pcapng','cap'],key='pcap_upload')
    if up:
        report=analyze_pcap_bytes(up.read(),up.name,{'target':target,'business_unit':unit,'classification':classification}); s=report['summary']
        st.markdown(f"""<div class="grid4"><div class="metric"><div class="label">Quantum Posture</div><div class="val">{s['Quantum Posture']}</div><div class="note">{badge(s['Overall Priority'])}</div></div><div class="metric"><div class="label">TLS Version</div><div class="val">{s['TLS Version']}</div></div><div class="metric"><div class="label">Cipher Suite</div><div class="val" style="font-size:17px">{s['Cipher Suite']}</div></div><div class="metric"><div class="label">Key Exchange</div><div class="val">{s['Key Exchange'].replace('secp256r1 / ','')}</div></div></div>""", unsafe_allow_html=True)
        st.markdown(f"""<div class="two"><div class="card dark"><h3>Executive Assessment</h3><p>RBI QuBOM identified {s['TLS Sessions']} TLS sessions. The final posture is <b>{s['Quantum Posture']}</b> with <b>{s['Overall Priority']}</b>. Priority is based on final selected cryptographic evidence, not a changing score.</p><div class="kpis"><div class="kpi"><small>Target</small><strong>{s['Target']}</strong></div><div class="kpi"><small>Priority 2</small><strong>{s['Priority 2']}</strong></div><div class="kpi"><small>Priority 3</small><strong>{s['Priority 3']}</strong></div></div></div><div class="card risk"><h3>Board-Level Risk</h3><p>Classical ECDHE/X25519/P-256/RSA/DHE/ECDSA remain quantum-vulnerable unless the server actually negotiates hybrid/PQC key exchange.</p>{badge(s['Overall Priority'])}</div></div>""", unsafe_allow_html=True)
        pc_tabs=st.tabs(['Report CBOM','Technical CBOM','TLS Flows','Findings','Compliance','Roadmap','Evidence + Logs','Exports'])
        with pc_tabs[0]: st.dataframe(pd.DataFrame(report['report_cbom']),use_container_width=True,hide_index=True)
        with pc_tabs[1]: st.dataframe(pd.DataFrame(report['cbom']),use_container_width=True,hide_index=True)
        with pc_tabs[2]: st.dataframe(pd.DataFrame(report['flows']),use_container_width=True,hide_index=True)
        with pc_tabs[3]: st.dataframe(pd.DataFrame(report['findings']),use_container_width=True,hide_index=True)
        with pc_tabs[4]: st.dataframe(pd.DataFrame(report['compliance']),use_container_width=True,hide_index=True)
        with pc_tabs[5]: st.dataframe(pd.DataFrame(report['roadmap']),use_container_width=True,hide_index=True)
        with pc_tabs[6]:
            st.dataframe(pd.DataFrame(report['evidence']),use_container_width=True,hide_index=True); st.markdown(f"<div class='console'>{chr(10).join(report['parser_logs'])}</div>",unsafe_allow_html=True)
            for x in report['limitations']: st.write('- '+x)
        with pc_tabs[7]:
            st.download_button('Download Board HTML Report',html_report(report),'rbi_qubom_board_report.html','text/html')
            st.download_button('Download Full JSON Report',json.dumps(report,indent=2),'rbi_qubom_report.json','application/json')
            st.download_button('Download Report CBOM CSV',pd.DataFrame(report['report_cbom']).to_csv(index=False),'rbi_qubom_report.csv','text/csv')
            st.download_button('Download Technical CBOM CSV',pd.DataFrame(report['cbom']).to_csv(index=False),'rbi_qubom_technical.csv','text/csv')
    else:
        st.info('Upload a PCAP to generate network cryptographic CBOM.')

with home_tabs[1]:
    src=st.file_uploader('Upload source code ZIP / TAR / single manifest/source file',type=['zip','tar','gz','tgz','json','txt','toml','xml','gradle','mod','lock','py','js','ts','java','go','rs','cs','php','rb','yml','yaml'],key='source_upload')
    if src:
        sr=analyze_source(src,target); sm=sr['summary']
        st.markdown(f"""<div class="grid4"><div class="metric"><div class="label">Files Scanned</div><div class="val">{sm['Files Scanned']}</div></div><div class="metric"><div class="label">SBOM Components</div><div class="val">{sm['SBOM Components']}</div></div><div class="metric"><div class="label">Source CBOM Findings</div><div class="val">{sm['Source CBOM Findings']}</div></div><div class="metric"><div class="label">Quantum Vulnerable</div><div class="val">{sm['Quantum-Vulnerable Findings']}</div>{badge('Priority 2')}</div></div>""", unsafe_allow_html=True)
        if sm['Parsing Notes']!='No parsing errors': st.warning(sm['Parsing Notes'])
        st_tabs=st.tabs(['Source Summary','SBOM','Source CBOM','Source Findings','Exports'])
        with st_tabs[0]: st.dataframe(pd.DataFrame(sm.items(),columns=['Metric','Value']),use_container_width=True,hide_index=True); st.dataframe(pd.DataFrame({'Manifest':sr['manifests']}),use_container_width=True,hide_index=True)
        with st_tabs[1]: st.dataframe(pd.DataFrame(sr['sbom']),use_container_width=True,hide_index=True)
        with st_tabs[2]: st.dataframe(pd.DataFrame(sr['source_cbom']),use_container_width=True,hide_index=True)
        with st_tabs[3]: st.dataframe(pd.DataFrame(sr['source_findings']),use_container_width=True,hide_index=True)
        with st_tabs[4]:
            st.download_button('Download Source Board HTML Report',source_html_report(sr),'rbi_qubom_source_board_report.html','text/html')
            st.download_button('Download Source SBOM CSV',pd.DataFrame(sr['sbom']).to_csv(index=False),'rbi_qubom_source_sbom.csv','text/csv')
            st.download_button('Download Source CBOM CSV',pd.DataFrame(sr['source_cbom']).to_csv(index=False),'rbi_qubom_source_cbom.csv','text/csv')
            st.download_button('Download Standard BOM JSON',json.dumps(sr['standard_bom_json'],indent=2),'rbi_qubom_standard_bom.json','application/json')
            st.download_button('Download SPDX-like JSON',json.dumps(sr['spdx_like_json'],indent=2),'rbi_qubom_spdx_like.json','application/json')
            st.download_button('Download BOM Integrity Manifest',json.dumps(sr['integrity'],indent=2),'rbi_qubom_integrity_manifest.json','application/json')
    else:
        st.info('Upload a source archive or manifest to generate source-code SBOM and CBOM.')

st.caption('RBI QuBOM v9 · Stable priority model · PCAP CBOM + Source-code SBOM/CBOM · Evidence indicators only, not formal compliance certification.')
