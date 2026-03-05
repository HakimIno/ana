import fitz
import base64
from typing import List, Dict
import structlog

logger = structlog.get_logger(__name__)


def _extract_layout_context(page: fitz.Page) -> str:
    """
    Extract rich structural information from the PDF page that the LLM
    can use to write accurate Typst code — exact font sizes, positions,
    column widths, border rectangles — instead of guessing from the image.
    """
    rect = page.rect
    page_w, page_h = rect.width, rect.height

    # ── 1. Text blocks with position and font size ─────────────────────
    blocks_info = []
    raw = page.get_text("rawdict", flags=fitz.TEXT_PRESERVE_WHITESPACE)
    for block in raw.get("blocks", []):
        if block.get("type") != 0:  # 0 = text block
            continue
        b = block["bbox"]  # (x0, y0, x1, y1) in points
        # Collect font info from lines/spans
        font_sizes = []
        bolds = []
        texts = []
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                font_sizes.append(round(span.get("size", 0), 1))
                bolds.append("Bold" in span.get("font", "") or span.get("flags", 0) & 16)
                texts.append(span.get("text", "").strip())
        if not texts:
            continue
        dominant_size = max(set(font_sizes), key=font_sizes.count) if font_sizes else 0
        is_bold = any(bolds)
        text_preview = " ".join(texts)[:60]
        # Normalise position as % of page size for LLM readability
        x_pct = round(b[0] / page_w * 100)
        y_pct = round(b[1] / page_h * 100)
        w_pct = round((b[2] - b[0]) / page_w * 100)
        blocks_info.append(
            f"  [{x_pct}%,{y_pct}%,w={w_pct}%] {dominant_size}pt"
            f"{'B' if is_bold else ''}: {text_preview!r}"
        )

    # ── 2. Rectangles / lines (table borders, boxes) ───────────────────
    drawings_info = []
    seen_rects = set()
    for path in page.get_drawings():
        for item in path.get("items", []):
            if item[0] == "re":  # rectangle
                r = item[1]
                # Normalise
                x_pct = round(r.x0 / page_w * 100)
                y_pct = round(r.y0 / page_h * 100)
                w_pct = round(r.width / page_w * 100)
                h_pct = round(r.height / page_h * 100)
                key = (x_pct, y_pct, w_pct, h_pct)
                if key in seen_rects or w_pct < 2 or h_pct < 1:
                    continue
                seen_rects.add(key)
                fill_info = ", fill=gray" if path.get("fill") else ""
                drawings_info.append(
                    f"  rect [{x_pct}%,{y_pct}%] w={w_pct}% h={h_pct}%{fill_info}"
                )

    # ── 3. Assemble summary ────────────────────────────────────────────
    lines = [
        f"PAGE: {round(page_w)}pt × {round(page_h)}pt (A4={595}pt×{842}pt)",
        f"MARGINS (estimated from content): "
        f"left≈{round(min((b[0] for b in (blk['bbox'] for blk in raw.get('blocks',[]) if blk.get('type')==0)), default=50))}pt",
    ]
    if blocks_info:
        lines.append(f"TEXT BLOCKS ({len(blocks_info)} total, positions as % of page):")
        lines.extend(blocks_info[:30])  # cap to avoid token explosion
    if drawings_info:
        lines.append(f"RECTANGLES/BORDERS ({len(drawings_info)} total):")
        lines.extend(drawings_info[:20])

    return "\n".join(lines)


def parse_pdf_for_ai(pdf_bytes: bytes) -> List[Dict[str, str]]:
    """
    Parses a PDF into a list of pages.
    Each page contains:
    - 'page_num':      1-indexed page number
    - 'image_base64': Base64-encoded PNG (2× scale for clarity)
    - 'text':         Extracted raw text
    - 'layout':       Rich structural context (positions, font sizes, rectangles)
    """
    logger.info("Parsing PDF for Multimodal AI")
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    pages = []

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)

        # 1. Raw text
        text = page.get_text("text")

        # 2. Image at 2× scale
        mat = fitz.Matrix(2, 2)
        pix = page.get_pixmap(matrix=mat)
        b64_img = base64.b64encode(pix.tobytes("png")).decode("utf-8")

        # 3. Rich layout context
        layout = _extract_layout_context(page)

        pages.append({
            "page_num": page_num + 1,
            "text": text,
            "image_base64": b64_img,
            "layout": layout,
        })

    doc.close()
    logger.info(f"Parsed {len(pages)} pages.")
    return pages
