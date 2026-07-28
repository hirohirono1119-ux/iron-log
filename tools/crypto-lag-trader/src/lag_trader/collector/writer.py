"""ティックのバッファリングと Parquet 書き出し。

メモリ上のバッファに貯め、flush() で
data/{quotes|trades}/date=YYYY-MM-DD/exchange=<name>/HHMMSS_<uniq>.parquet
に追記する(日付・取引所でパーティション分割、DESIGN.md §5 Phase 1)。
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from lag_trader.models import Quote, Trade

QUOTE_SCHEMA = pa.schema(
    [
        ("ts_local", pa.int64()),
        ("ts_exchange", pa.int64()),
        ("exchange", pa.string()),
        ("symbol", pa.string()),
        ("bid", pa.float64()),
        ("ask", pa.float64()),
        ("bid_qty", pa.float64()),
        ("ask_qty", pa.float64()),
    ]
)

TRADE_SCHEMA = pa.schema(
    [
        ("ts_local", pa.int64()),
        ("ts_exchange", pa.int64()),
        ("exchange", pa.string()),
        ("symbol", pa.string()),
        ("price", pa.float64()),
        ("qty", pa.float64()),
        ("side", pa.string()),
    ]
)


class TickWriter:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        # kind -> exchange -> rows
        self._buf: dict[str, dict[str, list[dict]]] = {
            "quotes": defaultdict(list),
            "trades": defaultdict(list),
        }
        self._seq = 0

    def add(self, rec: Quote | Trade) -> None:
        kind = "quotes" if isinstance(rec, Quote) else "trades"
        self._buf[kind][rec.exchange].append(asdict(rec))

    def pending_count(self) -> int:
        return sum(len(rows) for by_ex in self._buf.values() for rows in by_ex.values())

    def flush(self) -> list[Path]:
        """バッファを Parquet に書き出し、書いたファイルの一覧を返す。"""
        written: list[Path] = []
        now = datetime.now(timezone.utc)
        date = now.strftime("%Y-%m-%d")
        stamp = now.strftime("%H%M%S")
        for kind, schema in (("quotes", QUOTE_SCHEMA), ("trades", TRADE_SCHEMA)):
            by_ex = self._buf[kind]
            for exchange, rows in list(by_ex.items()):
                if not rows:
                    continue
                out_dir = self.data_dir / kind / f"date={date}" / f"exchange={exchange}"
                out_dir.mkdir(parents=True, exist_ok=True)
                self._seq += 1
                path = out_dir / f"{stamp}_{self._seq:06d}.parquet"
                table = pa.Table.from_pylist(rows, schema=schema)
                pq.write_table(table, path, compression="zstd")
                written.append(path)
                by_ex[exchange] = []
        return written
