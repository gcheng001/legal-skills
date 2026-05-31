#!/usr/bin/env python3
"""Lightweight layout lint for criminal-case visualization HTML/SVG files.

The checker is intentionally approximate. It catches common failures before
human review: missing viewBox, small bold Chinese text, text overflow outside a
nearby rect, and obvious text-to-text collisions.
"""

from __future__ import annotations

import argparse
import html
import re
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path


SVG_RE = re.compile(r"<svg\b[\s\S]*?</svg>", re.IGNORECASE)
TAG_NS_RE = re.compile(r"^\{.*\}")

# --- Hard-gate config (2026-05-30) ---------------------------------------
# These checks turn long-standing "wall rules" into machine-enforced ERRORs.
# Reason: prior outputs violated every documented rule (black cards, SVG
# timelines, blurred bold Chinese) because nothing failed the build.

# Allow-list of light fills the skill explicitly sanctions (see SKILL rule 6
# + chart-templates background colors). Anything darker that backs a sizeable
# rect/cell is treated as a forbidden dark card.
LIGHT_FILL_ALLOW = {
    "#ffffff", "#fff", "#f9f9f9", "#f9fafb", "#f3f4f6", "#f8fafc",
    "#fef2f2", "#fee2e2", "#fff7ed", "#ffedd5", "#fef3c7", "#fde68a",
    "#eff6ff", "#dbeafe", "#dcfce7", "#bbf7d0", "#f3e8ff", "#ede9fe",
    "#e5e7eb", "#d1d5db", "#fafafa", "#f1f5f9", "#ecfdf5", "#fff1f2",
}

# Color-word fallbacks that are unambiguously dark.
DARK_COLOR_WORDS = {"black", "#000", "#000000"}

# Sections whose content is text-dense and MUST be HTML table/grid, never SVG.
# Matched against the nearest preceding heading/section marker text.
TABLE_ONLY_KEYWORDS = ("时间轴", "时间图", "事实时间", "证据印证", "证据矩阵", "矩阵")

HEX_RE = re.compile(r"#[0-9a-fA-F]{3,6}\b")


def hex_luminance(hex_color: str) -> float | None:
    """Perceived luminance 0..255 for a #rgb / #rrggbb string, else None."""
    h = hex_color.strip().lower().lstrip("#")
    if len(h) == 3:
        h = "".join( c * 2 for c in h)
    if len(h) != 6:
        return None
    try:
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    except ValueError:
        return None
    return 0.299 * r + 0.587 * g + 0.114 * b


def is_dark_fill(value: str | None) -> bool:
    """True when a fill/background value is darker than the light allow-list."""
    if not value:
        return False
    v = value.strip().lower()
    if v in DARK_COLOR_WORDS:
        return True
    m = HEX_RE.search(v)
    if not m:
        return False
    hexv = m.group(0).lower()
    if hexv in LIGHT_FILL_ALLOW:
        return False
    lum = hex_luminance(hexv)
    # Threshold ~110: #1F2937 (lum~38) and #374151 (lum~62) are caught;
    # mid grays like #6B7280 (lum~113) used for *strokes/text* pass here and
    # are only flagged when they actually back a large rect (see caller).
    return lum is not None and lum < 110


@dataclass
class Box:
    x1: float
    y1: float
    x2: float
    y2: float

    @property
    def width(self) -> float:
        return max(0.0, self.x2 - self.x1)

    @property
    def height(self) -> float:
        return max(0.0, self.y2 - self.y1)

    def contains(self, other: "Box", pad: float = 0.0) -> bool:
        return (
            other.x1 >= self.x1 - pad
            and other.y1 >= self.y1 - pad
            and other.x2 <= self.x2 + pad
            and other.y2 <= self.y2 + pad
        )

    def intersects(self, other: "Box") -> bool:
        return not (
            self.x2 <= other.x1
            or other.x2 <= self.x1
            or self.y2 <= other.y1
            or other.y2 <= self.y1
        )

    def intersection_area(self, other: "Box") -> float:
        if not self.intersects(other):
            return 0.0
        return max(0.0, min(self.x2, other.x2) - max(self.x1, other.x1)) * max(
            0.0, min(self.y2, other.y2) - max(self.y1, other.y1)
        )


@dataclass
class TextItem:
    text: str
    box: Box
    font_size: float
    font_weight: int
    anchor: str
    line_no: int


def strip_ns(tag: str) -> str:
    return TAG_NS_RE.sub("", tag)


