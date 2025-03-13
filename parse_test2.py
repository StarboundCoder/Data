import re
from typing import List, Tuple, Dict
from bs4 import BeautifulSoup

class HTMLTableParser:
    def __init__(self, html2text_func):
        self.html2text = html2text_func
        self.table_counter = 0
        self.extracted_tables = {}

    def _generate_placeholder(self) -> str:
        """Generate a unique placeholder for a table."""
        self.table_counter += 1
        return f"$$PLACEHOLDER YOYO Table {self.table_counter}$$"

    def _extract_tables(self, html: str) -> str:
        """Extract all tables from HTML and replace with placeholders using BeautifulSoup."""
        from bs4 import BeautifulSoup
        
        # Parse HTML with BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        
        # Find all outermost tables (tables that are not nested within other tables)
        outermost_tables = []
        for table in soup.find_all('table'):
            if not table.find_parent('table'):
                outermost_tables.append(table)
        
        # Replace tables with placeholders
        result = str(soup)
        for table in reversed(outermost_tables):
            # Get the original HTML string of the table
            table_html = str(table)
            
            # Generate and store placeholder
            placeholder = self._generate_placeholder()
            self.extracted_tables[placeholder] = table_html
            
            # Replace the table with its placeholder
            table.replace_with(placeholder)
            
        return str(soup)

    def _parse_single_table(self, table_html: str, indent_level: int = 0) -> str:
        """Parse a single table, handling nested tables if present."""
        # First, extract any nested tables from cells
        processed_html = self._extract_tables(table_html)

        # Parse with BeautifulSoup
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(processed_html, 'html.parser')
        
        # Extract rows using BeautifulSoup instead of regex
        rows = soup.find_all('tr')
        if not rows:
            return ""

        # Extract headers from first row (both th and td elements)
        headers = []
        first_row = rows[0]
        for cell in first_row.find_all(['th', 'td']):
            headers.append(cell.decode_contents())  # Get inner HTML content

        # Process data rows
        result = []
        result.append("-" * 40)

        # Process each data row (skip header row)
        for row in rows[1:]:
            # Extract cells using BeautifulSoup instead of regex
            cells = row.find_all(['th', 'td'])
            
            # Process each cell
            for col_idx, cell in enumerate(cells):
                # Add header
                header = headers[col_idx] if col_idx < len(headers) else ""
                header_text = self.html2text(header).strip()
                
                # Process cell content
                cell_content = cell.decode_contents()  # Get inner HTML content
                cell_text = self.html2text(cell_content).strip()
                
                # Add indentation
                indent = " " * 4 * indent_level
                result.append(f"{indent}{header_text}:")
                
                # Check if cell contains a placeholder
                if cell_text.startswith("$$PLACEHOLDER YOYO"):
                    # Parse nested table
                    nested_table = self.extracted_tables[cell_text.strip()]
                    nested_result = self._parse_single_table(nested_table, indent_level + 1)
                    result.append(f"{indent}    [Nested Table]")
                    result.append(nested_result)
                else:
                    result.append(f"{indent}    {cell_text}")

        result.append("-" * 40)
        return "\n".join(result)

    def parse(self, html: str) -> str:
        """Main method to parse HTML with tables into formatted text."""
        if not html:
            return ""
            
        try:
            # Reset state
            self.table_counter = 0
            self.extracted_tables = {}

            # First extract all tables and replace with placeholders
            processed_html = self._extract_tables(html)

            # Process the main content with html2text
            result = self.html2text(processed_html)

            # Create a copy of the dictionary items to avoid modification during iteration
            tables_to_process = list(self.extracted_tables.items())

            # Replace all placeholders with their parsed tables
            for placeholder, table in tables_to_process:
                parsed_table = self._parse_single_table(table)
                result = result.replace(placeholder, parsed_table)

            return result
            
        except Exception as e:
            raise ValueError(f"Failed to parse HTML: {str(e)}")
