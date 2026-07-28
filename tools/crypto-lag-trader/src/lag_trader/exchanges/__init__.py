"""アダプタのレジストリ。設定の adapter 名 → クラスの対応表。

未実装の取引所(Binance Japan / GMOコイン / bitbank / Coincheck)は
Phase 1 ステップ3でここに追加する。
"""

from lag_trader.exchanges.base import ExchangeAdapter
from lag_trader.exchanges.binance_global import BinanceGlobalAdapter
from lag_trader.exchanges.bitflyer import BitflyerAdapter

ADAPTERS: dict[str, type[ExchangeAdapter]] = {
    BinanceGlobalAdapter.name: BinanceGlobalAdapter,
    BitflyerAdapter.name: BitflyerAdapter,
}
