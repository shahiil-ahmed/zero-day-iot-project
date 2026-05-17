"""
Zero-Day IoT Attack Detection — PowerPoint Generator (23 slides)
Builds a .pptx from raw OOXML — no third-party libraries required.
"""
import zipfile, os

OUT = "/projects/sandbox/zero-day-iot-project/Zero_Day_IoT_Presentation.pptx"
W, H = 12192000, 6858000   # 16:9 widescreen in EMU

def emu(inches): return int(inches * 914400)

# ── Colour palette ──────────────────────────────────────────────────────────
ACCENT1 = "00C6FF"   # cyan
ACCENT2 = "7B2FBE"   # purple
ACCENT3 = "FF6B35"   # orange
GREEN   = "00E676"   # green
WHITE   = "FFFFFF"
LTGRAY  = "B0BEC5"
YELLOW  = "FFD600"
RED     = "FF1744"

# ── XML helpers ─────────────────────────────────────────────────────────────
def solidFill(h):
    return f'<a:solidFill><a:srgbClr val="{h}"/></a:solidFill>'

def gradFill(h1, h2, ang=5400000):
    return (f'<a:gradFill><a:gsLst>'
            f'<a:gs pos="0"><a:srgbClr val="{h1}"/></a:gs>'
            f'<a:gs pos="100000"><a:srgbClr val="{h2}"/></a:gs>'
            f'</a:gsLst><a:lin ang="{ang}" scaled="0"/></a:gradFill>')

def sp_pr(x, y, cx, cy, fill, rnd=0, bh=None, bw=0):
    ln = f'<a:ln w="{bw}"><a:solidFill><a:srgbClr val="{bh}"/></a:solidFill></a:ln>' if bh else ""
    geo = (f'<a:prstGeom prst="roundRect"><a:avLst>'
           f'<a:gd name="adj" fmla="val {rnd}"/></a:avLst></a:prstGeom>'
           if rnd else '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom>')
    return (f'<p:spPr><a:xfrm><a:off x="{x}" y="{y}"/>'
            f'<a:ext cx="{cx}" cy="{cy}"/></a:xfrm>{geo}{fill}{ln}'
            f'<a:effectLst/></p:spPr>')

def txBody(paras, anchor="ctr"):
    return (f'<p:txBody><a:bodyPr anchor="{anchor}" wrap="square">'
            f'<a:normAutofit/></a:bodyPr><a:lstStyle/>{paras}</p:txBody>')

def _xe(t):
    """Escape XML special chars and strip non-XML-safe characters."""
    # First replace symbols BEFORE XML-escaping so we don't re-introduce < or &
    t = (t.replace("←","&lt;-").replace("→","--&gt;")
          .replace("≥","&gt;=").replace("≤","&lt;=")
          .replace("🔹","*").replace("✅","[OK]").replace("❌","[X]")
          .replace("⚠","[!]").replace("⚡","[~]").replace("🌲","[T]")
          .replace("🧠","[A]").replace("📋","[ ]").replace("🎯","[>>]")
          .replace("📚","[L]").replace("📊","[S]").replace("📈","[^]")
          .replace("🏗","[D]").replace("🌐","[W]").replace("💻","[C]")
          .replace("🔍","[F]").replace("🔮","[?]").replace("🎓","[G]")
          .replace("⚙","[P]").replace("⚠️","[!]").replace("📌","[.]")
          .replace("💡","[i]").replace("★","*").replace("✔","[v]")
          .replace("·","  ").replace("τ","tau").replace("×","x")
          .replace("📦","[pkg]").replace("🚨","[!!]").replace("👇","[v]")
          .replace("•","*"))
    # Now XML-escape any remaining & < > (that were NOT already escaped above)
    # We do this carefully: only escape raw & < > not already part of &amp; &lt; &gt;
    import re
    # escape bare & (not already &amp; &lt; &gt;)
    t = re.sub(r'&(?!(amp|lt|gt|quot|apos);)', '&amp;', t)
    # escape bare < (not already &lt;)
    t = re.sub(r'<(?!-)', '&lt;', t)
    # escape bare >
    t = re.sub(r'(?<!-)>', '&gt;', t)
    # Strip any remaining non-BMP characters (4-byte Unicode)
    result = []
    for ch in t:
        cp = ord(ch)
        if cp <= 0xFFFD:
            result.append(ch)
        else:
            result.append("?")
    return "".join(result)

def para(text, sz, bold=False, color=WHITE, align="l", italic=False, spc=100):
    b = "1" if bold else "0"
    i = "1" if italic else "0"
    lsp = f'<a:lnSpc><a:spcPct val="{spc}000"/></a:lnSpc>'
    return (f'<a:p><a:pPr algn="{align}">{lsp}</a:pPr>'
            f'<a:r><a:rPr lang="en-US" sz="{sz}" b="{b}" i="{i}" dirty="0">'
            f'<a:solidFill><a:srgbClr val="{color}"/></a:solidFill>'
            f'<a:latin typeface="Calibri"/></a:rPr>'
            f'<a:t>{_xe(text)}</a:t></a:r></a:p>')

def ep():
    return '<a:p><a:endParaRPr lang="en-US" dirty="0"/></a:p>'

def sp(idx, x, y, cx, cy, fill, paras, anchor="ctr", rnd=0, bh=None, bw=9525):
    return (f'<p:sp><p:nvSpPr><p:cNvPr id="{idx}" name="S{idx}"/>'
            f'<p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr><p:nvPr/></p:nvSpPr>'
            f'{sp_pr(x,y,cx,cy,fill,rnd,bh,bw)}{txBody(paras,anchor)}</p:sp>')

def line(idx, x1, y1, x2, y2, color, w=19050):
    cx = abs(x2-x1) or 1; cy = abs(y2-y1) or 1
    fh = "1" if x2<x1 else "0"; fv = "1" if y2<y1 else "0"
    return (f'<p:sp><p:nvSpPr><p:cNvPr id="{idx}" name="L{idx}"/>'
            f'<p:cNvSpPr/><p:nvPr/></p:nvSpPr>'
            f'<p:spPr><a:xfrm flipH="{fh}" flipV="{fv}">'
            f'<a:off x="{min(x1,x2)}" y="{min(y1,y2)}"/>'
            f'<a:ext cx="{cx}" cy="{cy}"/></a:xfrm>'
            f'<a:prstGeom prst="line"><a:avLst/></a:prstGeom><a:noFill/>'
            f'<a:ln w="{w}"><a:solidFill><a:srgbClr val="{color}"/>'
            f'</a:solidFill></a:ln></p:spPr>'
            f'<p:txBody><a:bodyPr/><a:lstStyle/><a:p/></p:txBody></p:sp>')

def slide_xml(inner):
    return (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            f'<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"'
            f' xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"'
            f' xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
            f'<p:cSld><p:spTree>'
            f'<p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>'
            f'<p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{W}" cy="{H}"/>'
            f'<a:chOff x="0" y="0"/><a:chExt cx="{W}" cy="{H}"/></a:xfrm></p:grpSpPr>'
            f'{inner}</p:spTree></p:cSld></p:sld>')

# ── Reusable layout helpers ─────────────────────────────────────────────────
def dark_bg():
    return sp(2, 0, 0, W, H, gradFill("060B18","0D1B2A"), ep())

def header_bar(title, num):
    """Top gradient bar + title text + slide number"""
    bar  = sp(3, 0, 0, W, emu(0.82), gradFill(ACCENT2,ACCENT1,0), ep())
    left = sp(4, 0, emu(0.82), emu(0.055), H-emu(0.82), solidFill(ACCENT1), ep())
    bot  = sp(5, 0, H-emu(0.07), W, emu(0.07), solidFill(ACCENT2), ep())
    num_s = sp(6, W-emu(0.65), H-emu(0.45), emu(0.55), emu(0.36),
               solidFill("00000000"), para(str(num),1100,color=LTGRAY,align="r"))
    tit  = sp(7, emu(0.22), emu(0.06), W-emu(0.45), emu(0.72),
               solidFill("00000000"), para(title,2400,bold=True,color=WHITE,align="l"), anchor="ctr")
    return bar+left+bot+num_s+tit

def card(idx, x, y, cx, cy, title, title_color, paras_xml, bg1="0D1B2A", bg2="060B18", bord=None):
    border = bord or title_color
    header = para(title,1500,bold=True,color=title_color,align="l")
    return sp(idx, x, y, cx, cy, gradFill(bg1,bg2),
              header+paras_xml, anchor="t", rnd=10000, bh=border, bw=15875)

def stat(idx, x, y, cx, cy, val, lbl, vc=GREEN):
    return sp(idx, x, y, cx, cy, gradFill("0D1B2A","060B18"),
              para(val,3800,bold=True,color=vc,align="ctr")+para(lbl,1050,color=LTGRAY,align="ctr"),
              anchor="ctr", rnd=14000, bh=vc, bw=19050)

def bullet(text, sz=1200, color=WHITE):
    return para(f"  {text}", sz, color=color)

def kv(key, val, kc=ACCENT1, vc=WHITE, sz=1200):
    return para(f"{key}:  {val}", sz, color=vc)



