"""
Zero Day IoT Attack Detection — Professional 27-Slide PPT Generator
Builds a fully valid .pptx from Python stdlib only (no python-pptx needed).
A .pptx file is a ZIP archive of XML (OOXML) parts.
"""

import zipfile
import os
import io

OUT_PATH = os.path.join(os.path.dirname(__file__), "Zero_Day_IoT_Presentation.pptx")

# ─────────────────────────────────────────────────────────────────────────────
# COLOUR PALETTE  (OOXML uses RRGGBB hex strings)
# ─────────────────────────────────────────────────────────────────────────────
C_BG_DARK   = "050B1F"   # near-black navy — slide background
C_BG_MID    = "0A1628"   # slightly lighter navy
C_ACCENT1   = "00D4FF"   # electric cyan — headings / highlights
C_ACCENT2   = "7B2FFF"   # purple — secondary accent
C_ACCENT3   = "00FF88"   # neon green — success / results
C_ACCENT4   = "FF4C4C"   # red — attacks / danger
C_ACCENT5   = "FFB800"   # amber — warning / known attacks
C_WHITE     = "FFFFFF"
C_LGRAY     = "B0C4DE"   # light-gray text
C_DGRAY     = "3A4A6B"   # dark-gray for dividers
C_CARD      = "0D1F3C"   # card / box background (glass-dark)
C_CARD2     = "122040"   # slightly lighter card

# ─────────────────────────────────────────────────────────────────────────────
# FONTS
# ─────────────────────────────────────────────────────────────────────────────
F_TITLE   = "Segoe UI"
F_BODY    = "Segoe UI"
F_MONO    = "Consolas"

# ─────────────────────────────────────────────────────────────────────────────
# EMU helpers  (English Metric Units: 1 inch = 914400 EMU)
# ─────────────────────────────────────────────────────────────────────────────
def emu(inches): return int(inches * 914400)

SW = emu(13.33)   # slide width  (widescreen 16:9)
SH = emu(7.5)     # slide height

# ─────────────────────────────────────────────────────────────────────────────
# LOW-LEVEL XML HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def _xrgb(c): return f'<a:srgbClr val="{c}"/>'

def sp_pr(x, y, w, h, fill=None, line_color=None, line_w=12700, rounding=None):
    """Shape properties XML fragment."""
    fill_xml = ""
    if fill == "none":
        fill_xml = "<a:noFill/>"
    elif fill:
        fill_xml = f"<a:solidFill>{_xrgb(fill)}</a:solidFill>"

    line_xml = ""
    if line_color:
        line_xml = (f'<a:ln w="{line_w}">'
                    f'<a:solidFill>{_xrgb(line_color)}</a:solidFill>'
                    f'</a:ln>')

    round_xml = ""
    if rounding:
        round_xml = f'<a:prstGeom prst="roundRect"><a:avLst><a:gd name="adj" fmla="val {rounding}"/></a:avLst></a:prstGeom>'
    else:
        round_xml = '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom>'

    return (f'<p:spPr>'
            f'<a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{w}" cy="{h}"/></a:xfrm>'
            f'{round_xml}'
            f'{fill_xml}'
            f'{line_xml}'
            f'</p:spPr>')

def txBody(paragraphs_xml, anchor="ctr", vert="horz", lIns=emu(0.1), rIns=emu(0.1), tIns=emu(0.05), bIns=emu(0.05)):
    return (f'<p:txBody>'
            f'<a:bodyPr anchor="{anchor}" vert="{vert}" lIns="{lIns}" rIns="{rIns}" tIns="{tIns}" bIns="{bIns}" wrap="square"/>'
            f'<a:lstStyle/>'
            f'{paragraphs_xml}'
            f'</p:txBody>')

def para(runs_xml, algn="l", spc_bef=0):
    spc = f'<a:spcBef><a:spcPts val="{spc_bef}"/></a:spcBef>' if spc_bef else ""
    return f'<a:p><a:pPr algn="{algn}">{spc}</a:pPr>{runs_xml}</a:p>'

def run(text, sz=18, bold=False, color=C_WHITE, font=F_BODY, italic=False):
    b_xml = "<a:b/>" if bold else ""
    i_xml = "<a:i/>" if italic else ""
    # Escape XML special characters AND encode non-BMP / emoji as XML numeric refs
    safe = []
    for ch in text:
        cp = ord(ch)
        if ch == '&':
            safe.append('&amp;')
        elif ch == '<':
            safe.append('&lt;')
        elif ch == '>':
            safe.append('&gt;')
        elif ch == '"':
            safe.append('&quot;')
        elif cp > 0xFFFF or (0xD800 <= cp <= 0xDFFF):
            safe.append(f'&#x{cp:X};')
        else:
            safe.append(ch)
    text_escaped = ''.join(safe)
    return (f'<a:r>'
            f'<a:rPr lang="en-US" sz="{sz}" dirty="0">'
            f'<a:solidFill>{_xrgb(color)}</a:solidFill>'
            f'<a:latin typeface="{font}"/>'
            f'{b_xml}{i_xml}'
            f'</a:rPr>'
            f'<a:t>{text_escaped}</a:t>'
            f'</a:r>')

def shape(sp_pr_xml, txbody_xml, shape_id, name="shape"):
    return (f'<p:sp>'
            f'<p:nvSpPr>'
            f'<p:cNvPr id="{shape_id}" name="{name}"/>'
            f'<p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr>'
            f'<p:nvPr/>'
            f'</p:nvSpPr>'
            f'{sp_pr_xml}'
            f'{txbody_xml}'
            f'</p:sp>')

def rect_shape(sid, name, x, y, w, h, fill, text_xml="", anchor="ctr",
               line_color=None, line_w=12700, rounding=None, lIns=emu(0.1), rIns=emu(0.1)):
    sp = sp_pr(x, y, w, h, fill=fill, line_color=line_color,
               line_w=line_w, rounding=rounding)
    tx = txBody(text_xml, anchor=anchor, lIns=lIns, rIns=rIns)
    return shape(sp, tx, sid, name)

# ─────────────────────────────────────────────────────────────────────────────
# SLIDE WRAPPER
# ─────────────────────────────────────────────────────────────────────────────
_SLIDE_NS = ('xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
             'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" '
             'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"')

def make_slide(body_xml, slide_idx, layout_rId="rId1"):
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld {_SLIDE_NS}>
  <p:cSld>
    <p:spTree>
      <p:nvGrpSpPr>
        <p:cNvPr id="1" name=""/>
        <p:cNvGrpSpPr/>
        <p:nvPr/>
      </p:nvGrpSpPr>
      <p:grpSpPr>
        <a:xfrm>
          <a:off x="0" y="0"/>
          <a:ext cx="{SW}" cy="{SH}"/>
          <a:chOff x="0" y="0"/>
          <a:chExt cx="{SW}" cy="{SH}"/>
        </a:xfrm>
      </p:grpSpPr>
      {body_xml}
    </p:spTree>
  </p:cSld>
  <p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>
</p:sld>"""

def slide_rel(layout_rId="rId1"):
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="{layout_rId}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>
</Relationships>"""

# ─────────────────────────────────────────────────────────────────────────────
# REUSABLE COMPONENT BUILDERS
# ─────────────────────────────────────────────────────────────────────────────
_SID = 100  # global shape-id counter

def next_id():
    global _SID
    _SID += 1
    return _SID

def bg(fill=C_BG_DARK):
    """Full-slide background rectangle."""
    return rect_shape(next_id(), "bg", 0, 0, SW, SH, fill=fill)

def gradient_header_bar(y=0, h=emu(1.15)):
    """Top accent bar with gradient simulation (two overlapping rects)."""
    r1 = rect_shape(next_id(), "hbar1", 0, y, SW, h, fill=C_BG_MID)
    r2 = rect_shape(next_id(), "hbar2", 0, y + h - emu(0.04), SW, emu(0.04), fill=C_ACCENT1)
    return r1 + r2

def slide_title(text, y=emu(0.18), sz=32, color=C_ACCENT1, bold=True, algn="l",
                x=emu(0.5), w=emu(12.3)):
    tx = para(run(text, sz=sz, bold=bold, color=color), algn=algn)
    sp = sp_pr(x, y, w, emu(0.7), fill="none")
    tb = txBody(tx, anchor="ctr")
    return shape(sp, tb, next_id(), "title")

def accent_line(y, x=emu(0.5), w=emu(12.3), color=C_ACCENT1, h=emu(0.04)):
    return rect_shape(next_id(), "acline", x, y, w, h, fill=color)

def footer_bar(text="Zero Day IoT Attack Detection | B.Tech Final Year Project | 2024"):
    tx = para(run(text, sz=12, color=C_LGRAY), algn="c")
    sp = sp_pr(0, SH - emu(0.35), SW, emu(0.35), fill=C_BG_MID)
    tb = txBody(tx)
    return shape(sp, tb, next_id(), "footer")

def card(sid_name, x, y, w, h, fill=C_CARD, line_color=C_DGRAY, rounding=60000):
    return rect_shape(next_id(), sid_name, x, y, w, h, fill=fill,
                      line_color=line_color, rounding=rounding)

def bullet_box(x, y, w, h, lines, base_sz=17, fill=C_CARD, lc=C_ACCENT1,
               rounding=40000, title=None, title_color=C_ACCENT1, title_sz=19):
    """Card with optional title and bullet lines."""
    paras = ""
    if title:
        paras += para(run(title, sz=title_sz, bold=True, color=title_color), algn="l", spc_bef=0)
    for line in lines:
        color = C_WHITE
        sz = base_sz
        bold = False
        prefix = "  ▸  "
        if isinstance(line, dict):
            color = line.get("color", C_WHITE)
            sz    = line.get("sz", base_sz)
            bold  = line.get("bold", False)
            prefix = line.get("prefix", "  ▸  ")
            line  = line.get("text", "")
        paras += para(run(prefix + line, sz=sz, bold=bold, color=color), algn="l", spc_bef=40)
    sp = sp_pr(x, y, w, h, fill=fill, line_color=lc, rounding=rounding)
    tb = txBody(paras, anchor="ctr", lIns=emu(0.15), rIns=emu(0.1))
    return shape(sp, tb, next_id(), "bullet")

def stat_card(x, y, w, h, value, label, val_color=C_ACCENT3, lbl_color=C_LGRAY):
    """Big-number stat card."""
    paras = (para(run(value, sz=36, bold=True, color=val_color), algn="c") +
             para(run(label, sz=15, color=lbl_color), algn="c"))
    return rect_shape(next_id(), "stat", x, y, w, h, fill=C_CARD,
                      line_color=C_ACCENT1, rounding=60000,
                      text_xml=paras)

def label_text(text, x, y, w, h, sz=15, color=C_LGRAY, bold=False, algn="l", anchor="t"):
    sp = sp_pr(x, y, w, h, fill="none")
    tx = txBody(para(run(text, sz=sz, bold=bold, color=color), algn=algn), anchor=anchor)
    return shape(sp, tx, next_id(), "lbl")

