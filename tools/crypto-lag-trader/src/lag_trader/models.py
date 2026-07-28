"""収集データの共通レコード型。全取引所のアダプタはこの2型に正規化して返す。"""

from __future__ import annotations

import time
from dataclasses import dataclass


def now_ms() -> int:
    """受信時刻(自マシン、UTC epoch ミリ秒)。ラグ分析はこの値を使う。"""
    return time.time_ns() // 1_000_000


@dataclass(slots=True)
class Quote:
    ts_local: int          # 受信時刻(epoch ms)
    ts_exchange: int | None  # 取引所打刻(epoch ms、なければ None)
    exchange: str
    symbol: str
    bid: float
    ask: float
    bid_qty: float
    ask_qty: float


@dataclass(slots=True)
class Trade:
    ts_local: int
    ts_exchange: int | None
    exchange: str
    symbol: str
    price: float
    qty: float
    side: str              # "buy" | "sell"(テイカー側の方向)
