"""エントリポイント: python -m lag_trader.collector"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from lag_trader.collector.runner import Collector
from lag_trader.config import load_collector, load_exchanges

CONFIG_DIR = Path("config")


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    exchanges = load_exchanges(CONFIG_DIR / "exchanges.yaml")
    cfg = load_collector(CONFIG_DIR / "strategy.yaml")
    try:
        asyncio.run(Collector(exchanges, cfg).run())
    except KeyboardInterrupt:
        logging.getLogger("collector").info("停止しました")


if __name__ == "__main__":
    main()
