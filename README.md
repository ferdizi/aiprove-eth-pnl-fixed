# eth-pnl-fixed — AIProve entry (FluxPulse)

Short-only EMA trend strategy for the frozen ETH 1-min dataset.

## Strategy
Short 1 ETH when EMA(120) < EMA(240) (downtrend), else flat. Never long.
Position changes only on EMA crossovers — 8 trades over 1440 bars.

## Local backtest (fee 0.12%/side, 1 ETH, no leverage)
- Strategy PnL: **+$31.14**, 8 trades, max drawdown $67.72
- Buy-and-hold: -$68.09
- Split-half: first half -$14.74, second half +$55.17

## Files
- `strategy.py` — the strategy + backtest (run `python3 strategy.py`)
- `backtest.py` — strategy comparison harness
- `bars.csv` — the frozen dataset (from AIProveRH/aiprove)
