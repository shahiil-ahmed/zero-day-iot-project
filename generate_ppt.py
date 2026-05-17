"""
Zero-Day IoT Attack Detection — PowerPoint Generator
Builds a .pptx file from raw OOXML without any third-party libraries.
"""
import zipfile, os, textwrap

OUT = "/projects/sandbox/zero-day-iot-project/Zero_Day_IoT_Presentation.pptx"

# ─── EMU helpers ────────────────────────────────────────────────────────────
# 1 inch = 914400 EMU  |  slide = 12192000 × 6858000 (widescreen 16:9)
W, H = 12192000, 6858000

def emu(inches): return int(inches * 914400)

# ─── Colour palette ─────────────────────────────────────────────────────────
DARK_BG   = "0A0E1A"   # near-black navy
MID_BG    = "0D1B2A"   # slide body bg
ACCENT1   = "00C6FF"   # cyan
ACCENT2   = "7B2FBE"   # purple
ACCENT3   = "FF6B35"   # orange
GREEN     = "00E676"   # result green
WHITE     = "FFFFFF"
LTGRAY    = "B0BEC5"
YELLOW    = "FFD600"

# ─── Shared XML fragments ───────────────────────────────────────────────────

def solidFill(hex6):
    return f'<a:solidFill><a:srgbClr val="{hex6}"/></a:solidFill>'

def gradFill(hex1, hex2, angle=5400000):
    return f'''<a:gradFill><a:gsLst>
      <a:gs pos="0"><a:srgbClr val="{hex1}"/></a:gs>
      <a:gs pos="100000"><a:srgbClr val="{hex2}"/></a:gs>
    </a:gsLst><a:lin ang="{angle}" scaled="0"/></a:gradFill>'''

def sp_pr(x, y, cx, cy, fill_xml, rounding=0, border_hex=None, border_w=0):
    ln = ""
    if border_hex:
        ln = f'<a:ln w="{border_w}"><a:solidFill><a:srgbClr val="{border_hex}"/></a:solidFill></a:ln>'
    rnd = f'<a:prstGeom prst="roundRect"><a:avLst><a:gd name="adj" fmla="val {rounding}"/></a:avLst></a:prstGeom>' if rounding else '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom>'
    return f'''<p:spPr>
  <a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>
  {rnd}
  {fill_xml}
  {ln}
  <a:effectLst/>
</p:spPr>'''

def txBody(paras_xml, anchor="ctr", wrap="square", vert="horz"):
    return f'''<p:txBody>
  <a:bodyPr anchor="{anchor}" wrap="{wrap}" vert="{vert}">
    <a:normAutofit/>
  </a:bodyPr>
  <a:lstStyle/>
  {paras_xml}
</p:txBody>'''

def para(text, sz, bold=False, color=WHITE, align="l", space_before=0, italic=False, spacing=100):
    b = "1" if bold else "0"
    i = "1" if italic else "0"
    al = align  # l, ctr, r
    spb = f'<a:spcBef><a:spcPts val="{space_before}"/></a:spcBef>' if space_before else ""
    lsp = f'<a:lnSpc><a:spcPct val="{spacing}000"/></a:lnSpc>'
    return f'''<a:p>
  <a:pPr algn="{al}">{spb}{lsp}</a:pPr>
  <a:r><a:rPr lang="en-US" sz="{sz}" b="{b}" i="{i}" dirty="0">
    <a:solidFill><a:srgbClr val="{color}"/></a:solidFill>
    <a:latin typeface="Calibri"/>
  </a:rPr><a:t>{text}</a:t></a:r>
</a:p>'''

def empty_para():
    return '<a:p><a:endParaRPr lang="en-US" dirty="0"/></a:p>'

def shape(idx, x, y, cx, cy, fill_xml, paras_xml, anchor="ctr", rounding=0, border_hex=None, border_w=9525):
    return f'''<p:sp>
  <p:nvSpPr>
    <p:cNvPr id="{idx}" name="Shape{idx}"/>
    <p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr>
    <p:nvPr/>
  </p:nvSpPr>
  {sp_pr(x,y,cx,cy,fill_xml,rounding,border_hex,border_w)}
  {txBody(paras_xml, anchor)}
</p:sp>'''

def line_shape(idx, x1, y1, x2, y2, color, w=19050):
    cx = x2 - x1
    cy = y2 - y1
    flipH = "1" if cx < 0 else "0"
    flipV = "1" if cy < 0 else "0"
    cx = abs(cx); cy = abs(cy)
    if cy == 0: cy = 1
    return f'''<p:sp>
  <p:nvSpPr>
    <p:cNvPr id="{idx}" name="Line{idx}"/>
    <p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr>
    <p:nvPr/>
  </p:nvSpPr>
  <p:spPr>
    <a:xfrm flipH="{flipH}" flipV="{flipV}">
      <a:off x="{min(x1,x2)}" y="{min(y1,y2)}"/>
      <a:ext cx="{cx}" cy="{cy}"/>
    </a:xfrm>
    <a:prstGeom prst="line"><a:avLst/></a:prstGeom>
    <a:noFill/>
    <a:ln w="{w}"><a:solidFill><a:srgbClr val="{color}"/></a:solidFill></a:ln>
  </p:spPr>
  <p:txBody><a:bodyPr/><a:lstStyle/><a:p/></p:txBody>
</p:sp>'''

def slide_xml(spTree_inner):
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
       xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
       xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <p:cSld>
    <p:spTree>
      <p:nvGrpSpPr>
        <p:cNvPr id="1" name=""/>
        <p:cNvGrpSpPr/>
        <p:nvPr/>
      </p:nvGrpSpPr>
      <p:grpSpPr>
        <a:xfrm><a:off x="0" y="0"/><a:ext cx="{W}" cy="{H}"/>
        <a:chOff x="0" y="0"/><a:chExt cx="{W}" cy="{H}"/></a:xfrm>
      </p:grpSpPr>
      {spTree_inner}
    </p:spTree>
  </p:cSld>
