"""
Application state management for EOY Cleanup Tool

Contains the AppState class and global state instance.
"""

from typing import List, Optional, Dict
from models import ProviderRow, NewOrderRow, InvalidRow, ReviewCategory


class AppState:
    """Application state management - in-memory session storage"""

    def __init__(self):
        self.wl_rows: List[ProviderRow] = []
        self.no_rows: List[NewOrderRow] = []
        self.invalid_rows: List[InvalidRow] = []  # Invalid/Inactive List providers
        self.categories: List[ReviewCategory] = []
        self.invalid_reasons: set = set()
        self.year: int = 2025
        self.undo_stack: List[Dict] = []
        self.redo_stack: List[Dict] = []
        self.current_category_id: Optional[str] = None
        self.loaded: bool = False

    def to_dict(self):
        """Serialize state for JSON storage"""
        return {
            'wl_rows': [row.to_dict() for row in self.wl_rows],
            'no_rows': [row.to_dict() for row in self.no_rows],
            'invalid_rows': [row.to_dict() for row in self.invalid_rows],
            'categories': [cat.to_dict() for cat in self.categories],
            'invalid_reasons': list(self.invalid_reasons),
            'year': self.year,
            'undo_stack': self.undo_stack[-50:],  # Keep last 50
            'current_category_id': self.current_category_id,
            'loaded': self.loaded
        }

    def clear(self):
        """Reset state to initial values"""
        self.wl_rows = []
        self.no_rows = []
        self.invalid_rows = []
        self.categories = []
        self.invalid_reasons = set()
        self.year = 2025
        self.undo_stack = []
        self.redo_stack = []
        self.current_category_id = None
        self.loaded = False


# Global state instance - imported by other modules
state = AppState()
