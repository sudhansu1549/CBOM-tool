import streamlit as st
import pandas as pd
import hashlib, json, tempfile, os, uuid
from pathlib import Path
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px

st.set_page_config(page_title='RBI CBOM | Board Dashboard', page_icon='🛡️', layout='wide')
st.markdown('''<style>
.main{background:linear-gradient(135deg,#f8fafc,#eef6ff 55%,#f7fafc)}.block-container{max-width:1380px;padding-top:1.4rem}.hero{background:rgba(255,255,255,.94);border:1px solid #e2e8f0;border-radius:34px;box-shadow:0 16px 40px rgba(15,23,42,.08);overflow:hidden;margin-bottom:20px}.heroTop{padding:34px;background:radial-gradient(circle at top right,#dbeafe,transparent 38%),linear-gradient(135deg,#fff,#f8fafc);display:grid;grid-template-columns:1fr 370px;gap:28px;align-items:center}.hero h1{font-size:46px;line-height:1.02;margin:12px 0;letter-spacing:-1.5px;color:#0f172a;font-weight:950}.sub{font-size:16px;line-height:1.65;color:#64748b}.badge{display:inline-flex;align-items:center;border-radius:999px;border:1px solid #e2e8f0;padding:7px 11px;font-size:12px;font-weight:850;background:#f8fafc;color:#334155;margin:2px}.bblue{background:#eff6ff;color:#1d4ed8;border-color:#bfdbfe}.bgreen{background:#ecfdf5;color:#047857;border-color:#a7f3d0}.bamber{background:#fffbeb;color:#b45309;border-color:#fde68a}.bred{background:#fef2f2;color:#b91c1c;border-color:#fecaca}.bviolet{background:#f5f3ff;color:#6d28d9;border-color:#ddd6fe}.uploadBox{background:white;border:1px solid #e2e8f0;border-radius:26px;padding:18px;box-shadow:0 8px 22px rgba(15,23,42,.06)}.grid4{display:grid;grid-template-columns:repeat(4,1fr);gap:18px;margin:18px 0}.metric{background:white;border:1px solid #e2e8f0;border-radius:26px;padding:22px;box-shadow:0 6px 18px rgba(15,23,42,.04)}.metric .label{font-size:11px;text-transform:uppercase;letter-spacing:.08em;color:#64748b;font-weight:900}.metric .val{font-size:24px;font-weight:950;margin-top:8px;word-break:break-word;color:#0f172a}.two{display:grid;grid-template-columns:2fr 1fr;gap:18px;margin-top:18px}.card{background:white;border:1px solid #e2e8f0;border-radius:28px;padding:24px;box-shadow:0 8px 22px rgba(15,23,42,.04)}.dark{background:#020617;color:white}.dark p,.dark .muted{color:#cbd5e1}.risk{background:#fffbeb;border-color:#fde68a}.risk h3,.risk p{color:#92400e}.kpis{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-top:18px}.kpi{border-radius:18px;background:rgba(255,255,255,.10);padding:14px}.kpi small{display:block;color:#cbd5e1}.kpi strong{display:block;margin-top:5px;color:white}.muted{color:#64748b}.sectionHead{display:flex;justify-content:space-between;gap:16px;align-items:flex-start;margin:28px 0 16px}.sectionHead h2{font-size:23px;margin:0;color:#0f172a}.desc{margin:7px 0 0;color:#64748b;line-height:1.6;font-size:14px}.findings{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}.finding{background:white;border:1px solid #e2e8f0;border-radius:24px;padding:18px;min-height:190px}.findingTop{display:flex;justify-content:space-between;gap:10px;margin-bottom:14px}.finding .title{font-size:13px;color:#64748b;font-weight:900}.finding .value{font-size:18px;font-weight:950;margin-top:5px;color:#0f172a}.finding .detail{font-size:13px;line-height:1.55;color:#475569;margin-top:12px}.foot{display:flex;justify-content:space-between;gap:10px;margin-top:14px;font-size:12px;color:#64748b}.console{font-family:monospace;background:#020617;color:#d1fae5;border-radius:20px;padding:16px;white-space:pre-wrap;font-size:12px;line-height:1.45;max-height:260px;overflow:auto}div[data-testid="stFileUploader"]{border:2px dashed #cbd5e1;border-radius:22px;padding:18px;background:#f8fafc}@media(max-width:1000px){.heroTop,.two,.grid4,.findings{grid-template-columns:1fr}.hero h1{font-size:34px}.kpis{grid-template-columns:1fr}}
</style>''', unsafe_allow_html=True)

