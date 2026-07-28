# crypto-lag-trader

暗号資産のリード・ラグ追随ツール(自分用)。複数取引所を監視し、値動きに時間差のある市場ペアを検出して、遅行市場側で追随売買する。

**設計書: [docs/DESIGN.md](docs/DESIGN.md)** — 戦略・アーキテクチャ・フェーズ計画・意思決定の記録はすべてここにある。

## 現在のフェーズ

**Phase 1: データ収集(Collector)**

実装済み:
- Binance グローバル(BTC/USDT、watch専用)・bitFlyer(BTC/JPY)の WebSocket 購読
- 最良気配(quotes)と約定(trades)の Parquet 記録(日付・取引所でパーティション)
- 自動再接続(指数バックオフ)、ハートビートログ、受信断の警告

未実装(この順で進める。docs/DESIGN.md §7):
1. 残りの取引所アダプタ: Binance Japan / GMOコイン / bitbank / Coincheck、USD/JPY レート取得
2. 日次サマリメール
3. Windows タスクスケジューラでの常駐化手順書
4. 1週間の連続収集 → Phase 2(ラグ分析)へ

## セットアップ(Windows)

[python.org](https://www.python.org/downloads/) から Python 3.12 以降をインストール後、PowerShell で:

```powershell
git clone <このリポジトリのURL>
cd crypto-lag-trader
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
copy .env.example .env   # 値は Phase 1 では空のままでよい
```

## 実行

```powershell
python -m lag_trader.collector
```

`data/` 配下にティックが1分ごとに書き出される。停止は Ctrl+C。

動作確認(収集したデータを覗く):

```python
import duckdb
duckdb.sql("select exchange, count(*) from 'data/quotes/*/*/*.parquet' group by 1").show()
```

## テスト

```powershell
pytest
```

## 運用上の注意(docs/DESIGN.md §4.1, §8)

- `.env` と `data/` はコミットしない(.gitignore 済み)
- 取引所の APIキーを作るときは**出金権限を付けない**
- 収集マシンはスリープ無効化 + NTP 時刻同期を設定する
