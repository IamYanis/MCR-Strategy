import pandas as pd

from src.signals.trend import moving_average_signal
from src.portfolio.backtest import run_backtest
from src.risk.metrics import (
    annualized_volatility,
    cagr,
    sharpe_ratio,
    max_drawdown,
)


MARKETS = [
    "sp500",
    "nasdaq",
    "europe",
    "treasuries",
    "gold",
    "oil",
    "usd",
]


results = []


for market in MARKETS:

    data = pd.read_csv(
        f"data/raw/{market}.csv",
        parse_dates=["Date"]
    )

    data["Return"] = data["Close"].pct_change()

    data = moving_average_signal(
        data,
        window=200
    )

    data = run_backtest(
        data,
        signal_column="Signal200"
    )

    # Buy & Hold
    data["BH_Cumulative"] = (
        1 + data["Return"]
    ).cumprod()

    bh_cagr = cagr(
        data["BH_Cumulative"].dropna(),
        data.loc[data["BH_Cumulative"].notna(), "Date"]
    )

    bh_volatility = annualized_volatility(
        data["Return"]
    )

    bh_sharpe = sharpe_ratio(
        data["Return"]
    )

    bh_drawdown = max_drawdown(
        data["BH_Cumulative"]
    )

    # MA200
    strategy_cagr = cagr(
        data["Strategy_Cumulative"].dropna(),
        data.loc[data["Strategy_Cumulative"].notna(), "Date"]
    )

    strategy_volatility = annualized_volatility(
        data["Strategy_Return"]
    )

    strategy_sharpe = sharpe_ratio(
        data["Strategy_Return"]
    )

    strategy_drawdown = max_drawdown(
        data["Strategy_Cumulative"]
    )

    results.append(
        {
            "Market": market,
            "BH_CAGR": bh_cagr,
            "MA200_CAGR": strategy_cagr,
            "BH_Volatility": bh_volatility,
            "MA200_Volatility": strategy_volatility,
            "BH_Sharpe": bh_sharpe,
            "MA200_Sharpe": strategy_sharpe,
            "BH_Max_Drawdown": bh_drawdown,
            "MA200_Max_Drawdown": strategy_drawdown,
        }
    )


results = pd.DataFrame(results)

print("\n--- MA200 SUR PLUSIEURS MARCHES ---")
print(results.to_string(index=False))