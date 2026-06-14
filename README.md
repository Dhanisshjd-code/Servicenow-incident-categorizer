# ServiceNow Incident Categorizer & Reporting Tool

This Python automation script parses unstructured ServiceNow incident exports to automatically extract tool categories and subcategories for operational reporting and analytics.

## Features
- **Dynamic File Ingestion:** Automatically finds and processes the newest raw data export (`raw_*.xlsx`) in the directory.
- **Regex Text Extraction:** Uses regular expressions to parse out structured `[Category/Subcategory]` tags.
- **Reporting Ready:** Inserts structured data right next to the incident descriptions, making it instantly ready for Excel Pivot Tables or PowerBI dashboards.

## Technologies Used
- Python 3.x
- Pandas
- Openpyxl
- Regex (re)
