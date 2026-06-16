"""Generate SVG screenshots of brew-tui for documentation.

Usage:
    python scripts/screenshots.py [output-dir]

Outputs SVG files to the given directory (default: docs/images/).
"""

import asyncio
import sys
from pathlib import Path

from brew_tui.app import BrewTUI, MaltAddition, HopAddition


OUTPUT_DIR = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("docs") / "images"


async def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    app = BrewTUI()
    async with app.run_test(headless=True, size=(140, 36)) as pilot:
        await pilot.pause()

        # ── 1. Default recipe state ──────────────────────────────
        app.save_screenshot(
            filename="screenshot-default.svg", path=str(OUTPUT_DIR)
        )

        # ── 2. Recipe with ingredients entered ───────────────────
        app.batch_size_l = 23.0
        app._malt_additions = [
            MaltAddition("Pale 2-Row", 4.5, 2.0, 37.0),
            MaltAddition("Munich", 0.5, 9.0, 35.0),
            MaltAddition("Crystal 60", 0.3, 60.0, 34.0),
        ]
        app._rebuild_malt_ui()
        app._hop_additions = [
            HopAddition("Cascade", 30.0, 5.5, 60.0),
            HopAddition("Citra", 20.0, 13.0, 15.0),
        ]
        app._rebuild_hop_ui()
        app.fg_estimate = 1.012
        app.mash_efficiency_pct = 72.0
        await pilot.pause()

        app.save_screenshot(
            filename="screenshot-recipe.svg", path=str(OUTPUT_DIR)
        )

        # ── 3. Select an IPA style to show gauges ────────────────
        app.style_query = "IPA"
        await pilot.pause()
        lv = app.query_one("#style-list")
        if len(lv.children) > 0:
            lv.focus()
            await pilot.pause()
            lv.action_select_cursor()
            await pilot.pause()

        app.save_screenshot(
            filename="screenshot-style.svg", path=str(OUTPUT_DIR)
        )

        # ── 4. Open inventory wizard ─────────────────────────────
        app.action_open_inventory()
        await pilot.pause()

        app.save_screenshot(
            filename="screenshot-inventory.svg", path=str(OUTPUT_DIR)
        )

    print(f"Screenshots saved to {OUTPUT_DIR}/")


asyncio.run(main())
