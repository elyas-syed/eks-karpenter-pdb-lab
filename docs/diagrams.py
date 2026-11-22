"""Generate AWS-style SVG diagrams for ARTICLE.md.

Usage: python3 docs/diagrams.py docs/images
PNG exports for platforms that don't render SVG: rsvg-convert -z 2 docs/images/NAME.svg -o docs/images/png/NAME.png

Shapes and glyphs are drawn from scratch and follow AWS diagram conventions
(group boundaries, category colors); no AWS icon assets are copied.
"""
import sys
from pathlib import Path
from xml.sax.saxutils import escape

OUT = Path(sys.argv[1])
OUT.mkdir(parents=True, exist_ok=True)

FONT = "Inter, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"
MONO = "'SF Mono', Menlo, Consolas, 'DejaVu Sans Mono', monospace"
INK = "#232F3E"
GREY = "#545B64"
LIGHT = "#D5DBDB"
ORANGE = "#ED7100"   # compute and containers
PURPLE = "#8C4FFF"   # networking
PINK = "#E7157B"     # application integration and management
RED = "#DD344C"      # security
TEAL = "#00A4A6"     # region and private subnet
GREEN = "#7AA116"    # public subnet
BLUE = "#147EBA"     # availability zone
POD_BLUE = "#2E73B8"
OK = "#1D8102"
WARN = "#B7791F"
BAD = "#D13212"


def svg(w, h, body, title, desc):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'viewBox="0 0 {w} {h}" role="img" aria-labelledby="title desc" font-family="{FONT}">'
        f'<title id="title">{escape(title)}</title><desc id="desc">{escape(desc)}</desc>'
        '<defs>'
        f'<marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
        f'<path d="M0,0 L10,5 L0,10 z" fill="{INK}"/></marker>'
        f'<marker id="arrow-bad" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto">'
        f'<path d="M0,0 L10,5 L0,10 z" fill="{BAD}"/></marker>'
        f'<marker id="arrow-ok" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto">'
        f'<path d="M0,0 L10,5 L0,10 z" fill="{OK}"/></marker>'
        '</defs>'
        f'<rect width="{w}" height="{h}" fill="#FFFFFF"/>{body}</svg>\n'
    )


def text(x, y, s, size=14, weight=400, fill=INK, anchor="start", family=None, italic=False):
    fam = f' font-family="{family}"' if family else ""
    sty = ' font-style="italic"' if italic else ""
    return (f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" fill="{fill}" '
            f'text-anchor="{anchor}"{fam}{sty}>{escape(s)}</text>')


def lines(x, y, items, size=13, lh=None, weight=400, fill=INK, anchor="start", family=None):
    lh = lh or round(size * 1.4)
    return "".join(text(x, y + i * lh, s, size, weight, fill, anchor, family) for i, s in enumerate(items))