def parse_float(value: str | None, default: float = 0.0) -> float:
    if not value:
        return default
    match = re.search(r"-?\d+(?:\.\d+)?", value)
    if not match:
        return default
    return float(match.group(0))


def parse_weight(value: str | None) -> int:
    if not value:
        return 400
    value = value.strip().lower()
    if value in {"normal", "regular"}:
        return 400
    if value in {"bold", "bolder"}:
        return 700
    match = re.search(r"\d+", value)
    return int(match.group(0)) if match else 400


def style_map(style: str | None) -> dict[str, str]:
    result: dict[str, str] = {}
    if not style:
        return result
    for part in style.split(";"):
        if ":" in part:
            key, value = part.split(":", 1)
            result[key.strip()] = value.strip()
    return result


def attr_or_style(elem: ET.Element, name: str, default: str | None = None) -> str | None:
    if name in elem.attrib:
        return elem.attrib[name]
    return style_map(elem.attrib.get("style")).get(name, default)


def text_content(elem: ET.Element) -> str:
    text = "".join(elem.itertext())
    return html.unescape(re.sub(r"\s+", " ", text)).strip()


def estimated_text_width(text: str, font_size: float) -> float:
    width = 0.0
    for ch in text:
        code = ord(ch)
        if ch.isspace():
            width += 0.35
        elif 0x4E00 <= code <= 0x9FFF or 0x3000 <= code <= 0x303F or 0xFF00 <= code <= 0xFFEF:
            width += 1.0
        elif ch in "MW@#%":
            width += 0.85
        else:
            width += 0.55
    return width * font_size


def line_number(source: str, needle: str) -> int:
    idx = source.find(needle)
    if idx < 0:
        return 0
    return source.count("\n", 0, idx) + 1


def parse_svg(source: str, index: int) -> tuple[list[Box], list[TextItem], list[str], list[str]]:
    warnings: list[str] = []
    errors: list[str] = []
    rects: list[Box] = []
    texts: list[TextItem] = []

    try:
        root = ET.fromstring(source)
    except ET.ParseError as exc:
        return rects, texts, warnings, [f"svg[{index}] XML parse error: {exc}"]

    if not root.attrib.get("viewBox"):
        warnings.append(f"svg[{index}] missing viewBox")

    for elem in root.iter():
        tag = strip_ns(elem.tag)
        if tag == "rect":
            x = parse_float(elem.attrib.get("x"))
            y = parse_float(elem.attrib.get("y"))
            w = parse_float(elem.attrib.get("width"))
            h = parse_float(elem.attrib.get("height"))
            if w > 0 and h > 0:
                rects.append(Box(x, y, x + w, y + h))
        elif tag == "text":
            text = text_content(elem)
            if not text:
                continue
            x = parse_float(elem.attrib.get("x"))
            y = parse_float(elem.attrib.get("y"))
            font_size = parse_float(attr_or_style(elem, "font-size"), 12.0)
            weight = parse_weight(attr_or_style(elem, "font-weight"))
            anchor = attr_or_style(elem, "text-anchor", "start") or "start"
            width = estimated_text_width(text, font_size)
            height = font_size * 1.25
            if anchor == "middle":
                x1 = x - width / 2
            elif anchor == "end":
                x1 = x - width
            else:
                x1 = x
            y1 = y - font_size
            item = TextItem(
                text=text,
                box=Box(x1, y1, x1 + width, y1 + height),
                font_size=font_size,
                font_weight=weight,
                anchor=anchor,
                line_no=line_number(source, text),
            )
            texts.append(item)
            if font_size < 16 and weight > 400:
                warnings.append(
                    f"svg[{index}] small bold text may blur: line {item.line_no}, "
                    f"font-size={font_size:g}, font-weight={weight}, text={text[:30]!r}"
                )

    return rects, texts, warnings, errors


def nearest_container(text: TextItem, rects: list[Box]) -> Box | None:
    cx = (text.box.x1 + text.box.x2) / 2
    cy = (text.box.y1 + text.box.y2) / 2
    candidates = [r for r in rects if r.x1 - 2 <= cx <= r.x2 + 2 and r.y1 - 8 <= cy <= r.y2 + 8]
    if not candidates:
        return None
    return min(candidates, key=lambda r: r.width * r.height)