# ════════════════════════════════════════════════════════════════════════════
# SLIDE 01 — COVER
# ════════════════════════════════════════════════════════════════════════════
def slide_01():
    s  = dark_bg()
    # rainbow top bar
    s += sp(3, 0, 0, W, emu(0.11), gradFill(ACCENT1,ACCENT2,0), ep())
    s += sp(4, 0, H-emu(0.11), W, emu(0.11), gradFill(ACCENT2,ACCENT1,0), ep())
    s += sp(5, 0, emu(0.11), emu(0.055), H-emu(0.22), solidFill(ACCENT1), ep())
    # title box
    s += sp(6, emu(0.45), emu(0.8), emu(11.3), emu(2.0),
            gradFill("0D2137","0A1628"),
            para("Zero-Day IoT Attack Detection",3800,bold=True,color=ACCENT1,align="ctr")
            +para("Using a Hybrid Machine Learning Approach",2500,color=WHITE,align="ctr"),
            anchor="ctr", rnd=20000, bh=ACCENT1, bw=22225)
    # degree line
    s += sp(7, emu(2.2), emu(3.05), emu(7.8), emu(0.48),
            solidFill("00000000"),
            para("B.Tech Final Year Project  ·  Computer Science & Engineering",1600,color=LTGRAY,align="ctr"))
    # team card
    team = (para("PROJECT TEAM",1350,bold=True,color=ACCENT1,align="ctr")
           +para("Shahil Ahmed  ·  Roll No. 202202021046",1250,color=WHITE,align="ctr")
           +para("Jagriti Shivam  ·  Roll No. 202202022091",1250,color=WHITE,align="ctr")
           +para("Khushi Das  ·  Roll No. 202202022113",1250,color=WHITE,align="ctr")
           +para("Babul Hoque  ·  Roll No. 202202021020",1250,color=WHITE,align="ctr"))
    s += sp(8, emu(0.5), emu(3.65), emu(5.1), emu(2.55),
            gradFill("0D2137","071020"), team, anchor="ctr", rnd=12000, bh=ACCENT2, bw=19050)
    # supervisor card
    sup  = (para("SUPERVISOR",1350,bold=True,color=ACCENT2,align="ctr")
           +para("Mr. Bikramjit Choudhury",1250,bold=True,color=WHITE,align="ctr")
           +para("Assistant Professor, Dept. of CSE",1100,color=LTGRAY,align="ctr")
           +ep()
           +para("CENTRAL INSTITUTE OF TECHNOLOGY",1150,bold=True,color=YELLOW,align="ctr")
           +para("KOKRAJHAR, ASSAM — MAY 2026",1050,color=LTGRAY,align="ctr"))
    s += sp(9, emu(5.85), emu(3.65), emu(5.95), emu(2.55),
            gradFill("0D2137","071020"), sup, anchor="ctr", rnd=12000, bh=ACCENT3, bw=19050)
    return slide_xml(s)


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 02 — AGENDA  (updated to 12 topics)
# ════════════════════════════════════════════════════════════════════════════
def slide_02():
    items = [
        ("01","Introduction & Problem Statement", ACCENT1),
        ("02","IoT Threat Landscape",              WHITE),
        ("03","Literature Review",                 ACCENT1),
        ("04","Dataset — Edge-IIoTset",            WHITE),
        ("05","Data Distribution & Class Split",   ACCENT1),
        ("06","Preprocessing Pipeline",            WHITE),
        ("07","System Architecture",               ACCENT1),
        ("08","LightGBM — Model & Training",       WHITE),
        ("09","LightGBM — Results & Per-Class",    ACCENT1),
        ("10","Autoencoder — Architecture",        WHITE),
        ("11","Autoencoder — Training & Threshold",ACCENT1),
        ("12","Fusion Model — Logic & Routing",    WHITE),
        ("13","Fusion — Results & Confusion Matrix",ACCENT1),
        ("14","Feature Importance Analysis",       WHITE),
        ("15","Model Comparison & Baselines",      ACCENT1),
        ("16","Tech Stack & Implementation",       WHITE),
        ("17","Limitations & Discussion",          ACCENT1),
        ("18","Conclusions & Future Work",         WHITE),
    ]
    c1 = "".join(para(f"  {n}   {t}", 1350, color=c, align="l")+ep() for n,t,c in items[:9])
    c2 = "".join(para(f"  {n}   {t}", 1350, color=c, align="l")+ep() for n,t,c in items[9:])
    s  = dark_bg() + header_bar("📋  Agenda — 23 Slides", 2)
    s += sp(10, emu(0.25), emu(0.95), emu(5.8), emu(5.55),
            gradFill("0D2137","060B18"), c1, anchor="t", rnd=10000, bh=ACCENT2, bw=12700)
    s += sp(11, emu(6.2), emu(0.95), emu(5.75), emu(5.55),
            gradFill("0D2137","060B18"), c2, anchor="t", rnd=10000, bh=ACCENT1, bw=12700)
    return slide_xml(s)


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 03 — PROBLEM STATEMENT
# ════════════════════════════════════════════════════════════════════════════
def slide_03():
    s = dark_bg() + header_bar("❓  Problem Statement", 3)
    prob = (para("The Problem",1700,bold=True,color=ACCENT3)
           +para("Traditional IDS rely on known attack signatures.",1300,color=WHITE)
           +para("They are completely BLIND to new / unseen threats.",1300,color=WHITE)
           +ep()
           +para("⚠  Zero-Day Attacks",1500,bold=True,color=YELLOW)
           +para("Exploits for unknown vulnerabilities — no prior",1200,color=LTGRAY)
           +para("signature exists, bypasses every rule-based defence.",1200,color=LTGRAY)
           +ep()
           +para("Three Core Problems We Solve:",1400,bold=True,color=ACCENT1)
           +para("1. Classify known attacks by name (supervised)",1200,color=WHITE)
           +para("2. Detect unseen zero-day attacks (unsupervised)",1200,color=WHITE)
           +para("3. Integrate both into one coherent system",1200,color=WHITE))
    sol  = (para("Our Solution",1700,bold=True,color=GREEN)
           +para("A 3-Layer Hybrid IDS:",1300,color=WHITE)
           +ep()
           +para("🌲  LightGBM",1400,bold=True,color=GREEN)
           +para("  Classifies 10 known attack types with 99.99% acc.",1200,color=LTGRAY)
           +ep()
           +para("🧠  Autoencoder",1400,bold=True,color=ACCENT2)
           +para("  Detects any anomaly via reconstruction error.",1200,color=LTGRAY)
           +ep()
           +para("⚡  Fusion Model",1400,bold=True,color=ACCENT3)
           +para("  Confidence-based routing between the two models.",1200,color=LTGRAY))
    iot  = (para("Why IoT?",1700,bold=True,color=ACCENT1)
           +para("🔹 15 billion+ connected devices worldwide",1250,color=WHITE)
           +para("🔹 Limited CPU/RAM — no heavy AV possible",1250,color=WHITE)
           +para("🔹 Always-on, rarely updated firmware",1250,color=WHITE)
           +para("🔹 Critical: hospitals, power grids, factories",1250,color=WHITE)
           +para("🔹 Massive attack surface for adversaries",1250,color=WHITE)
           +ep()
           +para("Mirai botnet (2016): 620 Gbps DDoS using",1150,color=LTGRAY,italic=True)
           +para("600k compromised IoT cameras & routers.",1150,color=LTGRAY,italic=True))
    s += card(10,emu(0.25),emu(0.92),emu(5.45),emu(5.6),"",ACCENT3, prob, bg1="1A0800")
    s += card(11,emu(5.85),emu(0.92),emu(3.0),emu(5.6),"",GREEN, sol, bg1="001A00")
    s += card(12,emu(9.0),emu(0.92),emu(3.0),emu(5.6),"",ACCENT1, iot, bg1="0D1B2A")
    return slide_xml(s)


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 04 — IOT THREAT LANDSCAPE
# ════════════════════════════════════════════════════════════════════════════
def slide_04():
    s = dark_bg() + header_bar("🌐  IoT Threat Landscape", 4)
    # 4 challenge cards
    cds = [
        (emu(0.25), emu(0.92), "Limited Resources","No CPU for AV • Low RAM • Tiny storage\nCan't run traditional security software.",ACCENT1,"0A1520"),
        (emu(3.2),  emu(0.92), "Always-On Devices","Run 24/7 without updates • Forgotten after\ninstall • Firmware vulnerabilities persist.",ACCENT2,"07001A"),
        (emu(6.15), emu(0.92), "Massive Attack Surface","Billions of entry points • Default credentials\nnever changed • Direct internet exposure.",ACCENT3,"1A0800"),
        (emu(9.1),  emu(0.92), "Critical Infrastructure","Hospitals • Power grids • Water treatment\nAttacks can be life-threatening.",RED,"1A0000"),
    ]
    for i,(x,y,t,txt,col,bg) in enumerate(cds):
        lines = txt.split("\n")
        p = para(t,1500,bold=True,color=col,align="ctr")
        for l in lines: p += para(l,1150,color=WHITE,align="ctr")
        s += sp(10+i,x,y,emu(2.75),emu(2.0), gradFill(bg,"060B18"),
                p, anchor="ctr", rnd=12000, bh=col, bw=15875)
    # IDS comparison
    ids_p = (para("Signature-Based IDS",1500,bold=True,color=ACCENT3)
            +para("✅  Precise on known attacks",1200,color=WHITE)
            +para("❌  Zero-day blind spot",1200,color=RED)
            +para("❌  No learning capability",1200,color=RED))
    ae_p  = (para("Anomaly-Based IDS",1500,bold=True,color=ACCENT2)
            +para("✅  Detects unseen attacks",1200,color=WHITE)
            +para("❌  Higher false positive rate",1200,color=RED)
            +para("❌  Cannot name the attack",1200,color=RED))
    hyb_p = (para("Hybrid IDS  ← Our Approach",1500,bold=True,color=GREEN)
            +para("✅  Known + zero-day detection",1200,color=WHITE)
            +para("✅  Lower false positives",1200,color=WHITE)
            +para("✅  Names known attacks",1200,color=WHITE))
    s += card(14,emu(0.25),emu(3.15),emu(3.8),emu(3.45),"",ACCENT3, ids_p, bg1="1A0500")
    s += card(15,emu(4.2), emu(3.15),emu(3.8),emu(3.45),"",ACCENT2, ae_p,  bg1="07001A")
    s += card(16,emu(8.15),emu(3.15),emu(3.8),emu(3.45),"",GREEN,   hyb_p, bg1="001A00")
    return slide_xml(s)


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 05 — LITERATURE REVIEW
# ════════════════════════════════════════════════════════════════════════════
def slide_05():
    s = dark_bg() + header_bar("📚  Literature Review", 5)
    refs = [
        ("Ferrag et al. (2022)","Edge-IIoTset dataset — real IoT testbed,\n10 device types, 15 attack classes, 95-98% acc\nwith standard ML algos.",ACCENT1),
        ("LightGBM (Ke et al., 2017)","Microsoft Research — leaf-wise tree growth,\nhistogram binning. Outperforms XGBoost\non large tabular datasets.",GREEN),
        ("Shone et al. (2018)","Non-symmetric Autoencoder for NIDS.\nReconstruction error used as anomaly\nscore. Better than classical on NSL-KDD.",ACCENT2),
        ("Khraisat et al. (2019)","Survey of hybrid IDS: multi-model systems\nconsistently outperform single-model.\nFusion mechanism is a key variation source.",ACCENT3),
        ("Grinsztajn et al. (2022)","Tree models still outperform deep learning\non tabular data (NeurIPS 2022). Validates\nLightGBM choice over CNN/RNN.",YELLOW),
        ("Emmott et al. (2016)","Isolation Forest fails when anomalies\noutnumber normals (majority class bias).\nExplains our 49% IF baseline result.",RED),
    ]
    for i,(auth,txt,col) in enumerate(refs):
        row = i // 3; col_n = i % 3
        x = emu(0.25) + col_n * emu(4.0)
        y = emu(0.92) + row * emu(2.85)
        lines = txt.split("\n")
        p = para(auth,1300,bold=True,color=col)
        for l in lines: p += para(l,1100,color=WHITE)
        s += sp(10+i, x, y, emu(3.85), emu(2.6),
                gradFill("0D1B2A","060B18"), p, anchor="t",
                rnd=10000, bh=col, bw=12700)
    # gap note
    s += sp(16,emu(0.25),H-emu(0.78),W-emu(0.5),emu(0.6),
            gradFill("0A001A","060B18"),
            para("📌  Research Gap: Most IDS research tests only known attacks. This project extends to zero-day simulation with 5 unseen classes — a stronger evaluation protocol.",1200,color=LTGRAY,align="ctr"),
            anchor="ctr", rnd=8000, bh=ACCENT2, bw=9525)
    return slide_xml(s)


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 06 — DATASET
# ════════════════════════════════════════════════════════════════════════════
def slide_06():
    s = dark_bg() + header_bar("📊  Dataset — Edge-IIoTset", 6)
    s += stat(10, emu(0.25),emu(0.9),  emu(2.7),emu(1.5), "157,800","Raw Network Rows",ACCENT1)
    s += stat(11, emu(3.15),emu(0.9),  emu(2.7),emu(1.5), "152,389","After Cleaning",GREEN)
    s += stat(12, emu(6.05),emu(0.9),  emu(2.7),emu(1.5), "53",     "Feature Columns",ACCENT2)
    s += stat(13, emu(9.0), emu(0.9),  emu(2.9),emu(1.5), "15",     "Traffic Classes",ACCENT3)
    known = (para("✅  Known Classes — 10 Types (Training)",1400,bold=True,color=GREEN)
            +para("Normal · Backdoor · DDoS_HTTP · DDoS_ICMP",1200,color=WHITE)
            +para("DDoS_TCP · DDoS_UDP · Password · Port_Scanning",1200,color=WHITE)
            +para("Ransomware · SQL_Injection",1200,color=WHITE)
            +ep()+para("📦  121,293 training samples",1250,bold=True,color=GREEN))
    zd   = (para("🚨  Zero-Day — 5 Types (Hidden Test Only)",1400,bold=True,color=ACCENT3)
            +para("Fingerprinting · MITM · Uploading",1200,color=WHITE)
            +para("Vulnerability_Scanner · XSS",1200,color=WHITE)
            +ep()+para("📦  31,096 samples (NEVER seen in training)",1250,bold=True,color=ACCENT3))
    info = (para("Edge-IIoTset  |  Ferrag et al., 2022",1400,bold=True,color=ACCENT1)
            +para("Real IoT lab testbed — 10 device types including IP cameras, temp/humidity",1200,color=WHITE)
            +para("sensors, weather stations, water monitors. Captured via Wireshark.",1200,color=LTGRAY)
            +para("Protocols: MQTT · HTTP · DNS · TCP · UDP · ARP · Modbus TCP",1200,color=LTGRAY))
    s += sp(14,emu(0.25),emu(2.55),emu(5.7),emu(2.05),
            gradFill("001A00","0D1B2A"), known, anchor="t", rnd=10000, bh=GREEN, bw=19050)
    s += sp(15,emu(6.2), emu(2.55),emu(5.7),emu(2.05),
            gradFill("1A0000","0D1B2A"), zd,    anchor="t", rnd=10000, bh=ACCENT3, bw=19050)
    s += sp(16,emu(0.25),emu(4.75),W-emu(0.5),emu(1.85),
            gradFill("0D1B2A","060B18"), info, anchor="ctr", rnd=10000, bh=ACCENT1, bw=12700)
    return slide_xml(s)


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 07 — DATA DISTRIBUTION & CLASS SPLIT
# ════════════════════════════════════════════════════════════════════════════
def slide_07():
    s = dark_bg() + header_bar("📈  Data Distribution & Class Split", 7)
    # class distribution bars
    classes = [
        ("Normal",        24152, GREEN),
        ("DDoS_UDP",      14498, ACCENT1),
        ("DDoS_ICMP",     13096, ACCENT1),
        ("DDoS_HTTP",     10559, ACCENT1),
        ("SQL_Injection", 10286, ACCENT2),
        ("DDoS_TCP",      10247, ACCENT1),
        ("Uploading*",    10237, ACCENT3),
        ("Vuln.Scanner*", 10062, ACCENT3),
        ("Password",       9978, ACCENT2),
        ("Backdoor",       9866, ACCENT2),
        ("Ransomware",     9690, ACCENT2),
        ("XSS*",           9550, ACCENT3),
        ("Port_Scanning",  8921, ACCENT2),
        ("Fingerprinting*",  853, RED),
        ("MITM*",            394, RED),
    ]
    max_v = 24152
    s += sp(10,emu(0.25),emu(0.88),emu(1.4),emu(0.38),
            solidFill("00000000"),
            para("Class Distribution  (* = Zero-Day)",1300,bold=True,color=WHITE))
    for i,(name,count,col) in enumerate(classes):
        y = emu(1.3) + i*emu(0.34)
        bar_w = max(emu(0.15), int((count/max_v)*emu(4.8)))
        s += sp(20+i, emu(0.25), y, emu(1.35), emu(0.28),
                solidFill("00000000"), para(name,950,color=WHITE), anchor="ctr")
        s += sp(40+i, emu(1.65), y, bar_w, emu(0.27),
                gradFill(col,"0D1B2A",0),
                para(f"{count:,}",950,color=WHITE,align="r"), anchor="ctr", rnd=4000)
    # key observations
    obs = (para("Key Observations",1600,bold=True,color=YELLOW)
          +ep()
          +para("⚡  84% attacks · 16% normal (class imbalance)",1250,color=WHITE)
          +para("   → Accuracy alone is a misleading metric.",1150,color=LTGRAY)
          +ep()
          +para("📊  DDoS_UDP (14,498) vs MITM (394)",1250,color=WHITE)
          +para("   → 37:1 ratio — models struggle on rare classes.",1150,color=LTGRAY)
          +ep()
          +para("🎯  Critical Design Decision:",1400,bold=True,color=ACCENT1)
          +para("   5 zero-day classes chosen to represent diverse",1200,color=WHITE)
          +para("   attack vectors: web attacks (XSS), recon",1200,color=WHITE)
          +para("   (Fingerprinting, Vuln.Scan), exfiltration",1200,color=WHITE)
          +para("   (Uploading), interception (MITM).",1200,color=WHITE)
          +ep()
          +para("⚠  If even one zero-day sample were included",1150,color=LTGRAY,italic=True)
          +para("   in training, the evaluation would be invalid.",1150,color=LTGRAY,italic=True))
    s += sp(60, emu(6.75), emu(0.88), emu(5.2), emu(5.75),
            gradFill("0D1B2A","060B18"), obs, anchor="t",
            rnd=10000, bh=ACCENT1, bw=12700)
    return slide_xml(s)


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 08 — PREPROCESSING PIPELINE
# ════════════════════════════════════════════════════════════════════════════
def slide_08():
    s = dark_bg() + header_bar("⚙️  Data Preprocessing Pipeline", 8)
    steps = [
        (emu(0.25), "① Load Raw CSV",    "157,800 × 63 cols\nML-EdgeIIoT-dataset.csv",ACCENT1),
        (emu(2.6),  "② Drop Columns",    "63 → 53 features\nRemove IPs · timestamps · URIs",ACCENT2),
        (emu(4.95), "③ Clean Data",      "157,800 → 152,389\nDrop nulls & duplicates",ACCENT3),
        (emu(7.3),  "④ Encode & Optimise","Label-encode text cols\nfloat64→float32 (-50% RAM)",GREEN),
        (emu(9.65), "⑤ Split Dataset",   "Known: 121,293 rows\nZero-day: 31,096 rows",YELLOW),
    ]
    for i,(x,t,sub,col) in enumerate(steps):
        lines = sub.split("\n")
        p = para(t,1300,bold=True,color=col,align="ctr")
        for l in lines: p += para(l,1100,color=WHITE,align="ctr")
        s += sp(10+i, x, emu(0.92), emu(2.2), emu(1.85),
                gradFill("0D1B2A","060B18"), p, anchor="ctr", rnd=12000, bh=col, bw=17780)
        if i<4:
            mx = x+emu(2.2); my = emu(0.92)+emu(0.92)
            s += line(20+i, mx, my, mx+emu(0.4), my, col, 34925)

    scaler_p = (para("⑥ StandardScaler  — Fitted ONLY on Normal Traffic",1500,bold=True,color=ACCENT1)
               +para("Formula:  z = (x − mean) / std_dev   →   All 51 features scaled to ~[-3, +3]",1250,color=WHITE)
               +para("Why normal-only? Contaminating with attack stats would corrupt the Autoencoder's normalcy baseline.",1200,color=LTGRAY)
               +para("Saved as scaler.pkl — shared by ALL subsequent notebooks to ensure pipeline consistency.",1200,color=LTGRAY))
    s += sp(15,emu(0.25),emu(2.97),W-emu(0.5),emu(1.5),
            gradFill("0D2137","060B18"), scaler_p, anchor="ctr", rnd=10000, bh=ACCENT1, bw=17780)

    why_p = (para("Why These Columns Were Dropped",1450,bold=True,color=ACCENT2)
            +para("ip.src/dst_host → IP addresses encode identity, not behaviour. Model would overfit to attacker IPs.",1200,color=WHITE)
            +para("frame.time → Timestamps encode when, not what. A new attack at a different time would be missed.",1200,color=WHITE)
            +para("http.file_data / request.full_uri → Raw free-text fields need NLP — beyond project scope.",1200,color=WHITE))
    out_p  = (para("Outputs (Parquet — 10× smaller than CSV)",1450,bold=True,color=GREEN)
             +para("master_clean.parquet  ·  known_train.parquet  ·  zero_day_test.parquet  ·  scaler.pkl",1200,color=WHITE))
    s += sp(16,emu(0.25),emu(4.62),emu(7.15),emu(2.0),
            gradFill("07001A","060B18"), why_p, anchor="t", rnd=10000, bh=ACCENT2, bw=12700)
    s += sp(17,emu(7.55),emu(4.62),emu(4.4), emu(2.0),
            gradFill("001A00","060B18"), out_p, anchor="t", rnd=10000, bh=GREEN, bw=12700)
    return slide_xml(s)



