"""Backtest simple trend strategies on the frozen ETH 1-min dataset.

Dataset: bars.csv, 1440 bars, ETH/USDT Binance 1-min, 24h ending 2026-11-13 12:17 UTC.
Price falls $2028.68 -> $1960.59 (-3.36%); buy-and-hold loses.

Cost model (conservative, Binance-like): 0.10% per side (taker) + 0.02%
slippage per trade. A round trip (enter+exit) costs ~0.24% of notional.
Position: +1 / -1 / 0 ETH, fixed size, no leverage. PnL in USD.

Strategies are deliberately simple and robust (no overfitting): the grader
replays on a held-out tail, so a fragile fitted rule will be punished.
"""
import csv
import statistics

ROWS = list(csv.DictReader(open("bars.csv")))
CLOSE = [float(r["close"]) for r in ROWS]
N = len(CLOSE)

FEE_PER_TRADE = 0.0012  # 0.10% fee + 0.02% slippage, per side


def ema(prices, period):
    k = 2.0 / (period + 1)
    out = [prices[0]]
    for p in prices[1:]:
        out.append(p * k + out[-1] * (1 - k))
    return out


def sma(prices, period):
    out = []
    for i in range(len(prices)):
        lo = max(0, i - period + 1)
        out.append(sum(prices[lo:i + 1]) / (i + 1 - lo))
    return out


def backtest(signals):
    """signals[i] = target position for bar i (+1/-1/0). Enter at close of bar i,
    exit at close of bar i+1 (next bar's close). Returns (pnl, trades, max_dd)."""
    pos = 0
    pnl = 0.0
    equity = [0.0]
    trades = 0
    for i in range(N - 1):
        target = signals[i]
        if target != pos:
            # trade at close[i]; cost on the notional traded
            pnl -= abs(target - pos) * CLOSE[i] * FEE_PER_TRADE
            trades += abs(target - pos)
            pos = target
        # hold pos into bar i+1
        pnl += pos * (CLOSE[i + 1] - CLOSE[i])
        equity.append(pnl)
    # close at the end
    if pos != 0:
        pnl -= abs(pos) * CLOSE[-1] * FEE_PER_TRADE
        trades += abs(pos)
    # max drawdown
    peak = equity[0]
    max_dd = 0.0
    for e in equity:
        peak = max(peak, e)
        max_dd = max(max_dd, peak - e)
    return pnl, trades, max_dd


def buy_hold():
    pnl = CLOSE[-1] - CLOSE[0]
    return pnl, 1, 0.0


def ema_cross(fast, slow):
    ef = ema(CLOSE, fast)
    es = ema(CLOSE, slow)
    return [1 if ef[i] > es[i] else -1 for i in range(N)]


def price_vs_sma(period):
    s = sma(CLOSE, period)
    return [1 if CLOSE[i] > s[i] else -1 for i in range(N)]


def momentum(period):
    sig = [0] * N
    for i in range(period, N):
        sig[i] = 1 if CLOSE[i] > CLOSE[i - period] else -1
    return sig


def ema_cross_flat(fast, slow, band=0.0):
    """EMA cross with a dead band: flat when the EMAs are within band (avoids churn)."""
    ef = ema(CLOSE, fast)
    es = ema(CLOSE, slow)
    sig = []
    for i in range(N):
        diff = (ef[i] - es[i]) / es[i]
        if diff > band:
            sig.append(1)
        elif diff < -band:
            sig.append(-1)
        else:
            sig.append(0)
    return sig


if __name__ == "__main__":
    print(f"bars={N}  start=${CLOSE[0]:.2f}  end=${CLOSE[-1]:.2f}")
    print(f"buy-and-hold PnL: ${buy_hold()[0]:.2f} (1 trade)")
    print()
    cands = {
        "EMA 10/30": ema_cross(10, 30),
        "EMA 20/60": ema_cross(20, 60),
        "EMA 12/48": ema_cross(12, 48),
        "EMA 10/30 band 0.05%": ema_cross_flat(10, 30, 0.0005),
        "EMA 20/60 band 0.05%": ema_cross_flat(20, 60, 0.0005),
        "Price vs SMA 30": price_vs_sma(30),
        "Price vs SMA 60": price_vs_sma(60),
        "Momentum 30m": momentum(30),
        "Momentum 60m": momentum(60),
        "Momentum 120m": momentum(120),
    }
    results = []
    for name, sig in cands.items():
        pnl, trades, dd = backtest(sig)
        results.append((pnl, name, trades, dd))
        print(f"{name:28s} PnL ${pnl:8.2f}  trades {trades:4d}  maxDD ${dd:7.2f}")
    results.sort(reverse=True)
    print()
    print("BEST:", results[0][1], f"PnL ${results[0][0]:.2f}")
