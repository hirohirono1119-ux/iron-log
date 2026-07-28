"""取引所アダプタの共通インターフェース。

各アダプタは WebSocket を購読し、Quote / Trade に正規化して yield する。
メッセージのパースは純関数(parse_*)に分離し、ネットワークなしで単体テストできるようにする。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator

from lag_trader.models import Quote, Trade


class ExchangeAdapter(ABC):
    name: str

    def __init__(self, symbols: list[str]):
        self.symbols = symbols

    @abstractmethod
    def stream(self) -> AsyncIterator[Quote | Trade]:
        """接続し、正規化済みレコードを流し続ける。切断時は例外を投げる(再接続は呼び出し側)。"""
        raise NotImplementedError
