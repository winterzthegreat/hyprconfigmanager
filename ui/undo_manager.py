"""
Undo/Redo manager for the Hyprland Config Manager.
"""

from typing import Callable


class UndoManager:
    """
    Tracks a stack of reversible operations.
    Each entry is (description, undo_fn, redo_fn).
    """

    MAX_HISTORY = 50

    def __init__(self):
        self._stack: list[tuple[str, Callable, Callable]] = []
        self._index: int = -1  # points to the last applied action
        self._on_change_callbacks: list[Callable] = []

    # ── Public API ────────────────────────────────────────────────────────────

    def push(self, description: str, undo_fn: Callable, redo_fn: Callable):
        """Record a new action. Clears any undone future actions."""
        # Discard anything after current index
        self._stack = self._stack[: self._index + 1]
        self._stack.append((description, undo_fn, redo_fn))
        # Trim to max history
        if len(self._stack) > self.MAX_HISTORY:
            self._stack = self._stack[-self.MAX_HISTORY :]
        self._index = len(self._stack) - 1
        self._notify()

    def undo(self):
        """Undo the last action."""
        if not self.can_undo:
            return
        desc, undo_fn, redo_fn = self._stack[self._index]
        self._index -= 1
        undo_fn()
        self._notify()
        return desc

    def redo(self):
        """Redo the next undone action."""
        if not self.can_redo:
            return
        self._index += 1
        desc, undo_fn, redo_fn = self._stack[self._index]
        redo_fn()
        self._notify()
        return desc

    @property
    def can_undo(self) -> bool:
        return self._index >= 0

    @property
    def can_redo(self) -> bool:
        return self._index < len(self._stack) - 1

    @property
    def undo_description(self) -> str:
        if not self.can_undo:
            return ""
        return self._stack[self._index][0]

    @property
    def redo_description(self) -> str:
        if not self.can_redo:
            return ""
        return self._stack[self._index + 1][0]

    def connect_changed(self, callback: Callable):
        """Register a callback to be called whenever the stack changes."""
        self._on_change_callbacks.append(callback)

    def _notify(self):
        for cb in self._on_change_callbacks:
            cb()
