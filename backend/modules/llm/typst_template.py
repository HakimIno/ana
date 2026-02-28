import re
import typst
import os
import tempfile
import structlog
from pathlib import Path
from typing import List, Dict, Any, Set

from config import settings

logger = structlog.get_logger(__name__)

class TypstTemplateHelper:
    """Helper for the AI to generate multi-page PDFs by filling a .typ template with data."""

    def __init__(self, storage_dir: Path = settings.STORAGE_DIR):
        self.storage_dir = storage_dir

    def get_template_content(self, template_name: str) -> str:
        """Read the template file content from storage."""
        template_name = template_name.replace("@", "")
        if not template_name.endswith(".typ"):
            template_name += ".typ"
            
        file_path = self.storage_dir / template_name
        if not file_path.exists():
            raise FileNotFoundError(f"Template not found: {template_name}")
            
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    def get_placeholders(self, template_name: str) -> List[str]:
        """
        Extract all placeholder names from a template.
        Returns a list of placeholder names (e.g. ['BRANCH_NAME', 'REVENUE', 'COST']).
        Use this to know exactly what keys your data dictionaries should have.
        """
        content = self.get_template_content(template_name)
        # Find {{KEY}} style placeholders
        placeholders = re.findall(r'\{\{\s*(\w+)\s*\}\}', content)
        # Find [[KEY]] style placeholders
        placeholders += re.findall(r'\[\[\s*(\w+)\s*\]\]', content)
        # Deduplicate while preserving order
        seen: Set[str] = set()
        unique = []
        for p in placeholders:
            if p not in seen:
                seen.add(p)
                unique.append(p)
        return unique

    def analyze_template_structure(self, template_name: str) -> Dict[str, Any]:
        """
        Heuristically analyzes the Typst template to provide structure hints for the AI,
        like how many columns are expected in a table.
        """
        content = self.get_template_content(template_name)
        
        hints = {"expected_table_columns": None, "headers": []}
        
        # Try to extract table headers (text inside bracket blocks right before table body)
        table_block = re.search(r'#table\((.*?)\{\{TABLE_BODY\}\}', content, re.DOTALL)
        if table_block:
            header_text = table_block.group(1)
            
            # Look for table definitions: columns: (1fr, 1fr, ...) INSIDE the table block
            col_match = re.search(r'columns:\s*\(([^)]+)\)', header_text)
            if col_match:
                # Count the number of parts separated by commas
                cols_str = col_match.group(1)
                num_cols = len(cols_str.split(','))
                hints["expected_table_columns"] = num_cols
            # Find words inside brackets or alignment blocks: e.g. align(center)[Budget] or [Item]
            raw_headers = re.findall(r'\[([^\]]+)\]', header_text)
            # Clean up the headers
            clean_headers = []
            for h in raw_headers:
                # Remove Typst formatting commands and extra whitespace
                cln = re.sub(r'#\w+\([^)]*\)', '', h) # remove like #align(right)
                cln = re.sub(r'#\w+', '', cln) # remove like #v
                cln = cln.replace('\\', ' ').replace('\n', ' ').strip()
                if cln and len(cln) > 1 and not cln.isnumeric() and "มกราคม" not in cln:
                    clean_headers.append(cln)
            
            # Keep only the last N headers if we found too many (since multiple header rows exist)
            if hints["expected_table_columns"] and len(clean_headers) >= hints["expected_table_columns"]:
                hints["headers"] = clean_headers[-hints["expected_table_columns"]:]
            else:
                hints["headers"] = clean_headers
                
        return hints

    def generate_pdf(self, template_name: str, data_list: List[Dict[str, Any]], output_filename: str = "generated_report.pdf") -> str:
        """
        Takes a template and a list of dictionaries (one per page/instance),
        injects the data, compiles to PDF, and saves it.
        Returns the download URL/Path.
        """
        try:
            template_content = self.get_template_content(template_name)
            
            # Detect all placeholders in the template
            template_placeholders = set(re.findall(r'\{\{\s*(\w+)\s*\}\}', template_content))
            template_placeholders |= set(re.findall(r'\[\[\s*(\w+)\s*\]\]', template_content))
            
            logger.info("template_placeholders_detected", placeholders=list(template_placeholders))
            
            if data_list:
                logger.info("data_keys_provided", keys=list(data_list[0].keys()), num_pages=len(data_list))
            
            combined_content = []
            
            for index, data_item in enumerate(data_list):
                page_content = template_content
                matched_placeholders = set()
                
                # Replace placeholders like {{KEY}} or [[KEY]] with actual values
                for key, value in data_item.items():
                    # Attempt to extract scalar value if the AI accidentally sent a 1x1 Polars Dataframe/Series
                    if hasattr(value, 'item') and callable(value.item):
                        try:
                            value = value.item()
                        except Exception:
                            pass
                            
                    # Format numbers with commas and appropriate decimal places
                    if isinstance(value, (int, float)) and not isinstance(value, bool):
                        key_upper = key.upper()
                        # If the key name implies a count/quantity, format as integer
                        if any(k in key_upper for k in ["CUSTOMER", "STAFF", "BRANCH", "BILL"]):
                            val_str = f"{int(value):,}"
                        else:
                            # Default to 2 decimal places for financial/generic numbers
                            val_str = f"{float(value):,.2f}"
                    else:
                        val_str = str(value)
                    
                    # Escape special Typst characters in the data values
                    val_str = val_str.replace("#", "\\#").replace("$", "\\$")
                    
                    # Case-insensitive replacement using re
                    pattern1 = re.compile(rf"\{{\{{\s*{re.escape(key)}\s*\}}\}}", re.IGNORECASE)
                    new_content = pattern1.sub(val_str, page_content)
                    if new_content != page_content:
                        matched_placeholders.add(key)
                    page_content = new_content
                    
                    pattern2 = re.compile(rf"\[\[\s*{re.escape(key)}\s*\]\]", re.IGNORECASE)
                    new_content = pattern2.sub(val_str, page_content)
                    if new_content != page_content:
                        matched_placeholders.add(key)
                    page_content = new_content
                
                # Check for remaining unreplaced placeholders
                remaining = re.findall(r'\{\{\s*(\w+)\s*\}\}', page_content)
                remaining += re.findall(r'\[\[\s*(\w+)\s*\]\]', page_content)
                
                if index == 0:
                    if matched_placeholders:
                        logger.info("placeholders_replaced", matched=list(matched_placeholders))
                    if remaining:
                        logger.warning("unreplaced_placeholders", remaining=remaining, 
                                     hint="Data keys don't match these template placeholders")
                    
                combined_content.append(page_content)
                
                # Add page break between instances, except after the last one
                if index < len(data_list) - 1:
                    combined_content.append("\n#pagebreak()\n")
            
            final_typst_code = "\n".join(combined_content)
            
            # Compile to PDF using a temporary file
            with tempfile.NamedTemporaryFile(suffix=".typ", mode="w", delete=False) as f:
                f.write(final_typst_code)
                temp_path = f.name
                
            try:
                pdf_bytes = typst.compile(temp_path)
            finally:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
            
            # Save the generated PDF
            output_path = self.storage_dir / output_filename
            with open(output_path, "wb") as f:
                f.write(pdf_bytes)
                
            logger.info("pdf_generated_successfully", path=str(output_path), pages=len(data_list))
            return f"/files/download/{output_filename}"
            
        except Exception as e:
            logger.error("Template generation failed", error=str(e))
            raise e