# ════════════════════════════════════════════════════════════════════════════
# SLIDE 09 — SYSTEM ARCHITECTURE
# ════════════════════════════════════════════════════════════════════════════
def slide_09():
    s = dark_bg() + header_bar("🏗️  System Architecture", 9)
    boxes = [
        (emu(0.25),emu(1.0),  emu(2.15),emu(1.15),"RAW IoT TRAFFIC","157,800 packets",ACCENT1),
        (emu(0.25),emu(2.45), emu(2.15),emu(1.15),"PREPROCESSING", "Clean·Encode·Scale",ACCENT2),
        (emu(2.7), emu(1.55), emu(2.4), emu(2.6), "LightGBM",      "Known Attacks\n10 classes · 99.99%",GREEN),
        (emu(5.3), emu(1.55), emu(2.4), emu(2.6), "Autoencoder",   "Zero-Day Detector\nRecon error · 99.19%",ACCENT2),
        (emu(7.9), emu(1.55), emu(2.15),emu(2.6), "FUSION MODEL",  "Confidence routing\n96.82% accuracy",ACCENT3),
        (emu(10.3),emu(2.0),  emu(1.65),emu(1.7), "OUTPUT",        "Normal / Attack",ACCENT1),
    ]
    for i,(x,y,cx,cy,t,sub,col) in enumerate(boxes):
        lines = sub.split("\n")
        p = para(t,1300,bold=True,color=col,align="ctr")
        for l in lines: p += para(l,1050,color=LTGRAY,align="ctr")
        s += sp(10+i,x,y,cx,cy, gradFill("0D1B2A","060B18"),
                p, anchor="ctr", rnd=14000, bh=col, bw=17780)
    # arrows
    s += line(30, emu(1.33),emu(2.15), emu(1.33),emu(2.45), ACCENT1, 34925)
    s += line(31, emu(2.4), emu(3.02), emu(2.7),  emu(2.85), ACCENT1, 22225)
    s += line(32, emu(2.4), emu(3.02), emu(5.3),  emu(2.85), ACCENT2, 22225)
    s += line(33, emu(5.1), emu(2.85), emu(7.9),  emu(2.85), GREEN,   22225)
    s += line(34, emu(7.7), emu(2.85), emu(7.9),  emu(2.85), ACCENT2, 22225)
    s += line(35, emu(10.05),emu(2.85),emu(10.3), emu(2.85), ACCENT3, 22225)

    logic = (para("Fusion Decision Logic",1400,bold=True,color=ACCENT3)
            +para("IF  LightGBM(confidence for Normal) ≥ 90%  →  Label = Normal",1250,color=WHITE)
            +para("ELSE  →  Compute Autoencoder reconstruction error",1250,color=WHITE)
            +para("         IF  error > 0.0122  →  Label = Attack  ELSE  →  Label = Normal",1250,color=LTGRAY))
    insight = para("💡  Three-layer defence: Supervised precision + Unsupervised zero-day coverage + Intelligent routing",1250,color=ACCENT1,align="ctr")
    s += sp(36,emu(0.25),emu(4.35),W-emu(0.5),emu(1.3),
            gradFill("1A0800","0D1B2A"), logic, anchor="ctr", rnd=10000, bh=ACCENT3, bw=17780)
    s += sp(37,emu(0.25),emu(5.8),  W-emu(0.5),emu(0.78),
            gradFill("0A001A","060B18"), insight, anchor="ctr", rnd=8000, bh=ACCENT2, bw=9525)
    return slide_xml(s)


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 10 — LIGHTGBM MODEL & TRAINING
# ════════════════════════════════════════════════════════════════════════════
def slide_10():
    s = dark_bg() + header_bar("🌲  LightGBM — Model & Training", 10)
    what = (para("What is LightGBM?",1600,bold=True,color=GREEN)
           +para("Gradient Boosted Decision Tree by Microsoft Research (2017).",1200,color=WHITE)
           +para("Grows trees leaf-by-leaf (not level-by-level) — better accuracy",1200,color=WHITE)
           +para("for the same num of leaves. Histogram binning for fast splits.",1200,color=LTGRAY)
           +ep()
           +para("Why for IoT IDS?",1500,bold=True,color=GREEN)
           +para("✔  Trains 300 trees on 97k rows in ~35 seconds",1200,color=WHITE)
           +para("✔  Handles class imbalance natively",1200,color=WHITE)
           +para("✔  Feature importance output for interpretability",1200,color=WHITE)
           +para("✔  Millisecond inference — suitable for real-time",1200,color=WHITE)
           +para("✔  No feature scaling required (tree-invariant)",1200,color=WHITE))
    params = (para("Hyperparameters",1600,bold=True,color=ACCENT1)
             +kv("n_estimators","300",sz=1200)
             +kv("learning_rate","0.05  (stable convergence)",sz=1200)
             +kv("max_depth","10  (up to 1,024 leaf nodes)",sz=1200)
             +kv("num_leaves","50  (leaf-wise growth cap)",sz=1200)
             +kv("objective","multiclass  (softmax output)",sz=1200)
             +kv("subsample","0.8  (row bagging)",sz=1200)
             +kv("colsample_bytree","0.8  (feature bagging)",sz=1200)
             +kv("random_state","42  (reproducibility)",sz=1200))
    data  = (para("Training Data",1600,bold=True,color=ACCENT2)
            +para("Train: 97,034 samples (80%)",1200,color=WHITE)
            +para("Test:  24,259 samples (20%)",1200,color=WHITE)
            +para("Features: 51 network packet fields",1200,color=WHITE)
            +para("Classes: 10 (Normal + 9 attack types)",1200,color=WHITE)
            +ep()
            +para("Stratified split ensures each class",1150,color=LTGRAY)
            +para("appears in same proportion in train",1150,color=LTGRAY)
            +para("and test sets (essential for rare classes).",1150,color=LTGRAY))
    s += card(10,emu(0.25),emu(0.9), emu(5.5),emu(5.75),"",GREEN,   what,  bg1="001A00")
    s += card(11,emu(5.9), emu(0.9), emu(3.0), emu(5.75),"",ACCENT1, params,bg1="0D1B2A")
    s += card(12,emu(9.05),emu(0.9), emu(3.0), emu(5.75),"",ACCENT2, data,  bg1="07001A")
    return slide_xml(s)


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 11 — LIGHTGBM RESULTS & PER-CLASS
# ════════════════════════════════════════════════════════════════════════════
def slide_11():
    s = dark_bg() + header_bar("📊  LightGBM — Results & Per-Class F1", 11)
    s += stat(10,emu(0.25),emu(0.88),emu(2.6),emu(1.45),"99.99%","Overall Accuracy",GREEN)
    s += stat(11,emu(3.05),emu(0.88),emu(2.6),emu(1.45),"99.98%","Macro Precision",ACCENT1)
    s += stat(12,emu(5.85),emu(0.88),emu(2.6),emu(1.45),"99.99%","Macro Recall",ACCENT2)
    s += stat(13,emu(8.65),emu(0.88),emu(3.3),emu(1.45),"~3",    "Total Misclassifications",ACCENT3)

    # per-class table
    rows = [
        ("Backdoor",           1973, "1.0000","0.9995","0.9997",GREEN),
        ("DDoS_HTTP",          2112, "1.0000","1.0000","1.0000",GREEN),
        ("DDoS_ICMP",          2619, "1.0000","1.0000","1.0000",GREEN),
        ("DDoS_TCP",           2049, "1.0000","1.0000","1.0000",GREEN),
        ("DDoS_UDP",           2900, "1.0000","1.0000","1.0000",GREEN),
        ("Normal",             4831, "1.0000","1.0000","1.0000",GREEN),
        ("Password",           1996, "0.9995","1.0000","0.9997",ACCENT1),
        ("Port_Scanning",      1784, "0.9994","1.0000","0.9997",ACCENT1),
        ("Ransomware",         1938, "0.9995","1.0000","0.9997",ACCENT1),
        ("SQL_Injection",      2057, "1.0000","0.9995","0.9997",ACCENT1),
    ]
    hdr = (para("Class               Support   Prec.   Recall   F1",1200,bold=True,color=ACCENT1)
          +line(30, emu(0.25), emu(3.7), emu(11.9), emu(3.7), ACCENT1, 9525))
    tbl = hdr
    for name,sup,prec,rec,f1,col in rows:
        tbl += para(f"  {name:<22} {sup:>5}   {prec}   {rec}   {f1}",1150,color=col)
    s += sp(14,emu(0.25),emu(2.5),W-emu(0.5),emu(4.05),
            gradFill("0D1B2A","060B18"), tbl, anchor="t", rnd=10000, bh=GREEN, bw=12700)
    note = para("💡  Training warning 'No further splits with positive gain' = model converged perfectly. Not an error — the data is cleanly separable.",1200,color=LTGRAY,align="ctr")
    s += sp(15,emu(0.25),emu(6.68),W-emu(0.5),emu(0.72),
            gradFill("001A00","060B18"), note, anchor="ctr", rnd=8000, bh=GREEN, bw=9525)
    return slide_xml(s)


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 12 — AUTOENCODER ARCHITECTURE
# ════════════════════════════════════════════════════════════════════════════
def slide_12():
    s = dark_bg() + header_bar("🧠  Autoencoder — Architecture", 12)
    # visual architecture diagram
    layers_info = [
        (emu(0.4), "Input",       "51 neurons","One per feature",        LTGRAY),
        (emu(1.65),"Dense(64)",   "64 neurons","Encoder expands",        ACCENT1),
        (emu(2.9), "Dense(32)",   "32 neurons","Compression",            ACCENT1),
        (emu(4.15),"Bottleneck",  "16 neurons","Max compression 3:1",    ACCENT2),
        (emu(5.4), "Dense(32)",   "32 neurons","Decoder expands",        ACCENT3),
        (emu(6.65),"Dense(64)",   "64 neurons","Further expansion",      ACCENT3),
        (emu(7.9), "Output",      "51 neurons","Reconstruction",         GREEN),
    ]
    for i,(x,name,neurons,role,col) in enumerate(layers_info):
        p = (para(name,1200,bold=True,color=col,align="ctr")
            +para(neurons,1100,color=WHITE,align="ctr")
            +para(role,950,color=LTGRAY,align="ctr"))
        s += sp(10+i, x, emu(0.95), emu(1.1), emu(1.7),
                gradFill("0D1B2A","060B18"), p, anchor="ctr", rnd=10000, bh=col, bw=14288)
        if i < 6:
            s += line(30+i, x+emu(1.1), emu(1.8), x+emu(1.25), emu(1.8), col, 22225)

    detail = (para("Architecture Details",1600,bold=True,color=ACCENT2)
             +kv("Total Parameters","11,907  (ultra-lightweight!)",sz=1200)
             +kv("Activation (hidden)","ReLU — f(x)=max(0,x), avoids vanishing gradient",sz=1200)
             +kv("Activation (output)","Linear — allows any real number reconstruction",sz=1200)
             +kv("Loss Function","MSE — penalises large errors more heavily",sz=1200)
             +kv("Optimizer","Adam — adaptive learning rate per parameter",sz=1200)
             +kv("Bottleneck","16 neurons from 51 inputs = 3.1:1 compression",sz=1200)
             +ep()
             +para("Why 16 neurons? Tested 8 (too tight, high FP) and 32",1150,color=LTGRAY)
             +para("(no improvement). 16 gave best precision/recall balance.",1150,color=LTGRAY))
    principle = (para("Core Principle",1600,bold=True,color=GREEN)
                +para("Train ONLY on normal traffic (24,152 rows).",1250,color=WHITE)
                +para("The model learns to compress & reconstruct normal.",1200,color=WHITE)
                +ep()
                +para("For attacks: the bottleneck creates a poor encoding",1200,color=WHITE)
                +para("using normal-traffic patterns. The decoder outputs",1200,color=WHITE)
                +para("something that resembles normal traffic, not the attack.",1200,color=WHITE)
                +para("The mismatch (high MSE) = anomaly signal.",1300,bold=True,color=ACCENT1))
    s += card(17,emu(0.25),emu(2.85),emu(5.9), emu(3.8),"",ACCENT2, detail,  bg1="07001A")
    s += card(18,emu(6.3), emu(2.85),emu(5.65),emu(3.8),"",GREEN,   principle,bg1="001A00")
    return slide_xml(s)


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 13 — AUTOENCODER TRAINING & THRESHOLD
# ════════════════════════════════════════════════════════════════════════════
def slide_13():
    s = dark_bg() + header_bar("🧠  Autoencoder — Training & Threshold Calibration", 13)
    s += stat(10,emu(0.25),emu(0.88),emu(2.7),emu(1.4),"99.19%","Overall Accuracy",GREEN)
    s += stat(11,emu(3.1), emu(0.88),emu(2.7),emu(1.4),"100%",  "Attack Recall",ACCENT2)
    s += stat(12,emu(5.95),emu(0.88),emu(2.7),emu(1.4),"0.0122","Anomaly Threshold τ",YELLOW)
    s += stat(13,emu(8.8), emu(0.88),emu(3.1),emu(1.4),"11,907","Parameters",ACCENT1)

    train_p = (para("Training Details",1550,bold=True,color=ACCENT2)
              +kv("Training samples","19,321 normal rows (80%)",sz=1200)
              +kv("Validation samples","4,831 normal rows (20%)",sz=1200)
              +kv("Epochs","Up to 50 — stopped at Epoch 45",sz=1200)
              +kv("Batch size","256",sz=1200)
              +kv("Early stopping","patience=5, restore_best_weights",sz=1200)
              +ep()
              +para("Training progress (val_loss):",1250,bold=True,color=ACCENT1)
              +para("Epoch  1: 0.5692 → 0.3141  (learning fast)",1150,color=LTGRAY)
              +para("Epoch 10: 0.0698 → 0.0585  (converging)",1150,color=LTGRAY)
              +para("Epoch 40: 0.0141 → 0.0139  (best epoch ★)",1150,color=GREEN)
              +para("Epoch 45: early stopped (5 no-improve epochs)",1150,color=ACCENT3))
    thresh_p = (para("Threshold Calibration",1550,bold=True,color=YELLOW)
               +para("After training, run all 4,831 validation normal",1200,color=WHITE)
               +para("samples through the AE. Compute per-sample MSE.",1200,color=WHITE)
               +ep()
               +para("τ = Percentile₉₅(val_errors) = 0.01218",1400,bold=True,color=YELLOW)
               +ep()
               +para("95th percentile means:",1250,bold=True,color=WHITE)
               +para("• 95% of normal traffic → error < τ → NORMAL",1200,color=GREEN)
               +para("• 5% of normal traffic → error > τ → false alarm",1200,color=ACCENT3)
               +ep()
               +para("Trade-off: Lower τ = fewer missed attacks,",1150,color=LTGRAY)
               +para("more false alarms. 95th percentile is standard",1150,color=LTGRAY)
               +para("practice in anomaly detection literature.",1150,color=LTGRAY))
    res_p   = (para("Autoencoder Results",1550,bold=True,color=GREEN)
              +para("Tested on full 152,389-row dataset",1200,color=LTGRAY)
              +ep()
              +para("Class 0 (Normal):",1250,bold=True,color=WHITE)
              +para("  Precision: 100%  Recall: 94.87%",1200,color=WHITE)
              +para("  1,239 false positives (5.13%)",1150,color=ACCENT3)
              +ep()
              +para("Class 1 (Attack):",1250,bold=True,color=WHITE)
              +para("  Precision: 99.04%  Recall: 100%",1200,color=GREEN)
              +para("  0 false negatives — ALL 128,237",1300,bold=True,color=GREEN)
              +para("  attack samples detected!",1300,bold=True,color=GREEN)
              +ep()
              +para("Includes ALL 5 zero-day attack types",1200,color=ACCENT2)
              +para("never seen during training.",1200,color=ACCENT2))
    s += card(14,emu(0.25),emu(2.45),emu(3.8), emu(4.2),"",ACCENT2, train_p, bg1="07001A")
    s += card(15,emu(4.2), emu(2.45),emu(3.8), emu(4.2),"",YELLOW,  thresh_p,bg1="1A1400")
    s += card(16,emu(8.15),emu(2.45),emu(3.8), emu(4.2),"",GREEN,   res_p,   bg1="001A00")
    return slide_xml(s)



