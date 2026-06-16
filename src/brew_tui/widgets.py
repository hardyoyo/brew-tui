"""Custom widgets for brew-tui."""

from rich.text import Text
from textual.reactive import reactive
from textual.widget import Widget


class GaugeBar(Widget):
    """Horizontal gauge showing a recipe value within a style range."""

    value = reactive(0.0)
    minimum = reactive(0.0)
    maximum = reactive(1.0)

    def render(self) -> Text:
        W = 20
        val, lo, hi = self.value, self.minimum, self.maximum

        if hi <= lo:
            return Text(f"  {'─' * W}  ", style="grey35")

        frac = max(0.0, min(1.0, (val - lo) / (hi - lo)))
        pos = round(frac * (W - 1))

        if val < lo:
            marker = "bold blue"
        elif val > hi:
            marker = "bold red"
        else:
            marker = "bold green"

        parts = []
        for i in range(W):
            if i < pos:
                parts.append(("▓", "grey46"))
            elif i == pos:
                parts.append(("●", marker))
            else:
                parts.append(("░", "grey35"))

        return Text.assemble(*parts)
