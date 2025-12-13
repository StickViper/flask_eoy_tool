"""
Common note patterns for batch handling

Defines patterns for detecting and transforming common call notes.
Used by validation pipeline to categorize rows for batch processing.
"""

import re
from typing import List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class NotePattern:
    """Pattern definition for a common note type"""
    id: str
    regex: re.Pattern
    action: str  # 'remove', 'transform', 'archive_ni'
    description: str
    transform_fn: Optional[callable] = None


# Compile patterns once for efficiency
COMMON_PATTERNS: List[NotePattern] = [
    # === REMOVE patterns (clear these notes) ===
    NotePattern(
        id='ask_for',
        regex=re.compile(r'\bask\s+for\b', re.IGNORECASE),
        action='remove',
        description='Ask for *'
    ),
    NotePattern(
        id='vm',
        regex=re.compile(r'\bvm\b', re.IGNORECASE),
        action='remove',
        description='vm *'
    ),
    NotePattern(
        id='call_back',
        regex=re.compile(r'\bcall\s*back\b', re.IGNORECASE),
        action='remove',
        description='Call back *'
    ),
    NotePattern(
        id='office_closed',
        regex=re.compile(r'\boffice\s+closed\b', re.IGNORECASE),
        action='remove',
        description='Office closed'
    ),
    NotePattern(
        id='impossible_reach',
        regex=re.compile(r'\bimpossible\s+to\s+reach\b', re.IGNORECASE),
        action='remove',
        description='Impossible to reach'
    ),
    NotePattern(
        id='number_out_of_service',
        regex=re.compile(r'\bnumber\s+out\s+of\s+service\b', re.IGNORECASE),
        action='remove',
        description='Number out of service'
    ),
    NotePattern(
        id='updated_number',
        regex=re.compile(r'\bupdated\s*#?\s*try\s+again\b', re.IGNORECASE),
        action='remove',
        description='updated # try again'
    ),
    NotePattern(
        id='gave_my_number',
        regex=re.compile(r'\bgave\s+my\s*#', re.IGNORECASE),
        action='remove',
        description='gave my #'
    ),
    NotePattern(
        id='email_sent',
        regex=re.compile(r'[\w.+-]+@[\w.-]+\s*:\s*sent\b', re.IGNORECASE),
        action='remove',
        description='*@*:sent (email sent)'
    ),

    # === TRANSFORM patterns (change to new format) ===
    NotePattern(
        id='same_network',
        regex=re.compile(r'\bsame\s+network\s*[-–]\s*multiple\s+locations?\b', re.IGNORECASE),
        action='transform',
        description='Same network - multiple locations → network(~N)',
        transform_fn=lambda note, count: f"network(~{count})"
    ),

    # === NOT INTERESTED patterns (archive the reason) ===
    NotePattern(
        id='ni_already',
        regex=re.compile(r'\bnot\s+interested\s*[:\-]?\s*already\s+(\w+)', re.IGNORECASE),
        action='archive_ni',
        description='Not interested: Already X'
    ),
    NotePattern(
        id='ni_dont_do',
        regex=re.compile(r'\bnot\s+interested\s*[:\-]?\s*(don\'?t|not)\s+do(ing)?\s+(\w+)', re.IGNORECASE),
        action='archive_ni',
        description='Not interested: Don\'t do X'
    ),
    NotePattern(
        id='ni_enough',
        regex=re.compile(r'\bnot\s+interested\s*[:\-]?\s*enough\b', re.IGNORECASE),
        action='archive_ni',
        description='Not interested: Enough'
    ),
]


def detect_patterns_in_note(note: str) -> List[Tuple[NotePattern, re.Match]]:
    """Find all matching patterns in a note string.

    Args:
        note: The note text to search

    Returns:
        List of (pattern, match) tuples for each match found
    """
    if not note:
        return []

    matches = []
    for pattern in COMMON_PATTERNS:
        match = pattern.regex.search(note)
        if match:
            matches.append((pattern, match))

    return matches


def split_notes(notes: str) -> List[str]:
    """Split notes by semicolon delimiter.

    Args:
        notes: Notes string, possibly with multiple entries

    Returns:
        List of individual note chunks, stripped of whitespace
    """
    if not notes:
        return []
    return [chunk.strip() for chunk in notes.split(';') if chunk.strip()]


def suggest_semicolon_insertion(notes: str) -> Optional[str]:
    """Check if notes might need semicolons and suggest insertion points.

    Args:
        notes: Notes string to check

    Returns:
        Suggested corrected string with semicolons, or None if no changes needed
    """
    if not notes or ';' in notes:
        return None

    # Keywords that often start new note entries
    markers = [
        r'\bvm\b',
        r'\bcall\s*back\b',
        r'\bnot\s+interested\b',
        r'\bask\s+for\b',
        r'\boffice\s+closed\b',
        r'\bsent\b',
        r'\bupdated\b',
        r'\bgave\b',
    ]

    # Find all marker positions
    positions = []
    for marker in markers:
        for match in re.finditer(marker, notes, re.IGNORECASE):
            positions.append(match.start())

    # If multiple markers found, suggest semicolons before each (except first)
    if len(positions) > 1:
        positions = sorted(set(positions))
        result = []
        last_pos = 0
        for pos in positions[1:]:  # Skip first marker
            result.append(notes[last_pos:pos].strip())
            last_pos = pos
        result.append(notes[last_pos:].strip())
        return '; '.join(result)

    return None


def get_ni_archive_text(pattern_id: str, match: re.Match) -> str:
    """Generate archived NI text from a match.

    Args:
        pattern_id: The pattern that matched
        match: The regex match object

    Returns:
        Formatted archive text like "Last time NI: Already works"
    """
    if pattern_id == 'ni_already':
        reason = match.group(1) if match.groups() else 'unspecified'
        return f"Last time NI: Already {reason}"
    elif pattern_id == 'ni_dont_do':
        procedure = match.group(3) if len(match.groups()) >= 3 else 'procedures'
        return f"Last time NI: No {procedure}"
    elif pattern_id == 'ni_enough':
        return "Last time NI: Enough"
    else:
        return "Last time NI: See notes"


# Summary info for UI
def get_pattern_summary():
    """Get summary of all patterns for display in UI"""
    return {
        'remove': [p for p in COMMON_PATTERNS if p.action == 'remove'],
        'transform': [p for p in COMMON_PATTERNS if p.action == 'transform'],
        'archive_ni': [p for p in COMMON_PATTERNS if p.action == 'archive_ni'],
    }