TLSVER={0x0301:'TLS 1.0',0x0302:'TLS 1.1',0x0303:'TLS 1.2',0x0304:'TLS 1.3'}
CIPH={0x1301:'TLS_AES_128_GCM_SHA256',0x1302:'TLS_AES_256_GCM_SHA384',0x1303:'TLS_CHACHA20_POLY1305_SHA256',0xC02F:'TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256',0xC030:'TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384',0x009C:'TLS_RSA_WITH_AES_128_GCM_SHA256',0x009D:'TLS_RSA_WITH_AES_256_GCM_SHA384',0x000A:'TLS_RSA_WITH_3DES_EDE_CBC_SHA',0x0005:'TLS_RSA_WITH_RC4_128_SHA'}
GROUP={0x001D:'x25519',0x0017:'secp256r1 / P-256',0x0018:'secp384r1 / P-384',0x0019:'secp521r1 / P-521',0x001E:'x448',0x11EC:'X25519 + ML-KEM-768 / Kyber-768 hybrid',0x6399:'X25519 + ML-KEM/Kyber hybrid draft',0x2F39:'ML-KEM-768 draft / experimental hybrid indicator'}

def bclass(v):
    v=str(v).lower()
    if 'critical' in v or 'priority 1' in v or 'not quantum' in v or 'deprecated' in v: return 'bred'
    if 'vulnerable' in v or 'priority 2' in v or 'medium' in v or 'partial' in v or 'risk' in v: return 'bamber'
    if 'manual' in v or 'unknown' in v or 'priority 3' in v: return 'bviolet'
    if 'safe' in v or 'ready' in v or 'observed' in v or 'low' in v or 'strong' in v: return 'bgreen'
    return 'bblue'
def badge(v): return f"<span class='badge {bclass(v)}'>{v}</span>"
def sha256_bytes(data): return hashlib.sha256(data).hexdigest()
def u16(b,o,le=False): return b[o]|(b[o+1]<<8) if le else (b[o]<<8)|b[o+1]
def u32(b,o,le=False): return (b[o]|(b[o+1]<<8)|(b[o+2]<<16)|(b[o+3]<<24))&0xffffffff if le else ((b[o]<<24)|(b[o+1]<<16)|(b[o+2]<<8)|b[o+3])&0xffffffff
def ip4(b,o): return f"{b[o]}.{b[o+1]}.{b[o+2]}.{b[o+3]}"

def read_packets(data):
    packets=[]; logs=[]
    if len(data)<24: return packets,['File too small']
    mbe=u32(data,0,False); mle=u32(data,0,True)
    if mbe==0x0a0d0d0a:
        off=0
        while off+12<=len(data):
            bt=u32(data,off,False); bl=u32(data,off+4,False)
            if bl<12 or off+bl>len(data): break
            if bt==6 and off+28<=len(data):
                caplen=u32(data,off+20,False); po=off+28
                if po+caplen<=off+bl: packets.append(data[po:po+caplen])
            off+=bl
        logs.append(f'Parsed PCAPNG packets: {len(packets)}'); return packets,logs
    if mbe==0xa1b2c3d4: le=False
    elif mbe==0xd4c3b2a1 or mle==0xa1b2c3d4: le=True
    else: return packets,[f'Unsupported PCAP magic: 0x{mbe:x}']
    off=24
    while off+16<=len(data):
        incl=u32(data,off+8,le); off+=16
        if off+incl>len(data): break
        packets.append(data[off:off+incl]); off+=incl
    logs.append(f'Parsed PCAP packets: {len(packets)}'); return packets,logs