</p:sld>'''

def bg(hex1, hex2=None, angle=5400000):
    fill = gradFill(hex1, hex2 or hex1, angle) if hex2 else solidFill(hex1)
    return shape(2, 0, 0, W, H, fill, empty_para())



# ════════════════════════════════════════════════════════════════════════════
# SLIDE BUILDERS
# ════════════════════════════════════════════════════════════════════════════

def slide_01_cover():
    """Stylish cover / title slide"""
    shapes = []
    # Full dark gradient background
    shapes.append(shape(2, 0, 0, W, H,
        gradFill("060B18", "0D1B2A", 5400000), empty_para()))

    # Decorative top accent bar (cyan)
    shapes.append(shape(3, 0, 0, W, emu(0.12),
        gradFill(ACCENT1, ACCENT2, 0), empty_para()))

    # Decorative bottom accent bar (purple)
    shapes.append(shape(4, 0, H - emu(0.12), W, emu(0.12),
        gradFill(ACCENT2, ACCENT1, 0), empty_para()))

    # Left glowing sidebar
    shapes.append(shape(5, 0, emu(0.12), emu(0.06), H - emu(0.24),
        solidFill(ACCENT1), empty_para()))

    # Title card box
    shapes.append(shape(6, emu(0.5), emu(0.9), emu(11.2), emu(1.9),
        gradFill("0D2137", "0A1628", 5400000),
        para("Zero-Day IoT Attack Detection", 3600, bold=True, color=ACCENT1, align="ctr")
        + para("Using a Hybrid Machine Learning Approach", 2400, bold=False, color=WHITE, align="ctr"),
        anchor="ctr", rounding=20000, border_hex=ACCENT1, border_w=19050))

    # Subtitle line
    shapes.append(shape(7, emu(2), emu(3.05), emu(8.2), emu(0.5),
        solidFill("00000000"),
        para("B.Tech Final Year Project  ·  Computer Science & Engineering", 1600, color=LTGRAY, align="ctr")))

    # Team box
    team_paras = (
        para("PROJECT TEAM", 1400, bold=True, color=ACCENT1, align="ctr")
        + para("Shahil Ahmed  ·  Roll No. 202202021046", 1300, color=WHITE, align="ctr")
        + para("Jagriti Shivam  ·  Roll No. 202202022091", 1300, color=WHITE, align="ctr")
        + para("Khushi Das  ·  Roll No. 202202022113", 1300, color=WHITE, align="ctr")
        + para("Babul Hoque  ·  Roll No. 202202021020", 1300, color=WHITE, align="ctr")
    )
    shapes.append(shape(8, emu(0.6), emu(3.7), emu(5.0), emu(2.5),
        gradFill("0D2137", "071020", 5400000),
        team_paras, anchor="ctr", rounding=12000, border_hex=ACCENT2, border_w=19050))

    # Supervisor / college box
    sup_paras = (
        para("SUPERVISOR", 1400, bold=True, color=ACCENT2, align="ctr")
        + para("Mr. Bikramjit Choudhury", 1300, bold=True, color=WHITE, align="ctr")
        + para("Assistant Professor, Dept. of CSE", 1100, color=LTGRAY, align="ctr")
        + empty_para()
        + para("CENTRAL INSTITUTE OF TECHNOLOGY", 1200, bold=True, color=YELLOW, align="ctr")
        + para("KOKRAJHAR, ASSAM — MAY 2026", 1100, color=LTGRAY, align="ctr")
    )
    shapes.append(shape(9, emu(5.9), emu(3.7), emu(5.9), emu(2.5),
        gradFill("0D2137", "071020", 5400000),
        sup_paras, anchor="ctr", rounding=12000, border_hex=ACCENT3, border_w=19050))

    # Decorative circuit dots
    for i, (xp, yp) in enumerate([(0.2,1.1),(0.2,5.5),(11.9,1.1),(11.9,5.5)]):
        shapes.append(shape(20+i, emu(xp)-emu(0.08), emu(yp)-emu(0.08),
            emu(0.16), emu(0.16), solidFill(ACCENT1), empty_para(),
            rounding=50000))

    return slide_xml("\n".join(shapes))



def content_slide(slide_num, title, body_shapes_xml):
    """Standard content slide with consistent header"""
    shapes = []
    # Background
    shapes.append(shape(2, 0, 0, W, H,
        gradFill("060B18", "0D1B2A", 5400000), empty_para()))
    # Top bar
    shapes.append(shape(3, 0, 0, W, emu(0.85),
        gradFill(ACCENT2, ACCENT1, 0), empty_para()))
    # Left accent
    shapes.append(shape(4, 0, emu(0.85), emu(0.06), H - emu(0.85),
        solidFill(ACCENT1), empty_para()))
    # Bottom bar
    shapes.append(shape(5, 0, H - emu(0.08), W, emu(0.08),
        solidFill(ACCENT2), empty_para()))
    # Slide number
    shapes.append(shape(6, W - emu(0.6), H - emu(0.45), emu(0.5), emu(0.35),
        solidFill("00000000"),
        para(str(slide_num), 1100, color=LTGRAY, align="r")))
    # Title
    shapes.append(shape(7, emu(0.25), emu(0.08), W - emu(0.5), emu(0.72),
        solidFill("00000000"),
        para(title, 2400, bold=True, color=WHITE, align="l"), anchor="ctr"))
    # Content
    shapes.append(body_shapes_xml)
    return slide_xml("\n".join(shapes))


def bullet_block(idx, x, y, cx, cy, items, title=None, title_color=ACCENT1):
    """A rounded box with optional title + bullet list"""
    paras = ""
    if title:
        paras += para(title, 1600, bold=True, color=title_color, align="l")
    for icon, text, sz, clr in items:
        paras += para(f"{icon}  {text}", sz, color=clr, align="l")
    return shape(idx, x, y, cx, cy,
        gradFill("0D2137", "091525", 5400000),
        paras, anchor="t", rounding=10000, border_hex=ACCENT1, border_w=12700)


def stat_box(idx, x, y, cx, cy, value, label, v_color=GREEN):
    paras = (para(value, 3600, bold=True, color=v_color, align="ctr")
             + para(label, 1100, color=LTGRAY, align="ctr"))
    return shape(idx, x, y, cx, cy,
        gradFill("0D2137", "060B18", 5400000),
        paras, anchor="ctr", rounding=15000, border_hex=v_color, border_w=19050)


# ─── Slide 02 — Agenda ───────────────────────────────────────────────────────
def slide_02_agenda():
    items = [
        ("01", "Problem Statement & Motivation",  ACCENT1),
        ("02", "IoT Security Landscape",           WHITE),
        ("03", "Dataset Overview",                 ACCENT1),
        ("04", "System Architecture",              WHITE),
        ("05", "LightGBM — Known Attack Classifier", ACCENT1),
        ("06", "Autoencoder — Zero-Day Detector",  WHITE),
        ("07", "Fusion Model",                     ACCENT1),
        ("08", "Results & Model Comparison",       WHITE),
        ("09", "Conclusions & Future Work",        ACCENT1),
    ]
    col1 = "".join(para(f"  {n}   {t}", 1500, color=c, align="l") + empty_para()
                   for n, t, c in items[:5])
    col2 = "".join(para(f"  {n}   {t}", 1500, color=c, align="l") + empty_para()
                   for n, t, c in items[5:])

    body = (
        shape(10, emu(0.3), emu(1.0), emu(5.7), emu(5.5),
              gradFill("0D2137","060B18",5400000), col1, anchor="t",
              rounding=10000, border_hex=ACCENT2, border_w=12700)
        + shape(11, emu(6.2), emu(1.0), emu(5.7), emu(5.5),
              gradFill("0D2137","060B18",5400000), col2, anchor="t",
              rounding=10000, border_hex=ACCENT1, border_w=12700)
    )
    return content_slide(2, "📋  Agenda", body)


# ─── Slide 03 — Problem Statement ────────────────────────────────────────────
def slide_03_problem():
    prob_paras = (
        para("The Problem", 1800, bold=True, color=ACCENT3, align="l")
        + para("Traditional Intrusion Detection Systems (IDS) rely on known", 1400, color=WHITE)
        + para("attack signatures — they are BLIND to new / unseen threats.", 1400, color=WHITE)
        + empty_para()
        + para("⚠  Zero-Day Attacks", 1600, bold=True, color=YELLOW)
        + para("Exploits for unknown vulnerabilities with no prior signature,", 1300, color=LTGRAY)
        + para("bypassing every conventional signature-based defence.", 1300, color=LTGRAY)
    )
    sol_paras = (
        para("Our Solution", 1800, bold=True, color=GREEN, align="l")
        + para("A Hybrid IDS combining:", 1400, color=WHITE)
        + empty_para()
        + para("🌲  LightGBM  — classifies 10 known attack types", 1350, color=ACCENT1)
        + para("🧠  Autoencoder  — detects any anomaly (zero-day)", 1350, color=ACCENT2)
        + para("⚡  Fusion Model  — intelligently routes decisions", 1350, color=ACCENT3)
    )
    iot_paras = (
        para("Why IoT?", 1800, bold=True, color=ACCENT1, align="l")
        + para("🔹 15 billion+ connected devices worldwide", 1300, color=WHITE)
        + para("🔹 Limited CPU/RAM — no heavy AV possible", 1300, color=WHITE)
        + para("🔹 Always-on, rarely updated firmware", 1300, color=WHITE)
        + para("🔹 Critical infrastructure: hospitals, power grids", 1300, color=WHITE)
        + para("🔹 Massive attack surface for adversaries", 1300, color=WHITE)
    )
    body = (
        shape(10, emu(0.3), emu(1.05), emu(7.4), emu(2.7),
              gradFill("1A0A00","0D1B2A",5400000), prob_paras, anchor="t",
              rounding=10000, border_hex=ACCENT3, border_w=19050)
        + shape(11, emu(0.3), emu(3.9), emu(7.4), emu(2.7),
              gradFill("0A1A00","0D1B2A",5400000), sol_paras, anchor="t",
              rounding=10000, border_hex=GREEN, border_w=19050)
        + shape(12, emu(7.9), emu(1.05), emu(4.0), emu(5.55),
              gradFill("0D1B2A","060B18",5400000), iot_paras, anchor="t",
              rounding=10000, border_hex=ACCENT1, border_w=19050)
    )
    return content_slide(3, "❓  Problem Statement", body)


# ─── Slide 04 — Dataset ──────────────────────────────────────────────────────
def slide_04_dataset():
    stats = (
        stat_box(10, emu(0.3),  emu(1.05), emu(2.7), emu(1.5), "157,800", "Raw Network Rows", ACCENT1)
        + stat_box(11, emu(3.2), emu(1.05), emu(2.7), emu(1.5), "152,389", "After Cleaning", GREEN)
        + stat_box(12, emu(6.1), emu(1.05), emu(2.7), emu(1.5), "53",      "Feature Columns", ACCENT2)
        + stat_box(13, emu(9.0), emu(1.05), emu(2.9), emu(1.5), "15",      "Traffic Classes", ACCENT3)
    )
    known_paras = (
        para("✅  Known Classes (Train — 10 types)", 1500, bold=True, color=GREEN)
        + para("Normal · Backdoor · DDoS_HTTP · DDoS_ICMP · DDoS_TCP", 1200, color=WHITE)
        + para("DDoS_UDP · Password · Port_Scanning · Ransomware · SQL_Injection", 1200, color=WHITE)
        + empty_para()
        + para("📦  121,293 samples", 1300, bold=True, color=GREEN)
    )
    zd_paras = (
        para("🚨  Zero-Day Classes (Hidden — 5 types)", 1500, bold=True, color=ACCENT3)
        + para("Fingerprinting · MITM · Uploading", 1200, color=WHITE)
        + para("Vulnerability Scanner · XSS", 1200, color=WHITE)
        + empty_para()
        + para("📦  31,096 samples  (never seen during training)", 1300, bold=True, color=ACCENT3)
    )
    info_paras = (
        para("Edge-IIoTset Dataset", 1500, bold=True, color=ACCENT1)
        + para("Real IoT testbed with 10 device types", 1200, color=LTGRAY)
        + para("Protocols: MQTT · HTTP · DNS · TCP · UDP · ARP · Modbus", 1200, color=LTGRAY)
        + para("Source: Kaggle (sibasispradhan/edge-iiotset-dataset)", 1100, color=LTGRAY, italic=True)
    )
    body = (
        stats
        + shape(14, emu(0.3), emu(2.75), emu(5.7), emu(1.95),
                gradFill("001A00","0D1B2A",5400000), known_paras, anchor="t",
                rounding=10000, border_hex=GREEN, border_w=19050)
        + shape(15, emu(6.2), emu(2.75), emu(5.7), emu(1.95),
                gradFill("1A0000","0D1B2A",5400000), zd_paras, anchor="t",
                rounding=10000, border_hex=ACCENT3, border_w=19050)
        + shape(16, emu(0.3), emu(4.85), emu(11.6), emu(1.8),
                gradFill("0D1B2A","060B18",5400000), info_paras, anchor="ctr",
                rounding=10000, border_hex=ACCENT1, border_w=12700)
    )
    return content_slide(4, "📊  Dataset — Edge-IIoTset", body)



# ─── Slide 05 — System Architecture ─────────────────────────────────────────
def slide_05_architecture():
    # Pipeline boxes
    boxes = [
        (emu(0.25), emu(1.05), emu(2.1),  emu(1.2), "RAW IoT TRAFFIC", "157,800 packets", ACCENT1, "141A0A1A"),
        (emu(0.25), emu(2.6),  emu(2.1),  emu(1.2), "PREPROCESSING",   "Clean · Encode · Scale", ACCENT2, "14071020"),
        (emu(2.65), emu(1.6),  emu(2.35), emu(2.7), "LightGBM",        "Known Attack Classifier\n10 classes · 99.99% acc", GREEN, "14001200"),
        (emu(5.3),  emu(1.6),  emu(2.35), emu(2.7), "Autoencoder",     "Zero-Day Detector\nAnomaly via recon error", ACCENT2, "14071020"),
        (emu(8.0),  emu(1.6),  emu(2.1),  emu(2.7), "FUSION MODEL",    "Confidence-based\ndecision routing", ACCENT3, "14140800"),
        (emu(10.3), emu(1.95), emu(1.65), emu(2.0), "OUTPUT",          "Normal / Attack", ACCENT1, "14001A0D"),
    ]
    shapes_xml = ""
    for idx, (x, y, cx, cy, title, sub, col, _) in enumerate(boxes):
        paras = para(title, 1400, bold=True, color=col, align="ctr") + para(sub, 1100, color=LTGRAY, align="ctr")
        shapes_xml += shape(10+idx, x, y, cx, cy,
            gradFill("0D1B2A","060B18",5400000), paras, anchor="ctr",
            rounding=15000, border_hex=col, border_w=19050)

    # Arrows (simple lines)
    # RAW → PREPROCESS
    shapes_xml += line_shape(30, emu(1.3), emu(2.25), emu(1.3), emu(2.6), ACCENT1, 38100)
    # PREPROCESS → LightGBM
    shapes_xml += line_shape(31, emu(2.35), emu(3.2), emu(2.65), emu(3.0), ACCENT1, 28575)
    # PREPROCESS → Autoencoder
    shapes_xml += line_shape(32, emu(2.35), emu(3.2), emu(5.3), emu(3.0), ACCENT2, 28575)
    # LightGBM → Fusion
    shapes_xml += line_shape(33, emu(5.0), emu(3.0), emu(8.0), emu(3.0), GREEN, 28575)
    # Autoencoder → Fusion
    shapes_xml += line_shape(34, emu(7.65), emu(3.0), emu(8.0), emu(3.0), ACCENT2, 28575)
    # Fusion → Output
    shapes_xml += line_shape(35, emu(10.1), emu(2.95), emu(10.3), emu(2.95), ACCENT3, 28575)

    # Logic description box
    logic_paras = (
        para("Fusion Logic:", 1400, bold=True, color=ACCENT3, align="l")
        + para("IF LightGBM confidence ≥ 90%  →  Trust LightGBM result", 1200, color=WHITE)
        + para("ELSE  →  Use Autoencoder reconstruction error to decide", 1200, color=WHITE)
    )
    shapes_xml += shape(36, emu(0.25), emu(4.1), emu(11.65), emu(1.3),
        gradFill("1A0800","0D1B2A",5400000), logic_paras, anchor="ctr",
        rounding=10000, border_hex=ACCENT3, border_w=19050)

    # Key insight
    shapes_xml += shape(37, emu(0.25), emu(5.55), emu(11.65), emu(1.0),
        gradFill("0A001A","060B18",5400000),
        para("💡  Three-layer defence: Supervised (known) + Unsupervised (anomaly) + Fusion (intelligent routing)", 1300, color=ACCENT1, align="ctr"),
        anchor="ctr", rounding=10000, border_hex=ACCENT2, border_w=12700)

    return content_slide(5, "🏗️  System Architecture", shapes_xml)


# ─── Slide 06 — LightGBM ─────────────────────────────────────────────────────
def slide_06_lightgbm():
    what_paras = (
        para("What is LightGBM?", 1600, bold=True, color=GREEN)
        + para("Gradient Boosted Decision Tree framework by Microsoft Research.", 1200, color=WHITE)
        + para("Grows trees leaf-by-leaf (not level-by-level) for better accuracy.", 1200, color=WHITE)
        + para("Uses histogram binning for blazing-fast training.", 1200, color=WHITE)
        + empty_para()
        + para("Why LightGBM for IoT IDS?", 1500, bold=True, color=GREEN)
        + para("✔  Handles 100k+ rows in seconds", 1200, color=LTGRAY)
        + para("✔  Works well on imbalanced classes", 1200, color=LTGRAY)
        + para("✔  Excellent feature importance output", 1200, color=LTGRAY)
        + para("✔  Lightweight — ideal for edge deployment", 1200, color=LTGRAY)
    )
    train_paras = (
        para("Training Setup", 1600, bold=True, color=ACCENT1)
        + para("Training set:  96,770 samples (80%)", 1200, color=WHITE)
        + para("Test set:      24,259 samples (20%)", 1200, color=WHITE)
        + para("Features:      51 network packet features", 1200, color=WHITE)
        + para("Classes:       10 (Normal + 9 attack types)", 1200, color=WHITE)
        + empty_para()
        + para("Top Features:", 1400, bold=True, color=ACCENT1)
        + para("tcp.srcport · tcp.options · tcp.dstport · tcp.ack", 1200, color=LTGRAY)
    )
    result_paras = (
        para("Results", 1600, bold=True, color=GREEN)
        + para("Overall Accuracy:  99.99%", 1400, bold=True, color=GREEN)
        + para("Macro F1-Score:    99.99%", 1300, color=WHITE)
        + para("Per-class F1 ≥ 99.97% on all 10 classes", 1200, color=LTGRAY)
        + empty_para()
        + para("Inference on 24,259 test samples:", 1200, color=LTGRAY)
        + para("Only ~3 misclassifications total", 1300, bold=True, color=ACCENT1)
    )
    body = (
        shape(10, emu(0.3), emu(1.05), emu(5.7), emu(5.5),
              gradFill("001A00","0D1B2A",5400000), what_paras, anchor="t",
              rounding=10000, border_hex=GREEN, border_w=19050)
        + shape(11, emu(6.2), emu(1.05), emu(2.6), emu(5.5),
              gradFill("0D1B2A","060B18",5400000), train_paras, anchor="t",
              rounding=10000, border_hex=ACCENT1, border_w=19050)
        + shape(12, emu(9.0), emu(1.05), emu(2.9), emu(5.5),
              gradFill("001A0D","060B18",5400000), result_paras, anchor="t",
              rounding=10000, border_hex=GREEN, border_w=19050)
    )
    return content_slide(6, "🌲  LightGBM — Known Attack Classifier", body)


# ─── Slide 07 — Autoencoder ──────────────────────────────────────────────────
def slide_07_autoencoder():
    arch_paras = (
        para("Architecture  (Symmetric)", 1600, bold=True, color=ACCENT2)
        + para("Input  →  53 features", 1200, color=WHITE)
        + para("Encoder: 53 → 32 → 16 (ReLU)", 1200, color=ACCENT1)
        + para("Bottleneck: 8 neurons", 1300, bold=True, color=ACCENT2)
        + para("Decoder: 8 → 16 → 32 → 53 (Sigmoid)", 1200, color=ACCENT1)
        + empty_para()
        + para("Total Parameters:  11,907  (lightweight!)", 1300, bold=True, color=GREEN)
        + para("Optimizer: Adam  |  Loss: MSE", 1200, color=LTGRAY)
        + para("Epochs: 20  |  Batch: 256", 1200, color=LTGRAY)
    )
    logic_paras = (
        para("How it Works", 1600, bold=True, color=ACCENT2)
        + para("1. Train ONLY on normal traffic (24,152 rows)", 1200, color=WHITE)
        + para("2. Learn to compress & reconstruct 'normal'", 1200, color=WHITE)
        + para("3. At inference, compute reconstruction error:", 1200, color=WHITE)
        + para("   error = mean( (input − output)² )", 1300, bold=True, color=ACCENT1)
        + empty_para()
        + para("Threshold = 0.0122", 1500, bold=True, color=YELLOW)
        + para("error > threshold  →  ANOMALY (attack!)", 1300, color=ACCENT3)
        + para("error ≤ threshold  →  NORMAL traffic", 1300, color=GREEN)
    )
    res_paras = (
        para("Results", 1600, bold=True, color=GREEN)
        + para("Overall Accuracy:  99.19%", 1400, bold=True, color=GREEN)
        + para("Tested on full 152,389-row dataset", 1200, color=LTGRAY)
        + empty_para()
        + para("Normal Precision:   100%", 1200, color=WHITE)
        + para("Attack Recall:      100%", 1200, color=WHITE)
        + para("Attack F1:           99.52%", 1200, color=WHITE)
        + empty_para()
        + para("Detects ALL 5 zero-day attack types", 1300, bold=True, color=ACCENT2)
        + para("without ever seeing them in training!", 1200, color=LTGRAY)
    )
    body = (
        shape(10, emu(0.3), emu(1.05), emu(3.8), emu(5.5),
              gradFill("07001A","0D1B2A",5400000), arch_paras, anchor="t",
              rounding=10000, border_hex=ACCENT2, border_w=19050)
        + shape(11, emu(4.3), emu(1.05), emu(4.3), emu(5.5),
              gradFill("0D1B2A","060B18",5400000), logic_paras, anchor="t",
              rounding=10000, border_hex=ACCENT1, border_w=19050)
        + shape(12, emu(8.8), emu(1.05), emu(3.1), emu(5.5),
              gradFill("001A0D","060B18",5400000), res_paras, anchor="t",
              rounding=10000, border_hex=GREEN, border_w=19050)
    )
    return content_slide(7, "🧠  Autoencoder — Zero-Day Anomaly Detector", body)



# ─── Slide 08 — Fusion Model ──────────────────────────────────────────────────
def slide_08_fusion():
    logic_paras = (
        para("Fusion Logic", 1700, bold=True, color=ACCENT3)
        + empty_para()
        + para("Step 1: Run LightGBM on input sample", 1300, color=WHITE)
        + para("Step 2: Get max class probability (confidence)", 1300, color=WHITE)
        + empty_para()
        + para("IF  confidence ≥ 0.90", 1400, bold=True, color=GREEN)
        + para("  → Accept LightGBM label (known attack name)", 1300, color=LTGRAY)
        + empty_para()
        + para("ELSE  (LightGBM unsure)", 1400, bold=True, color=ACCENT3)
        + para("  → Compute Autoencoder reconstruction error", 1300, color=LTGRAY)
        + para("  → If error > 0.0122 → flag as ATTACK", 1300, color=ACCENT3)
        + para("  → If error ≤ 0.0122 → label as NORMAL", 1300, color=GREEN)
    )
    why_paras = (
        para("Why This Works", 1700, bold=True, color=ACCENT1)
        + empty_para()
        + para("🎯 LightGBM is extremely confident (≥99.9%) on known attacks", 1250, color=WHITE)
        + para("   so it handles them with surgical precision.", 1200, color=LTGRAY)
        + empty_para()
        + para("🔍 When LightGBM is uncertain, it means the traffic", 1250, color=WHITE)
        + para("   doesn't match any known pattern — perfect handoff to", 1200, color=LTGRAY)
        + para("   the Autoencoder which detects any deviation from normal.", 1200, color=LTGRAY)
        + empty_para()
        + para("⚡ Result: Best of both worlds!", 1300, bold=True, color=YELLOW)
    )
    res_paras = (
        para("Fusion Results", 1700, bold=True, color=GREEN)
        + empty_para()
        + para("Test Set: Normal + 5 Zero-Day types", 1200, color=LTGRAY)
        + para("55,248 samples total", 1200, color=LTGRAY)
        + empty_para()
        + para("Accuracy:   96.82%", 1500, bold=True, color=GREEN)
        + para("Precision:  97.78%", 1300, color=WHITE)
        + para("Recall:     98.33%", 1300, color=WHITE)
        + para("F1-Score:   97.20%", 1300, color=WHITE)
        + empty_para()
        + para("vs Isolation Forest baseline: 49%", 1200, color=ACCENT3)
        + para("+47.82 percentage points improvement!", 1300, bold=True, color=GREEN)
    )
    body = (
        shape(10, emu(0.3), emu(1.05), emu(4.5), emu(5.5),
              gradFill("1A0800","0D1B2A",5400000), logic_paras, anchor="t",
              rounding=10000, border_hex=ACCENT3, border_w=19050)
        + shape(11, emu(5.0), emu(1.05), emu(3.9), emu(5.5),
              gradFill("0D1B2A","060B18",5400000), why_paras, anchor="t",
              rounding=10000, border_hex=ACCENT1, border_w=19050)
        + shape(12, emu(9.1), emu(1.05), emu(2.8), emu(5.5),
              gradFill("001A0D","060B18",5400000), res_paras, anchor="t",
              rounding=10000, border_hex=GREEN, border_w=19050)
    )
    return content_slide(8, "⚡  Fusion Model — Intelligent Decision Routing", body)


# ─── Slide 09 — Results Comparison ───────────────────────────────────────────
def slide_09_results():
    # Big stat boxes
    stats = (
        stat_box(10, emu(0.3),  emu(1.05), emu(2.7), emu(1.5), "99.99%", "LightGBM\n(Known Attacks)", GREEN)
        + stat_box(11, emu(3.2), emu(1.05), emu(2.7), emu(1.5), "99.19%", "Autoencoder\n(Zero-Day)", ACCENT2)
        + stat_box(12, emu(6.1), emu(1.05), emu(2.7), emu(1.5), "96.82%", "Fusion Model\n(Combined)", ACCENT1)
        + stat_box(13, emu(9.0), emu(1.05), emu(2.9), emu(1.5), "49.00%", "Isolation Forest\n(Baseline)", ACCENT3)
    )
    # Comparison table
    headers = para("Model", 1400, bold=True, color=ACCENT1, align="l")
    tbl_paras = (
        para("MODEL                  ACCURACY   PURPOSE", 1300, bold=True, color=ACCENT1)
        + line_shape(20, emu(0.4), emu(3.15), emu(11.5), emu(3.15), ACCENT1, 9525)
        + para("Isolation Forest       49.00%     Baseline anomaly detection", 1200, color=LTGRAY)
        + para("LightGBM               99.99%     Known attack classification", 1200, color=GREEN)
        + para("Autoencoder            99.19%     Zero-day anomaly detection", 1200, color=ACCENT2)
        + para("Fusion Model           96.82%     Hybrid detection system", 1200, color=ACCENT1)
    )

    tbl = shape(14, emu(0.3), emu(2.75), emu(11.6), emu(2.3),
        gradFill("0D1B2A","060B18",5400000), tbl_paras, anchor="t",
        rounding=10000, border_hex=ACCENT1, border_w=12700)

    key_paras = (
        para("Key Takeaways", 1500, bold=True, color=YELLOW)
        + para("✅  Fusion Model is +47.8pp better than Isolation Forest baseline", 1300, color=WHITE)
        + para("✅  Zero-day attacks detected without ANY prior labelled examples", 1300, color=WHITE)
        + para("✅  Only 11,907 parameters — deployable on IoT edge gateways", 1300, color=WHITE)
    )
    key = shape(15, emu(0.3), emu(5.2), emu(11.6), emu(1.4),
        gradFill("1A1400","0D1B2A",5400000), key_paras, anchor="ctr",
        rounding=10000, border_hex=YELLOW, border_w=19050)

    return content_slide(9, "📈  Results & Model Comparison", stats + tbl + key)


# ─── Slide 10 — Preprocessing Pipeline ───────────────────────────────────────
def slide_10_preprocessing():
    steps = [
        (emu(0.3),  emu(1.05), "① Load CSV",       "157,800 × 63 columns\nML-EdgeIIoT-dataset.csv", ACCENT1),
        (emu(2.6),  emu(1.05), "② Drop Columns",   "63 → 53 features\nRemove IP/timestamps/text", ACCENT2),
        (emu(4.9),  emu(1.05), "③ Clean Data",      "157,800 → 152,389 rows\nNull & duplicate removal", ACCENT3),
        (emu(7.2),  emu(1.05), "④ Encode & Optimise","Label encode text cols\nfloat64→float32 (50% RAM↓)", GREEN),
        (emu(9.5),  emu(1.05), "⑤ Split Dataset",   "Known: 121,293 rows\nZero-day: 31,096 rows", YELLOW),
    ]
    step_shapes = ""
    for idx, (x, y, title, sub, col) in enumerate(steps):
        paras = para(title, 1400, bold=True, color=col, align="ctr") + para(sub, 1150, color=WHITE, align="ctr")
        step_shapes += shape(10+idx, x, y, emu(2.1), emu(1.85),
            gradFill("0D1B2A","060B18",5400000), paras, anchor="ctr",
            rounding=12000, border_hex=col, border_w=19050)
        if idx < 4:
            mx = x + emu(2.1)
            my = y + emu(0.92)
            step_shapes += line_shape(20+idx, mx, my, mx+emu(0.5), my, col, 38100)

    scaler_paras = (
        para("⑥ StandardScaler", 1500, bold=True, color=ACCENT1)
        + para("Fitted ONLY on normal traffic — maintains anomaly detection integrity", 1250, color=WHITE)
        + para("Formula:  z = (x − mean) / std_dev   →   all features scaled to ~[-3, +3]", 1250, color=LTGRAY)
        + para("Saved as scaler.pkl — reused by all subsequent notebooks", 1200, color=LTGRAY)
    )
    step_shapes += shape(15, emu(0.3), emu(3.1), emu(11.6), emu(1.45),
        gradFill("0D2137","060B18",5400000), scaler_paras, anchor="ctr",
        rounding=10000, border_hex=ACCENT1, border_w=19050)

    parquet_paras = (
        para("Output Files (Parquet format — 10× smaller than CSV, type-safe)", 1300, bold=True, color=GREEN)
        + para("master_clean.parquet  ·  known_train.parquet  ·  zero_day_test.parquet  ·  scaler.pkl", 1200, color=WHITE)
    )
    step_shapes += shape(16, emu(0.3), emu(4.7), emu(11.6), emu(1.1),
        gradFill("001A00","060B18",5400000), parquet_paras, anchor="ctr",
        rounding=10000, border_hex=GREEN, border_w=12700)

    step_shapes += shape(17, emu(0.3), emu(5.95), emu(11.6), emu(0.65),
        gradFill("0A001A","060B18",5400000),
        para("💡  Scaler fitted on normal-only traffic ensures the Autoencoder gets a clean, uncontaminated normalisation baseline", 1200, color=LTGRAY, align="ctr"),
        anchor="ctr", rounding=8000, border_hex=ACCENT2, border_w=9525)

    return content_slide(10, "⚙️  Data Preprocessing Pipeline", step_shapes)



# ─── Slide 11 — Feature Importance ────────────────────────────────────────────
def slide_11_features():
    features = [
        ("tcp.srcport",   13467, ACCENT1),
        ("tcp.options",   12777, ACCENT2),
        ("tcp.dstport",    8849, GREEN),
        ("tcp.ack",        7849, ACCENT3),
        ("tcp.ack_raw",    6417, YELLOW),
        ("tcp.checksum",   6109, ACCENT1),
        ("tcp.seq",        4226, ACCENT2),
        ("http.request.method", 2213, GREEN),
        ("tcp.len",        2181, ACCENT3),
        ("udp.stream",     2009, YELLOW),
    ]
    max_imp = 13467
    bar_shapes = ""
    # Title
    bar_shapes += shape(10, emu(0.3), emu(1.05), emu(5.6), emu(0.5),
        solidFill("00000000"),
        para("Top 10 Feature Importances (LightGBM)", 1500, bold=True, color=ACCENT1))

    for i, (name, imp, col) in enumerate(features):
        y = emu(1.7) + i * emu(0.43)
        bar_w = int((imp / max_imp) * emu(5.2))
        bar_shapes += shape(11+i, emu(0.3), y, emu(1.55), emu(0.35),
            solidFill("00000000"), para(name, 1100, color=WHITE), anchor="ctr")
        bar_shapes += shape(21+i, emu(1.9), y, bar_w, emu(0.32),
            gradFill(col, "0D1B2A", 0), para(f"{imp:,}", 1000, color=WHITE, align="r"), anchor="ctr",
            rounding=5000)

    # Right-side insights
    ins_paras = (
        para("Key Insights", 1600, bold=True, color=ACCENT1)
        + empty_para()
        + para("🔹 TCP port features dominate (srcport, dstport)", 1250, color=WHITE)
        + para("   Different attack types use different ports.", 1150, color=LTGRAY)
        + empty_para()
        + para("🔹 TCP control fields are highly discriminative", 1250, color=WHITE)
        + para("   (ack, seq, checksum, options, flags)", 1150, color=LTGRAY)
        + empty_para()
        + para("🔹 HTTP request method distinguishes web attacks", 1250, color=WHITE)
        + para("   (SQL injection, XSS, upload attacks)", 1150, color=LTGRAY)
        + empty_para()
        + para("🔹 ARP / DNS / MQTT fields score near zero", 1250, color=LTGRAY)
        + para("   → Could be pruned to reduce model size", 1150, color=LTGRAY)
        + empty_para()
        + para("Model uses 51 features → 11 carry 90%+ of signal", 1300, bold=True, color=YELLOW)
    )
    bar_shapes += shape(31, emu(7.8), emu(1.05), emu(4.1), emu(5.6),
        gradFill("0D1B2A","060B18",5400000), ins_paras, anchor="t",
        rounding=10000, border_hex=ACCENT1, border_w=19050)

    return content_slide(11, "🔍  Feature Importance Analysis", bar_shapes)


# ─── Slide 12 — Conclusions & Future Work ─────────────────────────────────────
def slide_12_conclusions():
    conc_paras = (
        para("Conclusions", 1700, bold=True, color=GREEN)
        + empty_para()
        + para("✅  Hybrid IDS successfully detects both known attacks", 1300, color=WHITE)
        + para("     and zero-day threats simultaneously.", 1200, color=LTGRAY)
        + empty_para()
        + para("✅  LightGBM achieves 99.99% accuracy on 10 known", 1300, color=WHITE)
        + para("     attack types — near-perfect classification.", 1200, color=LTGRAY)
        + empty_para()
        + para("✅  Autoencoder detects 5 unseen zero-day attack", 1300, color=WHITE)
        + para("     types with 99.19% overall accuracy.", 1200, color=LTGRAY)
        + empty_para()
        + para("✅  Fusion Model: 96.82% on zero-day scenario", 1300, color=WHITE)
        + para("     vs Isolation Forest baseline of only 49%.", 1200, color=LTGRAY)
        + empty_para()
        + para("✅  11,907 parameter Autoencoder — deployable on", 1300, color=WHITE)
        + para("     resource-constrained IoT edge devices.", 1200, color=LTGRAY)
    )
    future_paras = (
        para("Future Work", 1700, bold=True, color=ACCENT2)
        + empty_para()
        + para("🔮  Real-time packet capture & live inference", 1300, color=WHITE)
        + para("🔮  Deploy on actual IoT hardware (Raspberry Pi)", 1300, color=WHITE)
        + para("🔮  Identify specific zero-day attack category", 1300, color=WHITE)
        + para("🔮  Continual learning — model updates online", 1300, color=WHITE)
        + para("🔮  GAN-based anomaly detection for richer signal", 1300, color=WHITE)
        + para("🔮  Federated learning across distributed IoT nodes", 1300, color=WHITE)
        + empty_para()
        + para("Dataset Limitation:", 1400, bold=True, color=ACCENT3)
        + para("Lab-collected traffic — real-world deployment", 1200, color=LTGRAY)
        + para("may show different distributions.", 1200, color=LTGRAY)
    )
    body = (
        shape(10, emu(0.3), emu(1.05), emu(5.7), emu(5.5),
              gradFill("001A00","0D1B2A",5400000), conc_paras, anchor="t",
              rounding=10000, border_hex=GREEN, border_w=19050)
        + shape(11, emu(6.2), emu(1.05), emu(5.7), emu(5.5),
              gradFill("07001A","0D1B2A",5400000), future_paras, anchor="t",
              rounding=10000, border_hex=ACCENT2, border_w=19050)
    )
    return content_slide(12, "✅  Conclusions & Future Work", body)


# ─── Slide 13 — Thank You ─────────────────────────────────────────────────────
def slide_13_thankyou():
    shapes = []
    shapes.append(shape(2, 0, 0, W, H,
        gradFill("060B18","0D1B2A",5400000), empty_para()))
    shapes.append(shape(3, 0, 0, W, emu(0.12),
        gradFill(ACCENT1, ACCENT2, 0), empty_para()))
    shapes.append(shape(4, 0, H-emu(0.12), W, emu(0.12),
        gradFill(ACCENT2, ACCENT1, 0), empty_para()))
    shapes.append(shape(5, 0, emu(0.12), emu(0.06), H-emu(0.24),
        solidFill(ACCENT1), empty_para()))

    shapes.append(shape(6, emu(1.5), emu(0.8), emu(9.2), emu(1.5),
        solidFill("00000000"),
        para("Thank You!", 5400, bold=True, color=ACCENT1, align="ctr"), anchor="ctr"))

    shapes.append(shape(7, emu(2.5), emu(2.4), emu(7.2), emu(0.55),
        solidFill("00000000"),
        para("Zero-Day IoT Attack Detection Using Hybrid ML Approach", 1500, color=LTGRAY, align="ctr")))

    # Team card
    team_paras = (
        para("PROJECT TEAM  ·  B.Tech CSE  ·  MAY 2026", 1300, bold=True, color=ACCENT1, align="ctr")
        + empty_para()
        + para("Shahil Ahmed  (202202021046)   ·   Jagriti Shivam  (202202022091)", 1300, color=WHITE, align="ctr")
        + para("Khushi Das  (202202022113)   ·   Babul Hoque  (202202021020)", 1300, color=WHITE, align="ctr")
        + empty_para()
        + para("Supervisor: Mr. Bikramjit Choudhury  |  Asst. Professor, Dept. of CSE", 1200, color=LTGRAY, align="ctr")
    )
    shapes.append(shape(8, emu(0.5), emu(3.1), emu(11.2), emu(1.95),
        gradFill("0D2137","071020",5400000), team_paras, anchor="ctr",
        rounding=15000, border_hex=ACCENT2, border_w=19050))

    shapes.append(shape(9, emu(1.5), emu(5.25), emu(9.2), emu(0.6),
        solidFill("00000000"),
        para("CENTRAL INSTITUTE OF TECHNOLOGY KOKRAJHAR, ASSAM  ·  www.cit.ac.in",
             1300, bold=True, color=YELLOW, align="ctr")))

    shapes.append(shape(10, emu(3.5), emu(5.95), emu(5.2), emu(0.55),
        solidFill("00000000"),
        para("Questions & Discussion Welcome 🎯", 1400, bold=True, color=GREEN, align="ctr")))

    return slide_xml("\n".join(shapes))



# ════════════════════════════════════════════════════════════════════════════
# PPTX PACKAGE BUILDER
# ════════════════════════════════════════════════════════════════════════════

SLIDES = [
    slide_01_cover(),
    slide_02_agenda(),
    slide_03_problem(),
    slide_04_dataset(),
    slide_10_preprocessing(),
    slide_05_architecture(),
    slide_06_lightgbm(),
    slide_07_autoencoder(),
    slide_08_fusion(),
    slide_09_results(),
    slide_11_features(),
    slide_12_conclusions(),
    slide_13_thankyou(),
]

N = len(SLIDES)

# ── Relationship helpers ─────────────────────────────────────────────────────
def slide_rels(slide_idx):
    return '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1"
    Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout"
    Target="../slideLayouts/slideLayout1.xml"/>
</Relationships>'''