def arrow_down(x, cy, h=emu(0.35), w=emu(0.35)):
    """Simple downward arrow (triangle) as a text shape."""
    tx = para(run("▼", sz=16, bold=True, color=C_ACCENT1), algn="c")
    sp = sp_pr(x - w//2, cy, w, h, fill="none")
    tb = txBody(tx)
    return shape(sp, tb, next_id(), "arrow")

def arrow_right(x, cy, w=emu(0.35), h=emu(0.28)):
    tx = para(run("▶", sz=14, bold=True, color=C_ACCENT1), algn="c")
    sp = sp_pr(x, cy - h//2, w, h, fill="none")
    tb = txBody(tx)
    return shape(sp, tb, next_id(), "arrowr")

# ─────────────────────────────────────────────────────────────────────────────
# SVG-STYLE BAR CHART using nested rects
# ─────────────────────────────────────────────────────────────────────────────
def bar_chart(x, y, w, h, data, title="", max_val=1.0):
    """
    data = list of (label, value, color)
    Renders horizontal bars as PPTX rectangles.
    """
    shapes = ""
    n = len(data)
    bar_h = int((h - emu(0.6)) / n) - emu(0.06)
    bar_max_w = int(w * 0.55)
    label_w = int(w * 0.32)
    val_w = int(w * 0.12)
    oy = y + emu(0.5) if title else y + emu(0.2)

    if title:
        sp = sp_pr(x, y, w, emu(0.45), fill="none")
        tb = txBody(para(run(title, sz=17, bold=True, color=C_ACCENT1), algn="c"))
        shapes += shape(sp, tb, next_id(), "chtitle")

    for i, (lbl, val, col) in enumerate(data):
        by = oy + i * (bar_h + emu(0.06))
        bar_w = int(bar_max_w * val / max_val)
        bar_x = x + label_w + emu(0.05)

        # label
        sp = sp_pr(x, by, label_w, bar_h, fill="none")
        tb = txBody(para(run(lbl, sz=13, color=C_LGRAY), algn="r"), anchor="ctr")
        shapes += shape(sp, tb, next_id(), f"blbl{i}")

        # background track
        shapes += rect_shape(next_id(), f"btrack{i}", bar_x, by + bar_h//4, bar_max_w, bar_h//2,
                             fill=C_DGRAY, rounding=20000)
        # actual bar
        if bar_w > 0:
            shapes += rect_shape(next_id(), f"bbar{i}", bar_x, by + bar_h//4, bar_w, bar_h//2,
                                fill=col, rounding=20000)

        # value label
        pct = f"{val*100:.1f}%"
        sp2 = sp_pr(bar_x + bar_max_w + emu(0.05), by, val_w, bar_h, fill="none")
        tb2 = txBody(para(run(pct, sz=14, bold=True, color=col), algn="l"), anchor="ctr")
        shapes += shape(sp2, tb2, next_id(), f"bval{i}")

    return shapes

# ─────────────────────────────────────────────────────────────────────────────
# FLOW BOX (for architecture / workflow diagrams)
# ─────────────────────────────────────────────────────────────────────────────
def flow_box(x, y, w, h, text, fill=C_CARD, lc=C_ACCENT1, sz=16, color=C_WHITE,
             bold=False, rounding=60000, sub_text=None, sub_color=C_LGRAY):
    paras = para(run(text, sz=sz, bold=bold, color=color), algn="c")
    if sub_text:
        paras += para(run(sub_text, sz=12, color=sub_color), algn="c")
    return rect_shape(next_id(), "fbox", x, y, w, h, fill=fill,
                      line_color=lc, rounding=rounding, text_xml=paras)

def nn_node(cx, cy, r, label, fill=C_ACCENT1, sz=12, color=C_BG_DARK):
    """Circle-ish node (square with big rounding)."""
    d = r * 2
    shapes = rect_shape(next_id(), "node", cx - r, cy - r, d, d, fill=fill,
                        line_color=C_WHITE, rounding=166666)
    sp = sp_pr(cx - r, cy - r, d, d, fill="none")
    tb = txBody(para(run(label, sz=sz, bold=True, color=color), algn="c"), anchor="ctr")
    shapes += shape(sp, tb, next_id(), "nodelbl")
    return shapes


# ─────────────────────────────────────────────────────────────────────────────
# SLIDE BUILDERS — 27 slides
# ─────────────────────────────────────────────────────────────────────────────

def s01_title():
    """Slide 1 — Title Slide"""
    b = bg(C_BG_DARK)

    # Dark overlay top band
    b += rect_shape(next_id(), "topband", 0, 0, SW, emu(0.12), fill="0A0E1F")

    # Decorative large circle (cybersecurity globe feel)
    b += rect_shape(next_id(), "circle1", SW - emu(4.2), emu(-1.5), emu(5.5), emu(5.5),
                    fill="091525", line_color="00D4FF", line_w=25400, rounding=166666)
    b += rect_shape(next_id(), "circle2", SW - emu(3.8), emu(-1.1), emu(4.7), emu(4.7),
                    fill="none", line_color="7B2FFF", line_w=12700, rounding=166666)
    b += rect_shape(next_id(), "circle3", SW - emu(3.3), emu(-0.6), emu(3.7), emu(3.7),
                    fill="none", line_color="00D4FF", line_w=6350, rounding=166666)

    # Accent left bar
    b += rect_shape(next_id(), "lbar", emu(0.35), emu(1.5), emu(0.06), emu(4.5), fill=C_ACCENT1)

    # College / Project tag
    sp = sp_pr(emu(0.55), emu(1.55), emu(7), emu(0.45), fill="none")
    tb = txBody(para(run("B.Tech Final Year Project  |  Department of Computer Science & Engineering",
                         sz=14, color=C_LGRAY), algn="l"), anchor="ctr")
    b += shape(sp, tb, next_id(), "dept")

    # Main title
    sp = sp_pr(emu(0.55), emu(2.1), emu(8.8), emu(1.5), fill="none")
    title_txt = (para(run("Zero Day IoT", sz=44, bold=True, color=C_ACCENT1), algn="l") +
                 para(run("Attack Detection", sz=44, bold=True, color=C_WHITE), algn="l") +
                 para(run("Using a Hybrid Machine Learning Approach", sz=24, color=C_LGRAY), algn="l"))
    tb = txBody(title_txt, anchor="t")
    b += shape(sp, tb, next_id(), "maintitle")

    # Subtitle line
    b += rect_shape(next_id(), "subline", emu(0.55), emu(3.75), emu(5.5), emu(0.04), fill=C_ACCENT1)

    # Team / Guide info cards
    info = [
        ("👥 Team", "Shahiil Ahmed  |  Final Year B.Tech CSE"),
        ("🎓 Guide", "Project Guide — Department of CSE"),
        ("🏛 Institution", "College of Information Technology (CIT)"),
        ("📅 Academic Year", "2024 – 2025"),
    ]
    for idx, (lbl, val) in enumerate(info):
        iy = emu(4.0) + idx * emu(0.65)
        sp = sp_pr(emu(0.55), iy, emu(8.5), emu(0.58), fill="none")
        txt = (para(run(f"{lbl}:  ", sz=13, bold=True, color=C_ACCENT1) +
                    run(val, sz=13, color=C_WHITE), algn="l"))
        tb = txBody(txt, anchor="ctr")
        b += shape(sp, tb, next_id(), f"info{idx}")

    # Bottom tag
    b += rect_shape(next_id(), "btag", 0, SH - emu(0.5), SW, emu(0.5), fill="0A0E1F")
    sp = sp_pr(0, SH - emu(0.45), SW, emu(0.4), fill="none")
    tb = txBody(para(run("Cybersecurity  ·  Artificial Intelligence  ·  IoT Edge Security  ·  Intrusion Detection",
                         sz=13, color=C_LGRAY), algn="c"), anchor="ctr")
    b += shape(sp, tb, next_id(), "btxt")

    return b


def s02_toc():
    """Slide 2 — Table of Contents"""
    b = bg() + gradient_header_bar() + footer_bar()
    b += slide_title("Table of Contents", y=emu(0.2))
    b += accent_line(emu(0.96))

    topics = [
        ("01", "Introduction to IoT Security"),
        ("02", "Problem Statement"),
        ("03", "Project Objectives"),
        ("04", "Why Zero-Day Detection is Difficult"),
        ("05", "Dataset Overview — Edge-IIoT"),
        ("06", "Data Preprocessing"),
        ("07", "Known vs. Unknown Attack Split"),
        ("08", "Overall System Architecture"),
        ("09", "LightGBM — Known Attack Classifier"),
        ("10", "LightGBM Workflow & Results"),
        ("11", "Autoencoder — Anomaly Detector"),
        ("12", "Autoencoder Architecture & Results"),
        ("13", "Why Fusion Model?"),
        ("14", "Fusion Model Workflow & Results"),
    ]
    extra = [
        ("15", "Model Comparison"),
        ("16", "Key Contributions"),
        ("17", "Limitations"),
        ("18", "Future Work"),
        ("19", "Conclusion"),
        ("20", "References"),
        ("21", "Thank You"),
    ]

    col_w = emu(5.9)
    # Left column
    for i, (num, title) in enumerate(topics):
        iy = emu(1.1) + i * emu(0.41)
        b += rect_shape(next_id(), f"tl{i}", emu(0.4), iy, emu(0.48), emu(0.33),
                       fill=C_ACCENT2, rounding=40000,
                       text_xml=para(run(num, sz=12, bold=True, color=C_WHITE), algn="c"))
        sp = sp_pr(emu(0.97), iy, col_w - emu(0.6), emu(0.33), fill="none")
        tb = txBody(para(run(title, sz=14, color=C_LGRAY), algn="l"), anchor="ctr")
        b += shape(sp, tb, next_id(), f"ttxt{i}")

    # Right column
    for i, (num, title) in enumerate(extra):
        iy = emu(1.1) + i * emu(0.41)
        b += rect_shape(next_id(), f"tr{i}", emu(6.85), iy, emu(0.48), emu(0.33),
                       fill=C_ACCENT1, rounding=40000,
                       text_xml=para(run(num, sz=12, bold=True, color=C_BG_DARK), algn="c"))
        sp = sp_pr(emu(7.42), iy, col_w - emu(0.6), emu(0.33), fill="none")
        tb = txBody(para(run(title, sz=14, color=C_LGRAY), algn="l"), anchor="ctr")
        b += shape(sp, tb, next_id(), f"txttr{i}")

    return b


def s03_intro():
    """Slide 3 — Introduction to IoT Security"""
    b = bg() + gradient_header_bar() + footer_bar()
    b += slide_title("Introduction to IoT Security")
    b += accent_line(emu(0.96))

    # Stats row
    stats = [
        ("15.9B+", "IoT Devices\nWorldwide (2023)", C_ACCENT3),
        ("75.4B", "Projected by 2025", C_ACCENT1),
        ("3x", "Attack Surface\nGrowth Rate", C_ACCENT4),
        ("$6T+", "Annual Cybercrime\nCost by 2025", C_ACCENT5),
    ]
    sw = emu(2.9)
    for i, (val, lbl, col) in enumerate(stats):
        sx = emu(0.4) + i * emu(3.1)
        b += stat_card(sx, emu(1.1), sw, emu(1.3), val, lbl, val_color=col)

    # Three info boxes
    boxes = [
        ("🔌  IoT Growth", C_ACCENT1, [
            "Billions of smart devices: sensors, cameras, wearables",
            "Embedded in hospitals, factories, smart cities, homes",
            "Generating terabytes of network traffic daily",
            "Connected via Wi-Fi, Bluetooth, Zigbee, MQTT, CoAP",
        ]),
        ("⚠️  Cyber Threats", C_ACCENT4, [
            "IoT is top target: 1.5 billion attacks in H1 2021",
            "DDoS botnets formed from compromised IoT devices",
            "Ransomware, MITM, credential theft on the rise",
            "Many devices ship with default/no security credentials",
        ]),
        ("💡  Edge Limitations", C_ACCENT5, [
            "Microcontrollers: 64KB–512KB RAM, slow CPUs",
            "No space for heavy antivirus or deep learning models",
            "Devices run 24/7, rarely receive security patches",
            "Traditional IDS requires cloud round-trip — too slow",
        ]),
    ]
    bw = emu(4.0)
    for i, (title, col, lines) in enumerate(boxes):
        bx = emu(0.4) + i * emu(4.3)
        b += bullet_box(bx, emu(2.6), bw, emu(4.3), lines,
                        title=title, title_color=col, base_sz=15, lc=col)
    return b


def s04_problem():
    """Slide 4 — Problem Statement"""
    b = bg() + gradient_header_bar() + footer_bar()
    b += slide_title("Problem Statement")
    b += accent_line(emu(0.96))

    # Main problem text
    sp = sp_pr(emu(0.5), emu(1.05), emu(12.3), emu(0.6), fill="none")
    tb = txBody(para(run(
        "Traditional Intrusion Detection Systems (IDS) rely on known attack signatures — "
        "they are completely blind to novel, unseen (Zero-Day) attacks.",
        sz=17, color=C_LGRAY), algn="l"), anchor="ctr")
    b += shape(sp, tb, next_id(), "probdesc")

    # Two comparison cards
    # Known Attack IDS
    b += rect_shape(next_id(), "knowncard", emu(0.4), emu(1.8), emu(5.9), emu(4.9),
                   fill=C_CARD, line_color=C_ACCENT5, rounding=60000)
    sp = sp_pr(emu(0.5), emu(1.85), emu(5.7), emu(0.5), fill="none")
    tb = txBody(para(run("⚡  Traditional IDS — Known Attacks", sz=17, bold=True, color=C_ACCENT5), algn="c"), anchor="ctr")
    b += shape(sp, tb, next_id(), "knownhdr")

    known_lines = [
        {"text": "Signature-based detection (pattern matching)", "color": C_WHITE, "sz": 15},
        {"text": "Works well for previously catalogued attacks", "color": C_WHITE, "sz": 15},
        {"text": "Requires frequent signature database updates", "color": C_LGRAY, "sz": 14},
        {"text": "Zero-Day attacks bypass signatures entirely", "color": C_ACCENT4, "sz": 15, "bold": True},
        {"text": "High computational cost for deep-learning IDS", "color": C_ACCENT4, "sz": 15},
        {"text": "Not suitable for lightweight IoT edge deployment", "color": C_ACCENT4, "sz": 15},
    ]
    for i, ln in enumerate(known_lines):
        iy = emu(2.45) + i * emu(0.57)
        sp = sp_pr(emu(0.55), iy, emu(5.6), emu(0.48), fill="none")
        tb = txBody(para(run(("  ✓  " if ln.get("color") == C_WHITE else "  ✗  ") + ln["text"],
                             sz=ln["sz"], color=ln.get("color", C_WHITE),
                             bold=ln.get("bold", False)), algn="l"), anchor="ctr")
        b += shape(sp, tb, next_id(), f"kl{i}")

    # Zero-Day card
    b += rect_shape(next_id(), "zdcard", emu(6.7), emu(1.8), emu(6.2), emu(4.9),
                   fill=C_CARD, line_color=C_ACCENT1, rounding=60000)
    sp = sp_pr(emu(6.8), emu(1.85), emu(6.0), emu(0.5), fill="none")
    tb = txBody(para(run("🛡  Zero-Day Attack Challenge", sz=17, bold=True, color=C_ACCENT1), algn="c"), anchor="ctr")
    b += shape(sp, tb, next_id(), "zdhdr")

    zd_lines = [
        {"text": "Never-before-seen attack patterns", "color": C_ACCENT4, "sz": 15, "bold": True},
        {"text": "No signatures available in any database", "color": C_ACCENT4, "sz": 15},
        {"text": "Attackers intentionally evolve techniques to evade", "color": C_LGRAY, "sz": 14},
        {"text": "Requires behavioural / anomaly detection approach", "color": C_ACCENT3, "sz": 15},
        {"text": "Our Solution: Autoencoder-based anomaly detection", "color": C_ACCENT3, "sz": 15, "bold": True},
        {"text": "Detects abnormal behaviour without prior knowledge", "color": C_ACCENT3, "sz": 15},
    ]
    for i, ln in enumerate(zd_lines):
        iy = emu(2.45) + i * emu(0.57)
        sp = sp_pr(emu(6.75), iy, emu(6.0), emu(0.48), fill="none")
        tb = txBody(para(run(("  ⚠  " if ln.get("color") == C_ACCENT4 else "  ✓  ") + ln["text"],
                             sz=ln["sz"], color=ln.get("color", C_WHITE),
                             bold=ln.get("bold", False)), algn="l"), anchor="ctr")
        b += shape(sp, tb, next_id(), f"zdl{i}")

    return b


def s05_objectives():
    """Slide 5 — Project Objectives"""
    b = bg() + gradient_header_bar() + footer_bar()
    b += slide_title("Project Objectives")
    b += accent_line(emu(0.96))

    objectives = [
        (C_ACCENT1, "01", "Known Attack Detection",
         "Build a supervised LightGBM classifier to identify 10 known IoT attack types with >99% accuracy"),
        (C_ACCENT2, "02", "Zero-Day Attack Detection",
         "Deploy an Autoencoder trained solely on normal traffic to detect unseen anomalous behaviour"),
        (C_ACCENT3, "03", "Lightweight Architecture",
         "Design a system deployable on edge gateways — Autoencoder has only 11,907 parameters"),
        (C_ACCENT5, "04", "Hybrid Fusion IDS",
         "Combine both models in a smart fusion layer for superior accuracy across known and zero-day threats"),
        (C_ACCENT4, "05", "Research Contribution",
         "Benchmark against Isolation Forest baseline and validate zero-day scenario with hidden attack split"),
        (C_LGRAY,   "06", "Edge Deployment Suitability",
         "Achieve real-time detection capability suitable for resource-constrained IoT edge environments"),
    ]

    cols = 2
    col_w = emu(6.3)
    for i, (col, num, title, desc) in enumerate(objectives):
        row, c = divmod(i, cols)
        ox = emu(0.4) + c * emu(6.5)
        oy = emu(1.15) + row * emu(2.0)

        b += rect_shape(next_id(), f"ob{i}", ox, oy, col_w, emu(1.85),
                       fill=C_CARD, line_color=col, rounding=60000)
        # Number badge
        b += rect_shape(next_id(), f"obn{i}", ox + emu(0.18), oy + emu(0.2),
                       emu(0.48), emu(0.48), fill=col, rounding=166666,
                       text_xml=para(run(num, sz=14, bold=True, color=C_BG_DARK), algn="c"))
        # Title
        sp = sp_pr(ox + emu(0.78), oy + emu(0.18), col_w - emu(0.95), emu(0.5), fill="none")
        tb = txBody(para(run(title, sz=17, bold=True, color=col), algn="l"), anchor="ctr")
        b += shape(sp, tb, next_id(), f"obt{i}")
        # Description
        sp = sp_pr(ox + emu(0.2), oy + emu(0.75), col_w - emu(0.4), emu(1.0), fill="none")
        tb = txBody(para(run(desc, sz=14, color=C_LGRAY), algn="l"), anchor="t",
                   lIns=emu(0.05), rIns=emu(0.05))
        b += shape(sp, tb, next_id(), f"obd{i}")

    return b


def s06_why_zeroday():
    """Slide 6 — Why Zero-Day Detection is Difficult"""
    b = bg() + gradient_header_bar() + footer_bar()
    b += slide_title("Why Zero-Day Detection is Difficult")
    b += accent_line(emu(0.96))

    # Central challenge graphic — concentric rings concept
    reasons = [
        (C_ACCENT4, "No Prior Signatures",
         "Zero-day attacks have never been catalogued. No fingerprint exists in any threat database."),
        (C_ACCENT2, "Constantly Evolving Threats",
         "Attackers continuously mutate techniques to evade detection — polymorphic and metamorphic malware."),
        (C_ACCENT5, "Normal vs. Malicious Boundary Blurs",
         "Sophisticated attacks mimic legitimate traffic patterns, making statistical separation extremely hard."),
        (C_ACCENT1, "High False Positive Risk",
         "Overly sensitive anomaly detectors flag normal traffic as attacks, causing alert fatigue."),
        (C_ACCENT3, "Limited Training Data",
         "By definition, zero-day samples cannot exist in training data — models must generalise beyond seen data."),
    ]

    for i, (col, title, desc) in enumerate(reasons):
        iy = emu(1.15) + i * emu(1.2)
        # Left icon badge
        b += rect_shape(next_id(), f"wb{i}", emu(0.4), iy, emu(0.6), emu(0.9),
                       fill=col, rounding=60000,
                       text_xml=para(run(str(i+1), sz=22, bold=True, color=C_BG_DARK), algn="c"))
        # Content card
        b += rect_shape(next_id(), f"wc{i}", emu(1.15), iy, emu(11.55), emu(0.9),
                       fill=C_CARD, line_color=col, rounding=40000)
        sp = sp_pr(emu(1.3), iy, emu(11.3), emu(0.42), fill="none")
        tb = txBody(para(run(title, sz=17, bold=True, color=col), algn="l"), anchor="ctr")
        b += shape(sp, tb, next_id(), f"wt{i}")
        sp = sp_pr(emu(1.3), iy + emu(0.42), emu(11.3), emu(0.45), fill="none")
        tb = txBody(para(run(desc, sz=14, color=C_LGRAY), algn="l"), anchor="t")
        b += shape(sp, tb, next_id(), f"wd{i}")

    return b


def s07_dataset():
    """Slide 7 — Dataset Overview"""
    b = bg() + gradient_header_bar() + footer_bar()
    b += slide_title("Dataset Overview — Edge-IIoT")
    b += accent_line(emu(0.96))

    # Key stats
    stats = [
        ("157,800", "Raw Rows", C_ACCENT1),
        ("152,389", "After Cleaning", C_ACCENT3),
        ("63→53", "Features", C_ACCENT2),
        ("15", "Traffic Classes", C_ACCENT5),
    ]
    for i, (v, l, c) in enumerate(stats):
        sx = emu(0.4) + i * emu(3.1)
        b += stat_card(sx, emu(1.1), emu(2.9), emu(1.15), v, l, val_color=c)

    # Dataset info card
    b += rect_shape(next_id(), "dsinfo", emu(0.4), emu(2.45), emu(4.7), emu(4.3),
                   fill=C_CARD, line_color=C_ACCENT1, rounding=60000)
    info_lines = [
        ("Dataset", "Edge-IIoT (ML-EdgeIIoT-dataset)", C_ACCENT1),
        ("Source", "Kaggle — sibasispradhan/edge-iiotset-dataset", C_LGRAY),
        ("Environment", "Simulated IoT Lab — Real network traffic", C_LGRAY),
        ("Protocol Coverage", "TCP, UDP, ICMP, HTTP, DNS, MQTT, ARP, Modbus", C_LGRAY),
        ("Normal Traffic", "24,152 rows (16%)", C_ACCENT3),
        ("Attack Traffic", "128,237 rows (84%)", C_ACCENT4),
        ("Train Split (Known)", "121,293 rows — 10 known attack types", C_ACCENT5),
        ("Zero-Day Hidden", "31,096 rows — 5 unseen attack types", C_ACCENT2),
    ]
    sp = sp_pr(emu(0.55), emu(2.5), emu(4.4), emu(0.45), fill="none")
    tb = txBody(para(run("📊  Dataset Properties", sz=16, bold=True, color=C_ACCENT1), algn="l"), anchor="ctr")
    b += shape(sp, tb, next_id(), "dshdr")
    for i, (k, v, c) in enumerate(info_lines):
        iy = emu(3.05) + i * emu(0.46)
        sp = sp_pr(emu(0.55), iy, emu(4.5), emu(0.42), fill="none")
        tb = txBody(para(run(f"{k}:  ", sz=13, bold=True, color=c) +
                         run(v, sz=13, color=C_LGRAY), algn="l"), anchor="ctr")
        b += shape(sp, tb, next_id(), f"di{i}")

    # Attack distribution (visual bar chart)
    b += rect_shape(next_id(), "distcard", emu(5.3), emu(2.45), emu(7.6), emu(4.3),
                   fill=C_CARD, line_color=C_ACCENT2, rounding=60000)
    sp = sp_pr(emu(5.5), emu(2.52), emu(7.2), emu(0.4), fill="none")
    tb = txBody(para(run("Attack Type Distribution", sz=15, bold=True, color=C_ACCENT2), algn="c"), anchor="ctr")
    b += shape(sp, tb, next_id(), "disthdr")

    # Horizontal mini-bars for top attacks
    attacks = [
        ("Normal", 24152, C_ACCENT3),
        ("DDoS_UDP", 14498, C_ACCENT4),
        ("DDoS_ICMP", 13096, C_ACCENT4),
        ("DDoS_HTTP", 10559, C_ACCENT4),
        ("SQL Injection", 10286, C_ACCENT2),
        ("DDoS_TCP", 10247, C_ACCENT4),
        ("Uploading*", 10237, C_ACCENT5),
        ("Vulnerability*", 10062, C_ACCENT5),
        ("Password", 9978, C_ACCENT1),
    ]
    max_v = 24152
    for i, (name, cnt, col) in enumerate(attacks):
        ay = emu(3.05) + i * emu(0.41)
        bar_max = emu(3.5)
        bar_w = int(bar_max * cnt / max_v)
        sp = sp_pr(emu(5.45), ay, emu(2.1), emu(0.33), fill="none")
        tb = txBody(para(run(name, sz=11, color=C_LGRAY), algn="r"), anchor="ctr")
        b += shape(sp, tb, next_id(), f"al{i}")
        b += rect_shape(next_id(), f"at{i}", emu(7.6), ay + emu(0.06), bar_max, emu(0.22),
                       fill=C_DGRAY, rounding=15000)
        if bar_w > 0:
            b += rect_shape(next_id(), f"ab{i}", emu(7.6), ay + emu(0.06), bar_w, emu(0.22),
                           fill=col, rounding=15000)
        sp = sp_pr(emu(11.2), ay, emu(1.5), emu(0.33), fill="none")
        tb = txBody(para(run(f"{cnt:,}", sz=11, color=col), algn="l"), anchor="ctr")
        b += shape(sp, tb, next_id(), f"av{i}")

    sp = sp_pr(emu(5.45), emu(6.7), emu(7.2), emu(0.25), fill="none")
    tb = txBody(para(run("* Marked types are Zero-Day (hidden during training)", sz=11,
                         color=C_ACCENT5, italic=True), algn="l"), anchor="ctr")
    b += shape(sp, tb, next_id(), "dsfoot")

    return b


def s08_preprocessing():
    """Slide 8 — Data Preprocessing"""
    b = bg() + gradient_header_bar() + footer_bar()
    b += slide_title("Data Preprocessing Pipeline")
    b += accent_line(emu(0.96))

    # Pipeline flow — 6 steps
    steps = [
        (C_ACCENT1, "01\nLoad", "Read CSV\n157,800 × 63"),
        (C_ACCENT2, "02\nDrop", "Remove 10\nirrelevant cols"),
        (C_ACCENT4, "03\nClean", "Remove nulls\n& duplicates"),
        (C_ACCENT5, "04\nEncode", "Label-encode\ntext columns"),
        (C_ACCENT3, "05\nScale", "StandardScaler\non normal traffic"),
        (C_ACCENT1, "06\nSplit", "Known(121K)\n+ Zero-Day(31K)"),
    ]

    sw2 = emu(1.85)
    sy = emu(1.2)
    sh2 = emu(1.3)
    for i, (col, title, desc) in enumerate(steps):
        sx = emu(0.35) + i * emu(2.15)
        b += rect_shape(next_id(), f"st{i}", sx, sy, sw2, sh2,
                       fill=C_CARD, line_color=col, rounding=60000)
        b += rect_shape(next_id(), f"stn{i}", sx + sw2//2 - emu(0.35), sy - emu(0.3),
                       emu(0.7), emu(0.38), fill=col, rounding=60000,
                       text_xml=para(run(title.split("\n")[0], sz=12, bold=True, color=C_BG_DARK), algn="c"))
        sp = sp_pr(sx + emu(0.05), sy + emu(0.05), sw2 - emu(0.1), sh2 - emu(0.1), fill="none")
        tb = txBody(para(run(title.split("\n")[1] if "\n" in title else title,
                             sz=14, bold=True, color=col), algn="c") +
                    para(run(desc, sz=12, color=C_LGRAY), algn="c"), anchor="ctr")
        b += shape(sp, tb, next_id(), f"stt{i}")
        if i < len(steps) - 1:
            b += arrow_right(sx + sw2 + emu(0.08), sy + sh2//2)

    # Detail boxes row 2
    details = [
        ("🗑  Columns Dropped", C_ACCENT4, [
            "frame.time, ip.src_host, ip.dst_host",
            "http.request.full_uri, http.file_data",
            "icmp.transmit_timestamp, mqtt.msg",
            "Reason: identifiers ≠ behaviour patterns",
        ]),
        ("🔢  Encoding & Memory", C_ACCENT5, [
            "Object columns → Label Encoding (.cat.codes)",
            "float64 → float32  (50% memory reduction)",
            "int64 → int32 / int8 as appropriate",
            "152,389 rows × 53 features final shape",
        ]),
        ("⚖  StandardScaler", C_ACCENT3, [
            "Fit ONLY on normal traffic (24,152 rows)",
            "Transform: (x − mean) / std → mean=0, std=1",
            "Saved as scaler.pkl — used in all models",
            "Critical: Autoencoder sensitive to scale",
        ]),
        ("📂  Output Files", C_ACCENT1, [
            "master_clean.parquet — full 152,389 rows",
            "known_train.parquet — 121,293 known rows",
            "zero_day_test.parquet — 31,096 hidden rows",
            "scaler.pkl — fitted StandardScaler saved",
        ]),
    ]
    dw = emu(3.05)
    for i, (title, col, lines) in enumerate(details):
        dx = emu(0.35) + i * emu(3.22)
        b += bullet_box(dx, emu(2.75), dw, emu(3.95), lines,
                        title=title, title_color=col, base_sz=13, lc=col)
    return b


def s09_known_vs_unknown():
    """Slide 9 — Known vs Unknown Attack Split"""
    b = bg() + gradient_header_bar() + footer_bar()
    b += slide_title("Known vs. Unknown Attack Split")
    b += accent_line(emu(0.96))

    # Explanation
    sp = sp_pr(emu(0.5), emu(1.05), emu(12.3), emu(0.5), fill="none")
    tb = txBody(para(run(
        "The most critical experimental design decision: 5 attack types are deliberately "
        "hidden from all training — simulating real-world zero-day scenarios.",
        sz=16, color=C_LGRAY), algn="l"), anchor="ctr")
    b += shape(sp, tb, next_id(), "expl")

    # Two columns: Known | Zero-Day
    # Known card
    b += rect_shape(next_id(), "kcard", emu(0.4), emu(1.7), emu(6.0), emu(5.3),
                   fill=C_CARD, line_color=C_ACCENT5, rounding=60000)
    sp = sp_pr(emu(0.5), emu(1.75), emu(5.8), emu(0.5), fill="none")
    tb = txBody(para(run("✅  KNOWN — Used in Training", sz=17, bold=True, color=C_ACCENT5), algn="c"), anchor="ctr")
    b += shape(sp, tb, next_id(), "khdr")

    known = [
        ("Normal", "24,152", C_ACCENT3),
        ("DDoS_UDP", "14,498", C_ACCENT4),
        ("DDoS_ICMP", "13,096", C_ACCENT4),
        ("DDoS_HTTP", "10,559", C_ACCENT4),
        ("SQL_injection", "10,286", C_ACCENT2),
        ("DDoS_TCP", "10,247", C_ACCENT4),
        ("Password", "9,978", C_ACCENT1),
        ("Backdoor", "9,866", C_ACCENT2),
        ("Ransomware", "9,690", C_ACCENT2),
        ("Port_Scanning", "8,921", C_ACCENT1),
    ]
    # Header row
    sp = sp_pr(emu(0.55), emu(2.35), emu(5.7), emu(0.35), fill="none")
    tb = txBody(para(run("Attack Type", sz=13, bold=True, color=C_ACCENT5) +
                     run("                    Count", sz=13, bold=True, color=C_ACCENT5), algn="l"), anchor="ctr")
    b += shape(sp, tb, next_id(), "kcolhdr")
    b += rect_shape(next_id(), "khr", emu(0.55), emu(2.72), emu(5.65), emu(0.03), fill=C_ACCENT5)

    for i, (name, cnt, col) in enumerate(known):
        iy = emu(2.8) + i * emu(0.41)
        bg_col = C_CARD2 if i % 2 == 0 else C_CARD
        b += rect_shape(next_id(), f"kr{i}", emu(0.55), iy, emu(5.65), emu(0.39),
                       fill=bg_col, rounding=20000)
        sp = sp_pr(emu(0.65), iy, emu(3.8), emu(0.39), fill="none")
        tb = txBody(para(run(name, sz=13, color=C_WHITE), algn="l"), anchor="ctr")
        b += shape(sp, tb, next_id(), f"kn{i}")
        sp = sp_pr(emu(4.5), iy, emu(1.6), emu(0.39), fill="none")
        tb = txBody(para(run(cnt, sz=13, bold=True, color=col), algn="r"), anchor="ctr")
        b += shape(sp, tb, next_id(), f"kc{i}")

    # Total
    sp = sp_pr(emu(0.55), emu(6.9), emu(5.65), emu(0.4), fill="none")
    tb = txBody(para(run("TOTAL  →  121,293 rows", sz=14, bold=True, color=C_ACCENT5), algn="c"), anchor="ctr")
    b += shape(sp, tb, next_id(), "ktot")

    # Zero-Day card
    b += rect_shape(next_id(), "zdcard", emu(6.7), emu(1.7), emu(6.2), emu(5.3),
                   fill=C_CARD, line_color=C_ACCENT4, rounding=60000)
    sp = sp_pr(emu(6.8), emu(1.75), emu(6.0), emu(0.5), fill="none")
    tb = txBody(para(run("🚨  ZERO-DAY — Hidden (Not in Training)", sz=16, bold=True, color=C_ACCENT4), algn="c"), anchor="ctr")
    b += shape(sp, tb, next_id(), "zdhdr")

    zd = [
        ("Uploading", "10,237", "Data Exfiltration"),
        ("Vulnerability Scanner", "10,062", "Reconnaissance"),
        ("XSS", "9,550", "Web Attack"),
        ("Fingerprinting", "853", "Reconnaissance"),
        ("MITM", "394", "Man-in-the-Middle"),
    ]
    sp = sp_pr(emu(6.85), emu(2.35), emu(5.9), emu(0.35), fill="none")
    tb = txBody(para(run("Attack Type", sz=13, bold=True, color=C_ACCENT4) +
                     run("         Count   Category", sz=13, bold=True, color=C_ACCENT4), algn="l"), anchor="ctr")
    b += shape(sp, tb, next_id(), "zdcolhdr")
    b += rect_shape(next_id(), "zdhr", emu(6.85), emu(2.72), emu(5.9), emu(0.03), fill=C_ACCENT4)

    for i, (name, cnt, cat) in enumerate(zd):
        iy = emu(2.8) + i * emu(0.65)
        b += rect_shape(next_id(), f"zdr{i}", emu(6.85), iy, emu(5.9), emu(0.58),
                       fill=C_CARD2, rounding=20000)
        sp = sp_pr(emu(6.95), iy, emu(2.9), emu(0.58), fill="none")
        tb = txBody(para(run(name, sz=13, color=C_WHITE), algn="l") +
                    para(run(cat, sz=11, color=C_LGRAY, italic=True), algn="l"), anchor="ctr")
        b += shape(sp, tb, next_id(), f"zdn{i}")
        sp = sp_pr(emu(9.9), iy, emu(2.6), emu(0.58), fill="none")
        tb = txBody(para(run(cnt, sz=14, bold=True, color=C_ACCENT4), algn="r"), anchor="ctr")
        b += shape(sp, tb, next_id(), f"zdc{i}")

    sp = sp_pr(emu(6.85), emu(6.1), emu(5.9), emu(0.5), fill="none")
    tb = txBody(para(run("TOTAL  →  31,096 rows", sz=14, bold=True, color=C_ACCENT4), algn="c"), anchor="ctr")
    b += shape(sp, tb, next_id(), "zdtot")

    sp = sp_pr(emu(6.85), emu(6.65), emu(5.9), emu(0.5), fill="none")
    tb = txBody(para(run("⚡  LightGBM NEVER sees these during training",
                         sz=13, bold=True, color=C_ACCENT1), algn="c"), anchor="ctr")
    b += shape(sp, tb, next_id(), "zdnote")

    return b


def s10_architecture():
    """Slide 10 — Overall System Architecture"""
    b = bg() + gradient_header_bar() + footer_bar()
    b += slide_title("Overall System Architecture")
    b += accent_line(emu(0.96))

    # Main architecture flow (vertical centre)
    cx = SW // 2
    boxes = [
        (emu(1.15), emu(0.85), "🌐  Raw IoT Network Traffic",
         "157,800 packets  ·  TCP/UDP/HTTP/MQTT/DNS/ARP",
         C_ACCENT1, C_BG_MID),
        (emu(1.45), emu(0.75), "⚙  Data Preprocessing",
         "Cleaning · Encoding · Normalization · Splitting",
         C_ACCENT2, C_CARD),
        (emu(1.45), emu(0.75), "Known Traffic (121K)  +  Normal Traffic (24K)",
         "Supervised path | Autoencoder path",
         C_ACCENT5, C_CARD),
    ]
    # Draw linear flow on left side
    flow_items = [
        ("🌐  IoT Traffic Input", "157,800 packets — 63 features", C_ACCENT1),
        ("⚙  Preprocessing", "Clean · Encode · Normalise · Split", C_ACCENT2),
        ("🌿  LightGBM Classifier", "Trained on 10 known attack types", C_ACCENT5),
        ("🧠  Autoencoder", "Trained on normal traffic only", C_ACCENT3),
        ("🔀  Fusion Logic", "IF confidence ≥90% normal → accept  ELSE → AE", C_ACCENT2),
        ("🛡  Final IDS Decision", "Known Attack Type  |  Zero-Day Anomaly  |  Normal", C_ACCENT1),
    ]

    # Left flow column
    fw = emu(5.2)
    fx = emu(0.5)
    for i, (title, sub, col) in enumerate(flow_items):
        fy = emu(1.15) + i * emu(1.0)
        b += rect_shape(next_id(), f"ff{i}", fx, fy, fw, emu(0.78),
                       fill=C_CARD, line_color=col, rounding=60000)
        sp = sp_pr(fx + emu(0.15), fy, fw - emu(0.15), emu(0.42), fill="none")
        tb = txBody(para(run(title, sz=16, bold=True, color=col), algn="l"), anchor="b")
        b += shape(sp, tb, next_id(), f"fft{i}")
        sp = sp_pr(fx + emu(0.15), fy + emu(0.42), fw - emu(0.15), emu(0.33), fill="none")
        tb = txBody(para(run(sub, sz=12, color=C_LGRAY), algn="l"), anchor="t")
        b += shape(sp, tb, next_id(), f"ffs{i}")
        if i < len(flow_items) - 1:
            b += arrow_down(fx + fw // 2, fy + emu(0.78), h=emu(0.25))

    # Right side — architecture details
    b += rect_shape(next_id(), "rcard", emu(6.1), emu(1.15), emu(6.8), emu(5.9),
                   fill=C_CARD, line_color=C_ACCENT1, rounding=60000)
    sp = sp_pr(emu(6.25), emu(1.2), emu(6.5), emu(0.45), fill="none")
    tb = txBody(para(run("Architecture Highlights", sz=17, bold=True, color=C_ACCENT1), algn="c"), anchor="ctr")
    b += shape(sp, tb, next_id(), "archdr")

    highlights = [
        (C_ACCENT5, "LightGBM",
         ["Gradient boosting — 10-class supervised classifier",
          "99.99% accuracy on known attack types",
          "Fast inference — tree-based (edge-friendly)"]),
        (C_ACCENT3, "Autoencoder",
         ["51→64→32→16→32→64→51 symmetric architecture",
          "Only 11,907 parameters — ultra-lightweight",
          "Detects anomalies via reconstruction error > 0.0122"]),
        (C_ACCENT2, "Fusion Layer",
         ["Threshold-based confidence routing",
          "LightGBM handles known, AE handles unknown",
          "96.82% accuracy on zero-day scenario"]),
    ]
    for i, (col, title, pts) in enumerate(highlights):
        hy = emu(1.85) + i * emu(1.7)
        b += rect_shape(next_id(), f"hc{i}", emu(6.25), hy, emu(6.4), emu(1.55),
                       fill=C_BG_MID, line_color=col, rounding=40000)
        sp = sp_pr(emu(6.4), hy + emu(0.08), emu(6.1), emu(0.38), fill="none")
        tb = txBody(para(run(f"■  {title}", sz=15, bold=True, color=col), algn="l"), anchor="ctr")
        b += shape(sp, tb, next_id(), f"hct{i}")
        for j, pt in enumerate(pts):
            iy2 = hy + emu(0.52) + j * emu(0.33)
            sp = sp_pr(emu(6.5), iy2, emu(5.95), emu(0.3), fill="none")
            tb = txBody(para(run("  •  " + pt, sz=12, color=C_LGRAY), algn="l"), anchor="ctr")
            b += shape(sp, tb, next_id(), f"hcp{i}{j}")

    return b


def s11_lightgbm():
    """Slide 11 — LightGBM Model"""
    b = bg() + gradient_header_bar() + footer_bar()
    b += slide_title("LightGBM — Known Attack Classifier")
    b += accent_line(emu(0.96))

    # Left column — Why LightGBM
    b += rect_shape(next_id(), "lgbcard", emu(0.4), emu(1.15), emu(5.7), emu(5.9),
                   fill=C_CARD, line_color=C_ACCENT5, rounding=60000)
    sp = sp_pr(emu(0.55), emu(1.2), emu(5.4), emu(0.48), fill="none")
    tb = txBody(para(run("⚡  Why LightGBM?", sz=18, bold=True, color=C_ACCENT5), algn="c"), anchor="ctr")
    b += shape(sp, tb, next_id(), "whyhdr")

    why_pts = [
        (C_ACCENT5, "Lightweight & Fast",
         "Tree-based model — no GPU needed, runs on edge CPUs in microseconds"),
        (C_ACCENT1, "High Accuracy",
         "Gradient boosting with leaf-wise growth achieves state-of-art tabular accuracy"),
        (C_ACCENT3, "Handles Imbalanced Data",
         "Built-in class_weight support for unequal attack class distribution"),
        (C_ACCENT2, "Feature Importance",
         "Provides interpretable feature rankings — critical for research validation"),
        (C_ACCENT4, "Multi-Class Native",
         "Single model natively classifies 10 attack categories simultaneously"),
    ]
    for i, (col, title, desc) in enumerate(why_pts):
        iy = emu(1.85) + i * emu(0.97)
        b += rect_shape(next_id(), f"wp{i}", emu(0.55), iy, emu(5.4), emu(0.85),
                       fill=C_BG_MID, line_color=col, rounding=40000)
        sp = sp_pr(emu(0.7), iy + emu(0.05), emu(5.1), emu(0.35), fill="none")
        tb = txBody(para(run(f"▸  {title}", sz=14, bold=True, color=col), algn="l"), anchor="ctr")
        b += shape(sp, tb, next_id(), f"wpt{i}")
        sp = sp_pr(emu(0.7), iy + emu(0.42), emu(5.1), emu(0.4), fill="none")
        tb = txBody(para(run(desc, sz=12, color=C_LGRAY), algn="l"), anchor="t")
        b += shape(sp, tb, next_id(), f"wpd{i}")

    # Right column — Model details
    b += rect_shape(next_id(), "lgbdetail", emu(6.3), emu(1.15), emu(6.6), emu(5.9),
                   fill=C_CARD, line_color=C_ACCENT1, rounding=60000)
    sp = sp_pr(emu(6.45), emu(1.2), emu(6.3), emu(0.48), fill="none")
    tb = txBody(para(run("🌿  Model Configuration", sz=18, bold=True, color=C_ACCENT1), algn="c"), anchor="ctr")
    b += shape(sp, tb, next_id(), "modcfghdr")

    params = [
        ("objective", "multiclass", C_ACCENT1),
        ("num_class", "10", C_ACCENT5),
        ("n_estimators", "300", C_ACCENT3),
        ("learning_rate", "0.05", C_ACCENT2),
        ("max_depth", "-1 (auto)", C_LGRAY),
        ("class_weight", "balanced", C_ACCENT3),
        ("Training Rows", "97,034  (80%)", C_ACCENT5),
        ("Test Rows", "24,259  (20%)", C_ACCENT5),
        ("Features Used", "51  (after PCA-less selection)", C_ACCENT1),
    ]
    sp = sp_pr(emu(6.45), emu(1.78), emu(6.3), emu(0.38), fill="none")
    tb = txBody(para(run("Parameter", sz=13, bold=True, color=C_ACCENT1) +
                     run("                                Value", sz=13, bold=True, color=C_ACCENT1), algn="l"), anchor="ctr")
    b += shape(sp, tb, next_id(), "cfgcolhdr")
    b += rect_shape(next_id(), "cfghr", emu(6.45), emu(2.17), emu(6.3), emu(0.03), fill=C_ACCENT1)

    for i, (k, v, c) in enumerate(params):
        iy = emu(2.25) + i * emu(0.5)
        bg_c = C_CARD2 if i % 2 == 0 else C_CARD
        b += rect_shape(next_id(), f"cfgr{i}", emu(6.45), iy, emu(6.3), emu(0.46),
                       fill=bg_c, rounding=15000)
        sp = sp_pr(emu(6.6), iy, emu(3.8), emu(0.46), fill="none")
        tb = txBody(para(run(k, sz=13, color=C_LGRAY), algn="l"), anchor="ctr")
        b += shape(sp, tb, next_id(), f"cfgk{i}")
        sp = sp_pr(emu(10.5), iy, emu(2.1), emu(0.46), fill="none")
        tb = txBody(para(run(v, sz=13, bold=True, color=c), algn="r"), anchor="ctr")
        b += shape(sp, tb, next_id(), f"cfgv{i}")

    return b


def s12_lgbm_workflow():
    """Slide 12 — LightGBM Workflow"""
    b = bg() + gradient_header_bar() + footer_bar()
    b += slide_title("LightGBM Workflow & Training Pipeline")
    b += accent_line(emu(0.96))

    # Flow diagram — horizontal
    flow = [
        ("Known Traffic\n121,293 rows", C_ACCENT5, "Input"),
        ("Train/Test\nSplit 80:20", C_ACCENT2, "Split"),
        ("Feature\nLearning", C_ACCENT1, "Learn"),
        ("Gradient\nBoosting\nTrees ×300", C_ACCENT3, "Train"),
        ("10-Class\nPrediction", C_ACCENT5, "Predict"),
    ]
    fw2 = emu(2.1)
    fh = emu(1.3)
    for i, (text, col, label) in enumerate(flow):
        fx = emu(0.4) + i * emu(2.55)
        fy = emu(1.15)
        b += rect_shape(next_id(), f"lf{i}", fx, fy, fw2, fh,
                       fill=C_CARD, line_color=col, rounding=60000)
        sp = sp_pr(fx + emu(0.05), fy, fw2 - emu(0.1), fh, fill="none")
        tb = txBody(para(run(text, sz=14, bold=(i==0 or i==4), color=col), algn="c"), anchor="ctr")
        b += shape(sp, tb, next_id(), f"lft{i}")
        b += rect_shape(next_id(), f"lfb{i}", fx + fw2//2 - emu(0.8), fy - emu(0.35),
                       emu(1.6), emu(0.28), fill=col, rounding=40000,
                       text_xml=para(run(label, sz=10, bold=True, color=C_BG_DARK), algn="c"))
        if i < len(flow) - 1:
            b += arrow_right(fx + fw2, fy + fh // 2)

    # Feature importance chart
    b += rect_shape(next_id(), "ficard", emu(0.4), emu(2.75), emu(6.2), emu(4.3),
                   fill=C_CARD, line_color=C_ACCENT5, rounding=60000)
    sp = sp_pr(emu(0.55), emu(2.82), emu(5.9), emu(0.42), fill="none")
    tb = txBody(para(run("Top 10 Feature Importance Scores", sz=15, bold=True, color=C_ACCENT5), algn="c"), anchor="ctr")
    b += shape(sp, tb, next_id(), "fihdr")

    features = [
        ("tcp.srcport",  13467, C_ACCENT1),
        ("tcp.options",  12777, C_ACCENT2),
        ("tcp.dstport",   8849, C_ACCENT5),
        ("tcp.ack",       7849, C_ACCENT3),
        ("tcp.ack_raw",   6417, C_ACCENT1),
        ("tcp.checksum",  6109, C_ACCENT2),
        ("tcp.seq",       4226, C_ACCENT5),
        ("http.request",  2213, C_ACCENT3),
        ("tcp.len",       2181, C_ACCENT1),
        ("udp.stream",    2009, C_ACCENT2),
    ]
    max_fi = 13467
    bar_max_w = emu(3.2)
    for i, (fname, score, col) in enumerate(features):
        iy = emu(3.35) + i * emu(0.36)
        sp = sp_pr(emu(0.55), iy, emu(1.9), emu(0.3), fill="none")
        tb = txBody(para(run(fname, sz=11, color=C_LGRAY), algn="r"), anchor="ctr")
        b += shape(sp, tb, next_id(), f"fn{i}")
        bw = int(bar_max_w * score / max_fi)
        b += rect_shape(next_id(), f"ftrack{i}", emu(2.5), iy + emu(0.04), bar_max_w, emu(0.22), fill=C_DGRAY, rounding=15000)
        if bw > 0:
            b += rect_shape(next_id(), f"fbar{i}", emu(2.5), iy + emu(0.04), bw, emu(0.22), fill=col, rounding=15000)
        sp = sp_pr(emu(5.75), iy, emu(0.75), emu(0.3), fill="none")
        tb = txBody(para(run(f"{score:,}", sz=10, color=col), algn="l"), anchor="ctr")
        b += shape(sp, tb, next_id(), f"fv{i}")

    # Class output panel
    b += rect_shape(next_id(), "outcard", emu(6.75), emu(2.75), emu(6.15), emu(4.3),
                   fill=C_CARD, line_color=C_ACCENT3, rounding=60000)
    sp = sp_pr(emu(6.9), emu(2.82), emu(5.85), emu(0.42), fill="none")
    tb = txBody(para(run("Output — 10 Known Attack Classes", sz=15, bold=True, color=C_ACCENT3), algn="c"), anchor="ctr")
    b += shape(sp, tb, next_id(), "outhdr")

    classes = ["Normal", "Backdoor", "DDoS_HTTP", "DDoS_ICMP", "DDoS_TCP",
               "DDoS_UDP", "Password", "Port_Scanning", "Ransomware", "SQL_injection"]
    colors = [C_ACCENT3, C_ACCENT4, C_ACCENT4, C_ACCENT4, C_ACCENT4,
              C_ACCENT4, C_ACCENT2, C_ACCENT2, C_ACCENT2, C_ACCENT2]
    for i, (cls, col) in enumerate(zip(classes, colors)):
        row, c = divmod(i, 2)
        cx2 = emu(6.9) + c * emu(3.0)
        cy = emu(3.35) + row * emu(0.56)
        b += rect_shape(next_id(), f"cls{i}", cx2, cy, emu(2.75), emu(0.48),
                       fill=C_BG_MID, line_color=col, rounding=30000)
        sp = sp_pr(cx2 + emu(0.1), cy, emu(2.55), emu(0.48), fill="none")
        tb = txBody(para(run(cls, sz=12, color=col), algn="c"), anchor="ctr")
        b += shape(sp, tb, next_id(), f"clst{i}")

    return b


def s13_lgbm_results():
    """Slide 13 — LightGBM Results"""
    b = bg() + gradient_header_bar() + footer_bar()
    b += slide_title("LightGBM Results")
    b += accent_line(emu(0.96))

    # Hero accuracy
    b += rect_shape(next_id(), "hero", emu(0.4), emu(1.15), emu(12.5), emu(1.1),
                   fill=C_CARD, line_color=C_ACCENT3, rounding=60000)
    sp = sp_pr(emu(0.6), emu(1.15), emu(12.1), emu(1.1), fill="none")
    tb = txBody(para(run("🏆  Overall Accuracy: ", sz=26, bold=True, color=C_WHITE) +
                     run("99.99%", sz=36, bold=True, color=C_ACCENT3), algn="c"), anchor="ctr")
    b += shape(sp, tb, next_id(), "heroacc")

    # Per-class metrics
    b += rect_shape(next_id(), "metcard", emu(0.4), emu(2.45), emu(8.1), emu(4.6),
                   fill=C_CARD, line_color=C_ACCENT5, rounding=60000)
    sp = sp_pr(emu(0.55), emu(2.52), emu(7.8), emu(0.42), fill="none")
    tb = txBody(para(run("Per-Class Performance Report", sz=15, bold=True, color=C_ACCENT5), algn="c"), anchor="ctr")
    b += shape(sp, tb, next_id(), "methdr")

    # Column headers
    headers = ["Class", "Precision", "Recall", "F1-Score", "Support"]
    col_widths = [emu(2.1), emu(1.3), emu(1.3), emu(1.3), emu(1.6)]
    col_x = [emu(0.55), emu(2.7), emu(4.05), emu(5.4), emu(6.75)]
    for j, (hdr, cx2) in enumerate(zip(headers, col_x)):
        sp = sp_pr(cx2, emu(3.0), col_widths[j], emu(0.35), fill="none")
        tb = txBody(para(run(hdr, sz=12, bold=True, color=C_ACCENT5), algn="c"), anchor="ctr")
        b += shape(sp, tb, next_id(), f"mh{j}")
    b += rect_shape(next_id(), "mhr", emu(0.55), emu(3.37), emu(7.8), emu(0.03), fill=C_ACCENT5)

    rows = [
        ("Backdoor",       "100.0%", "99.9%", "99.97%", "1,973"),
        ("DDoS_HTTP",      "100.0%", "100.0%","100.0%",  "2,112"),
        ("DDoS_ICMP",      "100.0%", "100.0%","100.0%",  "2,619"),
        ("DDoS_TCP",       "100.0%", "100.0%","100.0%",  "2,049"),
        ("DDoS_UDP",       "100.0%", "100.0%","100.0%",  "2,900"),
        ("Normal",         "100.0%", "100.0%","100.0%",  "4,831"),
        ("Password",       "99.9%",  "100.0%","99.97%",  "1,996"),
        ("Port_Scanning",  "99.9%",  "100.0%","99.97%",  "1,784"),
        ("Ransomware",     "99.9%",  "100.0%","99.97%",  "1,938"),
        ("SQL_injection",  "100.0%", "99.9%", "99.97%",  "2,057"),
    ]
    for i, row in enumerate(rows):
        iy = emu(3.45) + i * emu(0.38)
        bg_c = C_CARD2 if i % 2 == 0 else C_CARD
        b += rect_shape(next_id(), f"mr{i}", emu(0.55), iy, emu(7.8), emu(0.35),
                       fill=bg_c, rounding=15000)
        for j, (val, cx2) in enumerate(zip(row, col_x)):
            col = C_WHITE if j == 0 else (C_ACCENT3 if "100" in val else C_ACCENT5)
            sp = sp_pr(cx2, iy, col_widths[j], emu(0.35), fill="none")
            tb = txBody(para(run(val, sz=12, color=col, bold=(j==0)), algn="c"), anchor="ctr")
            b += shape(sp, tb, next_id(), f"mv{i}{j}")

    # Right side — confusion matrix heatmap simulation
    b += rect_shape(next_id(), "cmcard", emu(8.65), emu(2.45), emu(4.25), emu(4.6),
                   fill=C_CARD, line_color=C_ACCENT3, rounding=60000)
    sp = sp_pr(emu(8.8), emu(2.52), emu(3.9), emu(0.42), fill="none")
    tb = txBody(para(run("Confusion Matrix (Simulated)", sz=14, bold=True, color=C_ACCENT3), algn="c"), anchor="ctr")
    b += shape(sp, tb, next_id(), "cmhdr")

    classes_short = ["BD", "DH", "DI", "DT", "DU", "NR", "PW", "PS", "RW", "SQ"]
    n = 10
    cell_w = emu(0.35)
    cell_h = emu(0.33)
    cm_ox = emu(8.85)
    cm_oy = emu(3.05)
    for i in range(n):
        for j in range(n):
            cx3 = cm_ox + j * cell_w
            cy = cm_oy + i * cell_h
            if i == j:
                fill = C_ACCENT3
                txt_c = C_BG_DARK
                txt = "✓"
            else:
                fill = C_CARD2
                txt_c = C_LGRAY
                txt = "·"
            b += rect_shape(next_id(), f"cm{i}{j}", cx3, cy, cell_w - emu(0.02), cell_h - emu(0.02),
                           fill=fill, rounding=10000,
                           text_xml=para(run(txt, sz=10, color=txt_c, bold=(i==j)), algn="c"))
    # row labels
    for i, lbl in enumerate(classes_short):
        cy = cm_oy + i * cell_h
        sp = sp_pr(cm_ox - emu(0.6), cy, emu(0.55), cell_h, fill="none")
        tb = txBody(para(run(lbl, sz=10, color=C_LGRAY), algn="r"), anchor="ctr")
        b += shape(sp, tb, next_id(), f"cml{i}")

    # Key stats
    kstats = [
        ("Macro Avg F1", "99.99%", C_ACCENT3),
        ("Test Samples", "24,259", C_ACCENT1),
        ("Misclassified", "3 samples", C_ACCENT5),
    ]
    for i, (k, v, c) in enumerate(kstats):
        sy = emu(6.5) + i * emu(0.0) - i * emu(0.0)
        iy = emu(6.5)
        sx2 = emu(8.65) + i * emu(1.4)
        b += rect_shape(next_id(), f"ks{i}", sx2, iy, emu(1.35), emu(0.55),
                       fill=C_BG_MID, line_color=c, rounding=30000)
        sp = sp_pr(sx2, iy, emu(1.35), emu(0.28), fill="none")
        tb = txBody(para(run(v, sz=14, bold=True, color=c), algn="c"), anchor="ctr")
        b += shape(sp, tb, next_id(), f"kst{i}")
        sp = sp_pr(sx2, iy + emu(0.27), emu(1.35), emu(0.25), fill="none")
        tb = txBody(para(run(k, sz=10, color=C_LGRAY), algn="c"), anchor="ctr")
        b += shape(sp, tb, next_id(), f"ksl{i}")

    return b


def s14_autoencoder():
    """Slide 14 — Autoencoder Model"""
    b = bg() + gradient_header_bar() + footer_bar()
    b += slide_title("Autoencoder — Anomaly Detection")
    b += accent_line(emu(0.96))

    # Left explanation
    b += rect_shape(next_id(), "aecard", emu(0.4), emu(1.15), emu(6.5), emu(5.9),
                   fill=C_CARD, line_color=C_ACCENT3, rounding=60000)
    sp = sp_pr(emu(0.55), emu(1.2), emu(6.2), emu(0.48), fill="none")
    tb = txBody(para(run("🧠  How the Autoencoder Works", sz=17, bold=True, color=C_ACCENT3), algn="c"), anchor="ctr")
    b += shape(sp, tb, next_id(), "aehdr")

    steps_ae = [
        (C_ACCENT1, "1. Train on Normal Only",
         "Feed ONLY normal traffic (24,152 rows) into the Autoencoder during training"),
        (C_ACCENT2, "2. Learn Normal Behaviour",
         "The network compresses then reconstructs the input — it masters 'what normal looks like'"),
        (C_ACCENT3, "3. Reconstruction Error",
         "For each input, compute MSE between input and reconstruction output"),
        (C_ACCENT5, "4. Threshold Detection",
         "If MSE > 0.0122 (threshold) → ANOMALY detected (zero-day attack)"),
        (C_ACCENT4, "5. Zero-Day Alert",
         "The AE never saw these attack patterns — they cause high reconstruction error"),
    ]
    for i, (col, title, desc) in enumerate(steps_ae):
        iy = emu(1.88) + i * emu(0.98)
        b += rect_shape(next_id(), f"ae{i}", emu(0.55), iy, emu(6.2), emu(0.85),
                       fill=C_BG_MID, line_color=col, rounding=40000)
        b += rect_shape(next_id(), f"aen{i}", emu(0.58), iy + emu(0.2), emu(0.35), emu(0.35),
                       fill=col, rounding=166666,
                       text_xml=para(run(str(i+1), sz=12, bold=True, color=C_BG_DARK), algn="c"))
        sp = sp_pr(emu(1.02), iy + emu(0.05), emu(5.65), emu(0.35), fill="none")
        tb = txBody(para(run(title, sz=14, bold=True, color=col), algn="l"), anchor="ctr")
        b += shape(sp, tb, next_id(), f"aett{i}")
        sp = sp_pr(emu(1.02), iy + emu(0.43), emu(5.65), emu(0.38), fill="none")
        tb = txBody(para(run(desc, sz=12, color=C_LGRAY), algn="l"), anchor="t")
        b += shape(sp, tb, next_id(), f"aetd{i}")

    # Right — reconstruction error concept
    b += rect_shape(next_id(), "recard", emu(7.05), emu(1.15), emu(5.85), emu(5.9),
                   fill=C_CARD, line_color=C_ACCENT2, rounding=60000)
    sp = sp_pr(emu(7.2), emu(1.2), emu(5.55), emu(0.48), fill="none")
    tb = txBody(para(run("Reconstruction Error Concept", sz=16, bold=True, color=C_ACCENT2), algn="c"), anchor="ctr")
    b += shape(sp, tb, next_id(), "rehdr")

    # Simulate a threshold chart using bars
    error_data = [
        ("Normal 1", 0.003, C_ACCENT3, "Normal"),
        ("Normal 2", 0.005, C_ACCENT3, "Normal"),
        ("Normal 3", 0.008, C_ACCENT3, "Normal"),
        ("Normal 4", 0.009, C_ACCENT3, "Normal"),
        ("Zero-Day 1", 0.045, C_ACCENT4, "ANOMALY"),
        ("Zero-Day 2", 0.082, C_ACCENT4, "ANOMALY"),
        ("Zero-Day 3", 0.034, C_ACCENT4, "ANOMALY"),
        ("Zero-Day 4", 0.119, C_ACCENT4, "ANOMALY"),
    ]
    max_err = 0.13
    chart_x = emu(7.2)
    chart_y = emu(1.85)
    bar_h2 = emu(0.42)
    bar_max_w2 = emu(3.5)
    for i, (name, err, col, lbl) in enumerate(error_data):
        iy = chart_y + i * (bar_h2 + emu(0.06))
        bw = int(bar_max_w2 * err / max_err)
        sp = sp_pr(chart_x, iy, emu(1.45), bar_h2, fill="none")
        tb = txBody(para(run(name, sz=11, color=C_LGRAY), algn="r"), anchor="ctr")
        b += shape(sp, tb, next_id(), f"ren{i}")
        b += rect_shape(next_id(), f"retrack{i}", chart_x + emu(1.5), iy + bar_h2//4,
                       bar_max_w2, bar_h2//2, fill=C_DGRAY, rounding=15000)
        if bw > 0:
            b += rect_shape(next_id(), f"rebar{i}", chart_x + emu(1.5), iy + bar_h2//4,
                           bw, bar_h2//2, fill=col, rounding=15000)
        sp = sp_pr(chart_x + emu(5.1), iy, emu(0.65), bar_h2, fill="none")
        tb = txBody(para(run(lbl, sz=10, bold=True, color=col), algn="l"), anchor="ctr")
        b += shape(sp, tb, next_id(), f"relbl{i}")

    # Threshold line
    thresh_x = chart_x + emu(1.5) + int(bar_max_w2 * 0.0122 / max_err)
    thresh_h = len(error_data) * (bar_h2 + emu(0.06))
    b += rect_shape(next_id(), "thrline", thresh_x, chart_y - emu(0.15),
                   emu(0.03), thresh_h + emu(0.2), fill=C_ACCENT1)
    sp = sp_pr(thresh_x - emu(0.2), chart_y - emu(0.45), emu(1.4), emu(0.28), fill="none")
    tb = txBody(para(run("Threshold=0.0122", sz=10, bold=True, color=C_ACCENT1), algn="c"), anchor="ctr")
    b += shape(sp, tb, next_id(), "thrlbl")

    # Key insight
    b += rect_shape(next_id(), "insight", emu(7.2), emu(6.2), emu(5.55), emu(0.65),
                   fill=C_BG_MID, line_color=C_ACCENT3, rounding=40000)
    sp = sp_pr(emu(7.3), emu(6.2), emu(5.35), emu(0.65), fill="none")
    tb = txBody(para(run("💡  Low error → Normal  |  High error → Zero-Day Attack",
                         sz=14, bold=True, color=C_ACCENT3), algn="c"), anchor="ctr")
    b += shape(sp, tb, next_id(), "insighttxt")

    return b


def s15_ae_architecture():
    """Slide 15 — Autoencoder Architecture"""
    b = bg() + gradient_header_bar() + footer_bar()
    b += slide_title("Autoencoder Neural Network Architecture")
    b += accent_line(emu(0.96))

    # Architecture diagram — symmetric layers
    layers = [
        ("Input\n51", 51, C_ACCENT1, "Input Layer"),
        ("Encoder\n64", 64, C_ACCENT2, "Encoder"),
        ("Encoder\n32", 32, C_ACCENT2, "Encoder"),
        ("Bottleneck\n16", 16, C_ACCENT4, "Bottleneck"),
        ("Decoder\n32", 32, C_ACCENT3, "Decoder"),
        ("Decoder\n64", 64, C_ACCENT3, "Decoder"),
        ("Output\n51", 51, C_ACCENT1, "Reconstruction"),
    ]

    n = len(layers)
    lw = emu(1.55)
    spacing = SW / (n + 1)
    ly = emu(2.3)

    for i, (lbl, units, col, section) in enumerate(layers):
        lx = int(spacing * (i + 1)) - lw // 2
        # Section label above
        sp = sp_pr(lx, emu(1.1), lw, emu(0.38), fill="none")
        tb = txBody(para(run(section, sz=11, color=col, italic=True), algn="c"), anchor="ctr")
        b += shape(sp, tb, next_id(), f"sec{i}")

        # Node height proportional to units
        node_h = int(emu(0.25) + emu(2.8) * units / 70)
        node_y = ly + (emu(2.8) - node_h) // 2
        b += rect_shape(next_id(), f"layer{i}", lx, node_y, lw, node_h,
                       fill=col, line_color=C_WHITE, rounding=30000)
        # Label inside
        sp = sp_pr(lx, node_y, lw, node_h, fill="none")
        tb = txBody(para(run(lbl, sz=13, bold=True, color=C_BG_DARK), algn="c"), anchor="ctr")
        b += shape(sp, tb, next_id(), f"layerlbl{i}")

        # Units count below
        sp = sp_pr(lx, node_y + node_h + emu(0.1), lw, emu(0.3), fill="none")
        tb = txBody(para(run(f"{units} neurons", sz=11, color=col), algn="c"), anchor="ctr")
        b += shape(sp, tb, next_id(), f"layerunit{i}")

        # Connection arrow to next
        if i < n - 1:
            b += arrow_right(lx + lw + emu(0.02), ly + emu(1.4))

    # Bottleneck annotation
    bn_lx = int(spacing * 4) - lw // 2
    b += rect_shape(next_id(), "bnanno", bn_lx - emu(0.5), emu(5.35), lw + emu(1.0), emu(0.55),
                   fill="none", line_color=C_ACCENT4, rounding=30000)
    sp = sp_pr(bn_lx - emu(0.45), emu(5.35), lw + emu(0.9), emu(0.55), fill="none")
    tb = txBody(para(run("← Maximum Compression →\nLatent Space Representation", sz=11,
                         color=C_ACCENT4, italic=True), algn="c"), anchor="ctr")
    b += shape(sp, tb, next_id(), "bnannotxt")

    # Info cards row
    info_cards = [
        ("Total Parameters", "11,907", C_ACCENT3,
         "Ultra-lightweight — deployable on edge IoT gateways"),
        ("Architecture Type", "Symmetric\nAutoencoder", C_ACCENT1,
         "Encoder mirrors Decoder around 16-dim bottleneck"),
        ("Activation", "ReLU (hidden)\nSigmoid (output)", C_ACCENT2,
         "ReLU avoids vanishing gradient in deep encoder layers"),
        ("Training", "Normal Traffic Only\n24,152 rows", C_ACCENT5,
         "Learns clean traffic distribution; anomalies diverge"),
    ]
    iw = emu(3.0)
    for i, (label, val, col, desc) in enumerate(info_cards):
        ix = emu(0.4) + i * emu(3.22)
        b += rect_shape(next_id(), f"ic{i}", ix, emu(5.95), iw, emu(1.3),
                       fill=C_CARD, line_color=col, rounding=50000)
        sp = sp_pr(ix + emu(0.1), emu(6.0), iw - emu(0.2), emu(0.45), fill="none")
        tb = txBody(para(run(val, sz=14, bold=True, color=col), algn="c"), anchor="ctr")
        b += shape(sp, tb, next_id(), f"icv{i}")
        sp = sp_pr(ix + emu(0.1), emu(6.45), iw - emu(0.2), emu(0.28), fill="none")
        tb = txBody(para(run(label, sz=11, bold=True, color=C_WHITE), algn="c"), anchor="ctr")
        b += shape(sp, tb, next_id(), f"icl{i}")
        sp = sp_pr(ix + emu(0.1), emu(6.75), iw - emu(0.2), emu(0.45), fill="none")
        tb = txBody(para(run(desc, sz=10, color=C_LGRAY), algn="c"), anchor="t")
        b += shape(sp, tb, next_id(), f"icd{i}")

    return b


def s16_ae_results():
    """Slide 16 — Autoencoder Results"""
    b = bg() + gradient_header_bar() + footer_bar()
    b += slide_title("Autoencoder Results — Anomaly Detection")
    b += accent_line(emu(0.96))

    # Hero accuracy
    b += rect_shape(next_id(), "aehero", emu(0.4), emu(1.15), emu(12.5), emu(1.0),
                   fill=C_CARD, line_color=C_ACCENT3, rounding=60000)
    sp = sp_pr(emu(0.6), emu(1.15), emu(12.1), emu(1.0), fill="none")
    tb = txBody(para(run("Overall Accuracy: ", sz=24, bold=True, color=C_WHITE) +
                     run("99.19%", sz=34, bold=True, color=C_ACCENT3) +
                     run("   |   Tested on: ", sz=18, color=C_LGRAY) +
                     run("152,389", sz=22, bold=True, color=C_ACCENT1) +
                     run("  samples", sz=18, color=C_LGRAY), algn="c"), anchor="ctr")
    b += shape(sp, tb, next_id(), "aeherotext")

    # Metrics cards
    metrics = [
        ("Normal Precision", "100.0%", C_ACCENT3),
        ("Normal Recall", "94.87%", C_ACCENT5),
        ("Attack Precision", "99.04%", C_ACCENT3),
        ("Attack Recall", "100.0%", C_ACCENT1),
        ("Macro F1", "98.44%", C_ACCENT2),
        ("Threshold", "0.0122", C_ACCENT4),
    ]
    mw = emu(2.0)
    for i, (lbl, val, col) in enumerate(metrics):
        mx = emu(0.4) + i * emu(2.13)
        b += stat_card(mx, emu(2.35), mw, emu(1.2), val, lbl, val_color=col)

    # Classification table
    b += rect_shape(next_id(), "aemetcard", emu(0.4), emu(3.75), emu(5.8), emu(3.3),
                   fill=C_CARD, line_color=C_ACCENT2, rounding=60000)
    sp = sp_pr(emu(0.55), emu(3.82), emu(5.5), emu(0.4), fill="none")
    tb = txBody(para(run("Classification Report", sz=15, bold=True, color=C_ACCENT2), algn="c"), anchor="ctr")
    b += shape(sp, tb, next_id(), "aerephdr")

    headers = ["Class", "Precision", "Recall", "F1", "Support"]
    hx = [emu(0.55), emu(1.9), emu(2.9), emu(3.85), emu(4.8)]
    hw = [emu(1.3), emu(1.0), emu(1.0), emu(1.0), emu(1.1)]
    for j, (hdr, cx2) in enumerate(zip(headers, hx)):
        sp = sp_pr(cx2, emu(4.28), hw[j], emu(0.33), fill="none")
        tb = txBody(para(run(hdr, sz=12, bold=True, color=C_ACCENT2), algn="c"), anchor="ctr")
        b += shape(sp, tb, next_id(), f"aeh{j}")
    b += rect_shape(next_id(), "aehr2", emu(0.55), emu(4.62), emu(5.5), emu(0.03), fill=C_ACCENT2)

    ae_rows = [
        ("Normal (0)", "100.0%", "94.87%", "97.37%", "24,152"),
        ("Attack (1)", "99.04%", "100.0%", "99.52%", "128,237"),
        ("Accuracy", "–", "–", "99.19%", "152,389"),
        ("Macro Avg", "99.52%", "97.43%", "98.44%", "152,389"),
    ]
    for i, row in enumerate(ae_rows):
        iy = emu(4.7) + i * emu(0.55)
        bg_c = C_CARD2 if i % 2 == 0 else C_CARD
        b += rect_shape(next_id(), f"aerow{i}", emu(0.55), iy, emu(5.5), emu(0.5),
                       fill=bg_c, rounding=15000)
        for j, (val, cx2) in enumerate(zip(row, hx)):
            col = C_WHITE if j == 0 else (C_ACCENT3 if "100" in val or "99" in val else C_LGRAY)
            sp = sp_pr(cx2, iy, hw[j], emu(0.5), fill="none")
            tb = txBody(para(run(val, sz=12, color=col, bold=(j==0)), algn="c"), anchor="ctr")
            b += shape(sp, tb, next_id(), f"aecell{i}{j}")

    # Reconstruction error histogram simulation
    b += rect_shape(next_id(), "reshist", emu(6.4), emu(3.75), emu(6.5), emu(3.3),
                   fill=C_CARD, line_color=C_ACCENT4, rounding=60000)
    sp = sp_pr(emu(6.55), emu(3.82), emu(6.2), emu(0.4), fill="none")
    tb = txBody(para(run("Reconstruction Error Distribution", sz=14, bold=True, color=C_ACCENT4), algn="c"), anchor="ctr")
    b += shape(sp, tb, next_id(), "reshisthdr")

    # Normal distribution bars (low error)
    normal_bars = [0.02, 0.08, 0.22, 0.55, 0.85, 1.0, 0.7, 0.38, 0.12, 0.04]
    attack_bars = [0.0, 0.0, 0.01, 0.03, 0.08, 0.14, 0.25, 0.45, 0.72, 0.95]
    bar_w3 = emu(0.38)
    bar_base_y = emu(6.7)
    max_bar_h = emu(2.1)
    chart_ox = emu(6.6)

    for i, (nb, ab) in enumerate(zip(normal_bars, attack_bars)):
        bx = chart_ox + i * emu(0.55)
        # Normal bar
        nh = int(max_bar_h * nb)
        if nh > 0:
            b += rect_shape(next_id(), f"nhb{i}", bx, bar_base_y - nh, bar_w3, nh,
                           fill=C_ACCENT3, rounding=10000)
        # Attack bar (slightly offset)
        ah = int(max_bar_h * ab)
        if ah > 0:
            b += rect_shape(next_id(), f"ahb{i}", bx + emu(0.2), bar_base_y - ah,
                           bar_w3, ah, fill=C_ACCENT4, rounding=10000)

    # Threshold vertical line
    thresh_bx = chart_ox + int(10 * emu(0.55) * 0.0122 / 0.15)
    b += rect_shape(next_id(), "resthresh", chart_ox + emu(2.2), emu(4.3),
                   emu(0.04), emu(2.45), fill=C_ACCENT1)
    sp = sp_pr(chart_ox + emu(1.6), emu(4.1), emu(1.5), emu(0.28), fill="none")
    tb = txBody(para(run("Threshold", sz=11, bold=True, color=C_ACCENT1), algn="c"), anchor="ctr")
    b += shape(sp, tb, next_id(), "restlbl")

    # X-axis labels
    sp = sp_pr(chart_ox, emu(6.75), emu(2.0), emu(0.25), fill="none")
    tb = txBody(para(run("Low Error →", sz=10, color=C_ACCENT3), algn="l"), anchor="ctr")
    b += shape(sp, tb, next_id(), "lowlbl")
    sp = sp_pr(chart_ox + emu(3.5), emu(6.75), emu(2.5), emu(0.25), fill="none")
    tb = txBody(para(run("← High Error", sz=10, color=C_ACCENT4), algn="r"), anchor="ctr")
    b += shape(sp, tb, next_id(), "highlbl")

    # Legend
    b += rect_shape(next_id(), "leg1", emu(6.6), emu(6.45), emu(0.25), emu(0.2), fill=C_ACCENT3, rounding=10000)
    sp = sp_pr(emu(6.9), emu(6.42), emu(1.5), emu(0.25), fill="none")
    tb = txBody(para(run("Normal Traffic", sz=11, color=C_ACCENT3), algn="l"), anchor="ctr")
    b += shape(sp, tb, next_id(), "leg1t")
    b += rect_shape(next_id(), "leg2", emu(8.6), emu(6.45), emu(0.25), emu(0.2), fill=C_ACCENT4, rounding=10000)
    sp = sp_pr(emu(8.9), emu(6.42), emu(1.5), emu(0.25), fill="none")
    tb = txBody(para(run("Attack Traffic", sz=11, color=C_ACCENT4), algn="l"), anchor="ctr")
    b += shape(sp, tb, next_id(), "leg2t")

    return b


def s17_why_fusion():
    """Slide 17 — Why Fusion Model?"""
    b = bg() + gradient_header_bar() + footer_bar()
    b += slide_title("Why a Fusion Model?")
    b += accent_line(emu(0.96))

    # Header description
    sp = sp_pr(emu(0.5), emu(1.05), emu(12.3), emu(0.5), fill="none")
    tb = txBody(para(run(
        "Neither LightGBM nor Autoencoder alone achieves complete intrusion detection. "
        "Their complementary strengths make Fusion the optimal solution.",
        sz=16, color=C_LGRAY), algn="c"), anchor="ctr")
    b += shape(sp, tb, next_id(), "fusionintro")

    # Three cards
    # LightGBM strengths/weaknesses
    b += rect_shape(next_id(), "lgbfw", emu(0.4), emu(1.75), emu(3.95), emu(5.3),
                   fill=C_CARD, line_color=C_ACCENT5, rounding=60000)
    sp = sp_pr(emu(0.55), emu(1.82), emu(3.65), emu(0.48), fill="none")
    tb = txBody(para(run("🌿  LightGBM", sz=17, bold=True, color=C_ACCENT5), algn="c"), anchor="ctr")
    b += shape(sp, tb, next_id(), "lgbfwhdr")

    b += rect_shape(next_id(), "lgbstr", emu(0.55), emu(2.4), emu(3.65), emu(0.3), fill="none",
                   text_xml=para(run("✅  Strengths", sz=13, bold=True, color=C_ACCENT3), algn="l"))
    lgb_str = ["99.99% on known attacks", "Names the specific attack type", "Fast, lightweight inference"]
    lgb_wk = ["Cannot generalise to unseen attacks", "Predicts wrong class for zero-days", "Blind to novel threat patterns"]
    for i, pt in enumerate(lgb_str):
        iy = emu(2.78) + i * emu(0.42)
        sp = sp_pr(emu(0.6), iy, emu(3.6), emu(0.38), fill="none")
        tb = txBody(para(run("  ✓  " + pt, sz=13, color=C_ACCENT3), algn="l"), anchor="ctr")
        b += shape(sp, tb, next_id(), f"lstr{i}")
    b += rect_shape(next_id(), "lgbwkhdr", emu(0.55), emu(4.15), emu(3.65), emu(0.3), fill="none",
                   text_xml=para(run("❌  Weakness", sz=13, bold=True, color=C_ACCENT4), algn="l"))
    for i, pt in enumerate(lgb_wk):
        iy = emu(4.53) + i * emu(0.42)
        sp = sp_pr(emu(0.6), iy, emu(3.6), emu(0.38), fill="none")
        tb = txBody(para(run("  ✗  " + pt, sz=13, color=C_ACCENT4), algn="l"), anchor="ctr")
        b += shape(sp, tb, next_id(), f"lwk{i}")

    # Autoencoder strengths/weaknesses
    b += rect_shape(next_id(), "aefw", emu(4.6), emu(1.75), emu(3.95), emu(5.3),
                   fill=C_CARD, line_color=C_ACCENT3, rounding=60000)
    sp = sp_pr(emu(4.75), emu(1.82), emu(3.65), emu(0.48), fill="none")
    tb = txBody(para(run("🧠  Autoencoder", sz=17, bold=True, color=C_ACCENT3), algn="c"), anchor="ctr")
    b += shape(sp, tb, next_id(), "aefwhdr")
    b += rect_shape(next_id(), "aestr", emu(4.75), emu(2.4), emu(3.65), emu(0.3), fill="none",
                   text_xml=para(run("✅  Strengths", sz=13, bold=True, color=C_ACCENT3), algn="l"))
    ae_str = ["Detects zero-day / unseen attacks", "No labelled attack data needed", "Generalises beyond training data"]
    ae_wk = ["Cannot name specific attack types", "Higher false positive rate", "Threshold sensitivity issue"]
    for i, pt in enumerate(ae_str):
        iy = emu(2.78) + i * emu(0.42)
        sp = sp_pr(emu(4.8), iy, emu(3.6), emu(0.38), fill="none")
        tb = txBody(para(run("  ✓  " + pt, sz=13, color=C_ACCENT3), algn="l"), anchor="ctr")
        b += shape(sp, tb, next_id(), f"aestr{i}")
    b += rect_shape(next_id(), "aewkhdr", emu(4.75), emu(4.15), emu(3.65), emu(0.3), fill="none",
                   text_xml=para(run("❌  Weakness", sz=13, bold=True, color=C_ACCENT4), algn="l"))
    for i, pt in enumerate(ae_wk):
        iy = emu(4.53) + i * emu(0.42)
        sp = sp_pr(emu(4.8), iy, emu(3.6), emu(0.38), fill="none")
        tb = txBody(para(run("  ✗  " + pt, sz=13, color=C_ACCENT4), algn="l"), anchor="ctr")
        b += shape(sp, tb, next_id(), f"aewk{i}")

    # Fusion solution card
    b += rect_shape(next_id(), "fuscard", emu(8.8), emu(1.75), emu(4.1), emu(5.3),
                   fill=C_CARD, line_color=C_ACCENT1, rounding=60000)
    sp = sp_pr(emu(8.95), emu(1.82), emu(3.8), emu(0.48), fill="none")
    tb = txBody(para(run("🔀  Fusion Model", sz=17, bold=True, color=C_ACCENT1), algn="c"), anchor="ctr")
    b += shape(sp, tb, next_id(), "fusfwhdr")
    b += rect_shape(next_id(), "fusstr", emu(8.95), emu(2.4), emu(3.8), emu(0.3), fill="none",
                   text_xml=para(run("🏆  Combined Strengths", sz=13, bold=True, color=C_ACCENT1), algn="l"))
    fusion_pts = [
        "Routes known attacks through LightGBM",
        "Routes suspicious traffic through AE",
        "97% zero-day detection accuracy",
        "Reduced false positive rate",
        "Best of both supervised + unsupervised",
        "Single end-to-end IDS pipeline",
    ]
    for i, pt in enumerate(fusion_pts):
        iy = emu(2.78) + i * emu(0.5)
        col = C_ACCENT1 if i < 2 else (C_ACCENT3 if i == 2 else C_LGRAY)
        sp = sp_pr(emu(9.0), iy, emu(3.75), emu(0.42), fill="none")
        tb = txBody(para(run("  ★  " + pt, sz=13, color=col, bold=(i==2)), algn="l"), anchor="ctr")
        b += shape(sp, tb, next_id(), f"fpt{i}")

    return b


def s18_fusion_workflow():
    """Slide 18 — Fusion Model Workflow"""
    b = bg() + gradient_header_bar() + footer_bar()
    b += slide_title("Fusion Model Decision Workflow")
    b += accent_line(emu(0.96))

    # Subtitle
    sp = sp_pr(emu(0.5), emu(1.05), emu(12.3), emu(0.45), fill="none")
    tb = txBody(para(run(
        "Evaluated on: 24,152 Normal + 31,096 Zero-Day = 55,248 unseen test samples",
        sz=15, color=C_ACCENT1, italic=True), algn="c"), anchor="ctr")
    b += shape(sp, tb, next_id(), "fusionsub")

    # Flowchart
    box_w = emu(3.2)
    box_h = emu(0.85)
    # Step 1: Input
    b += flow_box(SW//2 - box_w//2, emu(1.65), box_w, box_h,
                  "🌐  IoT Traffic Input", fill=C_BG_MID, lc=C_ACCENT1, sz=16,
                  sub_text="55,248 test samples (Normal + Zero-Day)")
    b += arrow_down(SW//2, emu(1.65) + box_h)

    # Step 2: LightGBM prediction
    b += flow_box(SW//2 - box_w//2, emu(2.72), box_w, box_h,
                  "🌿  LightGBM Prediction", fill=C_CARD, lc=C_ACCENT5, sz=16,
                  sub_text="Predict class + confidence score")
    b += arrow_down(SW//2, emu(2.72) + box_h)

    # Decision diamond
    dia_w = emu(4.2)
    dia_h = emu(1.0)
    dia_x = SW//2 - dia_w//2
    dia_y = emu(3.79)
    b += rect_shape(next_id(), "diamond", dia_x, dia_y, dia_w, dia_h,
                   fill=C_ACCENT5, line_color=C_WHITE, rounding=166666,
                   text_xml=para(run("LightGBM says 'Normal'\n& Confidence ≥ 90%?",
                                     sz=15, bold=True, color=C_BG_DARK), algn="c"))

    # YES branch — right
    b += arrow_right(dia_x + dia_w, dia_y + dia_h//2, w=emu(0.7))
    b += flow_box(dia_x + dia_w + emu(0.7), dia_y - emu(0.1), emu(3.2), emu(1.2),
                  "✅  Accept as NORMAL", fill=C_CARD, lc=C_ACCENT3, sz=15,
                  sub_text="High-confidence Normal verdict\nfrom LightGBM is trusted")
    sp = sp_pr(dia_x + dia_w + emu(0.3), dia_y - emu(0.4), emu(0.8), emu(0.35), fill="none")
    tb = txBody(para(run("YES", sz=14, bold=True, color=C_ACCENT3), algn="c"), anchor="ctr")
    b += shape(sp, tb, next_id(), "yesl")

    # NO branch — down
    b += arrow_down(SW//2, dia_y + dia_h)
    sp = sp_pr(SW//2 + emu(0.15), dia_y + dia_h + emu(0.02), emu(0.6), emu(0.28), fill="none")
    tb = txBody(para(run("NO", sz=14, bold=True, color=C_ACCENT4), algn="l"), anchor="ctr")
    b += shape(sp, tb, next_id(), "nol")

    # Step: Use Autoencoder
    b += flow_box(SW//2 - box_w//2, dia_y + dia_h + emu(0.38), box_w, box_h,
                  "🧠  Autoencoder Evaluation", fill=C_CARD, lc=C_ACCENT3, sz=16,
                  sub_text="Compute reconstruction error (MSE)")
    b += arrow_down(SW//2, dia_y + dia_h + emu(0.38) + box_h)

    # AE Decision
    ae_dia_y = dia_y + dia_h + emu(0.38) + box_h + emu(0.35)
    b += rect_shape(next_id(), "aedia", dia_x, ae_dia_y, dia_w, dia_h,
                   fill=C_ACCENT3, line_color=C_WHITE, rounding=166666,
                   text_xml=para(run("MSE > Threshold\n(0.0122)?", sz=15, bold=True, color=C_BG_DARK), algn="c"))

    # AE YES
    b += arrow_right(dia_x + dia_w, ae_dia_y + dia_h//2, w=emu(0.7))
    b += flow_box(dia_x + dia_w + emu(0.7), ae_dia_y - emu(0.05), emu(3.0), emu(1.1),
                  "🚨  ZERO-DAY ANOMALY", fill=C_CARD, lc=C_ACCENT4, sz=14,
                  sub_text="Unknown attack detected!\nReconstruction error too high")
    sp2 = sp_pr(dia_x + dia_w + emu(0.3), ae_dia_y - emu(0.38), emu(0.8), emu(0.3), fill="none")
    tb2 = txBody(para(run("YES", sz=13, bold=True, color=C_ACCENT4), algn="c"), anchor="ctr")
    b += shape(sp2, tb2, next_id(), "aeyesl")

    # AE NO — left
    sp3 = sp_pr(dia_x - emu(1.2), ae_dia_y + dia_h//2 - emu(0.15), emu(1.15), emu(0.3), fill="none")
    tb3 = txBody(para(run("NO", sz=13, bold=True, color=C_ACCENT3), algn="c"), anchor="ctr")
    b += shape(sp3, tb3, next_id(), "aenol")
    b += rect_shape(next_id(), "aenoa", dia_x - emu(0.02), ae_dia_y + dia_h//2 - emu(0.02),
                   emu(0.04), emu(0.04), fill="none")
    b += flow_box(dia_x - emu(3.6), ae_dia_y - emu(0.05), emu(3.0), emu(1.1),
                  "✅  Accept as NORMAL", fill=C_CARD, lc=C_ACCENT3, sz=14,
                  sub_text="Low reconstruction error —\nconfirmed normal traffic")
    return b


def s19_fusion_results():
    """Slide 19 — Fusion Model Results"""
    b = bg() + gradient_header_bar() + footer_bar()
    b += slide_title("Fusion Model Results — Zero-Day Scenario")
    b += accent_line(emu(0.96))

    # Hero
    b += rect_shape(next_id(), "fushero", emu(0.4), emu(1.15), emu(12.5), emu(1.0),
                   fill=C_CARD, line_color=C_ACCENT1, rounding=60000)
    sp = sp_pr(emu(0.6), emu(1.15), emu(12.1), emu(1.0), fill="none")
    tb = txBody(para(run("Zero-Day Detection Accuracy: ", sz=22, bold=True, color=C_WHITE) +
                     run("96.82%", sz=34, bold=True, color=C_ACCENT3) +
                     run("  on 55,248 Unseen Samples", sz=17, color=C_LGRAY), algn="c"), anchor="ctr")
    b += shape(sp, tb, next_id(), "fusheroftxt")

    # Metric cards
    fus_metrics = [
        ("Normal Precision", "97.78%", C_ACCENT3),
        ("Normal Recall", "94.87%", C_ACCENT5),
        ("ZeroDay Precision", "96.11%", C_ACCENT2),
        ("ZeroDay Recall", "98.33%", C_ACCENT1),
        ("Macro Avg F1", "96.75%", C_ACCENT3),
        ("Test Samples", "55,248", C_ACCENT5),
    ]
    mw = emu(2.0)
    for i, (lbl, val, col) in enumerate(fus_metrics):
        mx = emu(0.4) + i * emu(2.13)
        b += stat_card(mx, emu(2.35), mw, emu(1.15), val, lbl, val_color=col)

    # Classification report table
    b += rect_shape(next_id(), "fusrepcard", emu(0.4), emu(3.7), emu(6.0), emu(3.4),
                   fill=C_CARD, line_color=C_ACCENT2, rounding=60000)
    sp = sp_pr(emu(0.55), emu(3.77), emu(5.7), emu(0.4), fill="none")
    tb = txBody(para(run("Classification Report", sz=15, bold=True, color=C_ACCENT2), algn="c"), anchor="ctr")
    b += shape(sp, tb, next_id(), "fusrephdr")

    headers = ["Class", "Precision", "Recall", "F1", "Support"]
    hx2 = [emu(0.55), emu(1.95), emu(2.95), emu(3.9), emu(4.85)]
    hw2 = [emu(1.35), emu(1.0), emu(1.0), emu(1.0), emu(1.1)]
    for j, (hdr, cx) in enumerate(zip(headers, hx2)):
        sp = sp_pr(cx, emu(4.23), hw2[j], emu(0.33), fill="none")
        tb = txBody(para(run(hdr, sz=12, bold=True, color=C_ACCENT2), algn="c"), anchor="ctr")
        b += shape(sp, tb, next_id(), f"frh{j}")
    b += rect_shape(next_id(), "frhr2", emu(0.55), emu(4.57), emu(5.7), emu(0.03), fill=C_ACCENT2)

    fus_rows = [
        ("Normal (0)",   "97.78%", "94.87%", "96.30%", "24,152"),
        ("Zero-Day (1)", "96.11%", "98.33%", "97.20%", "31,096"),
        ("Accuracy",     "–",      "–",       "96.82%", "55,248"),
        ("Macro Avg",    "96.94%", "96.60%",  "96.75%", "55,248"),
    ]
    for i, row in enumerate(fus_rows):
        iy = emu(4.65) + i * emu(0.6)
        bg_c = C_CARD2 if i % 2 == 0 else C_CARD
        b += rect_shape(next_id(), f"frr{i}", emu(0.55), iy, emu(5.7), emu(0.55),
                       fill=bg_c, rounding=15000)
        for j, (val, cx) in enumerate(zip(row, hx2)):
            col = C_WHITE if j == 0 else (C_ACCENT3 if "9" in val and "–" not in val else C_LGRAY)
            sp = sp_pr(cx, iy, hw2[j], emu(0.55), fill="none")
            tb = txBody(para(run(val, sz=12, color=col, bold=(j==0)), algn="c"), anchor="ctr")
            b += shape(sp, tb, next_id(), f"frc{i}{j}")

    # Right — confusion matrix simulation
    b += rect_shape(next_id(), "fuscmcard", emu(6.6), emu(3.7), emu(6.3), emu(3.4),
                   fill=C_CARD, line_color=C_ACCENT3, rounding=60000)
    sp = sp_pr(emu(6.75), emu(3.77), emu(5.95), emu(0.4), fill="none")
    pass

    # Build confusion matrix manually
    sp = sp_pr(emu(6.75), emu(3.77), emu(5.95), emu(0.4), fill="none")
    tb = txBody(para(run("Fusion Confusion Matrix (2×2)", sz=14, bold=True, color=C_ACCENT3), algn="c"), anchor="ctr")
    b += shape(sp, tb, next_id(), "fuscmhdr")

    cm_data = [
        [("22,902", C_ACCENT3, "True Normal"), ("1,250", C_ACCENT4, "False Alarm")],
        [("524",  C_ACCENT5, "Missed ZeroDay"), ("30,572", C_ACCENT3, "True ZeroDay")],
    ]
    labels_row = ["Pred: Normal", "Pred: ZeroDay"]
    labels_col = ["Act: Normal", "Act: ZeroDay"]
    cell_w2 = emu(2.3)
    cell_h2 = emu(1.1)
    cm_ox2 = emu(7.15)
    cm_oy2 = emu(4.35)
    for i, row in enumerate(cm_data):
        for j, (val, col, tip) in enumerate(row):
            cx4 = cm_ox2 + j * (cell_w2 + emu(0.1))
            cy2 = cm_oy2 + i * (cell_h2 + emu(0.1))
            fill = C_ACCENT3 if i == j else C_CARD2
            lc = C_ACCENT3 if i == j else C_ACCENT4
            b += rect_shape(next_id(), f"fce{i}{j}", cx4, cy2, cell_w2, cell_h2,
                           fill=fill if i==j else C_CARD2,
                           line_color=lc, rounding=30000)
            sp = sp_pr(cx4, cy2, cell_w2, cell_h2 * 2 // 3, fill="none")
            tb = txBody(para(run(val, sz=22, bold=True, color=col if i!=j else C_BG_DARK), algn="c"), anchor="b")
            b += shape(sp, tb, next_id(), f"fcval{i}{j}")
            sp = sp_pr(cx4, cy2 + cell_h2 * 2 // 3, cell_w2, cell_h2 // 3, fill="none")
            tb = txBody(para(run(tip, sz=10, color=C_LGRAY if i!=j else C_BG_DARK), algn="c"), anchor="t")
            b += shape(sp, tb, next_id(), f"fctip{i}{j}")

    # Col headers
    for j, lbl in enumerate(labels_row):
        cx4 = cm_ox2 + j * (cell_w2 + emu(0.1))
        sp = sp_pr(cx4, cm_oy2 - emu(0.38), cell_w2, emu(0.33), fill="none")
        tb = txBody(para(run(lbl, sz=11, color=C_LGRAY), algn="c"), anchor="ctr")
        b += shape(sp, tb, next_id(), f"fch{j}")
    # Row headers
    for i, lbl in enumerate(labels_col):
        cy2 = cm_oy2 + i * (cell_h2 + emu(0.1))
        sp = sp_pr(emu(6.65), cy2, emu(0.5), cell_h2, fill="none")
        tb = txBody(para(run(lbl, sz=10, color=C_LGRAY), algn="c"), anchor="ctr")
        b += shape(sp, tb, next_id(), f"fcrh{i}")

    # Important note
    b += rect_shape(next_id(), "fusnote", emu(0.4), emu(7.0), emu(12.5), emu(0.38),
                   fill=C_BG_MID, line_color=C_ACCENT1, rounding=30000)
    sp = sp_pr(emu(0.55), emu(7.0), emu(12.2), emu(0.38), fill="none")
    tb = txBody(para(run(
        "⚡  Fusion model evaluated ENTIRELY on data the system has never seen — "
        "true zero-day simulation with 5 hidden attack types", sz=13, bold=True, color=C_ACCENT1), algn="c"), anchor="ctr")
    b += shape(sp, tb, next_id(), "fusnotetxt")

    return b


def s20_comparison():
    """Slide 20 — Model Comparison"""
    b = bg() + gradient_header_bar() + footer_bar()
    b += slide_title("Model Comparison & Benchmarking")
    b += accent_line(emu(0.96))

    sp = sp_pr(emu(0.5), emu(1.05), emu(12.3), emu(0.4), fill="none")
    tb = txBody(para(run(
        "Benchmarked against Isolation Forest (standard anomaly detection baseline)",
        sz=14, color=C_LGRAY, italic=True), algn="c"), anchor="ctr")
    b += shape(sp, tb, next_id(), "compsub")

    # Comparison table
    b += rect_shape(next_id(), "comptable", emu(0.4), emu(1.6), emu(12.5), emu(4.0),
                   fill=C_CARD, line_color=C_ACCENT1, rounding=60000)

    headers = ["Model", "Purpose", "Accuracy", "Zero-Day", "Lightweight", "Production Ready"]
    hx3 = [emu(0.55), emu(2.45), emu(5.15), emu(6.55), emu(8.2), emu(9.95)]
    hw3 = [emu(1.85), emu(2.65), emu(1.35), emu(1.6), emu(1.7), emu(2.0)]
    for j, (hdr, cx) in enumerate(zip(headers, hx3)):
        sp = sp_pr(cx, emu(1.68), hw3[j], emu(0.38), fill="none")
        tb = txBody(para(run(hdr, sz=13, bold=True, color=C_ACCENT1), algn="c"), anchor="ctr")
        b += shape(sp, tb, next_id(), f"ch{j}")
    b += rect_shape(next_id(), "cthr", emu(0.55), emu(2.08), emu(12.2), emu(0.03), fill=C_ACCENT1)

    rows = [
        ("Isolation Forest", "Anomaly Detection\n(Baseline)", "49.0%", "Partial ⚠️", "✅ Yes", "❌ No"),
        ("LightGBM", "Known Attack\nClassification", "99.99%", "❌ No", "✅ Yes", "✅ Yes"),
        ("Autoencoder", "Zero-Day\nDetection", "99.19%", "✅ Yes", "✅ Yes", "✅ Yes"),
        ("Fusion Model\n★ Proposed", "Hybrid IDS\nSystem", "96.82%", "✅ 97%", "✅ Yes", "✅ Yes"),
    ]
    row_cols = [C_LGRAY, C_ACCENT5, C_ACCENT3, C_ACCENT1]
    for i, (row, rc) in enumerate(zip(rows, row_cols)):
        iy = emu(2.15) + i * emu(0.82)
        bg_c = C_CARD2 if i % 2 == 0 else C_CARD
        b += rect_shape(next_id(), f"cr{i}", emu(0.55), iy, emu(12.2), emu(0.78),
                       fill=bg_c if i < 3 else C_BG_MID,
                       line_color=rc if i == 3 else "none", rounding=20000)
        for j, (val, cx) in enumerate(zip(row, hx3)):
            bold = (i == 3)
            col = rc if (i == 3 or j == 0) else (C_ACCENT3 if "✅" in val else (C_ACCENT4 if "❌" in val else C_WHITE))
            if j == 2:  # accuracy column
                col = C_ACCENT3 if float(val.replace("%","").split(".")[0]) > 90 else C_ACCENT4
            sp = sp_pr(cx, iy, hw3[j], emu(0.78), fill="none")
            tb = txBody(para(run(val, sz=12, bold=bold, color=col), algn="c"), anchor="ctr")
            b += shape(sp, tb, next_id(), f"ccell{i}{j}")

    # Chart section
    b += rect_shape(next_id(), "chartcard", emu(0.4), emu(5.8), emu(12.5), emu(1.35),
                   fill=C_CARD, line_color=C_ACCENT2, rounding=60000)
    sp = sp_pr(emu(0.55), emu(5.87), emu(12.2), emu(0.38), fill="none")
    tb = txBody(para(run("Zero-Day Detection Accuracy Comparison", sz=14, bold=True, color=C_ACCENT2), algn="c"), anchor="ctr")
    b += shape(sp, tb, next_id(), "charthdr")

    chart_data = [
        ("Isolation Forest", 0.49, C_LGRAY),
        ("LightGBM", 0.0, C_ACCENT5),
        ("Autoencoder", 0.99, C_ACCENT3),
        ("Fusion Model ★", 0.97, C_ACCENT1),
    ]
    bar_max_w3 = emu(9.0)
    for i, (name, val, col) in enumerate(chart_data):
        ix = emu(0.55) + i * emu(3.15)
        label_w = emu(2.0)
        bw = int(bar_max_w3 / 4 * val)
        b += rect_shape(next_id(), f"zbtrack{i}", ix + label_w, emu(6.35), bar_max_w3 // 4, emu(0.45),
                       fill=C_DGRAY, rounding=15000)
        if bw > 0:
            b += rect_shape(next_id(), f"zbbar{i}", ix + label_w, emu(6.35), bw, emu(0.45),
                           fill=col, rounding=15000)
        sp = sp_pr(ix, emu(6.3), label_w, emu(0.55), fill="none")
        tb = txBody(para(run(name, sz=12, color=col, bold=(i==3)), algn="r"), anchor="ctr")
        b += shape(sp, tb, next_id(), f"zbn{i}")
        pct = f"{val*100:.0f}%" if val > 0 else "N/A"
        sp = sp_pr(ix + label_w + bar_max_w3 // 4 + emu(0.05), emu(6.3), emu(0.85), emu(0.55), fill="none")
        tb = txBody(para(run(pct, sz=13, bold=True, color=col), algn="l"), anchor="ctr")
        b += shape(sp, tb, next_id(), f"zbval{i}")

    return b


def s21_contributions():
    """Slide 21 — Key Contributions"""
    b = bg() + gradient_header_bar() + footer_bar()
    b += slide_title("Key Research Contributions")
    b += accent_line(emu(0.96))

    contribs = [
        (C_ACCENT1, "🔀", "Hybrid IDS Framework",
         "Novel combination of supervised LightGBM + unsupervised Autoencoder in a single end-to-end IoT intrusion detection pipeline"),
        (C_ACCENT3, "🎯", "Zero-Day Detection Capability",
         "Achieves 97% detection accuracy on 5 completely unseen attack types — simulating real-world zero-day scenarios"),
        (C_ACCENT2, "⚡", "Ultra-Lightweight Architecture",
         "Autoencoder with only 11,907 parameters — deployable on resource-constrained IoT edge gateways"),
        (C_ACCENT5, "📊", "Rigorous Zero-Day Simulation",
         "Strict experimental protocol: 5 attack types are fully hidden from training — ensuring valid zero-day evaluation"),
        (C_ACCENT4, "🏆", "Baseline Benchmarking",
         "Outperforms Isolation Forest (49%) baseline by 48 percentage points on zero-day detection accuracy"),
        (C_LGRAY,   "🔬", "Research-Grade Reproducibility",
         "All code, datasets, and model artifacts published — fully reproducible pipeline from raw data to final evaluation"),
    ]

    cols = 2
    cw = emu(6.1)
    for i, (col, icon, title, desc) in enumerate(contribs):
        row, c = divmod(i, cols)
        ox = emu(0.4) + c * emu(6.5)
        oy = emu(1.15) + row * emu(2.05)
        b += rect_shape(next_id(), f"contrib{i}", ox, oy, cw, emu(1.9),
                       fill=C_CARD, line_color=col, rounding=60000)
        # Icon
        b += rect_shape(next_id(), f"cbadge{i}", ox + emu(0.18), oy + emu(0.18),
                       emu(0.7), emu(0.7), fill=col, rounding=166666,
                       text_xml=para(run(icon, sz=20), algn="c"))
        # Title
        sp = sp_pr(ox + emu(1.0), oy + emu(0.15), cw - emu(1.15), emu(0.5), fill="none")
        tb = txBody(para(run(title, sz=17, bold=True, color=col), algn="l"), anchor="ctr")
        b += shape(sp, tb, next_id(), f"ctitle{i}")
        # Desc
        sp = sp_pr(ox + emu(0.2), oy + emu(0.75), cw - emu(0.4), emu(1.05), fill="none")
        tb = txBody(para(run(desc, sz=13, color=C_LGRAY), algn="l"), anchor="t",
                   lIns=emu(0.05), rIns=emu(0.05))
        b += shape(sp, tb, next_id(), f"cdesc{i}")

    return b


def s22_limitations():
    """Slide 22 — Limitations"""
    b = bg() + gradient_header_bar() + footer_bar()
    b += slide_title("Limitations")
    b += accent_line(emu(0.96))

    sp = sp_pr(emu(0.5), emu(1.05), emu(12.3), emu(0.45), fill="none")
    tb = txBody(para(run(
        "Honest academic assessment of current limitations — areas for future improvement.",
        sz=15, color=C_LGRAY, italic=True), algn="c"), anchor="ctr")
    b += shape(sp, tb, next_id(), "limsub")

    limitations = [
        (C_ACCENT4, "01", "Offline Dataset Evaluation",
         "The system was evaluated on a pre-collected static dataset (Edge-IIoT). "
         "Real-world deployment requires live packet capture and stream processing."),
        (C_ACCENT5, "02", "No Real-Time Deployment",
         "All experiments were conducted in a Colab environment. "
         "Performance on actual IoT hardware (Raspberry Pi, NVIDIA Jetson) remains untested."),
        (C_ACCENT2, "03", "Threshold Sensitivity",
         "The Autoencoder anomaly threshold (0.0122) was tuned on the current dataset. "
         "Different IoT environments may require threshold re-calibration."),
        (C_ACCENT1, "04", "Limited Dataset Diversity",
         "Edge-IIoT covers 14 attack types from a controlled lab environment. "
         "Real-world attacks may exhibit more diverse or combined attack patterns."),
        (C_LGRAY,   "05", "Class Imbalance in Zero-Day Set",
         "Fingerprinting (853 rows) and MITM (394 rows) are severely underrepresented "
         "compared to other zero-day types — may affect recall for rare attacks."),
    ]

    for i, (col, num, title, desc) in enumerate(limitations):
        iy = emu(1.65) + i * emu(1.06)
        b += rect_shape(next_id(), f"lim{i}", emu(0.4), iy, emu(12.5), emu(0.95),
                       fill=C_CARD, line_color=col, rounding=50000)
        b += rect_shape(next_id(), f"limnum{i}", emu(0.45), iy + emu(0.2),
                       emu(0.5), emu(0.5), fill=col, rounding=166666,
                       text_xml=para(run(num, sz=14, bold=True, color=C_BG_DARK), algn="c"))
        sp = sp_pr(emu(1.1), iy + emu(0.06), emu(11.65), emu(0.4), fill="none")
        tb = txBody(para(run(title, sz=16, bold=True, color=col), algn="l"), anchor="ctr")
        b += shape(sp, tb, next_id(), f"ltitle{i}")
        sp = sp_pr(emu(1.1), iy + emu(0.5), emu(11.65), emu(0.42), fill="none")
        tb = txBody(para(run(desc, sz=13, color=C_LGRAY), algn="l"), anchor="t")
        b += shape(sp, tb, next_id(), f"ldesc{i}")

    return b


def s23_future():
    """Slide 23 — Future Work"""
    b = bg() + gradient_header_bar() + footer_bar()
    b += slide_title("Future Work & Research Directions")
    b += accent_line(emu(0.96))

    futures = [
        (C_ACCENT1, "🔴", "Real-Time Deployment",
         "Integrate with live network capture (Scapy/TShark) for streaming IoT traffic analysis at edge gateways",
         "Short Term"),
        (C_ACCENT2, "🟣", "Advanced Fusion Strategies",
         "Replace threshold-based routing with a meta-learner (stacking) or attention-based fusion mechanism",
         "Medium Term"),
        (C_ACCENT3, "🟢", "Edge Hardware Validation",
         "Deploy and benchmark on Raspberry Pi 4, NVIDIA Jetson Nano — measure actual latency and power consumption",
         "Medium Term"),
        (C_ACCENT5, "🟡", "Explainable AI (XAI)",
         "Integrate SHAP values and LIME for interpretable anomaly explanations — critical for security analyst trust",
         "Medium Term"),
        (C_ACCENT4, "🔴", "Federated Learning",
         "Train across distributed IoT devices without centralising sensitive traffic data — privacy-preserving IDS",
         "Long Term"),
        (C_LGRAY,   "⬜", "Adversarial Robustness",
         "Evaluate system against adversarial examples designed to evade the Autoencoder's anomaly detection",
         "Long Term"),
    ]

    cols = 2
    fw3 = emu(6.1)
    for i, (col, icon, title, desc, term) in enumerate(futures):
        row, c = divmod(i, cols)
        ox = emu(0.4) + c * emu(6.5)
        oy = emu(1.15) + row * emu(2.05)
        b += rect_shape(next_id(), f"fw{i}", ox, oy, fw3, emu(1.9),
                       fill=C_CARD, line_color=col, rounding=60000)
        # Term badge
        b += rect_shape(next_id(), f"fwterm{i}", ox + fw3 - emu(1.4), oy + emu(0.15),
                       emu(1.25), emu(0.38), fill=col, rounding=40000,
                       text_xml=para(run(term, sz=10, bold=True, color=C_BG_DARK), algn="c"))
        # Icon + Title
        sp = sp_pr(ox + emu(0.15), oy + emu(0.18), fw3 - emu(1.65), emu(0.45), fill="none")
        tb = txBody(para(run(f"{icon}  {title}", sz=16, bold=True, color=col), algn="l"), anchor="ctr")
        b += shape(sp, tb, next_id(), f"fwtitle{i}")
        # Desc
        sp = sp_pr(ox + emu(0.2), oy + emu(0.72), fw3 - emu(0.4), emu(1.1), fill="none")
        tb = txBody(para(run(desc, sz=13, color=C_LGRAY), algn="l"), anchor="t",
                   lIns=emu(0.05), rIns=emu(0.05))
        b += shape(sp, tb, next_id(), f"fwdesc{i}")

    return b


def s24_conclusion():
    """Slide 24 — Conclusion"""
    b = bg() + gradient_header_bar() + footer_bar()
    b += slide_title("Conclusion")
    b += accent_line(emu(0.96))

    # Main conclusion text
    b += rect_shape(next_id(), "concbox", emu(0.4), emu(1.15), emu(12.5), emu(1.5),
                   fill=C_CARD, line_color=C_ACCENT1, rounding=60000)
    sp = sp_pr(emu(0.6), emu(1.15), emu(12.1), emu(1.5), fill="none")
    tb = txBody(para(run(
        "The proposed Hybrid Intrusion Detection System successfully combines "
        "supervised LightGBM classification and Autoencoder-based anomaly detection "
        "to identify both known and zero-day attacks in lightweight IoT edge environments, "
        "achieving 96.82% accuracy on completely unseen threat scenarios.",
        sz=16, color=C_WHITE), algn="c"), anchor="ctr")
    b += shape(sp, tb, next_id(), "conctxt")

    # Key takeaways
    takeaways = [
        (C_ACCENT3, "99.99%", "LightGBM accuracy on\n10 known attack types"),
        (C_ACCENT1, "99.19%", "Autoencoder accuracy on\nanomaly detection"),
        (C_ACCENT5, "96.82%", "Fusion model on\nzero-day scenario"),
        (C_ACCENT4, "48pp+", "Improvement over\nIsolation Forest baseline"),
    ]
    tw = emu(2.9)
    for i, (col, val, lbl) in enumerate(takeaways):
        tx2 = emu(0.4) + i * emu(3.12)
        b += stat_card(tx2, emu(2.9), tw, emu(1.3), val, lbl, val_color=col)

    # Summary bullets
    conclusions = [
        (C_ACCENT1,
         "Three-Layer Defence: LightGBM identifies known attacks with near-perfect accuracy; "
         "Autoencoder catches unknown anomalies; Fusion layer intelligently routes decisions"),
        (C_ACCENT3,
         "Lightweight Design: With only 11,907 Autoencoder parameters, the system is viable "
         "for deployment on resource-constrained IoT gateways and edge devices"),
        (C_ACCENT2,
         "Research Rigour: Strict experimental protocol (hidden zero-day split) ensures "
         "valid evaluation — no data leakage between training and zero-day testing"),
        (C_ACCENT5,
         "Practical Impact: Addresses a real-world IoT security gap — the inability of "
         "traditional IDS to detect never-before-seen attack patterns in real time"),
    ]
    for i, (col, text) in enumerate(conclusions):
        iy = emu(4.38) + i * emu(0.7)
        b += rect_shape(next_id(), f"conc{i}", emu(0.4), iy, emu(12.5), emu(0.62),
                       fill=C_CARD, line_color=col, rounding=40000)
        b += rect_shape(next_id(), f"concbar{i}", emu(0.4), iy, emu(0.08), emu(0.62), fill=col)
        sp = sp_pr(emu(0.62), iy, emu(12.2), emu(0.62), fill="none")
        tb = txBody(para(run(text, sz=13, color=C_LGRAY), algn="l"), anchor="ctr",
                   lIns=emu(0.05), rIns=emu(0.05))
        b += shape(sp, tb, next_id(), f"conctxt{i}")

    return b


def s25_references():
    """Slide 25 — References"""
    b = bg() + gradient_header_bar() + footer_bar()
    b += slide_title("References")
    b += accent_line(emu(0.96))

    refs = [
        ("[1]", "M. A. Ferrag et al. Edge-IIoTset: A New Comprehensive Realistic Cyber Security "
                "Dataset of IoT and IIoT Applications. IEEE Access, 2022."),
        ("[2]", "G. Ke et al. LightGBM: A Highly Efficient Gradient Boosting Decision Tree. "
                "Advances in Neural Information Processing Systems (NeurIPS), 2017."),
        ("[3]", "D. Bank, N. Koenigstein, R. Giryes. Autoencoders. "
                "Machine Learning for Data Science Handbook. Springer, 2023."),
        ("[4]", "M. Abadi et al. TensorFlow: A System for Large-Scale Machine Learning. "
                "USENIX OSDI, 2016. Online: https://www.tensorflow.org"),
        ("[5]", "F. T. Liu, K. M. Ting, Z.-H. Zhou. Isolation Forest. "
                "IEEE International Conference on Data Mining (ICDM), 2008."),
        ("[6]", "T. A. Tang, L. Mhamdi, D. McLernon et al. Deep Learning Approach for "
                "Network Intrusion Detection in Software Defined Networking. WINCOM, 2016."),
        ("[7]", "N. Moustafa and J. Slay. UNSW-NB15: A Comprehensive Data Set for "
                "Network Intrusion Detection Systems. MilCIS, IEEE, 2015."),
        ("[8]", "Y. Mirsky et al. Kitsune: An Ensemble of Autoencoders for Online "
                "Network Intrusion Detection. NDSS, 2018."),
        ("[9]", "F. Pedregosa et al. Scikit-learn: Machine Learning in Python. "
                "Journal of Machine Learning Research, 12, pp. 2825-2830, 2011."),
        ("[10]", "A. L. Buczak and E. Guven. A Survey of Data Mining and ML Methods "
                 "for Cyber Security Intrusion Detection. IEEE Comms. Surveys, 2016."),
    ]

    cols = 2
    rw = emu(6.1)
    for i, (num, text) in enumerate(refs):
        row, c = divmod(i, cols)
        rx = emu(0.4) + c * emu(6.5)
        ry = emu(1.1) + row * emu(1.17)
        b += rect_shape(next_id(), f"ref{i}", rx, ry, rw, emu(1.1),
                       fill=C_CARD, line_color=C_ACCENT2, rounding=40000)
        b += rect_shape(next_id(), f"refnum{i}", rx + emu(0.1), ry + emu(0.1),
                       emu(0.5), emu(0.9), fill="none",
                       text_xml=para(run(num, sz=13, bold=True, color=C_ACCENT2), algn="c"))
        sp = sp_pr(rx + emu(0.65), ry + emu(0.08), rw - emu(0.8), emu(0.95), fill="none")
        tb = txBody(para(run(text, sz=11, color=C_LGRAY), algn="l"), anchor="t",
                   lIns=emu(0.03), rIns=emu(0.03), tIns=emu(0.03))
        b += shape(sp, tb, next_id(), f"reftxt{i}")

    return b


def s26_thankyou():
    """Slide 26 — Thank You"""
    b = bg(C_BG_DARK)

    # Decorative rings
    b += rect_shape(next_id(), "ring1", SW//2 - emu(3.5), SH//2 - emu(3.5), emu(7), emu(7),
                   fill="none", line_color="00D4FF", line_w=12700, rounding=166666)
    b += rect_shape(next_id(), "ring2", SW//2 - emu(2.8), SH//2 - emu(2.8), emu(5.6), emu(5.6),
                   fill="none", line_color="7B2FFF", line_w=9525, rounding=166666)
    b += rect_shape(next_id(), "ring3", SW//2 - emu(2.2), SH//2 - emu(2.2), emu(4.4), emu(4.4),
                   fill="091525", line_color="00D4FF", line_w=6350, rounding=166666)

    # Main text
    sp = sp_pr(emu(2.0), emu(1.8), emu(9.3), emu(0.8), fill="none")
    tb = txBody(para(run("Thank You", sz=54, bold=True, color=C_ACCENT1), algn="c"), anchor="ctr")
    b += shape(sp, tb, next_id(), "ty")

    sp = sp_pr(emu(2.0), emu(2.7), emu(9.3), emu(0.55), fill="none")
    tb = txBody(para(run("Questions & Discussion", sz=26, color=C_ACCENT2), algn="c"), anchor="ctr")
    b += shape(sp, tb, next_id(), "qs")

    b += rect_shape(next_id(), "tyline", emu(4.0), emu(3.35), emu(5.3), emu(0.04), fill=C_ACCENT1)

    # Project summary
    sp = sp_pr(emu(2.5), emu(3.55), emu(8.3), emu(0.55), fill="none")
    tb = txBody(para(run("Zero Day IoT Attack Detection Using a Hybrid Machine Learning Approach",
                         sz=15, color=C_LGRAY), algn="c"), anchor="ctr")
    b += shape(sp, tb, next_id(), "projname")

    # Result pills
    results = [
        ("LightGBM  99.99%", C_ACCENT5),
        ("Autoencoder  99.19%", C_ACCENT3),
        ("Fusion Model  96.82%", C_ACCENT1),
    ]
    pw = emu(3.5)
    for i, (text, col) in enumerate(results):
        px = SW//2 - emu(5.4) + i * emu(3.65)
        b += rect_shape(next_id(), f"pill{i}", px, emu(4.25), pw, emu(0.55),
                       fill=C_CARD, line_color=col, rounding=60000,
                       text_xml=para(run(text, sz=14, bold=True, color=col), algn="c"))

    # Team info
    sp = sp_pr(emu(2.0), emu(5.1), emu(9.3), emu(0.4), fill="none")
    tb = txBody(para(run("Shahiil Ahmed  ·  B.Tech CSE  ·  College of Information Technology",
                         sz=14, color=C_LGRAY), algn="c"), anchor="ctr")
    b += shape(sp, tb, next_id(), "teaminfo")

    sp = sp_pr(emu(2.0), emu(5.55), emu(9.3), emu(0.4), fill="none")
    tb = txBody(para(run("Department of Computer Science & Engineering  ·  Academic Year 2024–2025",
                         sz=13, color=C_DGRAY), algn="c"), anchor="ctr")
    b += shape(sp, tb, next_id(), "deptinfo")

    # Bottom bar
    b += rect_shape(next_id(), "tybot", 0, SH - emu(0.55), SW, emu(0.55), fill="0A0E1F")
    sp = sp_pr(0, SH - emu(0.5), SW, emu(0.45), fill="none")
    tb = txBody(para(run(
        "Cybersecurity  ·  Artificial Intelligence  ·  IoT Edge Security  ·  Intrusion Detection Systems",
        sz=13, color=C_LGRAY), algn="c"), anchor="ctr")
    b += shape(sp, tb, next_id(), "tyfoottxt")

    return b



# ─────────────────────────────────────────────────────────────────────────────
# OOXML STATIC PARTS
# ─────────────────────────────────────────────────────────────────────────────

CONTENT_TYPES_TEMPLATE = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml"  ContentType="application/xml"/>
  <Override PartName="/ppt/presentation.xml"
    ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>
  <Override PartName="/ppt/slideMasters/slideMaster1.xml"
    ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"/>
  <Override PartName="/ppt/slideLayouts/slideLayout1.xml"
    ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/>
  <Override PartName="/ppt/theme/theme1.xml"
    ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>
  {slide_overrides}
</Types>"""

PRESENTATION_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/>
</Relationships>"""

def make_presentation_xml(n_slides):
    slide_refs = ""
    for i in range(1, n_slides + 1):
        slide_refs += f'  <p:sldId id="{255 + i}" r:id="rId{i + 3}"/>\n'

    slide_rels_in_prs = ""
    for i in range(1, n_slides + 1):
        slide_rels_in_prs += (f'  <Relationship Id="rId{i + 3}" '
                              f'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" '
                              f'Target="slides/slide{i}.xml"/>\n')

    return (f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:presentation xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
  xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
  xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
  saveSubsetFonts="1">
  <p:sldMasterIdLst>
    <p:sldMasterId id="2147483648" r:id="rId1"/>
  </p:sldMasterIdLst>
  <p:sldIdLst>
{slide_refs}  </p:sldIdLst>
  <p:sldSz cx="{SW}" cy="{SH}" type="custom"/>
  <p:notesSz cx="6858000" cy="9144000"/>
</p:presentation>""",
            f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="slideMasters/slideMaster1.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="theme/theme1.xml"/>
{slide_rels_in_prs}</Relationships>""")

SLIDE_MASTER = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldMaster xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
  xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
  xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <p:cSld>
    <p:bg>
      <p:bgPr>
        <a:solidFill><a:srgbClr val="{C_BG_DARK}"/></a:solidFill>
        <a:effectLst/>
      </p:bgPr>
    </p:bg>
    <p:spTree>
      <p:nvGrpSpPr>
        <p:cNvPr id="1" name=""/>
        <p:cNvGrpSpPr/>
        <p:nvPr/>
      </p:nvGrpSpPr>
      <p:grpSpPr>
        <a:xfrm>
          <a:off x="0" y="0"/>
          <a:ext cx="{SW}" cy="{SH}"/>
          <a:chOff x="0" y="0"/>
          <a:chExt cx="{SW}" cy="{SH}"/>
        </a:xfrm>
      </p:grpSpPr>
    </p:spTree>
  </p:cSld>
  <p:clrMap bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1"
    accent2="accent2" accent3="accent3" accent4="accent4" accent5="accent5"
    accent6="accent6" hlink="hlink" folHlink="folHlink"/>
  <p:sldLayoutIdLst>
    <p:sldLayoutId id="2147483649" r:id="rId1"/>
  </p:sldLayoutIdLst>
</p:sldMaster>"""

SLIDE_MASTER_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="../theme/theme1.xml"/>
</Relationships>"""

SLIDE_LAYOUT = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldLayout xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
  xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
  xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
  type="blank" preserve="1">
  <p:cSld name="Blank">
    <p:bg>
      <p:bgPr>
        <a:solidFill><a:srgbClr val="{C_BG_DARK}"/></a:solidFill>
        <a:effectLst/>
      </p:bgPr>
    </p:bg>
    <p:spTree>
      <p:nvGrpSpPr>
        <p:cNvPr id="1" name=""/>
        <p:cNvGrpSpPr/>
        <p:nvPr/>
      </p:nvGrpSpPr>
      <p:grpSpPr>
        <a:xfrm>
          <a:off x="0" y="0"/>
          <a:ext cx="{SW}" cy="{SH}"/>
          <a:chOff x="0" y="0"/>
          <a:chExt cx="{SW}" cy="{SH}"/>
        </a:xfrm>
      </p:grpSpPr>
    </p:spTree>
  </p:cSld>
  <p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>
</p:sldLayout>"""

SLIDE_LAYOUT_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="../slideMasters/slideMaster1.xml"/>
</Relationships>"""

THEME = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="ZeroDayTheme">
  <a:themeElements>
    <a:clrScheme name="ZeroDay">
      <a:dk1><a:srgbClr val="050B1F"/></a:dk1>
      <a:lt1><a:srgbClr val="FFFFFF"/></a:lt1>
      <a:dk2><a:srgbClr val="0A1628"/></a:dk2>
      <a:lt2><a:srgbClr val="B0C4DE"/></a:lt2>
      <a:accent1><a:srgbClr val="00D4FF"/></a:accent1>
      <a:accent2><a:srgbClr val="7B2FFF"/></a:accent2>
      <a:accent3><a:srgbClr val="00FF88"/></a:accent3>
      <a:accent4><a:srgbClr val="FF4C4C"/></a:accent4>
      <a:accent5><a:srgbClr val="FFB800"/></a:accent5>
      <a:accent6><a:srgbClr val="3A4A6B"/></a:accent6>
      <a:hlink><a:srgbClr val="00D4FF"/></a:hlink>
      <a:folHlink><a:srgbClr val="7B2FFF"/></a:folHlink>
    </a:clrScheme>
    <a:fontScheme name="ZeroDay">
      <a:majorFont><a:latin typeface="Segoe UI"/></a:majorFont>
      <a:minorFont><a:latin typeface="Segoe UI"/></a:minorFont>
    </a:fontScheme>
    <a:fmtScheme name="ZeroDay">
      <a:fillStyleLst>
        <a:solidFill><a:schemeClr val="phClr"/></a:solidFill>
        <a:solidFill><a:schemeClr val="phClr"/></a:solidFill>
        <a:solidFill><a:schemeClr val="phClr"/></a:solidFill>
      </a:fillStyleLst>
      <a:lnStyleLst>
        <a:ln w="6350"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln>
        <a:ln w="12700"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln>
        <a:ln w="19050"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln>
      </a:lnStyleLst>
      <a:effectStyleLst>
        <a:effectStyle><a:effectLst/></a:effectStyle>
        <a:effectStyle><a:effectLst/></a:effectStyle>
        <a:effectStyle><a:effectLst/></a:effectStyle>
      </a:effectStyleLst>
      <a:bgFillStyleLst>
        <a:solidFill><a:schemeClr val="phClr"/></a:solidFill>
        <a:solidFill><a:schemeClr val="phClr"/></a:solidFill>
        <a:solidFill><a:schemeClr val="phClr"/></a:solidFill>
      </a:bgFillStyleLst>
    </a:fmtScheme>
  </a:themeElements>
</a:theme>"""

# ─────────────────────────────────────────────────────────────────────────────
# MAIN ASSEMBLY
# ─────────────────────────────────────────────────────────────────────────────

def build_pptx():
    # Collect all 26 slides (we'll have 26 content slides)
    slide_builders = [
        s01_title,
        s02_toc,
        s03_intro,
        s04_problem,
        s05_objectives,
        s06_why_zeroday,
        s07_dataset,
        s08_preprocessing,
        s09_known_vs_unknown,
        s10_architecture,
        s11_lightgbm,
        s12_lgbm_workflow,
        s13_lgbm_results,
        s14_autoencoder,
        s15_ae_architecture,
        s16_ae_results,
        s17_why_fusion,
        s18_fusion_workflow,
        s19_fusion_results,
        s20_comparison,
        s21_contributions,
        s22_limitations,
        s23_future,
        s24_conclusion,
        s25_references,
        s26_thankyou,
    ]

    n = len(slide_builders)
    print(f"Building {n} slides...")

    slide_xmls = []
    for i, builder in enumerate(slide_builders):
        print(f"  Rendering slide {i+1}/{n}: {builder.__name__}...")
        try:
            body = builder()
            slide_xmls.append(make_slide(body, i + 1))
        except Exception as e:
            print(f"    WARNING: slide {i+1} failed ({e}), using placeholder")
            placeholder = (bg() + gradient_header_bar() + footer_bar() +
                           slide_title(f"Slide {i+1} — {builder.__name__}", y=emu(3.0)))
            slide_xmls.append(make_slide(placeholder, i + 1))

    # Slide content-type overrides
    slide_overrides = ""
    for i in range(1, n + 1):
        slide_overrides += (f'  <Override PartName="/ppt/slides/slide{i}.xml" '
                            f'ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>\n')

    prs_xml, prs_rels = make_presentation_xml(n)

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml",
                    CONTENT_TYPES_TEMPLATE.replace("{slide_overrides}", slide_overrides))
        zf.writestr("_rels/.rels", PRESENTATION_RELS)
        zf.writestr("ppt/presentation.xml", prs_xml)
        zf.writestr("ppt/_rels/presentation.xml.rels", prs_rels)
        zf.writestr("ppt/theme/theme1.xml", THEME)
        zf.writestr("ppt/slideMasters/slideMaster1.xml", SLIDE_MASTER)
        zf.writestr("ppt/slideMasters/_rels/slideMaster1.xml.rels", SLIDE_MASTER_RELS)
        zf.writestr("ppt/slideLayouts/slideLayout1.xml", SLIDE_LAYOUT)
        zf.writestr("ppt/slideLayouts/_rels/slideLayout1.xml.rels", SLIDE_LAYOUT_RELS)

        for i, xml in enumerate(slide_xmls, 1):
            zf.writestr(f"ppt/slides/slide{i}.xml", xml)
            zf.writestr(f"ppt/slides/_rels/slide{i}.xml.rels", slide_rel())

    with open(OUT_PATH, "wb") as f:
        f.write(buf.getvalue())

    size_kb = os.path.getsize(OUT_PATH) / 1024
    print(f"\n✅  Done! File saved to: {OUT_PATH}")
    print(f"    File size: {size_kb:.1f} KB")
    print(f"    Total slides: {n}")


if __name__ == "__main__":
    build_pptx()