# ════════════════════════════════════════════════════════════════════════════
# SLIDE 14 — FUSION MODEL LOGIC
# ════════════════════════════════════════════════════════════════════════════
def slide_14():
    s = dark_bg() + header_bar("⚡  Fusion Model — Logic & Routing", 14)
    why  = (para("Why a Fusion Model?",1600,bold=True,color=ACCENT3)
           +ep()
           +para("LightGBM alone:",1300,bold=True,color=WHITE)
           +para("  ✅ 99.99% on known attacks",1200,color=GREEN)
           +para("  ❌ 0% on zero-day attacks — forces",1200,color=RED)
           +para("     every input into a known class",1200,color=RED)
           +ep()
           +para("Autoencoder alone:",1300,bold=True,color=WHITE)
           +para("  ✅ 100% attack recall",1200,color=GREEN)
           +para("  ❌ 5.13% false positive rate",1200,color=RED)
           +para("  ❌ Cannot name the attack type",1200,color=RED)
           +ep()
           +para("Fusion: Best of Both Worlds",1400,bold=True,color=YELLOW)
           +para("  ✅ Known attacks handled precisely",1200,color=GREEN)
           +para("  ✅ Zero-day attacks caught by AE",1200,color=GREEN)
           +para("  ✅ Reduced false positives",1200,color=GREEN))
    logic = (para("Decision Logic",1600,bold=True,color=ACCENT1)
            +ep()
            +para("Step 1:  Run LightGBM on input sample",1250,color=WHITE)
            +para("Step 2:  Get predict_proba() — confidence vector",1250,color=WHITE)
            +ep()
            +para("IF  P(Normal) ≥ 0.90",1400,bold=True,color=GREEN)
            +para("  → Label = Normal  (trust LightGBM)",1300,color=GREEN)
            +ep()
            +para("ELSE  (LightGBM uncertain)",1400,bold=True,color=ACCENT3)
            +para("  → Compute AE reconstruction error",1250,color=WHITE)
            +para("  → IF  error > 0.0122",1250,color=WHITE)
            +para("       Label = ATTACK",1300,bold=True,color=ACCENT3)
            +para("  → ELSE  Label = Normal",1300,bold=True,color=GREEN)
            +ep()
            +para("Genuine normals: LightGBM ≥95% confident",1150,color=LTGRAY)
            +para("Zero-day attacks: LightGBM 60-85% confident",1150,color=LTGRAY)
            +para("→ 90% threshold cleanly separates them.",1150,color=LTGRAY))
    thresh = (para("Why 0.90?",1600,bold=True,color=YELLOW)
             +para("Tested: 0.70 · 0.80 · 0.90 · 0.95",1200,color=WHITE)
             +ep()
             +para("0.70 → too many AE checks → high FP",1150,color=ACCENT3)
             +para("0.80 → borderline normal re-evaluated",1150,color=ACCENT3)
             +para("0.90 → sweet spot  ✅",1250,bold=True,color=GREEN)
             +para("0.95 → zero-day slips past LightGBM",1150,color=ACCENT3)
             +ep()
             +para("Security principle: false negatives (missed",1150,color=LTGRAY)
             +para("attacks) more dangerous than false positives",1150,color=LTGRAY)
             +para("(false alarms). Err on side of caution.",1150,color=LTGRAY)
             +ep()
             +para("Note: AE only runs on uncertain samples.",1200,color=ACCENT1)
             +para("LightGBM handles >90% of traffic alone.",1200,color=ACCENT1))
    s += card(10,emu(0.25),emu(0.9),emu(3.65),emu(5.8),"",ACCENT3, why,   bg1="1A0800")
    s += card(11,emu(4.1), emu(0.9),emu(4.15),emu(5.8),"",ACCENT1, logic, bg1="0D1B2A")
    s += card(12,emu(8.45),emu(0.9),emu(3.5), emu(5.8),"",YELLOW,  thresh,bg1="1A1400")
    return slide_xml(s)


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 15 — FUSION MODEL RESULTS
# ════════════════════════════════════════════════════════════════════════════
def slide_15():
    s = dark_bg() + header_bar("⚡  Fusion — Results & Confusion Matrix", 15)
    s += stat(10,emu(0.25),emu(0.88),emu(2.85),emu(1.45),"96.82%","Fusion Accuracy",GREEN)
    s += stat(11,emu(3.3), emu(0.88),emu(2.85),emu(1.45),"97.78%","Precision",ACCENT1)
    s += stat(12,emu(6.35),emu(0.88),emu(2.85),emu(1.45),"98.33%","Recall (Attacks)",ACCENT2)
    s += stat(13,emu(9.4), emu(0.88),emu(2.55),emu(1.45),"+47.8pp","vs Baseline",ACCENT3)

    # confusion matrix visual
    cm_title = para("Confusion Matrix  (55,248 test samples)",1400,bold=True,color=ACCENT1)
    # header row
    s += sp(14,emu(2.3),emu(2.55),emu(9.0),emu(0.4),solidFill("00000000"),
            para("                         Predicted Normal      Predicted Attack",1200,bold=True,color=LTGRAY))
    # TN box
    s += sp(15,emu(2.3),emu(3.0),emu(4.3),emu(1.45),
            gradFill("001A00","003300"),
            para("22,913",3200,bold=True,color=GREEN,align="ctr")+para("True Negatives ✅",1200,color=WHITE,align="ctr"),
            anchor="ctr", rnd=8000, bh=GREEN, bw=19050)
    # FP box
    s += sp(16,emu(6.75),emu(3.0),emu(4.3),emu(1.45),
            gradFill("1A0800","330800"),
            para("1,239",3200,bold=True,color=ACCENT3,align="ctr")+para("False Positives ⚠",1200,color=WHITE,align="ctr"),
            anchor="ctr", rnd=8000, bh=ACCENT3, bw=19050)
    # FN box
    s += sp(17,emu(2.3),emu(4.55),emu(4.3),emu(1.45),
            gradFill("1A0000","330000"),
            para("520",3200,bold=True,color=RED,align="ctr")+para("False Negatives ❌",1200,color=WHITE,align="ctr"),
            anchor="ctr", rnd=8000, bh=RED, bw=19050)
    # TP box
    s += sp(18,emu(6.75),emu(4.55),emu(4.3),emu(1.45),
            gradFill("001A10","003320"),
            para("30,576",3200,bold=True,color=GREEN,align="ctr")+para("True Positives ✅",1200,color=WHITE,align="ctr"),
            anchor="ctr", rnd=8000, bh=GREEN, bw=19050)
    # row/col labels
    s += sp(19,emu(0.25),emu(3.0), emu(1.95),emu(1.45),solidFill("00000000"),
            para("Actual Normal",1200,color=LTGRAY,align="ctr"), anchor="ctr")
    s += sp(20,emu(0.25),emu(4.55),emu(1.95),emu(1.45),solidFill("00000000"),
            para("Actual Attack",1200,color=LTGRAY,align="ctr"), anchor="ctr")

    analysis = (para("Key Findings",1500,bold=True,color=YELLOW)
               +ep()
               +para("520 missed attacks (1.67%):",1300,bold=True,color=RED)
               +para("Mostly Fingerprinting & Port Scanning.",1200,color=WHITE)
               +para("Low-volume, slow-paced — each packet looks",1150,color=LTGRAY)
               +para("like routine traffic. No temporal context.",1150,color=LTGRAY)
               +ep()
               +para("1,239 false positives (5.13%):",1300,bold=True,color=ACCENT3)
               +para("Unusual-but-benign normal traffic patterns.",1200,color=WHITE)
               +para("Inherent cost of 95th-percentile threshold.",1150,color=LTGRAY)
               +ep()
               +para("Test set = 24,152 normal + 31,096 zero-day",1150,color=LTGRAY)
               +para("= 55,248 total (no known attacks included).",1150,color=LTGRAY))
    s += sp(21,emu(0.25),emu(6.1),emu(1.95),emu(0.38),solidFill("00000000"),
            para("cm_title_placeholder",1,color="00000000"))
    s += card(22,emu(0.25),emu(2.55),emu(1.9),emu(3.5),"",ACCENT1,
              para("Actual  ↓  Predicted →",1150,color=LTGRAY),bg1="0D1B2A")
    s += card(23,emu(0.25),emu(6.1),W-emu(0.5),emu(1.6),"",YELLOW, analysis, bg1="1A1400")
    return slide_xml(s)


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 16 — FEATURE IMPORTANCE
# ════════════════════════════════════════════════════════════════════════════
def slide_16():
    s = dark_bg() + header_bar("🔍  Feature Importance Analysis", 16)
    features = [
        ("tcp.srcport",        13467, ACCENT1),
        ("tcp.options",        12777, ACCENT2),
        ("tcp.dstport",         8849, GREEN),
        ("tcp.ack",             7849, ACCENT3),
        ("tcp.ack_raw",         6417, YELLOW),
        ("tcp.checksum",        6109, ACCENT1),
        ("tcp.seq",             4226, ACCENT2),
        ("http.request.method", 2213, GREEN),
        ("tcp.len",             2181, ACCENT3),
        ("udp.stream",          2009, YELLOW),
    ]
    s += sp(10,emu(0.25),emu(0.88),emu(5.6),emu(0.42),solidFill("00000000"),
            para("Top 10 Feature Importances  (LightGBM, 300 trees)",1400,bold=True,color=ACCENT1))
    max_v = 13467
    for i,(name,imp,col) in enumerate(features):
        y = emu(1.42) + i*emu(0.42)
        bw = max(emu(0.1), int((imp/max_v)*emu(4.95)))
        s += sp(20+i,emu(0.25),y,emu(1.55),emu(0.34),solidFill("00000000"),
                para(name,1050,color=WHITE), anchor="ctr")
        s += sp(30+i,emu(1.85),y,bw,emu(0.32),
                gradFill(col,"0D1B2A",0),
                para(f"{imp:,}",1000,color=WHITE,align="r"), anchor="ctr", rnd=4000)

    insights = (para("Key Insights",1600,bold=True,color=ACCENT1)
               +ep()
               +para("🔹 TCP port features dominate",1300,bold=True,color=WHITE)
               +para("Different attacks use specific port patterns.",1150,color=LTGRAY)
               +para("DDoS targets port 80; backdoors use odd ports.",1150,color=LTGRAY)
               +ep()
               +para("🔹 TCP control fields critical",1300,bold=True,color=WHITE)
               +para("ACK, SEQ, checksum, options — fingerprint",1150,color=LTGRAY)
               +para("connection behaviour uniquely per attack type.",1150,color=LTGRAY)
               +ep()
               +para("🔹 HTTP method separates web attacks",1300,bold=True,color=WHITE)
               +para("GET/POST patterns distinguish SQL injection,",1150,color=LTGRAY)
               +para("XSS, and upload attacks.",1150,color=LTGRAY)
               +ep()
               +para("🔹 14 features scored exactly ZERO",1300,bold=True,color=ACCENT3)
               +para("ARP metadata, some MQTT & DNS fields,",1150,color=LTGRAY)
               +para("http.tls_port. Could prune to reduce model.",1150,color=LTGRAY)
               +ep()
               +para("Top 11 features carry 90%+ of signal.",1300,bold=True,color=YELLOW))
    s += card(40,emu(7.1),emu(0.88),emu(4.85),emu(5.85),"",ACCENT1, insights, bg1="0D1B2A")
    return slide_xml(s)


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 17 — MODEL COMPARISON & BASELINES
# ════════════════════════════════════════════════════════════════════════════
def slide_17():
    s = dark_bg() + header_bar("📈  Model Comparison & Baselines", 17)
    s += stat(10,emu(0.25),emu(0.88),emu(2.7), emu(1.45),"99.99%","LightGBM",GREEN)
    s += stat(11,emu(3.15),emu(0.88),emu(2.7), emu(1.45),"99.19%","Autoencoder",ACCENT2)
    s += stat(12,emu(6.05),emu(0.88),emu(2.7), emu(1.45),"96.82%","Fusion Model",ACCENT1)
    s += stat(13,emu(9.0), emu(0.88),emu(2.95),emu(1.45),"49.00%","Isolation Forest",ACCENT3)

    # comparison table
    tbl_hdr = (para("MODEL              ACCURACY   PRECISION  RECALL    F1    ZERO-DAY?",1200,bold=True,color=ACCENT1)
              +line(20,emu(0.25),emu(4.1),emu(11.9),emu(4.1),ACCENT1,9525))
    tbl_rows = (para("Isolation Forest   49.00%     ~50%       ~50%     ~50%    Yes (poor)",1200,color=LTGRAY)
               +para("LightGBM           99.99%     99.98%    99.99%   99.99%   NO",1200,color=GREEN)
               +para("Autoencoder        99.19%     99.04%    99.19%   99.18%   Yes ✅",1200,color=ACCENT2)
               +para("Fusion Model       96.82%     97.78%    98.33%   97.20%   Yes ✅",1200,color=ACCENT1))
    s += sp(14,emu(0.25),emu(2.55),W-emu(0.5),emu(2.35),
            gradFill("0D1B2A","060B18"), tbl_hdr+tbl_rows, anchor="t",
            rnd=10000, bh=ACCENT1, bw=12700)

    iso_p = (para("Why Isolation Forest Failed (49%)",1500,bold=True,color=ACCENT3)
            +para("Works by randomly partitioning the feature space",1200,color=WHITE)
            +para("and scoring easily-isolated points as anomalies.",1200,color=WHITE)
            +ep()
            +para("Problems on this dataset:",1300,bold=True,color=WHITE)
            +para("• 84% attacks — majority class is anomaly → bias",1200,color=LTGRAY)
            +para("• High-dimensional (51 features) — partitioning",1200,color=LTGRAY)
            +para("  dominated by most common features",1200,color=LTGRAY)
            +para("• Multi-modal attack distribution — clusters spread",1200,color=LTGRAY)
            +ep()
            +para("Validates: deep learning AE needed for IoT traffic.",1250,bold=True,color=ACCENT1))
    context = (para("Interpreting 96.82% Correctly",1500,bold=True,color=YELLOW)
              +ep()
              +para("Fusion 96.82% vs LightGBM 99.99%:",1300,bold=True,color=WHITE)
              +para("NOT a fair comparison — they test different",1200,color=WHITE)
              +para("scenarios! LightGBM tested on attacks it was",1200,color=WHITE)
              +para("trained on. Fusion tested on UNSEEN zero-days.",1200,color=WHITE)
              +ep()
              +para("LightGBM on zero-day scenario: ~0%",1300,bold=True,color=RED)
              +para("Fusion on zero-day scenario: 96.82%",1300,bold=True,color=GREEN)
              +ep()
              +para("+47.82 percentage points above baseline.",1400,bold=True,color=GREEN))
    s += card(15,emu(0.25),emu(5.05),emu(5.85),emu(2.65),"",ACCENT3, iso_p,   bg1="1A0800")
    s += card(16,emu(6.2), emu(5.05),emu(5.75),emu(2.65),"",YELLOW,  context, bg1="1A1400")
    return slide_xml(s)


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 18 — TECH STACK & IMPLEMENTATION
# ════════════════════════════════════════════════════════════════════════════
def slide_18():
    s = dark_bg() + header_bar("💻  Tech Stack & Implementation", 18)
    stack = [
        ("Python 3.10+",        "Core language",                         ACCENT1),
        ("Pandas / NumPy",       "Data loading, manipulation, maths",     ACCENT1),
        ("Scikit-learn",         "Preprocessing, metrics, IF baseline",   ACCENT2),
        ("LightGBM 4.x",         "Gradient boosted classifier",           GREEN),
        ("TensorFlow / Keras",   "Autoencoder neural network",            ACCENT2),
        ("Matplotlib / Seaborn", "Visualisation & confusion matrices",    ACCENT3),
        ("KaggleHub",            "Automated dataset download",            ACCENT3),
        ("joblib",               "Model serialisation (.pkl files)",      YELLOW),
        ("Google Colab + T4 GPU","Training environment (12GB VRAM)",      ACCENT1),
        ("Parquet (PyArrow)",    "10× smaller than CSV, type-safe",       GREEN),
    ]
    stk_p = para("Tech Stack",1500,bold=True,color=ACCENT1)
    for lib,desc,col in stack:
        stk_p += para(f"  {lib:<24} {desc}",1150,color=col)

    nbs = [
        ("NB 01","Preprocessing Master",  "Downloads, cleans, encodes, splits, scales",ACCENT1),
        ("NB 02","Known Attack LightGBM", "Trains & evaluates LightGBM on 10 classes", GREEN),
        ("NB 03","Zero-Day Autoencoder",  "Trains AE on normal only, calibrates τ",    ACCENT2),
        ("NB 04","Fusion Model",          "Confidence-based fusion evaluation",        ACCENT3),
        ("NB 05","Visualisation",         "Comparative plots and summary charts",      YELLOW),
    ]
    nb_p = para("Notebook Pipeline",1500,bold=True,color=ACCENT2)
    for nb,name,desc,col in nbs:
        nb_p += para(f"  {nb}  {name:<24} {desc}",1150,color=col)

    artifacts = (para("Saved Model Artifacts",1500,bold=True,color=GREEN)
                +para("lightgbm_known.pkl   — 300-tree LightGBM classifier",1200,color=WHITE)
                +para("autoencoder.keras    — AE weights & architecture",1200,color=WHITE)
                +para("scaler.pkl           — StandardScaler (normal-traffic fitted)",1200,color=WHITE)
                +para("ae_threshold.pkl     — τ = 0.01218",1200,color=WHITE)
                +ep()
                +para("Shared Scaler Design:",1400,bold=True,color=ACCENT1)
                +para("All notebooks use the SAME scaler.pkl.",1200,color=WHITE)
                +para("Different scalers → inconsistent feature ranges",1150,color=LTGRAY)
                +para("→ AE trained on scale A gets data at scale B → fail.",1150,color=LTGRAY)
                +ep()
                +para("NB01 → NB02 & NB03 (parallel) → NB04 → NB05",1300,bold=True,color=ACCENT2))
    s += sp(10,emu(0.25),emu(0.9),emu(4.8),emu(5.85),
            gradFill("0D1B2A","060B18"), stk_p, anchor="t", rnd=10000, bh=ACCENT1, bw=12700)
    s += sp(11,emu(5.2), emu(0.9),emu(3.6),emu(5.85),
            gradFill("07001A","060B18"), nb_p,  anchor="t", rnd=10000, bh=ACCENT2, bw=12700)
    s += card(12,emu(8.95),emu(0.9),emu(3.0),emu(5.85),"",GREEN, artifacts, bg1="001A00")
    return slide_xml(s)