CONTENT_TYPES = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml"  ContentType="application/xml"/>
  <Override PartName="/ppt/presentation.xml"
    ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>
  <Override PartName="/ppt/slideMasters/slideMaster1.xml"
    ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"/>
  <Override PartName="/ppt/slideLayouts/slideLayout1.xml"
    ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/>
  <Override PartName="/docProps/app.xml"
    ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
''' + "".join(
    f'  <Override PartName="/ppt/slides/slide{i+1}.xml"\n'
    f'    ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>\n'
    for i in range(N)
) + '</Types>'

ROOT_RELS = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1"
    Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument"
    Target="ppt/presentation.xml"/>
  <Relationship Id="rId2"
    Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties"
    Target="docProps/core.xml"/>
  <Relationship Id="rId3"
    Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties"
    Target="docProps/app.xml"/>
</Relationships>'''

def prs_rels():
    lines = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
             '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">',
             '  <Relationship Id="rId0" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="slideMasters/slideMaster1.xml"/>']
    for i in range(N):
        lines.append(f'  <Relationship Id="rId{i+1}" '
                     f'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" '
                     f'Target="slides/slide{i+1}.xml"/>')
    lines.append('</Relationships>')
    return "\n".join(lines)

def presentation_xml():
    sz = f'<p:sldSz cx="{W}" cy="{H}" type="custom"/>'
    sldIdLst = "".join(
        f'<p:sldId id="{256+i}" r:id="rId{i+1}"/>' for i in range(N)
    )
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:prs xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
       xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
       xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
       saveSubsetFonts="1">
  <p:sldMasterIdLst><p:sldMasterId id="2147483648" r:id="rId0"/></p:sldMasterIdLst>
  <p:sldIdLst>{sldIdLst}</p:sldIdLst>
  {sz}
  <p:defaultTextStyle/>
