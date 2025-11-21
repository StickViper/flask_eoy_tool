"""
Sample 50 notes from Working List to show examples of non-standard notes
"""

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from collections import Counter
import re

def get_note_samples():
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
    sh = gc.open('OBGYN List 2025 - Use This List!')
    wl = sh.worksheet('Working List 2025')

    # Get all notes (column K)
    all_data = wl.get_all_values()
    headers = all_data[0]
    notes_col_idx = headers.index('Notes') if 'Notes' in headers else 10

    print("=" * 80)
    print("NOTES ANALYSIS - Working List 2025")
    print("=" * 80)

    # Collect all non-empty notes
    notes = []
    for i, row in enumerate(all_data[1:], 2):  # Skip header
        if len(row) > notes_col_idx and row[notes_col_idx]:
            notes.append({
                'row': i,
                'practice': row[0] if len(row) > 0 else '',
                'notes': row[notes_col_idx],
                'chunks': [c.strip() for c in row[notes_col_idx].split(';') if c.strip()]
            })

    print(f"\nTotal rows with notes: {len(notes)}")
    print(f"Total rows: {len(all_data) - 1}")
    print(f"Percentage with notes: {len(notes) / (len(all_data) - 1) * 100:.1f}%")

    # Analyze note chunks
    all_chunks = []
    for note in notes:
        all_chunks.extend(note['chunks'])

    # Count frequency
    chunk_freq = Counter(all_chunks)

    print(f"\n" + "=" * 80)
    print("COMMON NOTE PATTERNS (top 30)")
    print("=" * 80)
    for chunk, count in chunk_freq.most_common(30):
        print(f"  {count:4d}x  {chunk}")

    # Categorize chunks
    standard_patterns = [
        'not interested',
        'sent',
        ':sent',
        'vm x2',
        'vm x3',
        'vm',
        'network',
        'callback',
    ]

    standard_chunks = []
    non_standard_chunks = []

    for chunk in all_chunks:
        chunk_lower = chunk.lower()
        if any(pattern in chunk_lower for pattern in standard_patterns):
            standard_chunks.append(chunk)
        else:
            non_standard_chunks.append(chunk)

    print(f"\n" + "=" * 80)
    print(f"CHUNK CATEGORIZATION")
    print("=" * 80)
    print(f"  Standard chunks: {len(standard_chunks)} ({len(standard_chunks) / len(all_chunks) * 100:.1f}%)")
    print(f"  Non-standard chunks: {len(non_standard_chunks)} ({len(non_standard_chunks) / len(all_chunks) * 100:.1f}%)")

    # Sample 50 unique non-standard chunks
    unique_non_standard = list(set(non_standard_chunks))
    sample_size = min(50, len(unique_non_standard))

    print(f"\n" + "=" * 80)
    print(f"SAMPLE NON-STANDARD NOTES ({sample_size} unique examples)")
    print("=" * 80)
    for i, chunk in enumerate(unique_non_standard[:sample_size], 1):
        # Show how many times this appears
        count = non_standard_chunks.count(chunk)
        print(f"  {i:2d}. [{count}x] {chunk}")

    # Show full note examples
    print(f"\n" + "=" * 80)
    print(f"FULL NOTE EXAMPLES (showing context)")
    print("=" * 80)

    # Find notes with non-standard chunks
    examples = []
    for note in notes:
        has_non_standard = False
        for chunk in note['chunks']:
            chunk_lower = chunk.lower()
            if not any(pattern in chunk_lower for pattern in standard_patterns):
                has_non_standard = True
                break
        if has_non_standard:
            examples.append(note)

    # Show first 20 examples
    for i, example in enumerate(examples[:20], 1):
        print(f"\n{i}. Row {example['row']}: {example['practice']}")
        print(f"   Full notes: {example['notes']}")
        print(f"   Chunks: {example['chunks']}")

    # Identify potentially clearable notes
    print(f"\n" + "=" * 80)
    print(f"POTENTIALLY CLEARABLE NOTES")
    print("=" * 80)
    print(f"(Notes that might be safe to remove for new year)")

    clearable_patterns = [
        'long wait',
        'voicemail',
        'hold long time',
        'on hold',
        'busy',
        'no answer',
        'callback',
        'call back',
        'call again',
        'try again',
        'receptionist',
        'front desk',
        'Spanish',
        'leave message',
        'left message',
        'message left',
    ]

    clearable_examples = []
    for note in notes:
        for chunk in note['chunks']:
            chunk_lower = chunk.lower()
            if any(pattern in chunk_lower for pattern in clearable_patterns):
                clearable_examples.append({
                    'row': note['row'],
                    'practice': note['practice'],
                    'chunk': chunk,
                    'pattern': next(p for p in clearable_patterns if p in chunk_lower)
                })
                break

    # Group by pattern
    by_pattern = {}
    for ex in clearable_examples:
        pattern = ex['pattern']
        if pattern not in by_pattern:
            by_pattern[pattern] = []
        by_pattern[pattern].append(ex)

    for pattern, examples in sorted(by_pattern.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"\n  Pattern: '{pattern}' ({len(examples)} occurrences)")
        for ex in examples[:3]:  # Show first 3
            print(f"    - Row {ex['row']}: {ex['chunk']}")

if __name__ == '__main__':
    get_note_samples()