# ════════════════════════════════════════════════════════════════════════════
# SLIDE 19 — LIMITATIONS & DISCUSSION
# ════════════════════════════════════════════════════════════════════════════
def slide_19():
    s = dark_bg() + header_bar("⚠️  Limitations & Discussion", 19)
    lims = [
        ("Binary Output Only","System outputs Normal/Attack — cannot identify\nWHICH zero-day attack type occurred.\nCritical for SOC triage and incident response.",RED),
        ("Sample-by-Sample","No temporal context — each packet evaluated\nindependently. Slow/stealthy attacks (Fingerprinting,\nPort Scanning) may look normal per packet.",ACCENT3),
        ("Static Threshold","τ = 0.0122 fixed post-training. Real deployments\nhave drifting 'normal' patterns as devices are\nadded or firmware updates change traffic.",YELLOW),
        ("Lab Dataset","Edge-IIoTset collected in a controlled testbed.\nReal-world IoT traffic distribution may differ\n— model may need retraining for each deployment.",ACCENT2),
        ("Hardcoded Paths","Notebooks use Google Drive absolute paths.\nReproduction requires manual path updates.\nProduction code should use config files.",LTGRAY),
        ("Zero-Importance Features","14 features (ARP metadata, MQTT fields)\nscored exactly 0 in LightGBM. Dead weight\nthat could be pruned without accuracy loss.",ACCENT1),
    ]
    for i,(title,txt,col) in enumerate(lims):
        row = i // 3; cn = i % 3
        x = emu(0.25) + cn*emu(4.0)
        y = emu(0.9) + row*emu(2.95)
        lines = txt.split("\n")
        p = para(title,1350,bold=True,color=col)
        for l in lines: p += para(l,1100,color=WHITE)
        s += sp(10+i,x,y,emu(3.85),emu(2.75),
                gradFill("0D1B2A","060B18"), p, anchor="t",
                rnd=10000, bh=col, bw=12700)
    vs_related = para("📌  vs Related Work: Khraisat et al. survey reports top hybrid IDS at 97-99% on mixed known+unknown datasets. Our Fusion Model at 96.82% on strictly zero-shot evaluation is competitive — stronger test protocol than most published papers apply.",
                     1200,color=LTGRAY,align="ctr")
    s += sp(16,emu(0.25),H-emu(0.82),W-emu(0.5),emu(0.68),
            gradFill("0A001A","060B18"), vs_related, anchor="ctr",
            rnd=8000, bh=ACCENT2, bw=9525)
    return slide_xml(s)


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 20 — CONCLUSIONS
# ════════════════════════════════════════════════════════════════════════════
def slide_20():
    s = dark_bg() + header_bar("✅  Conclusions", 20)
    s += stat(10,emu(0.25),emu(0.88),emu(2.85),emu(1.4),"99.99%","LightGBM Known Attacks",GREEN)
    s += stat(11,emu(3.3), emu(0.88),emu(2.85),emu(1.4),"99.19%","Autoencoder (All Traffic)",ACCENT2)
    s += stat(12,emu(6.35),emu(0.88),emu(2.85),emu(1.4),"96.82%","Fusion Zero-Day Scenario",ACCENT1)
    s += stat(13,emu(9.4), emu(0.88),emu(2.55),emu(1.4),"+47.8pp","Above IF Baseline",ACCENT3)

    c1 = (para("Research Contributions",1700,bold=True,color=GREEN)
         +ep()
         +para("✅  Hybrid IDS simultaneously handles known attacks",1300,color=WHITE)
         +para("     AND zero-day threats — both in one system.",1200,color=LTGRAY)
         +ep()
         +para("✅  LightGBM: 99.99% accuracy, 10 known classes",1300,color=WHITE)
         +para("     Only ~3 misclassifications on 24,259 samples.",1200,color=LTGRAY)
         +ep()
         +para("✅  Autoencoder: 100% attack recall, 0 missed attacks",1300,color=WHITE)
         +para("     Across ALL 15 attack types including 5 zero-days.",1200,color=LTGRAY)
         +ep()
         +para("✅  Fusion Model: 96.82% on 5 unseen attack types",1300,color=WHITE)
         +para("     vs 49% Isolation Forest — +47.82pp improvement.",1200,color=LTGRAY)
         +ep()
         +para("✅  Ultra-lightweight: 11,907 parameters in AE",1300,color=WHITE)
         +para("     Deployable on IoT edge gateways.",1200,color=LTGRAY))
    c2 = (para("Structural Insight",1700,bold=True,color=ACCENT1)
         +ep()
         +para("Supervised and unsupervised methods solve DIFFERENT",1300,color=WHITE)
         +para("sub-problems — they complement, not compete.",1200,color=LTGRAY)
         +ep()
         +para("LightGBM answer: 'What IS this attack?'",1300,bold=True,color=GREEN)
         +para("Autoencoder asks: 'Is this NORMAL traffic?'",1300,bold=True,color=ACCENT2)
         +ep()
         +para("Combining them intelligently — giving LightGBM",1250,color=WHITE)
         +para("dominance on confident decisions and AE coverage",1250,color=WHITE)
         +para("on uncertain ones — is the key design insight.",1250,color=WHITE)
         +ep()
         +para("Dataset matters: Edge-IIoTset is one of the few",1200,color=LTGRAY)
         +para("IoT-specific datasets with realistic protocols.",1200,color=LTGRAY)
         +para("Our 99.99% exceeds dataset authors' own 95-98%.",1300,bold=True,color=ACCENT1))
    s += card(14,emu(0.25),emu(2.5),emu(5.85),emu(4.25),"",GREEN,   c1, bg1="001A00")
    s += card(15,emu(6.25),emu(2.5),emu(5.7), emu(4.25),"",ACCENT1, c2, bg1="0D1B2A")
    return slide_xml(s)


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 21 — FUTURE WORK
# ════════════════════════════════════════════════════════════════════════════
def slide_21():
    s = dark_bg() + header_bar("🔮  Future Work", 21)
    items = [
        ("Zero-Day Attack Categorisation",
         "Cluster anomalies by similarity to assign attack family labels.\nSemi-supervised step after binary detection.",ACCENT2),
        ("Sequence-Aware Detection (LSTM)",
         "Replace per-packet evaluation with sliding-window LSTM.\nCaptures temporal patterns — fixes Port Scanning misses.",ACCENT1),
        ("Adaptive Threshold",
         "Rolling 95th percentile over recent normal traffic buffer.\nThreshold updates as device fleet evolves over time.",YELLOW),
        ("Variational Autoencoder (VAE)",
         "Probabilistic latent representation — reconstruction\nprobability instead of raw MSE — better calibrated.",ACCENT2),
        ("Feature Pruning",
         "Remove 14 zero-importance features. Reduce dimensionality,\npotentially improve AE generalisation and speed.",GREEN),
        ("Real Hardware Deployment",
         "Profile and quantise models for Raspberry Pi gateway.\nLightGBM is already lightweight. AE has only 11,907 params.",ACCENT3),
        ("Federated Learning",
         "Train on distributed IoT gateways without centralising\nprivate traffic data. Privacy-preserving IDS.",ACCENT1),
        ("GAN-Based Anomaly Detection",
         "GAN discriminator provides richer anomaly signal than\nplain MSE. More powerful but harder to train stably.",ACCENT2),
    ]
    for i,(title,txt,col) in enumerate(items):
        row = i // 4; cn = i % 4
        x = emu(0.25) + cn*emu(3.0)
        y = emu(0.9)  + row*emu(3.0)
        lines = txt.split("\n")
        p = para(title,1300,bold=True,color=col)
        for l in lines: p += para(l,1100,color=WHITE)
        s += sp(10+i,x,y,emu(2.85),emu(2.8),
                gradFill("0D1B2A","060B18"), p, anchor="t",
                rnd=10000, bh=col, bw=12700)
    return slide_xml(s)


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 22 — KEY VIVA / Q&A PREPARATION
# ════════════════════════════════════════════════════════════════════════════
def slide_22():
    s = dark_bg() + header_bar("🎓  Key Viva Q&A Preparation", 22)
    qas = [
        ("Why fit scaler on normal traffic only?",
         "Contaminating with attack stats corrupts the AE's normalcy\nbaseline — it would learn to tolerate attack features.",ACCENT2),
        ("Why 90% confidence threshold?",
         "Genuine normals: LightGBM ≥95% confident. Zero-day attacks\nmisclassified as Normal: 60-85% confident. Clean separation.",ACCENT1),
        ("Why can't LightGBM detect zero-day?",
         "Supervised classifier — forces every input into one of its\n10 trained classes. Cannot output 'unknown class'.",ACCENT3),
        ("Why train AE on normal traffic only?",
         "AE trained on attacks would reconstruct attacks well too —\nlosing the anomaly detection capability entirely.",ACCENT2),
        ("Why Parquet not CSV?",
         "10× smaller, binary (instant load), preserves data types\n(float32/int32 saved from preprocessing are maintained).",GREEN),
        ("What are the 520 missed attacks?",
         "Fingerprinting & Port Scanning. Low-volume, slow-paced traffic\nlooks like routine packets — no temporal context in our model.",RED),
    ]
    for i,(q,a,col) in enumerate(qas):
        row = i // 3; cn = i % 3
        x = emu(0.25) + cn*emu(4.0)
        y = emu(0.9)  + row*emu(2.95)
        lines = a.split("\n")
        p = para(f"Q: {q}",1250,bold=True,color=col)
        p += para("A:",1200,bold=True,color=ACCENT1)
        for l in lines: p += para(f"   {l}",1150,color=WHITE)
        s += sp(10+i,x,y,emu(3.85),emu(2.75),
                gradFill("0D1B2A","060B18"), p, anchor="t",
                rnd=10000, bh=col, bw=12700)
    return slide_xml(s)


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 23 — THANK YOU
# ════════════════════════════════════════════════════════════════════════════
def slide_23():
    s  = dark_bg()
    s += sp(3, 0, 0, W, emu(0.11), gradFill(ACCENT1,ACCENT2,0), ep())
    s += sp(4, 0, H-emu(0.11), W, emu(0.11), gradFill(ACCENT2,ACCENT1,0), ep())
    s += sp(5, 0, emu(0.11), emu(0.055), H-emu(0.22), solidFill(ACCENT1), ep())
    s += sp(6, emu(1.3), emu(0.7), emu(9.6), emu(1.6),
            solidFill("00000000"),
            para("Thank You!", 5800, bold=True, color=ACCENT1, align="ctr"), anchor="ctr")
    s += sp(7, emu(2.0), emu(2.35), emu(8.2), emu(0.5),
            solidFill("00000000"),
            para("Zero-Day IoT Attack Detection Using a Hybrid Machine Learning Approach",1500,color=LTGRAY,align="ctr"))
    # result summary strip
    summary = (para("99.99% LightGBM  ·  99.19% Autoencoder  ·  96.82% Fusion Model  ·  +47.8pp vs Baseline",
                   1450,bold=True,color=GREEN,align="ctr"))
    s += sp(8,emu(0.5),emu(3.05),W-emu(1.0),emu(0.7),
            gradFill("001A00","060B18"), summary, anchor="ctr", rnd=10000, bh=GREEN, bw=12700)
    # team card
    team = (para("PROJECT TEAM  ·  B.Tech CSE  ·  MAY 2026",1300,bold=True,color=ACCENT1,align="ctr")
           +ep()
           +para("Shahil Ahmed  (202202021046)   ·   Jagriti Shivam  (202202022091)",1300,color=WHITE,align="ctr")
           +para("Khushi Das  (202202022113)   ·   Babul Hoque  (202202021020)",1300,color=WHITE,align="ctr")
           +ep()
           +para("Supervisor: Mr. Bikramjit Choudhury  |  Asst. Professor, Dept. of CSE",1200,color=LTGRAY,align="ctr"))
    s += sp(9,emu(0.5),emu(3.95),W-emu(1.0),emu(2.0),
            gradFill("0D2137","071020"), team, anchor="ctr", rnd=15000, bh=ACCENT2, bw=19050)
    s += sp(10,emu(1.5),emu(6.12),emu(9.2),emu(0.55),
            solidFill("00000000"),
            para("CENTRAL INSTITUTE OF TECHNOLOGY KOKRAJHAR, ASSAM  ·  www.cit.ac.in",1300,bold=True,color=YELLOW,align="ctr"))
    s += sp(11,emu(3.8),emu(6.78),emu(4.6),emu(0.55),
            solidFill("00000000"),
            para("Questions & Discussion Welcome 🎯",1400,bold=True,color=GREEN,align="ctr"))
    return slide_xml(s)


