"""
Read STATS sheet formulas to understand structure for duplication
"""

import gspread
from oauth2client.service_account import ServiceAccountCredentials

def read_formulas():
    # Authenticate
    scope = [
        'https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/drive'
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name(
        'credentials.json',
        scope
    )
    gc = gspread.authorize(creds)

    # Open sheet
    sh = gc.open('OBGYN List 2025 - Use This List!')
    stats = sh.worksheet('STATS')

    print("=" * 80)
    print("STATS FORMULAS (sample from key cells)")
    print("=" * 80)

    # Read formulas from key cells
    # Row 2, Col C (ORDER SECURED count)
    # Row 3, Col C (NOT INTERESTED count)
    # Row 4, Col C (CALLBACK count)
    # etc.

    cells_to_check = [
        ('C2', 'ORDER SECURED yellow count'),
        ('C3', 'NOT INTERESTED white count'),
        ('C4', 'CALLBACK fuchsia count'),
        ('C5', 'UNCALLED white count'),
        ('C6', 'VERIFY red count'),
        ('K6', 'Hit % formula (if exists)'),
    ]

    for cell_addr, description in cells_to_check:
        try:
            cell = stats.acell(cell_addr, value_render_option='FORMULA')
            print(f"\n{cell_addr} ({description}):")
            print(f"  Formula: {cell.value}")
        except Exception as e:
            print(f"\n{cell_addr} ({description}): Error - {e}")

    # Also check if there are any references to "Working List 2025"
    print("\n" + "=" * 80)
    print("SEARCHING FOR SHEET REFERENCES")
    print("=" * 80)

    all_formulas = stats.get('A1:Z52', value_render_option='FORMULA')
    references = set()

    for row_idx, row in enumerate(all_formulas, 1):
        for col_idx, cell in enumerate(row, 1):
            if cell and isinstance(cell, str):
                if 'Working List 2025' in cell or "'Working List 2025'" in cell:
                    col_letter = chr(64 + col_idx)
                    references.add(f"{col_letter}{row_idx}: {cell[:100]}")

    if references:
        print(f"\nFound {len(references)} cells referencing 'Working List 2025':")
        for ref in sorted(references):
            print(f"  {ref}")
    else:
        print("\nNo direct 'Working List 2025' references found")
        print("(Formulas may use indirect references or named ranges)")

if __name__ == '__main__':
    read_formulas()
