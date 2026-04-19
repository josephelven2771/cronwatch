"""Tag-based filtering and grouping of history entries."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict
from cronwatch.history import HistoryEntry


@dataclass
class TagIndex:
    """Maps tags to lists of matching entries."""
    _index: Dict[str, List[HistoryEntry]] = field(default_factory=dict)

    def add(self, entry: HistoryEntry) -> None:
        for tag in entry.tags if hasattr(entry, 'tags') and entry.tags else []:
            self._index.setdefault(tag, []).append(entry)

    def get(self, tag: str) -> List[HistoryEntry]:
        return list(self._index.get(tag, []))

    def all_tags(self) -> List[str]:
        return sorted(self._index.keys())


def tag_entries(entries: List[HistoryEntry], tags: List[str]) -> List[HistoryEntry]:
    """Return entries whose tags overlap with the given tag list."""
    if not tags:
        return list(entries)
    tag_set = set(tags)
    result = []
    for e in entries:
        entry_tags = set(e.tags) if hasattr(e, 'tags') and e.tags else set()
        if entry_tags & tag_set:
            result.append(e)
    return result


def build_tag_index(entries: List[HistoryEntry]) -> TagIndex:
    idx = TagIndex()
    for e in entries:
        idx.add(e)
    return idx


def group_by_tag(entries: List[HistoryEntry]) -> Dict[str, List[HistoryEntry]]:
    """Group entries by each of their tags."""
    groups: Dict[str, List[HistoryEntry]] = {}
    for e in entries:
        for tag in (e.tags if hasattr(e, 'tags') and e.tags else []):
            groups.setdefault(tag, []).append(e)
    return groups