def parse_client_hello(b):
    try:
        if len(b)<42: return None
        o=2+32; sid=b[o]; o+=1+sid
        cslen=u16(b,o); o+=2+cslen
        comp=b[o]; o+=1+comp
        if o+2>len(b): return {'sni':'','groups':[],'pq_offer':False}
        extlen=u16(b,o); o+=2; end=min(o+extlen,len(b))
        sni=''; groups=[]; pq=False; versions=[]
        while o+4<=end:
            et=u16(b,o); el=u16(b,o+2); o+=4; e=min(o+el,end)
            if et==0 and o+2<=e:
                p=o+2
                while p+3<=e:
                    nt=b[p]; nl=u16(b,p+1); p+=3
                    if nt==0 and p+nl<=e: sni=b[p:p+nl].decode('utf-8','ignore')
                    p+=nl
            elif et==10 and o+2<=e:
                gl=u16(b,o); p=o+2
                while p+2<=e and p<o+2+gl:
                    g=u16(b,p); groups.append(GROUP.get(g,f'group 0x{g:04x}')); p+=2
            elif et==43 and o<e:
                l=b[o]; p=o+1
                while p+2<=e and p<o+1+l:
                    v=u16(b,p); versions.append(TLSVER.get(v,f'0x{v:04x}')); p+=2
            elif et==51 and o+2<=e:
                kl=u16(b,o); p=o+2
                while p+4<=e and p<o+2+kl:
                    g=u16(b,p); klen=u16(b,p+2); name=GROUP.get(g,f'group 0x{g:04x}'); groups.append(name)
                    if any(x in name.lower() for x in ['ml-kem','kyber','hybrid']) or klen>1000: pq=True
                    p+=4+klen
            o=e
        if any(any(x in g.lower() for x in ['ml-kem','kyber','hybrid']) for g in groups): pq=True
        return {'sni':sni,'groups':groups,'pq_offer':pq,'versions':versions}
    except Exception: return None

def parse_server_hello(b):
    try:
        if len(b)<38: return None
        o=0; legacy=u16(b,o); o+=2+32
        sid=b[o]; o+=1+sid
        cipher=u16(b,o); o+=2; o+=1
        final=TLSVER.get(legacy,f'0x{legacy:04x}'); evidence='legacy_version field'; group=''
        if o+2<=len(b):
            extlen=u16(b,o); o+=2; end=min(o+extlen,len(b))
            while o+4<=end:
                et=u16(b,o); el=u16(b,o+2); o+=4; e=min(o+el,end)
                if et==43 and el>=2:
                    v=u16(b,o); final=TLSVER.get(v,f'0x{v:04x}'); evidence='ServerHello supported_versions extension'
                elif et==51 and el>=4:
                    g=u16(b,o); group=GROUP.get(g,f'group 0x{g:04x}')
                o=e
        return {'tls_version':final,'version_evidence':evidence,'cipher':CIPH.get(cipher,f'0x{cipher:04x}'),'group':group}
    except Exception: return None

def parse_tls_records(payload, flow):
    o=0
    while o+5<=len(payload):
        ctype=payload[o]; ln=u16(payload,o+3)
        if ctype not in [20,21,22,23] or ln<=0 or o+5+ln>len(payload): break
        if ctype==22:
            p=o+5; end=o+5+ln
            while p+4<=end:
                htype=payload[p]; hlen=(payload[p+1]<<16)|(payload[p+2]<<8)|payload[p+3]; hp=p+4; he=hp+hlen
                if he>end: break
                if htype==1:
                    ch=parse_client_hello(payload[hp:he]);
                    if ch: flow['client_hellos'].append(ch)
                elif htype==2:
                    sh=parse_server_hello(payload[hp:he]);
                    if sh: flow['server_hellos'].append(sh)
                p=he
        o+=5+ln

def parse_packets(packets):
    flows={}
    for p in packets:
        if len(p)<34: continue
        eth=u16(p,12); ipoff=14
        if eth==0x8100 and len(p)>=18: eth=u16(p,16); ipoff=18
        if eth!=0x0800 and len(p)>=16 and u16(p,14)==0x0800: eth=0x0800; ipoff=16
        if eth!=0x0800 or ipoff+20>len(p): continue
        ihl=(p[ipoff]&15)*4
        if p[ipoff+9]!=6: continue
        src=ip4(p,ipoff+12); dst=ip4(p,ipoff+16); toff=ipoff+ihl
        if toff+20>len(p): continue
        sp=u16(p,toff); dp=u16(p,toff+2); doff=((p[toff+12]>>4)&15)*4; payoff=toff+doff
        payload=p[payoff:]
        if len(payload)<5: continue
        key=(src,sp,dst,dp); flows.setdefault(key,{'src':src,'sport':sp,'dst':dst,'dport':dp,'client_hellos':[],'server_hellos':[]})
        parse_tls_records(payload,flows[key])
    return flows