</p:prs>'''

SLIDE_MASTER = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldMaster xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
             xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
             xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <p:cSld><p:spTree>
    <p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
    <p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/>
    <a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>
  </p:spTree></p:cSld>
  <p:clrMap bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1"
            accent2="accent2" accent3="accent3" accent4="accent4"
            accent5="accent5" accent6="accent6" hlink="hlink" folHlink="folHlink"/>
  <p:sldLayoutIdLst><p:sldLayoutId id="2147483649" r:id="rId1"/></p:sldLayoutIdLst>
  <p:txStyles><p:titleStyle/><p:bodyStyle/><p:otherStyle/></p:txStyles>
</p:sldMaster>'''

SLIDE_MASTER_RELS = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1"
    Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout"
    Target="../slideLayouts/slideLayout1.xml"/>
</Relationships>'''

SLIDE_LAYOUT = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldLayout xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
             xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
             xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
             type="blank" preserve="1">
  <p:cSld name="Blank"><p:spTree>
    <p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
    <p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/>
    <a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>
  </p:spTree></p:cSld>
  <p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>
</p:sldLayout>'''

SLIDE_LAYOUT_RELS = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1"
    Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster"
    Target="../slideMasters/slideMaster1.xml"/>
</Relationships>'''

APP_XML = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties">
  <Application>Microsoft Office PowerPoint</Application>
  <Slides>''' + str(N) + '''</Slides>
</Properties>'''

