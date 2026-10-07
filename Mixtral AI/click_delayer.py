"""
click_delayer.py
═══════════════════════════════════════════════════════════════════
Reusable click-delay event filter to prevent click-through / double-activation.

Problem: A single mouse press+release can open a dropdown AND select the
item underneath because the release event fires after the menu pops up.

Solution: After a MouseButtonPress, block MouseButtonRelease for a short
configurable delay (default 150ms). This consumes the "opening click"
so it never reaches the newly-shown menu items.
"""

import time
from PyQt5.QtCore import QObject, QEvent, QTimer


class ClickDelayerFilter(QObject):
    """
    Event filter that suppresses MouseButtonRelease events for a short
    window after a MouseButtonPress on the watched widget.

    Usage:
        filter = ClickDelayerFilter(delay_ms=150, parent=widget)
        widget.installEventFilter(filter)

    Works on QPushButton, QMenu, QComboBox, QWidgetAction containers, etc.
    """

    def __init__(self, delay_ms: int = 150, parent=None):
        super().__init__(parent)
        self.delay_ms = delay_ms
        self._locked = False
        self._press_time = 0.0

    def _unlock(self):
        self._locked = False

    def eventFilter(self, obj, event):
        # Only care about left-button press/release
        if event.type() == QEvent.MouseButtonPress:
            # Lock immediately on press
            self._locked = True
            self._press_time = time.time()
            # Schedule unlock
            QTimer.singleShot(self.delay_ms, self._unlock)

        elif event.type() == QEvent.MouseButtonRelease and self._locked:
            # Consume the release event while locked
            return True  # Event handled (blocked)

        return super().eventFilter(obj, event)


def install_click_delay(widget, delay_ms: int = 150):
    """
    Convenience helper: create and install a ClickDelayerFilter on a widget.
    Returns the filter instance (kept alive by widget parentage).
    """
    filter_obj = ClickDelayerFilter(delay_ms=delay_ms, parent=widget)
    widget.installEventFilter(filter_obj)
    return filter_obj