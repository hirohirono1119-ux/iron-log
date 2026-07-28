"""YAML 設定の読み込み。"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class ExchangeConfig:
    name: str
    adapter: str
    roles: list[str]
    symbols: list[str]
    fees: dict = field(default_factory=dict)


@dataclass
class CollectorConfig:
    data_dir: Path
    flush_interval_sec: int
    watchdog_stale_sec: int


def load_exchanges(path: Path) -> list[ExchangeConfig]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    return [
        ExchangeConfig(
            name=name,
            adapter=cfg["adapter"],
            roles=list(cfg.get("role", ["watch"])),
            symbols=list(cfg["symbols"]),
            fees=cfg.get("fees", {}),
        )
        for name, cfg in raw["exchanges"].items()
    ]


def load_collector(path: Path) -> CollectorConfig:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    c = raw["collector"]
    return CollectorConfig(
        data_dir=Path(c.get("data_dir", "data")),
        flush_interval_sec=int(c.get("flush_interval_sec", 60)),
        watchdog_stale_sec=int(c.get("watchdog_stale_sec", 30)),
    )
