import pyarrow.parquet as pq

from lag_trader.collector.writer import TickWriter
from lag_trader.models import Quote, Trade


def test_writer_flush_partitions(tmp_path):
    w = TickWriter(tmp_path)
    w.add(Quote(1000, None, "bitflyer", "BTC_JPY", 7400000, 7400500, 0.2, 0.1))
    w.add(Quote(1001, 999, "binance_global", "BTCUSDT", 50000.1, 50000.2, 2.5, 1.0))
    w.add(Trade(1002, 998, "bitflyer", "BTC_JPY", 7400000, 0.005, "buy"))
    assert w.pending_count() == 3

    files = w.flush()
    assert len(files) == 3  # quotes×2取引所 + trades×1
    assert w.pending_count() == 0
    assert w.flush() == []  # 空バッファでは何も書かない

    quote_files = [f for f in files if "quotes" in str(f)]
    assert any("exchange=bitflyer" in str(f) for f in quote_files)
    assert any("exchange=binance_global" in str(f) for f in quote_files)
    assert all("date=" in str(f) for f in files)

    # ts_exchange の None が nullable int として読み戻せること
    bf = next(f for f in quote_files if "exchange=bitflyer" in str(f))
    table = pq.read_table(bf)
    assert table.num_rows == 1
    assert table.column("ts_exchange").null_count == 1