def parts(cipher,ver):
    u=cipher.upper(); k='TLS 1.3 key schedule' if ver=='TLS 1.3' or 'TLS_AES' in u or 'CHACHA20' in u else 'ECDHE' if 'ECDHE' in u else 'RSA static key exchange' if u.startswith('TLS_RSA') else 'Unknown'
    enc='AES-256-GCM' if 'AES_256_GCM' in u else 'AES-128-GCM' if 'AES_128_GCM' in u else 'ChaCha20-Poly1305' if 'CHACHA20' in u else '3DES' if '3DES' in u else 'RC4' if 'RC4' in u else 'Unknown'
    mac='SHA-384' if 'SHA384' in u else 'SHA-256' if 'SHA256' in u else 'SHA-1' if 'SHA' in u else 'AEAD/Unknown'
    return k,enc,mac,(ver=='TLS 1.3' or k=='ECDHE')

def qclass(ver,cipher,kx,group,client_pq):
    t=' '.join([ver,cipher,kx,group]).lower()
    if any(x in t for x in ['ml-kem','kyber','hybrid']): return {'qr':'Quantum Ready / Hybrid Observed','safe':'Yes','priority':'Priority 4','risk':'Low','asset':group or 'Hybrid PQC','etype':'Observed','conf':0.90,'note':'Hybrid/PQC key exchange was negotiated.'}
    if ver=='TLS 1.3' or any(x in t for x in ['ecdhe','ecdh','rsa','dhe','secp','x25519','x448']):
        note='Classical asymmetric key exchange is visible or strongly expected; vulnerable to Shor at Q-Day.'
        if client_pq: note+=' Client offered PQ/hybrid, but server did not negotiate PQ/hybrid in observed ServerHello.'
        return {'qr':'Quantum Vulnerable','safe':'No','priority':'Priority 2','risk':'Medium','asset':group or kx,'etype':'Observed' if group else 'Risk Indicator','conf':0.88 if group else 0.72,'note':note}
    return {'qr':'Requires Manual Validation','safe':'No','priority':'Priority 3','risk':'Unknown','asset':'Unknown','etype':'Requires Manual Validation','conf':0.5,'note':'Incomplete handshake evidence.'}