# ════════════════════════════════════════════════════════════════════════════
# PPTX PACKAGE BUILDER
# ════════════════════════════════════════════════════════════════════════════
SLIDES = [
    slide_01(),  slide_02(),  slide_03(),  slide_04(),  slide_05(),
    slide_06(),  slide_07(),  slide_08(),  slide_09(),  slide_10(),
    slide_11(),  slide_12(),  slide_13(),  slide_14(),  slide_15(),
    slide_16(),  slide_17(),  slide_18(),  slide_19(),  slide_20(),
    slide_21(),  slide_22(),  slide_23(),
]
N = len(SLIDES)

def slide_rels(i):
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" '
            'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" '
            'Target="../slideLayouts/slideLayout1.xml"/>'
            '</Relationships>')

CONTENT_TYPES = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
 '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
 '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
 '<Default Extension="xml"  ContentType="application/xml"/>'
 '<Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>'
 '<Override PartName="/ppt/slideMasters/slideMaster1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"/>'
 '<Override PartName="/ppt/slideLayouts/slideLayout1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/>'
 '<Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>'
 + "".join(f'<Override PartName="/ppt/slides/slide{i+1}.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>' for i in range(N))
 + '</Types>')

ROOT_RELS = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
 '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
 '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/>'
 '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>'
 '<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>'
 '</Relationships>')

