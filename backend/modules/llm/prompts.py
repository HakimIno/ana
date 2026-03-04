"""
System prompts for the Analyst Agent.

The system prompt is loaded from prompts.yaml for maintainability.
Legacy text-based prompt is preserved in prompts_legacy.py for rollback.
"""
import yaml
from pathlib import Path
from functools import lru_cache

_PROMPT_DIR = Path(__file__).parent


@lru_cache(maxsize=1)
def _load_yaml_config() -> dict:
    """Load and cache the YAML prompt configuration."""
    yaml_path = _PROMPT_DIR / "prompts.yaml"
    with open(yaml_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _render_section(title: str, items) -> str:
    """Render a section from YAML config into prompt text."""
    lines = [f"### {title}"]
    if isinstance(items, list):
        for item in items:
            lines.append(f"- {item}")
    elif isinstance(items, dict):
        for key, value in items.items():
            if isinstance(value, list):
                lines.append(f"**{key.upper()}**")
                for item in value:
                    lines.append(f"- {item}")
            elif isinstance(value, dict):
                lines.append(f"**{key}**")
                for k, v in value.items():
                    lines.append(f"  - `{k}`: {v}")
            else:
                lines.append(f"- **{key}**: {value}")
    else:
        lines.append(str(items))
    return "\n".join(lines)


def _render_polars_cheatsheet(config: dict) -> str:
    """Render the Polars cheatsheet section."""
    cheat = config.get("polars_cheatsheet", {})
    lines = ["### POLARS CHEATSHEET — USE THESE EXACT PATTERNS:", "```"]
    
    correct = cheat.get("correct", {})
    wrong = cheat.get("wrong", {})
    
    lines.append("# ✅ CORRECT                              # ❌ WRONG (will error)")
    for key in correct:
        c = correct[key]
        w = wrong.get(key, "")
        if w:
            lines.append(f"{c:<42} {w}")
        else:
            lines.append(c)
    lines.append("```")
    
    note = cheat.get("critical_note", "")
    if note:
        lines.append(f"\n**CRITICAL**: {note}")
    return "\n".join(lines)


def load_system_prompt() -> str:
    """
    Build the system prompt from prompts.yaml.
    
    Returns a formatted string ready to use as the LLM system message.
    """
    config = _load_yaml_config()
    
    sections = []
    
    # Output format rule (most critical)
    output_fmt = config.get("output_format", {})
    sections.append(f"⚠️ CRITICAL OUTPUT FORMAT RULE: {output_fmt.get('critical_rule', '')}")
    
    # Identity
    identity = config.get("identity", {})
    sections.append(f"You are a {identity.get('role', 'Data Analyst')}. {identity.get('goal', '')}")
    
    # Data Architecture
    data_arch = config.get("data_architecture", {})
    sections.append(_render_section("DATA ARCHITECTURE", data_arch))
    
    # Code Environment
    code_env = config.get("code_environment", {})
    sections.append(_render_section("CODE EXECUTION ENVIRONMENT", code_env))
    
    # Core Rules
    rules = config.get("rules", {})
    for rule_name, rule_items in rules.items():
        title = rule_name.upper().replace("_", " ")
        sections.append(_render_section(title, rule_items))
    
    # Polars Cheatsheet
    sections.append(_render_polars_cheatsheet(config))
    
    # Charts
    charts = config.get("charts", {})
    sections.append(_render_section("CHART GENERATION — CRITICAL RULES", charts))
    
    # Anomaly Detection
    anomaly = config.get("anomaly_detection", [])
    sections.append(_render_section("ANOMALY DETECTION", anomaly))
    
    # Auto-retry
    retry = config.get("auto_retry", {})
    sections.append(_render_section("AUTO-RETRY BEHAVIOR", retry))
    
    # Date Handling (critical for model compatibility)
    date_handling = config.get("date_handling", {})
    if date_handling:
        sections.append(_render_section("DATE HANDLING — CRITICAL", date_handling))
    
    # Language & Formatting
    lang = config.get("language", {})
    sections.append(_render_section("LANGUAGE AND FORMATTING", lang))
    
    # Output Schema
    schema = config.get("output_schema", {})
    sections.append(_render_section("OUTPUT SCHEMA (JSON Only)", schema))
    
    # PDF Generation
    pdf = config.get("pdf_generation", {})
    sections.append(_render_section("PDF TEMPLATE GENERATION", pdf))
    
    return "\n\n".join(sections)


# ──────────────────────────────────────────────
# Module-level exports (backward compatible)
# ──────────────────────────────────────────────

ANALYST_SYSTEM_PROMPT = load_system_prompt()

QUERY_PROMPT_TEMPLATE = """
## SYSTEM DATE:
{current_date}

## ACTIVE FILE (Target for Analysis):
{filename}

## AVAILABLE DATAFRAMES (USE THESE EXACT VARIABLE NAMES IN CODE):
{available_files}

## CONVERSATION HISTORY:
{history}

## VERIFIED BUSINESS INTELLIGENCE (Source of Truth):
{calculated_metrics}

## DOCUMENT CONTEXT (RAG):
{rag_context}

## USER INTENT:
{user_question}

Respond in JSON. Be direct and precise. Use only verified data.
"""