def analyze(data,meta):
    packets,logs=read_packets(data); flows_raw=parse_packets(packets)
    h=sha256_bytes(data); cbom=[]; evidence=[]; findings=[]; flows=[]; algos={}
    for key,fl in flows_raw.items():
        for sh in fl['server_hellos']:
            ch=fl['client_hellos'][-1] if fl['client_hellos'] else {'sni':'','groups':[],'pq_offer':False}
            kx,enc,mac,fs=parts(sh['cipher'],sh['tls_version']); group=sh['group']; q=qclass(sh['tls_version'],sh['cipher'],kx,group,ch.get('pq_offer',False))
            flags=[]
            if sh['tls_version'] in ['SSLv3','TLS 1.0','TLS 1.1']: flags.append('TLS_LEGACY_VERSION')
            if any(x in sh['cipher'].upper() for x in ['RC4','3DES','DES','NULL','EXPORT','MD5']): flags.append('WEAK_CIPHER')
            if q['priority']=='Priority 2': flags.append('QUANTUM_VULNERABLE_ASYMMETRIC')
            if sh['tls_version']=='TLS 1.3' and not group: flags.append('KEY_SHARE_GROUP_NOT_EXTRACTED')
            if ch.get('pq_offer') and not any(x in group.lower() for x in ['ml-kem','kyber','hybrid']): flags.append('CLIENT_PQ_OFFER_SERVER_NOT_PQ')
            ev=f'EVD-TLS-{len(evidence)+1:04d}'; sni=ch.get('sni','')
            rec={'CBOM ID':f'CBOM-{len(cbom)+1:06d}','Asset':q['asset'],'Protocol':'TLS','TLS Version':sh['tls_version'],'TLS Version Evidence':sh['version_evidence'],'Cipher Suite':sh['cipher'],'Symmetric Encryption':enc,'Hash / KDF':mac,'Key Exchange':group or kx,'Client Offered PQ/Hybrid':'Yes' if ch.get('pq_offer') else 'No','Client Offered Groups':', '.join(ch.get('groups',[])[:8]),'Forward Secrecy':fs,'Quantum Readiness':q['qr'],'Quantum Safe':q['safe'],'Priority':q['priority'],'Risk':q['risk'],'Source':f"{fl['src']}:{fl['sport']}",'Destination':f"{fl['dst']}:{fl['dport']}",'SNI':sni,'Evidence Type':q['etype'],'Confidence':q['conf'],'Executive Note':q['note'],'Recommended Migration':'Plan hybrid/PQC migration using ML-KEM for key establishment and ML-DSA/SLH-DSA for signatures where supported.' if q['priority']=='Priority 2' else 'Maintain monitoring.','Policy Flags':', '.join(flags),'Evidence ID':ev}
            cbom.append(rec); evidence.append({'Evidence ID':ev,'Frame':'built-in-parser','Source':rec['Source'],'Destination':rec['Destination'],'Protocol':'TLS','Observed Value':f"{sh['tls_version']} via {sh['version_evidence']} / {sh['cipher']} / {group or kx}",'Defensibility':q['etype'],'Confidence':q['conf'],'PCAP SHA256':h})
            flows.append({'Source':rec['Source'],'Destination':rec['Destination'],'SNI':sni,'TLS':sh['tls_version'],'Version Evidence':sh['version_evidence'],'Cipher':sh['cipher'],'KEX':group or kx,'Quantum':q['qr']})
            algos.setdefault(q['asset'],{'Algorithm':q['asset'],'Quantum Threat':q['qr'],'Priority':q['priority'],'Recommended Migration':rec['Recommended Migration'],'Connections':0,'Evidence Type':q['etype'],'Confidence':q['conf']}); algos[q['asset']]['Connections']+=1
            for flag in flags:
                findings.append({'Finding':{'QUANTUM_VULNERABLE_ASYMMETRIC':'Quantum-vulnerable asymmetric cryptography','KEY_SHARE_GROUP_NOT_EXTRACTED':'TLS 1.3 key-share group not extracted','CLIENT_PQ_OFFER_SERVER_NOT_PQ':'Client PQ offer seen, but server did not negotiate PQ/hybrid','TLS_LEGACY_VERSION':'Deprecated TLS protocol','WEAK_CIPHER':'Weak cipher suite'}.get(flag,flag),'Value':rec['Asset'],'Status':rec['Risk'],'Evidence Type':'Risk Indicator' if 'QUANTUM' in flag or 'CLIENT' in flag else rec['Evidence Type'],'Confidence':rec['Confidence'],'Detail':rec['Executive Note'],'Evidence ID':ev,'Endpoint':rec['Destination'],'Policy':'default_network'})
    qsafe=sum(1 for r in cbom if r['Quantum Safe']=='Yes'); qv=sum(1 for r in cbom if r['Quantum Safe']=='No' and r['Priority'] in ['Priority 2','Priority 3']); deprecated=sum(1 for r in cbom if 'TLS_LEGACY_VERSION' in r['Policy Flags'] or 'WEAK_CIPHER' in r['Policy Flags']); quantum_score=round(100*qsafe/max(qsafe+qv,1),1); overall='Priority 1' if deprecated else 'Priority 2' if qv else 'Priority 4'; primary=cbom[0] if cbom else {}
    return {'document':{'Tool Name':'RBI CBOM','Scan ID':str(uuid.uuid4()),'Assessment Date':datetime.now().strftime('%B %d, %Y'),'Target Application':meta['target'],'Scanner Version':'RBI CBOM PQC Scanner v5.0','Parser Engine':'Built-in PCAP/TLS parser','Total Packets':len(packets),'PCAP SHA256':h},'summary':{'Quantum Readiness':'Quantum Ready' if quantum_score==100 else 'Partially Ready' if quantum_score>0 else 'Not Quantum Ready','Overall Risk':overall,'TLS Version':primary.get('TLS Version','Not observable'),'TLS Version Evidence':primary.get('TLS Version Evidence','Not observable'),'Cipher Suite':primary.get('Cipher Suite','Not observable'),'Key Exchange':primary.get('Key Exchange','Not observable'),'Quantum Readiness Score':quantum_score,'Total Assets':len(cbom),'Quantum Safe':qsafe,'Quantum Vulnerable / Weakened':qv,'Deprecated':deprecated},'cbom':cbom,'algorithms':list(algos.values()),'findings':findings,'flows':flows,'evidence':evidence,'recommendations':[{'Recommendation':'Begin PQC migration planning','Category':'Quantum Readiness','Timeline':'30–90 Days','Priority':'Priority 2','Affected':qv,'Executive Action':'Create a crypto-agility and PQC migration program.','Technical Action':'Inventory RSA/ECDH/ECDSA/DHE usage and test hybrid TLS/PQC options.','Verification':'Track reduction of Priority 2 assets.'},{'Recommendation':'Establish continuous CBOM inventory','Category':'Governance','Timeline':'2–4 Weeks','Priority':'Priority 3','Affected':len(cbom),'Executive Action':'Mandate recurring CBOM updates.','Technical Action':'Schedule periodic PCAP-based discovery.','Verification':'Monthly CBOM trend report.'}],'compliance':[{'Framework':'NIST PQC Migration','Status':'Gap' if qv else 'Positive Indicator','Evidence Type':'Risk Indicator','Executive Note':'Classical ECC/RSA/DHE are Shor-vulnerable unless hybrid/PQ is negotiated.'},{'Framework':'RBI / Financial Sector Cyber Resilience','Status':'PQC Roadmap Required' if qv else 'Technical Indicator','Evidence Type':'Risk Indicator','Executive Note':'Board-level quantum-risk roadmap should be documented.'}],'parser_logs':logs+[f'TLS ServerHello records found: {len(cbom)}','Accuracy rule: TLS 1.3 is identified from ServerHello supported_versions, not legacy_version.'],'limitations':['If ServerHello is not present, negotiated TLS/cipher cannot be identified.','TLS 1.3 is not automatically quantum-safe; classical ECDHE remains Shor-vulnerable.','This is PCAP-only evidence, not legal/regulatory certification.']}