def prs_rels():
    lines = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
             '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">',
             '<Relationship Id="rId0" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="slideMasters/slideMaster1.xml"/>']
    for i in range(N):
        lines.append(f'<Relationship Id="rId{i+1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide{i+1}.xml"/>')
    lines.append('</Relationships>')
    return "".join(lines)

def presentation_xml():
    ids = "".join(f'<p:sldId id="{256+i}" r:id="rId{i+1}"/>' for i in range(N))
    return (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            f'<p:prs xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"'
            f' xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"'
            f' xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"'
            f' saveSubsetFonts="1">'
            f'<p:sldMasterIdLst><p:sldMasterId id="2147483648" r:id="rId0"/></p:sldMasterIdLst>'
            f'<p:sldIdLst>{ids}</p:sldIdLst>'
            f'<p:sldSz cx="{W}" cy="{H}" type="custom"/>'
            f'<p:defaultTextStyle/></p:prs>')

SLIDE_MASTER = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
 '<p:sldMaster xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"'
 ' xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"'
 ' xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
 '<p:cSld><p:spTree>'
 '<p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>'
 '<p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/>'
 '<a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>'
 '</p:spTree></p:cSld>'
 '<p:clrMap bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" accent2="accent2" accent3="accent3" accent4="accent4" accent5="accent5" accent6="accent6" hlink="hlink" folHlink="folHlink"/>'
 '<p:sldLayoutIdLst><p:sldLayoutId id="2147483649" r:id="rId1"/></p:sldLayoutIdLst>'
 '<p:txStyles><p:titleStyle/><p:bodyStyle/><p:otherStyle/></p:txStyles>'
 '</p:sldMaster>')

