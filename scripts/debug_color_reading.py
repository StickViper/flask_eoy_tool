"""Debug color reading issue"""

import gspread
from gspread_formatting import get_effective_format
from oauth2client.service_account import ServiceAccountCredentials

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
gc = gspread.authorize(creds)
sh = gc.open('OBGYN List 2025 - Use This List!')

wl = sh.worksheet('Working List 2025')

# Get ALL data first
all_data = wl.get_all_values()
print(f'Total rows in sheet (including header): {len(all_data)}')
print(f'Data rows: {len(all_data) - 1}')

# Sample first 10 rows to see structure
print('\nFirst 10 data rows:')
for i in range(1, min(11, len(all_data))):
    row = all_data[i]
    practice = row[0] if len(row) > 0 else ''
    status = row[9] if len(row) > 9 else ''
    print(f'  Row {i+1}: {practice[:30]:<30} | Status: {status}')

# Now test color reading on a SAMPLE (to avoid rate limits)
print('\nTesting color reading on rows 2-52 (every 5th row):')
for row_num in range(2, 52, 5):
    try:
        fmt = get_effective_format(wl, f'A{row_num}')
        if fmt and hasattr(fmt, 'backgroundColor'):
            bg = fmt.backgroundColor
            if hasattr(bg, 'red'):
                r = int(bg.red * 255) if bg.red else 0
                g = int(bg.green * 255) if bg.green else 0
                b = int(bg.blue * 255) if bg.blue else 0
                hex_color = f'#{r:02x}{g:02x}{b:02x}'
                practice = all_data[row_num-1][0] if len(all_data[row_num-1]) > 0 else ''
                print(f'  Row {row_num}: {hex_color} | {practice[:40]}')
            else:
                print(f'  Row {row_num}: No RGB values')
        else:
            print(f'  Row {row_num}: No format/backgroundColor')
    except Exception as e:
        print(f'  Row {row_num}: Error - {e}')