def html_report(report): return '<html><body><h1>RBI CBOM Board Report</h1>'+pd.DataFrame(report['summary'].items(),columns=['Metric','Value']).to_html(index=False)+pd.DataFrame(report['cbom']).to_html(index=False)+'</body></html>'

st.sidebar.title('🛡️ RBI CBOM'); target=st.sidebar.text_input('Target Application','RBI-Website'); business_unit=st.sidebar.text_input('Business Unit','Network'); classification=st.sidebar.selectbox('Classification',['CONFIDENTIAL','INTERNAL','RESTRICTED','PUBLIC'])
st.markdown("""<div class='hero'><div class='heroTop'><div><span class='badge bblue'>RBI CBOM</span><span class='badge bviolet'>Quantum Readiness</span><span class='badge'>Built-in PCAP Parser</span><h1>RBI CBOM Quantum Readiness Dashboard</h1><p class='sub'>Board-level dashboard for TLS discovery, CBOM inventory, compliance mapping, and quantum-risk assessment. This version uses a built-in parser to correctly detect TLS 1.3 from ServerHello supported_versions.</p></div><div class='uploadBox'><b>Upload PCAP / PCAPNG</b><p class='muted'>No tshark dependency for core TLS detection.</p>""",unsafe_allow_html=True)
up=st.file_uploader('Upload PCAP / PCAPNG / CAP',type=['pcap','pcapng','cap'],label_visibility='collapsed')
st.markdown('</div></div></div>',unsafe_allow_html=True)
if not up: st.info('Upload a PCAP to generate the RBI CBOM board-ready assessment.'); st.stop()
report=analyze(up.read(),{'target':target,'business_unit':business_unit,'classification':classification}); s=report['summary']
st.markdown(f"""<div class='grid4'><div class='metric'><div class='label'>Quantum Readiness</div><div class='val'>{s['Quantum Readiness']}</div><div class='note'>{badge(s['Overall Risk'])}</div></div><div class='metric'><div class='label'>TLS Version</div><div class='val'>{s['TLS Version']}</div><div class='note'>{badge(s['TLS Version Evidence'])}</div></div><div class='metric'><div class='label'>Cipher Suite</div><div class='val' style='font-size:17px'>{s['Cipher Suite']}</div><div class='note'>{badge('Strong / Review')}</div></div><div class='metric'><div class='label'>Key Exchange</div><div class='val'>{s['Key Exchange']}</div><div class='note'>{badge('Classical / PQ Review')}</div></div></div>""",unsafe_allow_html=True)
st.markdown(f"""<div class='two'><div class='card dark'><h3>Executive Assessment</h3><p>RBI CBOM identified {s['Total Assets']} cryptographic observations. TLS version is <b>{s['TLS Version']}</b> using <b>{s['TLS Version Evidence']}</b>. Quantum readiness is <b>{s['Quantum Readiness']}</b>.</p><div class='kpis'><div class='kpi'><small>Target</small><strong>{target}</strong></div><div class='kpi'><small>Assets</small><strong>{s['Total Assets']}</strong></div><div class='kpi'><small>Quantum Score</small><strong>{s['Quantum Readiness Score']}%</strong></div></div></div><div class='card risk'><h3>Board-Level Risk</h3><p>Classical ECDHE/X25519/P-256/RSA/DHE/ECDSA are quantum-vulnerable unless hybrid/PQC key exchange is actually negotiated.</p>{badge('HNDL risk present' if s['Quantum Vulnerable / Weakened']>0 else 'No PQC gap observed')}</div></div>""",unsafe_allow_html=True)
cbom_df=pd.DataFrame(report['cbom'])
c1,c2,c3=st.columns(3)
with c1:
    fig=go.Figure(go.Indicator(mode='gauge+number',value=s['Quantum Readiness Score'],title={'text':'Quantum Readiness Score'},gauge={'axis':{'range':[0,100]},'bar':{'color':'#2563eb'},'steps':[{'range':[0,40],'color':'#fef2f2'},{'range':[40,75],'color':'#fffbeb'},{'range':[75,100],'color':'#ecfdf5'}]})); fig.update_layout(height=300,margin=dict(l=20,r=20,t=50,b=20),paper_bgcolor='rgba(0,0,0,0)'); st.plotly_chart(fig,use_container_width=True)