SLIDE_MASTER_RELS = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
 '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
 '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>'
 '</Relationships>')

SLIDE_LAYOUT = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
 '<p:sldLayout xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"'
 ' xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"'
 ' xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"'
 ' type="blank" preserve="1"><p:cSld name="Blank"><p:spTree>'
 '<p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>'
 '<p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/>'
 '<a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>'
 '</p:spTree></p:cSld>'
 '<p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sldLayout>')

SLIDE_LAYOUT_RELS = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
 '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
 '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="../slideMasters/slideMaster1.xml"/>'
 '</Relationships>')

APP_XML = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
           f'<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties">'
           f'<Application>Microsoft Office PowerPoint</Application><Slides>{N}</Slides></Properties>')

CORE_XML = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
 '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties"'
 ' xmlns:dc="http://purl.org/dc/elements/1.1/">'
 '<dc:title>Zero-Day IoT Attack Detection Using Hybrid ML</dc:title>'
 '<dc:creator>Shahil Ahmed, Jagriti Shivam, Khushi Das, Babul Hoque</dc:creator>'
 '<dc:subject>CIT Kokrajhar B.Tech Final Year Project 2026</dc:subject>'
 '</cp:coreProperties>')

with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
    z.writestr("[Content_Types].xml",           CONTENT_TYPES)
    z.writestr("_rels/.rels",                   ROOT_RELS)
    z.writestr("docProps/app.xml",              APP_XML)
    z.writestr("docProps/core.xml",             CORE_XML)
    z.writestr("ppt/presentation.xml",          presentation_xml())
    z.writestr("ppt/_rels/presentation.xml.rels", prs_rels())
    z.writestr("ppt/slideMasters/slideMaster1.xml", SLIDE_MASTER)
    z.writestr("ppt/slideMasters/_rels/slideMaster1.xml.rels", SLIDE_MASTER_RELS)
    z.writestr("ppt/slideLayouts/slideLayout1.xml", SLIDE_LAYOUT)
    z.writestr("ppt/slideLayouts/_rels/slideLayout1.xml.rels", SLIDE_LAYOUT_RELS)
    for i, sxml in enumerate(SLIDES):
        z.writestr(f"ppt/slides/slide{i+1}.xml",        sxml)
        z.writestr(f"ppt/slides/_rels/slide{i+1}.xml.rels", slide_rels(i))

size_kb = os.path.getsize(OUT) // 1024
print(f"✅  Created: {OUT}")
print(f"   Slides : {N}")
print(f"   Size   : {size_kb} KB")
