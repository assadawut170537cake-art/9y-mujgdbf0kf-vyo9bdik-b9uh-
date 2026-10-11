"""
Simplified 2D Emoji Avatar.
Replaces the complex 3D HoloAvatar with a lightweight state-based emoji display.
"""

from __future__ import annotations

from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QPainter, QColor

class HoloAvatar:
    """Animated 2D emoji head. One instance per HUD canvas.

    Lifecycle:
        av = HoloAvatar()
        av.step(dt, amp, speaking=..., muted=...)          # once per tick
        av.paint(painter, cx, cy, r, primary, accent, bg)  # once per frame
    """

    shaded = False

    def __init__(self) -> None:
        self.SPAN = 2.0  # Dummy span to keep caller sizing math intact
        self.current_emoji = "😐"
        self._glow = 0.0

    def step(self, dt: float, amp: float, speaking: bool = False,
             muted: bool = False, state: str = "",
             v_open: float | None = None, v_wide: float = 0.0,
             v_level: float | None = None,
             v_seq: list | None = None, v_hop: float = 0.02) -> None:
        """Advance the animation state."""
        st = (state or "").upper()
        
        # State machine for the emoji
        if st in ("SLEEPING", "STANDBY", "OFFLINE"):
            self.current_emoji = "😴"
        elif st in ("THINKING", "PROCESSING"):
            self.current_emoji = "🤔"
        elif st == "LISTENING":
            self.current_emoji = "👂"
        elif speaking and not muted:
            self.current_emoji = "🗣️"
        else:
            self.current_emoji = "😐"

        # Simple glow smoothing based on amplitude
        amp = max(0.0, min(1.0, float(amp)))
        target_glow = (0.0 if muted else amp)
        self._glow += (target_glow - self._glow) * min(1.0, dt * 10.0)

    def glance(self, dx: float, dy: float, hold: float = 1.1) -> None:
        """Stub for compatibility."""
        pass

    def paint(self, p: QPainter, cx: float, cy: float, r: float,
              primary: QColor, accent: QColor, bg: QColor | None = None) -> None:
        """Draw the emoji centered at (cx, cy)."""
        # Draw a subtle pulsing aura based on audio amplitude
        p.setPen(Qt.PenStyle.NoPen)
        bg_col = QColor(primary)
        bg_col.setAlpha(int(20 + 60 * self._glow))
        p.setBrush(bg_col)
        
        ar = r * (1.0 + 0.3 * self._glow)
        p.drawEllipse(QRectF(cx - ar, cy - ar, ar * 2, ar * 2))
        
        # Draw the emoji text
        font = p.font()
        # Scale emoji font size based on the available radius
        font.setPixelSize(int(r * 1.3))
        p.setFont(font)
        
        # Draw text
        p.setPen(primary)
        p.drawText(QRectF(cx - r, cy - r, r * 2, r * 2), 
                   Qt.AlignmentFlag.AlignCenter, 
                   self.current_emoji)