with c2:
    if not cbom_df.empty: fig=px.pie(cbom_df,names='Quantum Readiness',hole=.58,title='Quantum Posture Mix'); fig.update_layout(height=300,paper_bgcolor='rgba(0,0,0,0)'); st.plotly_chart(fig,use_container_width=True)
with c3:
    if not cbom_df.empty:
        d=cbom_df['Protocol'].value_counts().reset_index(); d.columns=['Protocol','Count']; fig=px.bar(d,x='Protocol',y='Count',text='Count',title='Protocol Observations'); fig.update_layout(height=300,paper_bgcolor='rgba(0,0,0,0)'); st.plotly_chart(fig,use_container_width=True)

st.markdown("<div class='sectionHead'><div><h2>Evidence-Backed Findings</h2><p class='desc'>Every claim is labelled with evidence type and confidence.</p></div></div>",unsafe_allow_html=True)
cards=''
for f in report['findings'][:6]: cards+=f"<div class='finding'><div class='findingTop'>{badge(f['Evidence Type'])}{badge(f['Confidence'])}</div><div class='title'>{f['Finding']}</div><div class='value'>{f['Value']}</div><div class='detail'>{f['Detail']}</div><div class='foot'><span>{f['Status']}</span><span>{f['Evidence ID']}</span></div></div>"
st.markdown(f"<div class='findings'>{cards or '<div class=card><b>No high-risk findings from parsed evidence.</b></div>'}</div>",unsafe_allow_html=True)

tabs=st.tabs(['Executive CBOM','TLS Evidence','Compliance','Roadmap','Evidence Explorer','Exports'])
with tabs[0]: st.dataframe(cbom_df,use_container_width=True,hide_index=True); st.markdown('### Algorithm Security'); st.dataframe(pd.DataFrame(report['algorithms']),use_container_width=True,hide_index=True)
with tabs[1]: st.dataframe(pd.DataFrame(report['flows']),use_container_width=True,hide_index=True)
with tabs[2]: st.dataframe(pd.DataFrame(report['compliance']),use_container_width=True,hide_index=True); st.markdown('### Findings'); st.dataframe(pd.DataFrame(report['findings']),use_container_width=True,hide_index=True)
with tabs[3]: st.dataframe(pd.DataFrame(report['recommendations']),use_container_width=True,hide_index=True)
with tabs[4]: st.dataframe(pd.DataFrame(report['evidence']),use_container_width=True,hide_index=True); st.markdown('### Parser Log'); st.markdown(f"<div class='console'>{chr(10).join(report['parser_logs'])}</div>",unsafe_allow_html=True); st.markdown('### Limitations'); [st.write('- '+x) for x in report['limitations']]
with tabs[5]: st.download_button('Download Board-Ready HTML Report',html_report(report),'rbi_cbom_board_report.html','text/html'); st.download_button('Download Full JSON Report',json.dumps(report,indent=2),'rbi_cbom_report.json','application/json'); st.download_button('Download CBOM CSV',cbom_df.to_csv(index=False),'rbi_cbom.csv','text/csv')
st.caption('RBI CBOM v5 · Built-in PCAP/TLS parser · TLS 1.3 supported_versions correction · PCAP evidence mode.')
