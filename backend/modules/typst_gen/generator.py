import re
import yaml
import typst
from pathlib import Path
from typing import List, Dict
import structlog
from api.deps import get_llm_client_for_model

logger = structlog.get_logger(__name__)

_PROMPT_FILE = Path(__file__).parent / "prompts.yaml"


def _load_prompt_config() -> dict:
    """Load the YAML prompt configuration file."""
    with open(_PROMPT_FILE, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def _classify_document(text_sample: str, config: dict) -> str:
    """
    Classify the document type using keyword search on extracted text.
    Returns the key of the best matching document_type in the YAML config.
    """
    doc_types = config.get('document_types', {})
    text_lower = text_sample.lower()
    
    best_match = "general"
    best_score = 0
    
    for type_key, type_config in doc_types.items():
        if type_key == "general":
            continue
        keywords = type_config.get('keywords', [])
        score = sum(1 for kw in keywords if kw.lower() in text_lower)
        if score > best_score:
            best_score = score
            best_match = type_key
    
    logger.info(f"Document classified as: {best_match} (score: {best_score})")
    return best_match


def _build_system_prompt(doc_type: str, config: dict) -> str:
    """
    Dynamically assemble the system prompt based on detected document type.
    Always includes base rules (role, output_rules, special_chars) plus
    the document-type-specific section.
    """
    base = config.get('base', {})
    doc_types = config.get('document_types', {})
    type_config = doc_types.get(doc_type, doc_types.get('general', {}))
    
    sections = [
        base.get('role', ''),
        base.get('output_rules', ''),
        type_config.get('prompt', ''),
        base.get('special_chars', ''),
        base.get('closing', ''),
    ]
    
    return '\n\n'.join(s.strip() for s in sections if s.strip())


def _sanitize_typst_code(code: str) -> str:
    """
    Post-processing step to fix common Typst syntax errors deterministically.
    Runs before each compilation attempt to catch LLM mistakes.
    """
    # 1. Escape $ for currency (followed by digits/spaces before digits)
    code = re.sub(r'(?<!\\)\$(?=\d)', r'\\$', code)
    
    # 2. Escape @ in email-like patterns
    code = re.sub(r'(?<!\\)@(?=[a-zA-Z])', r'\\@', code)
    
    # 3. Replace #image(...) calls with rect placeholders
    code = re.sub(r'#image\([^)]+\)', '#rect(width: 60pt, height: 60pt, fill: luma(220))', code)
    
    # 4. Strip any leftover markdown code fences
    code = re.sub(r'^```[a-z]*\n?', '', code, flags=re.MULTILINE)
    code = re.sub(r'\n?```$', '', code, flags=re.MULTILINE)

    # 4b. Fix #text(...) where LLM writes ] instead of ) before the content block [
    #     Root cause: LLM closes the wrong bracket, turning `#text(weight: "bold")[x]`
    #     into `#text(weight: "bold"][x]` which prematurely closes any outer [ content.
    #
    #     Fix strategy: wherever `weight: "bold"][` appears, insert the missing )
    #     Works at ANY nesting depth — standalone, inside content block, mid-content.
    #       [#text(weight: "bold"][x]  →  [#text(weight: "bold")[x]  ✓
    #        #text(weight: "bold"][x]  →   #text(weight: "bold")[x]  ✓
    #     [txt #text(weight: "bold"][x] more]  →  [txt #text(weight: "bold")[x] more]  ✓
    code = re.sub(r'(weight\s*:\s*["\']bold["\']\s*)\]\[', r'\1)[', code)
    # Also catch multi-arg cases: #text(size: 11pt, weight: "bold"][x]
    code = re.sub(r'(#text\([^)\]]+)\]\[', r'\1)[', code)

    # 4c. Remove backslash line continuations — not valid in Typst
    #     LLM sometimes writes: [some text] \
    #     which causes "the character `\` is not valid in code"
    code = re.sub(r'\s*\\\s*\n', '\n', code)

    # 5a. Replace grid.cell(...) with table.cell(...) — wrong namespace inside #table
    code = code.replace('grid.cell(', 'table.cell(')

    # 5b. Flatten row(...) calls — LLM sometimes wraps rows in a non-existent row()
    #     row([a], [b], [c])  →  [a], [b], [c]
    def _flatten_row(m: re.Match) -> str:
        return m.group(1)
    code = re.sub(r'\brow\(([^)]+)\)', _flatten_row, code)

    # 5c. Flatten bare tuple-style rows on a single line:
    #     (  [a], [b], [c]  ),   →   [a], [b], [c],
    #     Only matches lines where the entire line is (...) containing only cells/table.cell
    #     Safe: won't touch fill: lambdas or other legitimate parenthesised expressions
    def _flatten_tuple_row(m: re.Match) -> str:
        inner = m.group(1).strip().rstrip(',')
        return inner + ','
    code = re.sub(
        r'^\s*\(\s*((?:(?:table\.cell\([^)]*\)\[[^\]]*\]|table\.cell\([^)]*\)|\[[^\]]*\])\s*,?\s*)+)\s*\),?\s*$',
        _flatten_tuple_row,
        code,
        flags=re.MULTILINE,
    )

    # 5d. Wrap orphaned spanning args into table.cell()
    #     LLM sometimes writes:  rowspan: 2, [*header*],
    #     instead of:            table.cell(rowspan: 2)[*header*],
    #     This pattern appears as a bare line starting with rowspan:/colspan:
    def _wrap_orphan_span(m: re.Match) -> str:
        key = m.group(1)    # "rowspan" or "colspan"
        val = m.group(2)    # e.g. "2"
        content = m.group(3)  # e.g. "[*header*]"
        return f'table.cell({key}: {val}){content},'
    code = re.sub(
        r'^\s*(rowspan|colspan):\s*(\d+),\s*(\[[^\]]*\]),?\s*$',
        _wrap_orphan_span,
        code,
        flags=re.MULTILINE,
    )

    # 5e. Strip # from function calls in code mode (argument lists)
    #     Inside function args like table.header(...), Typst is in code mode.
    #     LLM writes: table.header(..., #text(size: 0pt)[], ...)
    #     Correct:    table.header(..., text(size: 0pt)[], ...)
    #     Pattern: #identifier( preceded by a comma+whitespace or opening paren
    code = re.sub(r'(?<=,\s)#([a-z][a-z0-9_]*)\(', r'\1(', code)
    # Also handle case with no space after comma
    code = re.sub(r'(?<=,)#([a-z][a-z0-9_]*)\(', r'\1(', code)

    #    Problem A: AI writes table.cell(rowspan: 2, [content]) — content INSIDE ()
    #               Correct: table.cell(rowspan: 2)[content] — content OUTSIDE
    #    Problem B: Duplicate named args table.cell(rowspan: 2, ..., rowspan: 2)[content]
    def _fix_table_cell(m: re.Match) -> str:
        inner = m.group(1)
        trailing = m.group(2)  # e.g. "[content]" or ""

        # Split args by comma, but respect nested brackets
        parts = []
        depth = 0
        current = ''
        for ch in inner:
            if ch == '[':
                depth += 1
            elif ch == ']':
                depth -= 1
            if ch == ',' and depth == 0:
                parts.append(current.strip())
                current = ''
            else:
                current += ch
        if current.strip():
            parts.append(current.strip())

        # Separate out content blocks (parts that are [...]) from named args
        named_args = []
        content_blocks = []
        seen_keys = set()
        for part in parts:
            part = part.strip().rstrip(',')
            kv = re.match(r'(rowspan|colspan|align|fill|inset|x|y)\s*:', part)
            if kv:
                key = kv.group(1)
                if key not in seen_keys:  # deduplicate
                    seen_keys.add(key)
                    named_args.append(part)
            elif re.match(r'^\[', part):  # content block inside parens
                content_blocks.append(part)
            elif part:
                named_args.append(part)

        args_str = ', '.join(named_args)
        # Prefer content that was already outside the parens (trailing), then inside
        if trailing:
            return f'table.cell({args_str}){trailing}'
        elif content_blocks:
            content_str = ''.join(content_blocks)
            return f'table.cell({args_str}){content_str}'
        else:
            return f'table.cell({args_str})'

    # Process ALL table.cell(...) calls — both with and without trailing [content]
    # Group 1: args inside parens, Group 2: optional [content] block outside
    code = re.sub(r'table\.cell\(([^)]+)\)(\[[^\]]*\])?', _fix_table_cell, code)

    # 6. Clamp colspan/rowspan values to valid range per table
    #    "cell's colspan would cause it to exceed the available column(s)"
    #    Parse each #table(columns: (...)) to get column count, then cap any
    #    colspan/rowspan in that table's body.
    def _clamp_spanning_in_table(table_src: str, col_count: int) -> str:
        """Cap colspan/rowspan values inside a single table block."""
        def _cap(m: re.Match) -> str:
            key = m.group(1)
            val = int(m.group(2))
            # colspan must be ≤ col_count; rowspan not easily bounded, leave >1 alone but cap ≥ col_count
            if key == 'colspan':
                val = min(val, col_count)
            # rowspan: cap to a sane maximum (avoid huge values)
            elif key == 'rowspan':
                val = min(val, 20)
            return f'{key}: {val}'
        return re.sub(r'\b(colspan|rowspan):\s*(\d+)', _cap, table_src)

    def _process_tables(src: str) -> str:
        """Find each #table(...) block and apply span clamping."""
        result = []
        pos = 0
        for m in re.finditer(r'#table\s*\(', src):
            result.append(src[pos:m.start()])
            start = m.start()
            # Find matching closing paren by tracking depth
            depth = 0
            i = m.end() - 1  # position of the opening (
            while i < len(src):
                if src[i] == '(':
                    depth += 1
                elif src[i] == ')':
                    depth -= 1
                    if depth == 0:
                        break
                i += 1
            table_src = src[start:i + 1]

            # Count columns from `columns: (entry, entry, ...)` or `columns: N`
            col_count = None
            col_m = re.search(r'\bcolumns\s*:\s*\(([^)]+)\)', table_src)
            if col_m:
                # Count comma-separated entries (handles fractions, auto, pt values)
                entries = [e.strip() for e in col_m.group(1).split(',') if e.strip()]
                col_count = len(entries)
            else:
                int_m = re.search(r'\bcolumns\s*:\s*(\d+)', table_src)
                if int_m:
                    col_count = int(int_m.group(1))

            if col_count and col_count > 0:
                table_src = _clamp_spanning_in_table(table_src, col_count)

            result.append(table_src)
            pos = i + 1
        result.append(src[pos:])
        return ''.join(result)

    code = _process_tables(code)

    return code.strip()



async def generate_typst(pages: List[Dict[str, str]], model: str = "openrouter/google/gemini-2.5-flash") -> str:
    """
    Two-step AI pipeline:
    1. CLASSIFY: Extract document type from OCR text via keyword matching.
    2. GENERATE: Build a tailored system prompt, then call the LLM with vision
                 input, followed by an self-correction agentic loop.
    """
    config = _load_prompt_config()
    client, actual_model_id = get_llm_client_for_model(model)
    
    # ── Step 1: Classify document type ───────────────────────────────────
    all_text = " ".join(p.get('text', '') for p in pages)
    doc_type = _classify_document(all_text, config)
    
    # ── Step 2: Build dynamic prompt for this document type ───────────────
    system_prompt = _build_system_prompt(doc_type, config)
    logger.info(f"Using dynamic prompt for document type: {doc_type}")
    
    # ── Step 3: Build user messages ───────────────────────────────────────
    messages = [{"role": "system", "content": system_prompt}]
    
    user_content: list = [
        {"type": "text", "text": (
            f"Convert the following {doc_type.replace('_', ' ')} document "
            f"into a Typst document.\n\n"
            f"CRITICAL PAGE COUNT RULE: The original PDF has EXACTLY {len(pages)} page(s). "
            f"Your Typst output MUST also produce EXACTLY {len(pages)} page(s) — no more, no less. "
            f"If your content overflows, reduce font sizes, margins, or vertical spacing to fit. "
            f"NEVER let content spill to an extra page."
        )}
    ]
    
    for page in pages:
        layout_ctx = page.get('layout', '')
        intro = (
            f"--- Page {page['page_num']} ---\n"
            f"EXTRACTED TEXT:\n{page['text']}\n\n"
        )
        if layout_ctx:
            intro += (
                f"PDF LAYOUT STRUCTURE (use these exact measurements for accurate Typst output):\n"
                f"{layout_ctx}\n\n"
                f"Use the font sizes above to set #set text(size: Xpt). "
                f"Use the x% positions to derive column widths as fr fractions. "
                f"Use the rect positions to identify table borders and bordered boxes.\n"
            )
        user_content.append({"type": "text", "text": intro})
        user_content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/png;base64,{page['image_base64']}",
                "detail": "high"
            }
        })
    
    messages.append({"role": "user", "content": user_content})
    
    # ── Step 4: LLM Generation + Self-Correction Loop ────────────────────
    max_retries = 3
    for attempt in range(max_retries):
        logger.info(f"Calling LLM {actual_model_id} (Attempt {attempt+1}/{max_retries})")
        try:
            response = client.chat.completions.create(
                model=actual_model_id,
                messages=messages,
                temperature=0.1,
            )
            raw_output = response.choices[0].message.content or ""
            raw_output = _sanitize_typst_code(raw_output)
            
            logger.info("Testing Typst compilation locally...")
            try:
                typst.compile(raw_output.encode('utf-8'))
                logger.info("Typst compilation successful!")
                return raw_output
            except Exception as compile_err:
                error_msg = getattr(compile_err, 'diagnostic', None) or str(compile_err)
                logger.warning(f"Typst compilation error: {error_msg}")
                
                if attempt == max_retries - 1:
                    logger.error("Max retries reached. Returning best-effort code.")
                    return raw_output
                
                # Append the previous attempt and the error for self-correction
                messages.append({"role": "assistant", "content": raw_output})
                numbered = '\n'.join(f"{i+1:03d} | {l}" for i, l in enumerate(raw_output.split('\n')))
                messages.append({
                    "role": "user",
                    "content": (
                        f"The generated code failed to compile.\n\n"
                        f"Code with line numbers:\n```typst\n{numbered}\n```\n\n"
                        f"Compiler errors:\n```\n{error_msg}\n```\n\n"
                        f"REMINDER: The output MUST be exactly {len(pages)} page(s). "
                        f"If fixing errors causes overflow, reduce margins/font sizes/spacing.\n\n"
                        f"Please fix ALL the errors and output the ENTIRE corrected Typst code. DO NOT TRUNCATE."
                    )
                })
                
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            raise
    
    return ""
