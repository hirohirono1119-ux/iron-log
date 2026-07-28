"""Binance グローバル(watch専用データソース)。

combined stream で bookTicker(最良気配)と trade(約定)を購読する。
bookTicker にはタイムスタンプが含まれないため ts_exchange は None。
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator

import websockets

from lag_trader.exchanges.base import ExchangeAdapter
from lag_trader.models import Quote, Trade, now_ms

WS_BASE = "wss://stream.binance.com:9443/stream"


def stream_url(symbols: list[str]) -> str:
    streams = "/".join(
        f"{s.lower()}@{ch}" for s in symbols for ch in ("bookTicker", "trade")
    )
    return f"{WS_BASE}?streams={streams}"


def parse_message(raw: str, exchange: str = "binance_global") -> Quote | Trade | None:
    msg = json.loads(raw)
    data = msg.get("data")
    if not data:
        return None
    ts = now_ms()
    if data.get("e") == "trade":
        return Trade(
            ts_local=ts,
            ts_exchange=data.get("T"),
            exchange=exchange,
            symbol=data["s"],
            price=float(data["p"]),
            qty=float(data["q"]),
            side="sell" if data["m"] else "buy",  # m=true は買い板に当たった売り
        )
    if "b" in data and "a" in data:  # bookTicker
        return Quote(
            ts_local=ts,
            ts_exchange=None,
            exchange=exchange,
            symbol=data["s"],
            bid=float(data["b"]),
            ask=float(data["a"]),
            bid_qty=float(data["B"]),
            ask_qty=float(data["A"]),
        )
    return None


class BinanceGlobalAdapter(ExchangeAdapter):
    name = "binance_global"

    async def stream(self) -> AsyncIterator[Quote | Trade]:
        async with websockets.connect(stream_url(self.symbols), ping_interval=20) as ws:
            async for raw in ws:
                rec = parse_message(raw, self.name)
                if rec is not None:
                    yield rec
