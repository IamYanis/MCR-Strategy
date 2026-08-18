import pandas as pd

from src.signals.trend import moving_average_buffer_signal
from src.portfolio.dynamic_portfolio import run_dynamic_portfolio
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
    "usd",
]

BUFFERS = [
    0.00,
    0.01,
    0.02,
]

MAX_WEIGHT = 0.30

# Coûts de transaction testés
TRANSACTION_COST_BPS = [
    0,
    5,
    10,
    20,
] #Ici, 10 bps = 0,10 % du montant effectivement tradé.


# -----------------------
# Cash

cash = pd.read_csv(
    "data/raw/cash_rate.csv",
    parse_dates=["Date"]
)

cash["Cash_Rate"] = cash["Close"] / 100

cash["Cash_Return"] = (
    (1 + cash["Cash_Rate"]) ** (1 / 252) - 1
)

cash = cash[
    ["Date", "Cash_Return"]
].copy()


# -----------------------
# Résultats

results = []


for buffer in BUFFERS:

    market_datasets = []

    for market in MARKETS:

        data = pd.read_csv(
            f"data/raw/{market}.csv",
            parse_dates=["Date"]
        )

        # Rendement de l'actif
        data["Return"] = data["Close"].pct_change()

        # Signal MA200 avec buffer
        data = moving_average_buffer_signal(
            data,
            window=200,
            buffer=buffer,
        )

        signal_column = (
            f"Signal200_B{int(buffer * 100)}"
        )

        # Décalage d'un jour pour éviter le look-ahead bias
        data["Position"] = (
            data[signal_column]
            .shift(1)
            .fillna(0)
        )

        # Colonnes nécessaires au portefeuille dynamique
        market_data = data[
            [
                "Date",
                "Return",
                "Position",
            ]
        ].copy()

        market_data = market_data.rename(
            columns={
                "Return": f"{market}_return",
                "Position": f"{market}_signal",
            }
        )

        market_datasets.append(
            market_data
        )


    # -----------------------
    # Fusion sur la période commune

    combined = market_datasets[0]

    for market_data in market_datasets[1:]:

        combined = combined.merge(
            market_data,
            on="Date",
            how="inner",
        )


    # Ajouter le cash
    combined = combined.merge(
        cash,
        on="Date",
        how="left",
    )

    combined["Cash_Return"] = (
        combined["Cash_Return"]
        .ffill()
        .fillna(0)
    )


    # -----------------------
    # Nombre de changements de signal

    signal_columns = [
        f"{market}_signal"
        for market in MARKETS
    ]

    signal_change_matrix = (
        combined[signal_columns]
        .diff()
        .abs()
        .fillna(0)
    )

    total_signal_changes = (
        signal_change_matrix.sum().sum()
    )

    days_with_change = (
        signal_change_matrix.sum(axis=1) > 0
    ).sum()


    # -----------------------
    # Portefeuille dynamique

    portfolio = run_dynamic_portfolio(
        data=combined,
        markets=MARKETS,
        max_weight=MAX_WEIGHT,
    )

    # -----------------------
    # Turnover

    daily_turnover = (
        portfolio["Turnover"].mean()
    )

    annual_turnover = (
        daily_turnover * 252
    )


    # -----------------------
    # Performance avec différents coûts de transaction

    for cost_bps in TRANSACTION_COST_BPS:

        cost_rate = cost_bps / 10000

        # Coût payé uniquement lorsque le portefeuille trade
        portfolio["Transaction_Cost"] = (
            portfolio["Turnover"]
            * cost_rate
        )

        portfolio["Net_Return"] = (
            portfolio["Portfolio_Return"]
            - portfolio["Transaction_Cost"]
        )

        portfolio["Net_Cumulative"] = (
            1 + portfolio["Net_Return"]
        ).cumprod()


        # -----------------------
        # Métriques nettes

        portfolio_cagr = cagr(
            portfolio["Net_Cumulative"],
            portfolio["Date"],
        )

        volatility = annualized_volatility(
            portfolio["Net_Return"]
        )

        sharpe = sharpe_ratio(
            portfolio["Net_Return"]
        )

        drawdown = max_drawdown(
            portfolio["Net_Cumulative"]
        )


        # -----------------------
        # Stocker les résultats

        results.append(
            {
                "Buffer": buffer,
                "Cost_bps": cost_bps,
                "CAGR": portfolio_cagr,
                "Volatility": volatility,
                "Sharpe": sharpe,
                "Max_Drawdown": drawdown,
                "Signal_Changes": total_signal_changes,
                "Days_With_Change": days_with_change,
                "Daily_Turnover": daily_turnover,
                "Annual_Turnover": annual_turnover,
            }
        )


results = pd.DataFrame(results)


# -----------------------
# Affichage

print("\n--- BUFFER MA200 + PORTEFEUILLE DYNAMIQUE ---")

print(
    results.to_string(
        index=False,
        formatters={
            "Buffer": "{:.0%}".format,
            "CAGR": "{:.2%}".format,
            "Volatility": "{:.2%}".format,
            "Sharpe": "{:.2f}".format,
            "Max_Drawdown": "{:.2%}".format,
            "Signal_Changes": "{:.0f}".format,
            "Days_With_Change": "{:.0f}".format,
            "Daily_Turnover": "{:.4%}".format,
            "Annual_Turnover": "{:.2%}".format,
            "Cost_bps": "{:.0f}".format,
        }
    )
)