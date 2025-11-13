"""
Core models for django-coreagenda.

This module provides all the core entities for executive meeting management:
- Meeting: Executive meetings
- AgendaItem: Items to be discussed in meetings
- Presenter: Presenters for agenda items
- ActionItem: Tasks arising from meetings
- Minute: Meeting minutes and notes
- AttendanceRecord: Meeting attendance tracking
- ExternalRequest: External party requests for agenda items
"""

from .meeting import Meeting
from .agenda_item import AgendaItem
from .presenter import Presenter
from .action_item import ActionItem
from .minute import Minute
from .attendance import AttendanceRecord
from .external_request import ExternalRequest

__all__ = [
    'Meeting',
    'AgendaItem',
    'Presenter',
    'ActionItem',
    'Minute',
    'AttendanceRecord',
    'ExternalRequest',
]
