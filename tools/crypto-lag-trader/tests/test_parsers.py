import json

from lag_trader.exchanges.binance_global import parse_message, stream_url
from lag_trader.exchanges.bitflyer import parse_channel_message
from lag_trader.models import Quote, Trade


def test_binance_stream_url():
    url = stream_url(["BTCUSDT"])
    assert "btcusdt@bookTicker" in url and "btcusdt@trade" in url


def test_binance_book_ticker():
    raw = json.dumps(
        {
            "stream": "btcusdt@bookTicker",
            "data": {"u": 1, "s": "BTCUSDT", "b": "50000.1", "B": "2.5", "a": "50000.2", "A": "1.0"},
        }
    )
    rec = parse_message(raw)
    assert isinstance(rec, Quote)
    assert rec.bid == 50000.1 and rec.ask == 50000.2
    assert rec.ts_exchange is None
    assert rec.ts_local > 0


def test_binance_trade():
    raw = json.dumps(
        {
            "stream": "btcusdt@trade",
            "data": {
                "e": "trade", "E": 1722140000123, "s": "BTCUSDT", "t": 9,
                "p": "50001.5", "q": "0.01", "T": 1722140000120, "m": True,
            },
        }
    )
    rec = parse_message(raw)
    assert isinstance(rec, Trade)
    assert rec.side == "sell"
    assert rec.ts_exchange == 1722140000120


def test_bitflyer_ticker():
    msg = {
        "timestamp": "2026-07-28T03:04:05.1234567Z",
        "best_bid": 7400000, "best_ask": 7400500,
        "best_bid_size": 0.2, "best_ask_size": 0.1,
    }
    recs = parse_channel_message("lightning_ticker_BTC_JPY", msg)
    assert len(recs) == 1
    q = recs[0]
    assert isinstance(q, Quote)
    assert q.symbol == "BTC_JPY"
    assert q.ts_exchange is not None


def test_bitflyer_executions():
    msg = [
        {"id": 1, "side": "BUY", "price": 7400000, "size": 0.005, "exec_date": "2026-07-28T03:04:05.12Z"},
        {"id": 2, "side": "SELL", "price": 7399999, "size": 0.01, "exec_date": "2026-07-28T03:04:05.13Z"},
    ]
    recs = parse_channel_message("lightning_executions_BTC_JPY", msg)
    assert [r.side for r in recs] == ["buy", "sell"]
    assert all(isinstance(r, Trade) for r in recs)