def lint_layout(rects: list[Box], texts: list[TextItem], index: int) -> tuple[list[str], list[str]]:
    warnings: list[str] = []
    errors: list[str] = []

    for item in texts:
        container = nearest_container(item, rects)
        if container and not container.contains(item.box, pad=4):
            errors.append(
                f"svg[{index}] text likely overflows containing box: line {item.line_no}, "
                f"text={item.text[:40]!r}"
            )

    for i, a in enumerate(texts):
        for b in texts[i + 1 :]:
            if abs(a.box.y1 - b.box.y1) < max(a.font_size, b.font_size) * 0.35:
                continue
            area = a.box.intersection_area(b.box)
            if area <= 0:
                continue
            smaller = max(1.0, min(a.box.width * a.box.height, b.box.width * b.box.height))
            if area / smaller > 0.18:
                errors.append(
                    f"svg[{index}] text boxes overlap: line {a.line_no} {a.text[:24]!r} / "
                    f"line {b.line_no} {b.text[:24]!r}"
                )

    return warnings, errors


def gate_dark_cards(raw: str) -> list[str]:
    """ERROR on dark-filled SVG rects / dark-background CSS used as card faces.

    Skill rule 6 forbids dark/black boxes (user-confirmed dislike). Prior
    outputs used fill="#1F2937" on large rects for charts 4/5.
    """
    errors: list[str] = []

    # 1) SVG <rect ... fill="#1F2937"> with non-trivial size.
    for m in re.finditer(r"<rect\b[^>]*>", raw, re.IGNORECASE):
        tag = m.group(0)
        fill = None
        fm = re.search(r'fill\s*[:=]\s*["\']?\s*(#[0-9a-fA-F]{3,6}|black)', tag)
        if fm:
            fill = fm.group(1)
        if not is_dark_fill(fill):
            continue
        w = parse_float(re.search(r'width\s*=\s*["\']?([\d.]+)', tag).group(1)) if re.search(r'width\s*=', tag) else 0.0
        h = parse_float(re.search(r'height\s*=\s*["\']?([\d.]+)', tag).group(1)) if re.search(r'height\s*=', tag) else 0.0
        if w * h >= 2500:  # ~50x50 and up = a card face, not a thin accent bar
            errors.append(
                f"forbidden dark card: <rect fill={fill}> size {w:g}x{h:g} "
                f"at line {line_number(raw, tag[:40])} (rule 6: no dark/black boxes)"
            )

    # 1b) Bare <rect> with no fill attribute AND no class to back it via CSS.
    # SVG defaults such a rect to BLACK fill -> renders as a black card. This
    # is the real root cause of charts 4/5 black boxes (fill was never set;
    # only `.node rect{fill:#FFF}` existed, so non-.node cards went black).
    # A class only "backs" a rect's fill if its CSS body sets `fill:` to a
    # real color (not `none`, and `stroke:` does NOT count — that was the
    # charts 4/5 trap: `.node rect { stroke: ... }` with no fill -> black).
    def _has_fill(body: str) -> bool:
        fm = re.search(r'(?<!-)fill\s*:\s*([^;}\s]+)', body)
        return bool(fm) and fm.group(1).strip().lower() not in {"none", "transparent"}

    css_rect_classes: set[str] = set()
    for cm in re.finditer(r'\.([\w-]+(?:\.[\w-]+)*)\s+rect\s*\{([^}]*)\}', raw):
        if _has_fill(cm.group(2)):
            # ".node.neutral" -> {"node","neutral"}; match if rect has ALL? No —
            # CSS compound needs all; but keep permissive: any token present.
            css_rect_classes.update(cm.group(1).split("."))
    if re.search(r'(^|[^.\w])rect\s*\{([^}]*)\}', raw):
        for cm in re.finditer(r'(^|[^.\w])rect\s*\{([^}]*)\}', raw):
            if _has_fill(cm.group(2)):
                css_rect_classes.add("__bare_rect__")
                break
    for m in re.finditer(r'<rect\b[^>]*?>', raw, re.DOTALL):
        tag = m.group(0)
        if re.search(r'fill\s*[:=]', tag):
            continue  # explicit fill (attr or inline style) — handled above
        cls_m = re.search(r'class\s*=\s*["\']([^"\']*)["\']', tag)
        classes = set(cls_m.group(1).split()) if cls_m else set()
        backed = bool(classes & css_rect_classes) or "__bare_rect__" in css_rect_classes
        # also check parent <g class="..."> within 200 chars before the rect
        if not backed:
            ctx = raw[max(0, m.start() - 200):m.start()]
            for gm in re.finditer(r'<g\b[^>]*class\s*=\s*["\']([^"\']*)["\']', ctx):
                if set(gm.group(1).split()) & css_rect_classes:
                    backed = True
        w = parse_float(re.search(r'width\s*=\s*["\']?([\d.]+)', tag).group(1)) if re.search(r'width\s*=', tag) else 0.0
        h = parse_float(re.search(r'height\s*=\s*["\']?([\d.]+)', tag).group(1)) if re.search(r'height\s*=', tag) else 0.0
        if not backed and w * h >= 2500:
            errors.append(
                f"bare <rect> with no fill (renders BLACK): size {w:g}x{h:g} "
                f"at line {line_number(raw, tag[:50])} — set fill or a CSS-backed class "
                f"(rule 6 root cause: SVG default fill is black)"
            )

    # 2) CSS background: dark on card-like classes.
    for m in re.finditer(r'background[a-z-]*\s*:\s*(#[0-9a-fA-F]{3,6}|black)', raw, re.IGNORECASE):
        val = m.group(1)
        if is_dark_fill(val):
            errors.append(
                f"forbidden dark background in CSS: {val} at line "
                f"{raw.count(chr(10), 0, m.start()) + 1} (rule 6: no dark/black boxes)"
            )
    return errors


