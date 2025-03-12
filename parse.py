import re
from typing import List, Tuple, Dict

class HTMLTableParser:
    def __init__(self, html2text_func):
        self.html2text = html2text_func
        self.table_counter = 0
        self.extracted_tables = {}

    def _generate_placeholder(self) -> str:
        """Generate a unique placeholder for a table."""
        self.table_counter += 1
        return f"<<PLACEHOLDER YOYO Table {self.table_counter}>>"

    def _extract_tables(self, html: str) -> str:
        """Extract all tables from HTML and replace with placeholders."""
        # Find all outermost tables using stack-based approach
        start_tag_pattern = re.compile(r"<\s*table")
        end_tag_pattern = re.compile(r"<\s*/\s*table")
        
        stack = []
        outermost_tables = []
        
        # Find all start and end tag matches
        start_tags = [(m.start(), m.end()) for m in start_tag_pattern.finditer(html)]
        end_tags = [(m.start(), m.end()) for m in end_tag_pattern.finditer(html)]
        
        # Merge and sort all tags by their start position
        all_tags = sorted(start_tags + end_tags, key=lambda x: x[0])
        
        # Find outermost tables using stack
        for start, end in all_tags:
            tag_content = html[start:end]
            if re.match(start_tag_pattern, tag_content):
                stack.append(start)
            elif re.match(end_tag_pattern, tag_content):
                if stack:
                    start_pos = stack.pop()
                    if not stack:  # If stack is empty, it's an outermost table
                        outermost_tables.append((start_pos, end))
        
        # Replace tables with placeholders in reverse order
        result = html
        for start, end in reversed(outermost_tables):
            table = result[start:end]
            placeholder = self._generate_placeholder()
            self.extracted_tables[placeholder] = table
            result = result[:start] + placeholder + result[end:]
            
        return result

    def _parse_single_table(self, table_html: str, indent_level: int = 0) -> str:
        """Parse a single table, handling nested tables if present."""
        # First, extract any nested tables from cells
        processed_html = self._extract_tables(table_html)

        # Extract rows
        row_pattern = r'<tr[^>]*>(.*?)</tr>'
        rows = re.findall(row_pattern, processed_html, re.DOTALL)
        if not rows:
            return ""

        # Extract headers (first row)
        cell_pattern = r'<t[dh][^>]*>(.*?)</t[dh]>'
        headers = re.findall(cell_pattern, rows[0], re.DOTALL)
        
        # Process data rows
        result = []
        result.append("-" * 40)

        # Process each row
        for row_idx, row in enumerate(rows):
            cells = re.findall(cell_pattern, row, re.DOTALL)
            
            # Process each cell
            for col_idx, cell in enumerate(cells):
                if row_idx == 0:  # Skip header row as we'll use it for each data row
                    continue
                    
                # Add header
                header = headers[col_idx] if col_idx < len(headers) else ""
                header_text = self.html2text(header).strip()
                
                # Process cell content
                cell_text = self.html2text(cell).strip()
                
                # Add indentation
                indent = " " * 4 * indent_level
                result.append(f"{indent}{header_text}:")
                
                # Check if cell contains a placeholder
                if cell_text.startswith("<<PLACEHOLDER YOYO"):
                    # Parse nested table
                    nested_table = self.extracted_tables[cell_text]
                    nested_result = self._parse_single_table(nested_table, indent_level + 1)
                    result.append(f"{indent}    [Nested Table]")
                    result.append(nested_result)
                else:
                    result.append(f"{indent}    {cell_text}")

        result.append("-" * 40)
        return "\n".join(result)

    def parse(self, html: str) -> str:
        """Main method to parse HTML with tables into formatted text."""
        # Reset state
        self.table_counter = 0
        self.extracted_tables = {}

        # First extract all tables and replace with placeholders
        processed_html = self._extract_tables(html)

        # Process the main content with html2text
        result = self.html2text(processed_html)

        # Replace all placeholders with their parsed tables
        for placeholder, table in self.extracted_tables.items():
            parsed_table = self._parse_single_table(table)
            result = result.replace(placeholder, parsed_table)

        return result
