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


# Charger toutes les données
sp500 = pd.read_csv(
    "data/raw/sp500.csv",
    parse_dates=["Date"]
)

# Rendements journaliers
sp500["Return"] = sp500["Close"].pct_change()


# Horizons de tendance à tester
windows = [200, 250]


# Sous-périodes
periods = {
    "2000-2009": ("2000-01-01", "2009-12-31"),
    "2010-2019": ("2010-01-01", "2019-12-31"),
    "2020-2026": ("2020-01-01", "2026-12-31"),
}


results = []


for window in windows:

    # IMPORTANT :
    # on calcule la moyenne mobile AVANT de découper les périodes.
    # Ainsi, le début d'une période peut utiliser l'historique précédent.
    data = moving_average_signal(
        sp500,
        window=window
    )

    signal_column = f"Signal{window}"

    data = run_backtest(
        data,
        signal_column=signal_column
    )

    for period_name, (start_date, end_date) in periods.items():

        period_data = data[
            (data["Date"] >= start_date)
            & (data["Date"] <= end_date)
        ].copy()


        # Buy & Hold sur cette sous-période
        bh_returns = period_data["Return"]

        bh_annual_return = annualized_return(
            bh_returns
        )

        bh_volatility = annualized_volatility(
            bh_returns
        )

        bh_sharpe = sharpe_ratio(
        bh_returns
        )

        # Performance cumulée Buy & Hold
        bh_cumulative = (1 + bh_returns).cumprod()

        bh_cagr_data = pd.DataFrame({
            "Date": period_data["Date"],
            "Cumulative": bh_cumulative,
        }).dropna()

        bh_period_cagr = cagr(
            bh_cagr_data["Cumulative"]
            / bh_cagr_data["Cumulative"].iloc[0],
            bh_cagr_data["Date"]
        )

        bh_drawdown = max_drawdown(
            bh_cumulative
        )






        annual_return = annualized_return(
            period_data["Strategy_Return"]
        )

        volatility = annualized_volatility(
            period_data["Strategy_Return"]
        )

        # On retire les lignes où la stratégie n'a pas encore
        # de valeur cumulée exploitable
        cagr_data = period_data.dropna(
            subset=["Strategy_Cumulative"]
        )


        period_cagr = cagr(
            cagr_data["Strategy_Cumulative"]
            / cagr_data["Strategy_Cumulative"].iloc[0],
            cagr_data["Date"]
        )

        sharpe = sharpe_ratio(
        period_data["Strategy_Return"]
        )

        drawdown = max_drawdown(
            period_data["Strategy_Cumulative"]
        )

        results.append(
            {
                "Window": window,
                "Period": period_name,

                "BH_CAGR": bh_period_cagr,
                "Strategy_CAGR": period_cagr,

                "BH_Volatility": bh_volatility,
                "Strategy_Volatility": volatility,

                "BH_Sharpe": bh_sharpe,
                "Strategy_Sharpe": sharpe,

                "BH_Max_Drawdown": bh_drawdown,
                "Strategy_Max_Drawdown": drawdown,
            }
        )


results = pd.DataFrame(results)

print("\n--- ROBUSTESSE PAR PERIODE ---")
print(results.to_string(index=False))