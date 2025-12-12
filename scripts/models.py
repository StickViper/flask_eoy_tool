"""
Data models for EOY Cleanup Tool

Dataclasses representing rows from Google Sheets and review categories.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict


@dataclass
class ProviderRow:
    """Single row from Working List"""
    row_num: int
    practice: str
    phone: str
    address: str
    city: str
    state: str
    zip: str
    qty_2023: str
    qty_2024: str
    qty_2025: str
    status: str
    notes: str
    bg_color: str

    # Validation results
    issues: List[Dict] = field(default_factory=list)
    matched_no_row: Optional[int] = None
    match_confidence: float = 0.0
    duplicate_group_id: Optional[int] = None
    network_name: Optional[str] = None

    # User decisions
    action: Optional[str] = None
    field_edits: Dict[str, str] = field(default_factory=dict)

    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'row_num': self.row_num,
            'practice': self.practice,
            'phone': self.phone,
            'address': self.address,
            'city': self.city,
            'state': self.state,
            'zip': self.zip,
            'qty_2023': self.qty_2023,
            'qty_2024': self.qty_2024,
            'qty_2025': self.qty_2025,
            'status': self.status,
            'notes': self.notes,
            'bg_color': self.bg_color,
            'issues': self.issues,
            'matched_no_row': self.matched_no_row,
            'match_confidence': self.match_confidence,
            'duplicate_group_id': self.duplicate_group_id,
            'network_name': self.network_name,
            'action': self.action,
            'field_edits': self.field_edits
        }


@dataclass
class NewOrderRow:
    """Single row from New Orders"""
    row_num: int
    practice: str
    address: str
    city: str
    state: str
    zip: str
    qty_2025: str

    matched_wl_rows: List[int] = field(default_factory=list)
    is_orphan: bool = False

    def to_dict(self):
        return {
            'row_num': self.row_num,
            'practice': self.practice,
            'address': self.address,
            'city': self.city,
            'state': self.state,
            'zip': self.zip,
            'qty_2025': self.qty_2025,
            'matched_wl_rows': self.matched_wl_rows,
            'is_orphan': self.is_orphan
        }


@dataclass
class InvalidRow:
    """Single row from Invalid/Inactive List"""
    row_num: int
    practice: str
    phone: str
    address: str
    city: str
    state: str
    reason: str  # Why they're invalid

    def to_dict(self):
        return {
            'row_num': self.row_num,
            'practice': self.practice,
            'phone': self.phone,
            'address': self.address,
            'city': self.city,
            'state': self.state,
            'reason': self.reason
        }


@dataclass
class ReviewCategory:
    """Group of issues for review"""
    id: str
    name: str
    description: str
    row_nums: List[int]
    allow_batch: bool
    primary_action: Optional[str] = None
    secondary_actions: List[str] = field(default_factory=list)

    @property
    def row_count(self) -> int:
        """Number of rows in this category"""
        return len(self.row_nums)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'row_count': len(self.row_nums),
            'row_nums': self.row_nums,
            'allow_batch': self.allow_batch,
            'primary_action': self.primary_action,
            'secondary_actions': self.secondary_actions
        }
