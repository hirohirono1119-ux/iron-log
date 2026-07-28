"""Collector 本体: アダプタごとの購読タスク + 定期フラッシュ + ウォッチドッグ。

再接続は指数バックオフ(1→2→…→最大60秒)。受信断はログで警告する
(取引の制御に関わるウォッチドッグは Phase 3 の執行プロセス側で実装する)。
"""

from __future__ import annotations

import asyncio
import logging
import time

from lag_trader.collector.writer import TickWriter
from lag_trader.config import CollectorConfig, ExchangeConfig
from lag_trader.exchanges import ADAPTERS

log = logging.getLogger("collector")

BACKOFF_MAX_SEC = 60


class Collector:
    def __init__(self, exchanges: list[ExchangeConfig], cfg: CollectorConfig):
        self.cfg = cfg
        self.writer = TickWriter(cfg.data_dir)
        self.last_recv: dict[str, float] = {}
        self.recv_count: dict[str, int] = {}
        self.adapters = []
        for ex in exchanges:
            cls = ADAPTERS.get(ex.adapter)
            if cls is None:
                log.warning("adapter未実装のためスキップ: %s", ex.name)
                continue
            self.adapters.append(cls(ex.symbols))

    async def run(self) -> None:
        if not self.adapters:
            raise SystemExit("有効なアダプタがありません")
        tasks = [asyncio.create_task(self._subscribe_forever(a)) for a in self.adapters]
        tasks.append(asyncio.create_task(self._flush_forever()))
        tasks.append(asyncio.create_task(self._watchdog_forever()))
        try:
            await asyncio.gather(*tasks)
        finally:
            self.writer.flush()

    async def _subscribe_forever(self, adapter) -> None:
        backoff = 1
        while True:
            try:
                log.info("[%s] 接続開始", adapter.name)
                async for rec in adapter.stream():
                    self.writer.add(rec)
                    self.last_recv[adapter.name] = time.monotonic()
                    self.recv_count[adapter.name] = self.recv_count.get(adapter.name, 0) + 1
                    backoff = 1
                log.warning("[%s] ストリーム終了、再接続します", adapter.name)
            except asyncio.CancelledError:
                raise
            except Exception as e:
                log.warning("[%s] 切断: %r — %d秒後に再接続", adapter.name, e, backoff)
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, BACKOFF_MAX_SEC)

    async def _flush_forever(self) -> None:
        while True:
            await asyncio.sleep(self.cfg.flush_interval_sec)
            n = self.writer.pending_count()
            files = self.writer.flush()
            if files:
                log.info("flush: %d 件 → %d ファイル", n, len(files))

    async def _watchdog_forever(self) -> None:
        interval = max(5, self.cfg.watchdog_stale_sec // 2)
        while True:
            await asyncio.sleep(interval)
            now = time.monotonic()
            counts = ", ".join(f"{k}={v}" for k, v in sorted(self.recv_count.items()))
            log.info("heartbeat: %s", counts or "(受信なし)")
            for adapter in self.adapters:
                last = self.last_recv.get(adapter.name)
                if last is not None and now - last > self.cfg.watchdog_stale_sec:
                    log.warning(
                        "[%s] %d秒以上データ受信なし", adapter.name, int(now - last)
                    )