def gate_dangling_filter_refs(raw: str) -> list[str]:
    """ERROR when a CSS/element filter references a #id not defined in the SAME svg.

    THE charts 4/5 black-card root cause: `.node rect { filter: url(#shadow); }`
    applies to every svg, but `<filter id="shadow">` was defined only inside
    svg[1]. In every other svg the rects reference a missing filter, and
    headless Chrome renders them as solid BLACK. Pure fill/grep checks miss this.
    """
    errors: list[str] = []

    # Collect filter ids referenced from CSS (apply to ALL svgs that match).
    css_blocks = re.findall(r"<style\b[^>]*>([\s\S]*?)</style>", raw, re.IGNORECASE)
    css_text = "\n".join(css_blocks)
    css_filter_ids = set(re.findall(r"filter\s*:\s*url\(#([\w-]+)\)", css_text))
    # Does CSS target rect / .node rect etc.? If so, every svg with such rects
    # needs the id defined locally.
    css_targets_rect = bool(re.search(r"rect\s*\{[^}]*filter\s*:\s*url\(#", css_text))

    sources = SVG_RE.findall(raw)
    for idx, svg in enumerate(sources, start=1):
        local_ids = set(re.findall(r'<filter\b[^>]*id\s*=\s*["\']([\w-]+)["\']', svg))
        # inline filter="url(#x)" usages inside this svg
        inline_refs = set(re.findall(r'filter\s*=\s*["\']url\(#([\w-]+)\)["\']', svg))
        style_refs = set(re.findall(r'filter\s*:\s*url\(#([\w-]+)\)', svg))
        refs = inline_refs | style_refs
        # If CSS applies a filter to rects and this svg has <rect>, the css id
        # must resolve locally too.
        if css_targets_rect and re.search(r"<rect\b", svg):
            refs |= css_filter_ids
        missing = {r for r in refs if r and r not in local_ids}
        for mid in sorted(missing):
            errors.append(
                f"svg[{idx}] references filter #{mid} not defined in this <svg> "
                f"(renders BLACK in Chrome). Define <filter id=\"{mid}\"> inside "
                f"EACH svg that uses it, or drop the filter. (charts 4/5 root cause)"
            )
    return errors


def gate_table_only_sections(raw: str) -> list[str]:
    """ERROR when a text-dense section (timeline/matrix) contains an SVG.

    These MUST be HTML table/grid. Prior output put the timeline in SVG and the
    cards overlapped + text was clipped.
    """
    errors: list[str] = []
    # Split into <section ...> blocks; fall back to heading-delimited chunks.
    blocks = re.split(r'(?=<section\b)', raw, flags=re.IGNORECASE)
    if len(blocks) <= 1:
        blocks = re.split(r'(?=<h[1-3]\b)', raw, flags=re.IGNORECASE)
    for blk in blocks:
        head = blk[:400]
        if not any(kw in head for kw in TABLE_ONLY_KEYWORDS):
            continue
        if re.search(r"<svg\b", blk, re.IGNORECASE):
            label = next((kw for kw in TABLE_ONLY_KEYWORDS if kw in head), "?")
            errors.append(
                f"text-dense section '{label}' uses <svg>; must be HTML table/grid "
                f"(2026-05-29 routing rule + charts 2/6 spec)"
            )
    return errors