CORE_XML = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
                   xmlns:dc="http://purl.org/dc/elements/1.1/">
  <dc:title>Zero-Day IoT Attack Detection Using Hybrid ML</dc:title>
  <dc:creator>Shahil Ahmed, Jagriti Shivam, Khushi Das, Babul Hoque</dc:creator>
  <dc:subject>CIT Kokrajhar B.Tech Final Year Project 2026</dc:subject>
</cp:coreProperties>'''

# ── Write the zip ────────────────────────────────────────────────────────────
with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
    z.writestr("[Content_Types].xml", CONTENT_TYPES)
    z.writestr("_rels/.rels", ROOT_RELS)
    z.writestr("docProps/app.xml", APP_XML)
    z.writestr("docProps/core.xml", CORE_XML)
    z.writestr("ppt/presentation.xml", presentation_xml())
    z.writestr("ppt/_rels/presentation.xml.rels", prs_rels())
    z.writestr("ppt/slideMasters/slideMaster1.xml", SLIDE_MASTER)
    z.writestr("ppt/slideMasters/_rels/slideMaster1.xml.rels", SLIDE_MASTER_RELS)
    z.writestr("ppt/slideLayouts/slideLayout1.xml", SLIDE_LAYOUT)
    z.writestr("ppt/slideLayouts/_rels/slideLayout1.xml.rels", SLIDE_LAYOUT_RELS)
    for i, sxml in enumerate(SLIDES):
        z.writestr(f"ppt/slides/slide{i+1}.xml", sxml)
        z.writestr(f"ppt/slides/_rels/slide{i+1}.xml.rels", slide_rels(i))

size_kb = os.path.getsize(OUT) // 1024
print(f"✅  Created: {OUT}")
print(f"   Slides:  {N}")
print(f"   Size:    {size_kb} KB")
