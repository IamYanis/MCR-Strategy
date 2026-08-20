import pandas as pd

from src.signals.trend import moving_average_signal
from src.portfolio.backtest import run_backtest
from src.risk.metrics import (
    annualized_return,
    annualized_volatility,
    cagr,
    sharpe_ratio,
    max_drawdown,
)


# Charger les données
sp500 = pd.read_csv(
    "data/raw/sp500.csv",
    parse_dates=["Date"]
)

# Rendement journalier
sp500["Return"] = sp500["Close"].pct_change()

# Horizons que nous voulons comparer
windows = [50, 100, 150, 200, 250]

# Tableau dans lequel nous stockerons les résultats
results = []


for window in windows:

    # Créer le signal correspondant
    data = moving_average_signal(
        sp500,
        window=window
    )

    signal_column = f"Signal{window}"

    # Backtest
    data = run_backtest(
        data,
        signal_column=signal_column
    )

    # Mesures de performance
    annual_return = annualized_return(
        data["Strategy_Return"]
    )

    volatility = annualized_volatility(
        data["Strategy_Return"]
    )

    strategy_cagr = cagr(
        data["Strategy_Cumulative"],
        data["Date"]
    )

    sharpe = sharpe_ratio(
        data["Strategy_Return"]
    )

    drawdown = max_drawdown(
        data["Strategy_Cumulative"]
    )

    # Stocker les résultats
    results.append(
        {
            "Window": window,
            "CAGR": strategy_cagr,
            "Volatility": volatility,
            "Sharpe": sharpe,
            "Max_Drawdown": drawdown,
        }
    )


# Transformer les résultats en tableau
results = pd.DataFrame(results)

print("\n--- COMPARAISON DES HORIZONS ---")
print(results.to_string(index=False))