def gate_bold_chinese(raw: str) -> list[str]:
    """ERROR on small bold Chinese in SVG text (strokes merge, illegible).

    Complements the per-SVG WARN: this scans the whole file including CSS
    classes so a .process-title{font-weight:600} hidden in <style> still fails.
    """
    errors: list[str] = []
    han = re.compile(r"[一-鿿]")
    # SVG text elements carrying font-weight >=600 attribute.
    for m in re.finditer(r"<text\b[^>]*>(.*?)</text>", raw, re.IGNORECASE | re.DOTALL):
        tag, inner = m.group(0), m.group(1)
        if not han.search(inner):
            continue
        wm = re.search(r'font-weight\s*[:=]\s*["\']?\s*(\d{3}|bold|bolder)', tag)
        if not wm:
            continue
        weight = parse_weight(wm.group(1))
        size = parse_float(attr_value(tag, "font-size"), 12.0)
        if weight > 400 and size < 16:
            errors.append(
                f"small bold Chinese in SVG: weight={weight} size={size:g} "
                f"text={inner.strip()[:24]!r} at line {line_number(raw, tag[:40])} "
                f"(rule 2: Chinese font-weight must be 400 under 16px)"
            )
    return errors


def attr_value(tag: str, name: str) -> str | None:
    m = re.search(rf'{name}\s*[:=]\s*["\']?\s*([^"\';\s>]+)', tag)
    return m.group(1) if m else None


def gate_palette_contract(raw: str) -> list[str]:
    """ERROR when output deviates from the locked Claude-orange Scheme-A contract.

    The skill's whole point is determinism: every case must look identical.
    Two regressions this catches:
      1. cold-gray page background #F9F9F9 (contract mandates warm white #FAFAF9)
      2. Mermaid graphs missing clusterBkg override -> default mustard subgraph
    """
    errors: list[str] = []

    # 1) Cold-gray page background. Match `--c-page` var or body background.
    for m in re.finditer(r'--c-page\s*:\s*(#[0-9a-fA-F]{3,6})', raw):
        if m.group(1).lower() in {"#f9f9f9", "#f9fafb", "#f3f4f6"}:
            errors.append(
                f"cold-gray page background {m.group(1)} at line "
                f"{raw.count(chr(10), 0, m.start()) + 1}; contract requires warm white #FAFAF9 (rule 6)"
            )

    # 2) Mermaid init blocks must set clusterBkg to avoid default mustard.
    #    Only check files that actually contain mermaid init directives.
    for m in re.finditer(r"%%\{init:.*?\}%%", raw, re.DOTALL):
        block = m.group(0)
        if "subgraph" in raw and "clusterBkg" not in block:
            errors.append(
                "Mermaid init present but missing clusterBkg override; "
                "subgraph will render default mustard. Add clusterBkg:'#FAFAF9' (模板铁律)"
            )
            break
    return errors


def lint_file(path: Path) -> int:
    raw = path.read_text(encoding="utf-8", errors="replace")
    sources = SVG_RE.findall(raw)
    if not sources and "<svg" in raw:
        sources = [raw]

    warnings: list[str] = []
    errors: list[str] = []

    if not sources:
        warnings.append("no inline SVG found; HTML/CSS layout still requires PNG visual review")

    if "position:absolute" in raw or "position: absolute" in raw:
        warnings.append("absolute-positioned element found; confirm it does not cover the diagram")

    # --- Hard gates: documented rules, now build-failing -------------------
    errors.extend(gate_dark_cards(raw))
    errors.extend(gate_dangling_filter_refs(raw))
    errors.extend(gate_table_only_sections(raw))
    errors.extend(gate_bold_chinese(raw))
    errors.extend(gate_palette_contract(raw))

    for idx, svg in enumerate(sources, start=1):
        rects, texts, svg_warnings, svg_errors = parse_svg(svg, idx)
        warnings.extend(svg_warnings)
        errors.extend(svg_errors)
        if svg_errors:
            continue
        layout_warnings, layout_errors = lint_layout(rects, texts, idx)
        warnings.extend(layout_warnings)
        errors.extend(layout_errors)

    for msg in warnings:
        print(f"WARN: {msg}")
    for msg in errors:
        print(f"ERROR: {msg}")

    if errors:
        print(f"FAIL: {len(errors)} error(s), {len(warnings)} warning(s)")
        return 1
    print(f"PASS: {len(warnings)} warning(s)")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Lint SVG/HTML diagram layout")
    parser.add_argument("file", type=Path, help="HTML or SVG file to check")
    args = parser.parse_args()
    if not args.file.exists():
        print(f"ERROR: file not found: {args.file}")
        return 2
    return lint_file(args.file)


if __name__ == "__main__":
    sys.exit(main())
