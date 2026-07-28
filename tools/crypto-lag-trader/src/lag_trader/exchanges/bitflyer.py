"""bitFlyer Lightning Realtime API(JSON-RPC 2.0 over WebSocket)。

lightning_ticker_<SYMBOL>(最良気配)と lightning_executions_<SYMBOL>(約定)を購読する。
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from datetime import datetime, timezone

import websockets

from lag_trader.exchanges.base import ExchangeAdapter
from lag_trader.models import Quote, Trade, now_ms

WS_URL = "wss://ws.lightstream.bitflyer.com/json-rpc"


def _iso_to_ms(iso: str) -> int | None:
    # 例: "2026-07-28T03:04:05.1234567Z"(小数7桁のことがあるため6桁に丸める)
    try:
        head, _, frac = iso.rstrip("Z").partition(".")
        frac = (frac + "000000")[:6]
        dt = datetime.fromisoformat(f"{head}.{frac}").replace(tzinfo=timezone.utc)
        return int(dt.timestamp() * 1000)
    except ValueError:
        return None


def parse_channel_message(
    channel: str, message: dict | list, exchange: str = "bitflyer"
) -> list[Quote | Trade]:
    ts = now_ms()
    if channel.startswith("lightning_ticker_"):
        symbol = channel.removeprefix("lightning_ticker_")
        m = message
        return [
            Quote(
                ts_local=ts,
                ts_exchange=_iso_to_ms(m["timestamp"]),
                exchange=exchange,
                symbol=symbol,
                bid=float(m["best_bid"]),
                ask=float(m["best_ask"]),
                bid_qty=float(m["best_bid_size"]),
                ask_qty=float(m["best_ask_size"]),
            )
        ]
    if channel.startswith("lightning_executions_"):
        symbol = channel.removeprefix("lightning_executions_")
        return [
            Trade(
                ts_local=ts,
                ts_exchange=_iso_to_ms(e["exec_date"]),
                exchange=exchange,
                symbol=symbol,
                price=float(e["price"]),
                qty=float(e["size"]),
                side=e["side"].lower() if e.get("side") else "unknown",
            )
            for e in message
        ]
    return []


class BitflyerAdapter(ExchangeAdapter):
    name = "bitflyer"

    async def stream(self) -> AsyncIterator[Quote | Trade]:
        async with websockets.connect(WS_URL, ping_interval=20) as ws:
            for i, symbol in enumerate(self.symbols):
                for j, ch in enumerate((f"lightning_ticker_{symbol}", f"lightning_executions_{symbol}")):
                    await ws.send(
                        json.dumps(
                            {
                                "jsonrpc": "2.0",
                                "method": "subscribe",
                                "params": {"channel": ch},
                                "id": i * 2 + j + 1,
                            }
                        )
                    )
            async for raw in ws:
                msg = json.loads(raw)
                if msg.get("method") != "channelMessage":
                    continue  # subscribe への応答など
                params = msg["params"]
                for rec in parse_channel_message(params["channel"], params["message"], self.name):
                    yield rec