def rect(x, y, w, h, stroke=INK, fill="none", sw=1.5, rx=0, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{d}/>'


def arrow(d, color=INK, sw=1.6, marker="arrow", dash=None):
    ds = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{sw}" marker-end="url(#{marker})"{ds}/>'


# ---------- glyphs: simple white line art inside a colored tile ----------

def glyph(kind, x, y, s):
    """White glyph drawn in a tile at (x, y) of size s."""
    c = 'fill="none" stroke="#FFFFFF" stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round"'
    sw = max(1.6, s / 22)
    st = c.format(sw=sw)
    m = s * 0.22
    a, b, w = x + m, y + m, s - 2 * m
    if kind == "eks":  # three stacked containers
        h = w / 3.4
        return "".join(f'<rect x="{a}" y="{b + i * (h + w * 0.05)}" width="{w}" height="{h}" rx="2" {st}/>' for i in range(3))
    if kind == "ec2":  # chip with pins
        inner = f'<rect x="{a + w*0.15}" y="{b + w*0.15}" width="{w*0.7}" height="{w*0.7}" rx="2" {st}/>'
        pins = ""
        for i in range(3):
            p = a + w * (0.3 + 0.2 * i)
            pins += f'<path d="M{p},{b} V{b + w*0.15} M{p},{b + w*0.85} V{b + w} M{a},{p - a + b} H{a + w*0.15} M{a + w*0.85},{p - a + b} H{a + w}" {st}/>'
        return inner + pins
    if kind == "nat":  # two crossing arrows
        return (f'<path d="M{a},{b + w*0.3} H{a + w} M{a + w*0.78},{b + w*0.1} L{a + w},{b + w*0.3} L{a + w*0.78},{b + w*0.5} '
                f'M{a + w},{b + w*0.7} H{a} M{a + w*0.22},{b + w*0.5} L{a},{b + w*0.7} L{a + w*0.22},{b + w*0.9}" {st}/>')
    if kind == "sqs":  # queue: three message bars and an arrow
        out = "".join(f'<rect x="{a + i * w*0.24}" y="{b + w*0.25}" width="{w*0.18}" height="{w*0.5}" rx="1.5" {st}/>' for i in range(3))
        return out + f'<path d="M{a + w*0.74},{b + w*0.5} H{a + w} M{a + w*0.88},{b + w*0.38} L{a + w},{b + w*0.5} L{a + w*0.88},{b + w*0.62}" {st}/>'
    if kind == "events":  # bus with three taps
        out = f'<path d="M{a},{b + w*0.5} H{a + w}" {st}/>'
        for i in range(3):
            px = a + w * (0.15 + 0.35 * i)
            out += f'<circle cx="{px}" cy="{b + w*(0.18 if i % 2 == 0 else 0.82)}" r="{w*0.1}" {st}/>'
            out += f'<path d="M{px},{b + w*(0.28 if i % 2 == 0 else 0.72)} V{b + w*0.5}" {st}/>'
        return out
    if kind == "iam":  # key
        return (f'<circle cx="{a + w*0.3}" cy="{b + w*0.5}" r="{w*0.22}" {st}/>'
                f'<path d="M{a + w*0.52},{b + w*0.5} H{a + w} M{a + w*0.8},{b + w*0.5} V{b + w*0.72} M{a + w*0.95},{b + w*0.5} V{b + w*0.66}" {st}/>')
    if kind == "ssm":  # parameter document
        return (f'<path d="M{a + w*0.15},{b} H{a + w*0.65} L{a + w*0.85},{b + w*0.2} V{b + w} H{a + w*0.15} Z" {st}/>'
                f'<path d="M{a + w*0.3},{b + w*0.45} H{a + w*0.7} M{a + w*0.3},{b + w*0.65} H{a + w*0.7} M{a + w*0.3},{b + w*0.85} H{a + w*0.55}" {st}/>')
    if kind == "laptop":
        return (f'<rect x="{a + w*0.1}" y="{b + w*0.1}" width="{w*0.8}" height="{w*0.55}" rx="2" {st}/>'
                f'<path d="M{a - w*0.05},{b + w*0.8} H{a + w*1.05}" {st}/>')
    if kind == "cloud":
        return (f'<path d="M{a + w*0.2},{b + w*0.8} H{a + w*0.8} A{w*0.2},{w*0.2} 0 0 0 {a + w*0.78},{b + w*0.4} '
                f'A{w*0.28},{w*0.28} 0 0 0 {a + w*0.25},{b + w*0.42} A{w*0.2},{w*0.2} 0 0 0 {a + w*0.2},{b + w*0.8} Z" {st}/>')
    if kind == "region":
        return (f'<circle cx="{a + w/2}" cy="{b + w/2}" r="{w*0.45}" {st}/>'
                f'<path d="M{a + w*0.05},{b + w/2} H{a + w*0.95} M{a + w/2},{b + w*0.05} C{a + w*0.15},{b + w*0.35} {a + w*0.15},{b + w*0.65} {a + w/2},{b + w*0.95} '
                f'M{a + w/2},{b + w*0.05} C{a + w*0.85},{b + w*0.35} {a + w*0.85},{b + w*0.65} {a + w/2},{b + w*0.95}" {st}/>')
    if kind == "vpc":
        return (f'<rect x="{a}" y="{b + w*0.3}" width="{w}" height="{w*0.6}" rx="2" {st}/>'
                f'<path d="M{a + w*0.25},{b + w*0.3} V{b + w*0.1} A{w*0.25},{w*0.25} 0 0 1 {a + w*0.75},{b + w*0.1} V{b + w*0.3}" {st}/>')
    if kind == "subnet":
        return f'<rect x="{a + w*0.1}" y="{b + w*0.1}" width="{w*0.8}" height="{w*0.8}" rx="2" {st}/>'
    return ""


def tile(x, y, kind, color, s=48, rx=None):
    rx = s * 0.12 if rx is None else rx
    return f'<rect x="{x}" y="{y}" width="{s}" height="{s}" rx="{rx}" fill="{color}"/>' + glyph(kind, x, y, s)


def service(x, y, kind, color, title, sub, s=48):
    """Tile with a two-line centered label beneath it."""
    cx = x + s / 2
    return (tile(x, y, kind, color, s)
            + text(cx, y + s + 20, title, 13, 600, INK, "middle")
            + text(cx, y + s + 37, sub, 12, 400, GREY, "middle"))


def group(x, y, w, h, label, color, kind, fill="none", dash=None, label_color=None, sw=1.6):
    """AWS-style group: boundary plus a small icon tile in the top-left corner."""
    return (rect(x, y, w, h, color, fill, sw, 0, dash)
            + tile(x, y, kind, color, 26, 0)
            + text(x + 34, y + 18, label, 13, 600, label_color or color))


def chip(x, y, w, label, dot, dashed=False, h=26):
    d = ' stroke-dasharray="4 3"' if dashed else ""
    fill = "#F7F7F7" if dashed else "#FFFFFF"
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{h/2}" fill="{fill}" stroke="#AAB7B8" stroke-width="1"{d}/>'
            f'<circle cx="{x + 14}" cy="{y + h/2}" r="5" fill="{dot}"/>'
            + text(x + 26, y + h / 2 + 4.5, label, 12, 500, GREY if dashed else INK))


# ---------- 1. architecture ----------

def architecture():
    W, H = 1240, 754
    b = []
    # Operator and legend (left column)
    b.append(tile(56, 96, "laptop", GREY, 52))
    b.append(text(82, 170, "Operator", 13, 600, INK, "middle"))
    b.append(text(82, 187, "kubectl · Terraform", 12, 400, GREY, "middle"))
    b.append(text(82, 204, "scripts/lab.sh", 12, 400, GREY, "middle"))

    lx, ly = 20, 520
    b.append(text(lx, ly, "Legend", 13, 700))
    b.append(f'<circle cx="{lx + 6}" cy="{ly + 22}" r="5" fill="{ORANGE}"/>' + text(lx + 18, ly + 27, "Karpenter controller", 12, 400, GREY))
    b.append(f'<circle cx="{lx + 6}" cy="{ly + 46}" r="5" fill="{POD_BLUE}"/>' + text(lx + 18, ly + 51, "Demo replica", 12, 400, GREY))
    b.append(f'<circle cx="{lx + 6}" cy="{ly + 70}" r="5" fill="#AAB7B8"/>' + text(lx + 18, ly + 75, "Setup-only pressure", 12, 400, GREY))
    b.append(rect(lx, ly + 88, 14, 12, ORANGE, "none", 1.4, 0, "4 3") + text(lx + 18, ly + 99, "Temporary node", 12, 400, GREY))

    # Groups
    b.append(group(176, 24, 1044, 714, "AWS Cloud", INK, "cloud", sw=1.8))
    b.append(group(196, 62, 1004, 658, "Region · us-east-2 (Ohio)", TEAL, "region", dash="6 4"))

    # Regional services row
    b.append(service(262, 96, "eks", ORANGE, "Amazon EKS 1.36", "AWS-managed control plane"))
    b.append(service(472, 96, "iam", RED, "IAM + EKS Pod Identity", "controller and node roles"))
    b.append(service(682, 96, "ssm", PINK, "SSM Parameter Store", "AL2023 AMI ID"))
    b.append(service(878, 96, "events", PINK, "Amazon EventBridge", "EC2 health and Spot events"))
    b.append(service(1078, 96, "sqs", PINK, "Amazon SQS", "interruption queue"))
    b.append(arrow("M934,120 H1070"))
    b.append(arrow("M112,122 H254"))
    b.append(text(225, 112, "HTTPS", 11, 500, GREY, "middle"))

    # VPC and AZs
    b.append(group(216, 226, 964, 478, "VPC · 10.72.0.0/16", PURPLE, "vpc"))
    b.append(group(236, 264, 540, 424, "Availability Zone A", BLUE, "region", dash="6 4"))
    b.append(group(796, 264, 364, 424, "Availability Zone B", BLUE, "region", dash="6 4"))

    for (x, w) in ((256, 500), (816, 324)):
        b.append(group(x, 304, w, 92, "Public subnet", GREEN, "subnet", fill="#F2F6E8", label_color="#3B6E00"))
        b.append(tile(x + 18, 336, "nat", PURPLE, 44))
        b.append(text(x + 74, 356, "NAT gateway", 13, 600))
        b.append(text(x + 74, 373, "one per AZ for egress", 12, 400, GREY))
        b.append(group(x, 412, w, 260, "Private subnet", TEAL, "subnet", fill="#E6F6F7", label_color="#007A7C"))

    def node(x, y, w, h, title, sub, price, temporary=False):
        out = rect(x, y, w, h, ORANGE, "#FFFFFF" if not temporary else "#FFF8F1", 1.6, 4, "6 4" if temporary else None)
        out += tile(x + 12, y + 12, "ec2", ORANGE, 34)
        out += text(x + 56, y + 27, title, 13, 700)
        out += text(x + 56, y + 43, sub, 12, 400, GREY)
        out += text(x + w - 12, y + h - 12, price, 12, 600, GREY, "end")
        return out

    # AZ A: managed worker and temporary Karpenter node
    b.append(node(276, 452, 210, 200, "Managed worker", "m5.xlarge · On-Demand", "$0.192/h"))
    b.append(chip(288, 512, 186, "karpenter controller", ORANGE))
    b.append(chip(288, 546, 186, "demo replica", POD_BLUE))
    b.append(chip(288, 580, 186, "pressure (setup only)", "#AAB7B8", dashed=True))

    b.append(node(536, 452, 204, 200, "Karpenter node", "m5a.large · temporary", "$0.086/h", temporary=True))
    b.append(chip(548, 512, 180, "demo replica", POD_BLUE))
    b.append(lines(548, 572, ["Tainted for the experiment.", "Launched for the third", "replica, then removed", "by consolidation."], 12, 17, 400, GREY))

    b.append(arrow("M474,525 H528"))
    b.append(text(506, 516, "launch", 11, 500, GREY, "middle"))
    b.append(text(506, 544, "delete", 11, 500, GREY, "middle"))

    # AZ B: managed worker
    b.append(node(836, 452, 210, 200, "Managed worker", "m5.xlarge · On-Demand", "$0.192/h"))
    b.append(chip(848, 512, 186, "karpenter controller", ORANGE))
    b.append(chip(848, 546, 186, "demo replica", POD_BLUE))
    b.append(chip(848, 580, 186, "pressure (setup only)", "#AAB7B8", dashed=True))

    # SQS -> controller in AZ B
    b.append(arrow("M1102,186 V525 H1042", dash="5 4"))
    b.append(text(1094, 210, "interruption messages", 11, 500, GREY, "end"))

    body = "".join(b)
    return svg(W, H, body,
               "Lab architecture: EKS with Karpenter across two Availability Zones",
               "An EKS 1.36 cluster in us-east-2 with one managed m5.xlarge worker per Availability Zone in private subnets, "
               "a NAT gateway per zone, two Karpenter controller replicas, and a temporary Karpenter-launched m5a.large node "
               "that consolidation later removes. EventBridge sends interruption events to an SQS queue read by Karpenter.")


# ---------- 2. the four gates ----------

def gates():
    W, H = 1240, 440
    b = []
    y, h = 60, 150

    def box(x, w, color, fill, head, body_lines, badge=None, owner=None):
        out = rect(x, y, w, h, color, fill, 1.8, 8)
        tx = x + 16
        if badge:
            out += f'<circle cx="{x + 26}" cy="{y + 28}" r="13" fill="{color}"/>' + text(x + 26, y + 33, badge, 13, 700, "#FFFFFF", "middle")
            tx = x + 48
        out += text(tx, y + 33, head, 13.5, 700, INK)
        out += lines(x + 16, y + 62, body_lines, 12.5, 18, 400, INK)
        if owner:
            out += text(x + 16, y + h - 14, owner, 11.5, 600, color)
        return out

    b.append(box(20, 160, GREY, "#F4F6F6", "Candidate", ["Node is underutilized", "for consolidateAfter", "(30 s in this lab)."]))
    gx = [214, 418, 622, 826]
    specs = [
        ("1", "Pod budget", ["Can every pod on", "the node be evicted", "right now?"], "Kubernetes Eviction API"),
        ("2", "NodePool budget", ["May Karpenter", "disrupt one more", "node right now?"], "Karpenter"),
        ("3", "Scheduling", ["Do the pods fit on", "other nodes (requests,", "spread, taints, volumes)?"], "Karpenter simulation"),
        ("4", "Price", ["Delete, or replace", "with a cheaper", "instance?"], "Karpenter"),
    ]
    for x, (n, head, bl, owner) in zip(gx, specs):
        b.append(box(x, 176, "#2E73B8", "#F1F7FD", head, bl, n, owner))
    b.append(box(1036, 184, OK, "#F2F8F0", "Consolidated", ["Node drained and", "terminated. EC2", "billing stops."]))

    for x0, x1 in ((180, 214), (390, 418), (594, 622), (798, 826), (1002, 1036)):
        b.append(arrow(f"M{x0 + 2},{y + h/2} H{x1 - 3}", OK, 1.8, "arrow-ok"))
    for x0 in (180, 390, 594, 798):
        pass
    for x0 in (391, 595, 799, 1003):
        b.append(text(x0 + 13, y + h / 2 - 8, "yes", 11, 700, OK, "middle"))

    # "no" branches
    ry = 290
    for x in gx:
        cx = x + 88
        b.append(arrow(f"M{cx},{y + h + 2} V{ry - 4}", BAD, 1.8, "arrow-bad"))
        b.append(text(cx + 8, y + h + 36, "no", 11, 700, BAD))
    b.append(rect(214, ry, 788, 64, BAD, "#FDF2F1", 1.8, 8))
    b.append(text(608, ry + 27, "Node stays and EC2 keeps billing", 15, 700, BAD, "middle"))
    b.append(text(608, ry + 48, "Check DisruptionBlocked events, PDB status, NodePool budgets and Karpenter controller logs.", 12.5, 400, INK, "middle"))

    b.append(text(20, 32, "Four gates every voluntary consolidation must pass", 17, 700))
    b.append(text(20, 400, "Simplified view: Karpenter evaluates these together, and any one of them can block a consolidation.", 12.5, 400, GREY))
    b.append(text(20, 420, "Forceful disruption (expiration, interruption) is not rate-limited by NodePool budgets.", 12.5, 400, GREY))
    return svg(W, H, "".join(b),
               "Four gates for Karpenter consolidation",
               "An underutilized node is consolidated only if its pods can be evicted under their PDBs, the NodePool disruption "
               "budget allows another disruption, the pods fit elsewhere, and deleting or replacing the node saves money. "
               "Failing any gate keeps the node running.")


# ---------- 3. experiment phases ----------

def phases():
    W, H = 1240, 470
    b = [text(20, 32, "One variable at a time: three phases on the same node", 17, 700)]
    cards = [
        ("PHASE 1", "Restrictive PDB", BAD, "#FDF2F1", 0, 1, ["minAvailable: 100%", "budgets: nodes: \"1\""],
         "✕", "Blocked", ["Karpenter emits DisruptionBlocked", "naming pdb-lab/demo. A dry-run", "eviction gets 429 TooManyRequests."]),
        ("PHASE 2", "NodePool budget at zero", WARN, "#FDF8EE", 1, 0, ["maxUnavailable: 1", "budgets: nodes: \"0\""],
         "Ⅱ", "Held", ["The PDB now admits an eviction,", "but the node stays untouched for", "the whole control window."]),
        ("PHASE 3", "Both budgets open", OK, "#F2F8F0", 1, 1, ["maxUnavailable: 1", "budgets: nodes: \"1\""],
         "✓", "Consolidated", ["Underutilized delete, 0 replacements.", "3 Ready endpoints in all 15 samples.", "80 of 80 HTTP requests succeeded."]),
    ]
    xs = [20, 434, 848]
    cw, top = 372, 56
    for x, (ph, title, color, fill, pdb, pool, cfg, sym, outcome, ol) in zip(xs, cards):
        b.append(rect(x, top, cw, 396, LIGHT, "#FFFFFF", 1.4, 10))
        b.append(f'<path d="M{x},{top + 10} A10,10 0 0 1 {x + 10},{top} H{x + cw - 10} A10,10 0 0 1 {x + cw},{top + 10} V{top + 56} H{x} Z" fill="{color}"/>')
        b.append(text(x + 18, top + 23, ph, 11.5, 700, "#FFFFFF"))
        b.append(text(x + 18, top + 44, title, 16, 700, "#FFFFFF"))

        def dial(yy, label, val):
            ok = val > 0
            c = OK if ok else BAD
            return (text(x + 18, yy + 17, label, 13, 500, INK)
                    + rect(x + cw - 74, yy, 56, 26, c, c, 1, 13)
                    + text(x + cw - 46, yy + 18, str(val), 14, 700, "#FFFFFF", "middle"))
        b.append(dial(top + 74, "PDB allowed disruptions", pdb))
        b.append(dial(top + 110, "NodePool budget (nodes)", pool))

        b.append(rect(x + 18, top + 152, cw - 36, 56, LIGHT, "#F7F8F8", 1, 6))
        b.append(lines(x + 30, top + 175, cfg, 12.5, 20, 500, INK, family=MONO))

        b.append(rect(x + 18, top + 226, cw - 36, 150, color, fill, 1.6, 8))
        b.append(f'<circle cx="{x + 46}" cy="{top + 256}" r="16" fill="{color}"/>')
        b.append(text(x + 46, top + 262, sym, 16, 700, "#FFFFFF", "middle"))
        b.append(text(x + 72, top + 262, outcome, 17, 700, color))
        b.append(lines(x + 34, top + 302, ol, 12.5, 20, 400, INK))

    for x in (392, 806):
        b.append(arrow(f"M{x + 2},{top + 200} H{x + 40}", INK, 1.8))
        b.append(text(x + 21, top + 190, "change", 10.5, 600, GREY, "middle"))
        b.append(text(x + 21, top + 222, "one", 10.5, 600, GREY, "middle"))
    return svg(W, H, "".join(b),
               "Three experiment phases",
               "Phase 1 uses a PDB with minAvailable 100 percent and a NodePool budget of one: Karpenter is blocked. "
               "Phase 2 allows one eviction but sets the NodePool budget to zero: the node is held. "
               "Phase 3 allows both: Karpenter deletes the underutilized node with no failed requests.")


# ---------- 4. before / after ----------

def before_after():
    W, H = 1240, 450
    b = [text(20, 32, "What consolidation removed", 17, 700)]

    def node(x, y, w, title, sub, price, pods, temporary=False):
        h = 64 + 34 * 3 + 30
        out = rect(x, y, w, h, ORANGE, "#FFF8F1" if temporary else "#FFFFFF", 1.6, 6, "6 4" if temporary else None)
        out += tile(x + 12, y + 12, "ec2", ORANGE, 32)
        out += text(x + 52, y + 26, title, 13, 700)
        out += text(x + 52, y + 42, sub, 12, 400, GREY)
        for i, (label, dot) in enumerate(pods):
            out += chip(x + 12, y + 60 + i * 34, w - 24, label, dot)
        out += text(x + w - 12, y + h - 12, price, 12.5, 700, GREY, "end")
        return out

    K = ("karpenter controller", ORANGE)
    D = ("demo replica", POD_BLUE)
    # Before panel
    b.append(rect(20, 52, 560, 330, LIGHT, "#FAFBFB", 1.4, 10))
    b.append(text(40, 80, "Before · 3 nodes", 14, 700))
    b.append(node(40, 96, 168, "Worker A", "m5.xlarge", "$0.192/h", [K, D]))
    b.append(node(220, 96, 168, "Worker B", "m5.xlarge", "$0.192/h", [K, D]))
    b.append(node(400, 96, 168, "Karpenter node", "m5a.large", "$0.086/h", [D], temporary=True))
    b.append(text(40, 362, "EC2 compute: $0.470 per hour", 15, 700))

    # Arrow
    b.append(arrow("M590,216 H660", INK, 2.2))
    b.append(text(625, 200, "delete", 12, 700, GREY, "middle"))

    # After panel
    b.append(rect(672, 52, 548, 330, LIGHT, "#FAFBFB", 1.4, 10))
    b.append(text(692, 80, "After · 2 nodes", 14, 700))
    b.append(node(692, 96, 250, "Worker A", "m5.xlarge", "$0.192/h", [K, D, D]))
    b.append(node(954, 96, 250, "Worker B", "m5.xlarge", "$0.192/h", [K, D]))
    b.append(text(692, 362, "EC2 compute: $0.384 per hour", 15, 700))

    b.append(rect(20, 396, 1200, 42, OK, "#F2F8F0", 1.4, 8))
    b.append(text(620, 423, "Saving: $0.086 per hour, about $63 per month for one stuck m5a.large (On-Demand, Ohio, EC2 compute only)", 13.5, 600, OK, "middle"))
    return svg(W, H, "".join(b),
               "Cluster before and after consolidation",
               "Before: two m5.xlarge workers and one m5a.large Karpenter node, $0.470 per hour of EC2 compute. "
               "After: the three demo replicas run on the two workers, $0.384 per hour, a saving of $0.086 per hour.")


for name, fn in (("architecture", architecture), ("four-gates", gates), ("experiment-phases", phases), ("before-after", before_after)):
    (OUT / f"{name}.svg").write_text(fn(), encoding="utf-8")
    print("wrote", OUT / f"{name}.svg")
