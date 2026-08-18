import pandas as pd

from src.signals.trend import moving_average_signal
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

# -----------------------
# Rendement du cash

cash = pd.read_csv(
    "data/raw/cash_rate.csv",
    parse_dates=["Date"]
)

# ^IRX est exprimé comme un taux annuel en pourcentage.
# Exemple : 5.25 signifie environ 5.25 % par an.
cash["Cash_Rate"] = cash["Close"] / 100

# Conversion du taux annuel en rendement journalier
cash["Cash_Return"] = (
    (1 + cash["Cash_Rate"]) ** (1 / 252) - 1
)

cash = cash[
    ["Date", "Cash_Return"]
].copy()

#------------------------


all_returns = []
all_trend_returns = []
all_signals = []


for market in MARKETS:

    data = pd.read_csv(
        f"data/raw/{market}.csv",
        parse_dates=["Date"]
    )

    data["Return"] = data["Close"].pct_change()

    # Signal MA200
    data = moving_average_signal(
        data,
        window=200
    )

    # Position du lendemain
    data["Position"] = data["Signal200"].shift(1)

    data["Position"] = data["Position"].fillna(0)


    # Conserver la position de chaque marché
    market_position = data[
        ["Date", "Position"]
    ].copy()

    market_position = market_position.rename(
        columns={"Position": market}
    )

    all_signals.append(market_position)

    # Rendement avec filtre de tendance
    # Ajouter le rendement du cash
    data = data.merge(
        cash,
        on="Date",
        how="left"
    )

    # Certains jours peuvent ne pas avoir de cotation ^IRX.
    # On propage donc le dernier taux connu.
    data["Cash_Return"] = (
        data["Cash_Return"].ffill().fillna(0)
    )

    # Si MA200 = 1 : rendement de l'actif
    # Si MA200 = 0 : rendement du cash
    data["Trend_Return"] = (
        data["Position"] * data["Return"]
        + (1 - data["Position"]) * data["Cash_Return"]
    )

    # On conserve uniquement Date + rendement
    market_returns = data[
        ["Date", "Return"]
    ].copy()

    market_returns = market_returns.rename(
        columns={"Return": market}
    )

    trend_returns = data[
        ["Date", "Trend_Return"]
    ].copy()

    trend_returns = trend_returns.rename(
        columns={"Trend_Return": market}
    )

    all_returns.append(market_returns)
    all_trend_returns.append(trend_returns)


# -----------------------
# Fusionner les marchés

bh = all_returns[0]
trend = all_trend_returns[0]

signals = all_signals[0]

for market_data in all_returns[1:]:
    bh = bh.merge(
        market_data,
        on="Date",
        how="inner"
    )

for market_data in all_trend_returns[1:]:
    trend = trend.merge(
        market_data,
        on="Date",
        how="inner"
    )


for signal_data in all_signals[1:]:
    signals = signals.merge(
        signal_data,
        on="Date",
        how="inner"
    )

# -----------------------
# DIAGNOSTIC DES CHANGEMENTS DE SIGNAL

print("\n--- CHANGEMENTS DE SIGNAL MA200 ---")

years = (
    signals["Date"].max() - signals["Date"].min()
).days / 365.25

total_signal_changes = 0

for market in MARKETS:

    # 1 lorsqu'un signal change par rapport au jour précédent
    changes = signals[market].diff().abs()

    number_of_changes = (
        changes.fillna(0) > 0
    ).sum()

    changes_per_year = (
        number_of_changes / years
    )

    total_signal_changes += number_of_changes

    print(
        f"{market:12s} : "
        f"{number_of_changes:4d} changements "
        f"({changes_per_year:.2f}/an)"
    )


# Nombre de jours où au moins un marché change de signal
signal_change_matrix = (
    signals[MARKETS]
    .diff()
    .abs()
    .fillna(0)
)

days_with_change = (
    signal_change_matrix.sum(axis=1) > 0
).sum()

days_per_year_with_change = (
    days_with_change / years
)

print(
    f"\nTotal des changements individuels : "
    f"{total_signal_changes}"
)

print(
    f"Jours avec au moins un changement : "
    f"{days_with_change}"
)

print(
    f"Jours de trading liés aux signaux / an : "
    f"{days_per_year_with_change:.2f}"
)

# -----------------------
# Portefeuille équipondéré

bh["Portfolio_Return"] = (
    bh[MARKETS].mean(axis=1)
)

trend["Portfolio_Return"] = (
    trend[MARKETS].mean(axis=1)
)


# -----------------------
# Portefeuille Trend avec redistribution

# On aligne les rendements et les signaux sur les mêmes dates
redistributed = bh.merge(
    signals,
    on="Date",
    suffixes=("_return", "_signal")
)

# Nombre de marchés actifs chaque jour
signal_columns = [
    f"{market}_signal"
    for market in MARKETS
]

redistributed["Active_Count"] = (
    redistributed[signal_columns].sum(axis=1)
)

# Évite une division par zéro lorsqu'aucun marché n'est actif
active_count = redistributed["Active_Count"].where(
    redistributed["Active_Count"] != 0
)

# Rendement quotidien du portefeuille redistribué
redistributed["Portfolio_Return"] = 0.0

for market in MARKETS:

    return_column = f"{market}_return"
    signal_column = f"{market}_signal"

    redistributed["Portfolio_Return"] += (
        redistributed[return_column]
        * redistributed[signal_column]
        / active_count
    )


# -----------------------
# Analyse de concentration

print("\n--- CONCENTRATION DU PORTEFEUILLE REDISTRIBUÉ ---")

print(
    f"Nombre moyen d'actifs actifs : "
    f"{redistributed['Active_Count'].mean():.2f}"
)

print(
    f"Nombre minimum d'actifs actifs : "
    f"{redistributed['Active_Count'].min():.0f}"
)

print(
    f"Nombre maximum d'actifs actifs : "
    f"{redistributed['Active_Count'].max():.0f}"
)

for n in range(len(MARKETS) + 1):

    frequency = (
        redistributed["Active_Count"].eq(n).mean()
    )

    print(
        f"{n} actif(s) actif(s) : "
        f"{frequency:.2%} des jours"
    )


redistributed["Max_Weight"] = (
    1 / redistributed["Active_Count"].where(
        redistributed["Active_Count"] != 0
    )
)

print(
    f"\nPoids maximal moyen : "
    f"{redistributed['Max_Weight'].mean():.2%}"
)

print(
    f"Poids maximal observé : "
    f"{redistributed['Max_Weight'].max():.2%}"
)


# Si aucun marché n'est actif, le portefeuille est 100 % cash
redistributed = redistributed.merge(
    cash,
    on="Date",
    how="left"
)

redistributed["Cash_Return"] = (
    redistributed["Cash_Return"].ffill().fillna(0)
)

redistributed["Portfolio_Return"] = (
    redistributed["Portfolio_Return"].fillna(
        redistributed["Cash_Return"]
    )
)



# -----------------------
# Robustesse du plafond de concentration

CAP_LEVELS = [0.30, 0.40, 0.50]

cap_results = []

for max_weight in CAP_LEVELS:

    capped = redistributed.copy()

    capped["Portfolio_Return_Capped"] = 0.0

    # Poids équipondéré entre les actifs actifs
    equal_weight = (
        1 / capped["Active_Count"].where(
            capped["Active_Count"] != 0
        )
    )

    # Plafond appliqué à chaque actif
    market_weight = equal_weight.clip(
        upper=max_weight
    )

    for market in MARKETS:

        return_column = f"{market}_return"
        signal_column = f"{market}_signal"

        capped["Portfolio_Return_Capped"] += (
            capped[return_column]
            * capped[signal_column]
            * market_weight
        )

    # Poids total investi dans les actifs
    capped["Invested_Weight"] = (
        capped["Active_Count"] * market_weight
    ).fillna(0)

    # Le reste est placé en cash
    capped["Cash_Weight"] = (
        1 - capped["Invested_Weight"]
    )

    capped["Portfolio_Return_Capped"] += (
        capped["Cash_Weight"]
        * capped["Cash_Return"]
    )


    # -----------------------
    # TURNOVER DU PORTEFEUILLE CAPPED

    for market in MARKETS:

        signal_column = f"{market}_signal"

        capped[f"{market}_weight"] = (
            capped[signal_column]
            * market_weight
        )

    # Colonnes contenant les poids des actifs
    weight_columns = [
        f"{market}_weight"
        for market in MARKETS
    ]

    # On inclut également le cash
    weight_columns.append("Cash_Weight")

    # Variation absolue des poids entre deux jours
    weight_changes = (
        capped[weight_columns]
        .diff()
        .abs()
    )

    # Turnover quotidien
    capped["Turnover"] = (
        weight_changes.sum(axis=1) / 2
    )

    average_daily_turnover = (
        capped["Turnover"].mean()
    )

    annual_turnover = (
        average_daily_turnover * 252
    )



    # Performance cumulée
    capped["Cumulative"] = (
        1 + capped["Portfolio_Return_Capped"]
    ).cumprod()

    cap_cagr = cagr(
        capped["Cumulative"],
        capped["Date"]
    )

    cap_volatility = annualized_volatility(
        capped["Portfolio_Return_Capped"]
    )

    cap_sharpe = sharpe_ratio(
        capped["Portfolio_Return_Capped"]
    )

    cap_drawdown = max_drawdown(
        capped["Cumulative"]
    )

    cap_results.append(
        {
            "Cap": max_weight,
            "CAGR": cap_cagr,
            "Volatility": cap_volatility,
            "Sharpe": cap_sharpe,
            "Max_Drawdown": cap_drawdown,
            "Average_Invested": capped["Invested_Weight"].mean(),
            "Average_Cash": capped["Cash_Weight"].mean(),
            "Daily_Turnover": average_daily_turnover,
            "Annual_Turnover": annual_turnover,
        }
    )

cap_results = pd.DataFrame(cap_results)

# -----------------------
# TEST DU PORTEFEUILLE DYNAMIQUE

dynamic_results = []

for max_weight in CAP_LEVELS:

    dynamic = run_dynamic_portfolio(
        data=redistributed,
        markets=MARKETS,
        max_weight=max_weight,
    )

    dynamic["Cumulative"] = (
        1 + dynamic["Portfolio_Return"]
    ).cumprod()

    dynamic_cagr = cagr(
        dynamic["Cumulative"],
        dynamic["Date"]
    )

    dynamic_volatility = annualized_volatility(
        dynamic["Portfolio_Return"]
    )

    dynamic_sharpe = sharpe_ratio(
        dynamic["Portfolio_Return"]
    )

    dynamic_drawdown = max_drawdown(
        dynamic["Cumulative"]
    )

    dynamic_daily_turnover = (
        dynamic["Turnover"].mean()
    )

    dynamic_annual_turnover = (
        dynamic_daily_turnover * 252
    )

    dynamic_results.append(
        {
            "Cap": max_weight,
            "CAGR": dynamic_cagr,
            "Volatility": dynamic_volatility,
            "Sharpe": dynamic_sharpe,
            "Max_Drawdown": dynamic_drawdown,
            "Daily_Turnover": dynamic_daily_turnover,
            "Annual_Turnover": dynamic_annual_turnover,
        }
    )

dynamic_results = pd.DataFrame(dynamic_results)


redistributed["Cumulative"] = (
    1 + redistributed["Portfolio_Return"]
).cumprod()

redistributed_cagr = cagr(
    redistributed["Cumulative"],
    redistributed["Date"]
)

redistributed_volatility = annualized_volatility(
    redistributed["Portfolio_Return"]
)

redistributed_sharpe = sharpe_ratio(
    redistributed["Portfolio_Return"]
)

redistributed_drawdown = max_drawdown(
    redistributed["Cumulative"]
)
# -----------------------
# Performance cumulée

bh["Cumulative"] = (
    1 + bh["Portfolio_Return"]
).cumprod()

trend["Cumulative"] = (
    1 + trend["Portfolio_Return"]
).cumprod()


# -----------------------
# Métriques Buy & Hold

bh_cagr = cagr(
    bh["Cumulative"],
    bh["Date"]
)

bh_volatility = annualized_volatility(
    bh["Portfolio_Return"]
)

bh_sharpe = sharpe_ratio(
    bh["Portfolio_Return"]
)

bh_drawdown = max_drawdown(
    bh["Cumulative"]
)




# -----------------------
# Métriques Trend

trend_cagr = cagr(
    trend["Cumulative"],
    trend["Date"]
)

trend_volatility = annualized_volatility(
    trend["Portfolio_Return"]
)

trend_sharpe = sharpe_ratio(
    trend["Portfolio_Return"]
)

trend_drawdown = max_drawdown(
    trend["Cumulative"]
)


# -----------------------
# Résultats

print("\n--- PORTEFEUILLE MULTI-ASSETS ---")

print(f"\nBuy & Hold - CAGR : {bh_cagr:.2%}")
print(f"Trend MA200 - CAGR : {trend_cagr:.2%}")

print(f"\nBuy & Hold - volatilité : {bh_volatility:.2%}")
print(f"Trend MA200 - volatilité : {trend_volatility:.2%}")

print(f"\nBuy & Hold - Sharpe : {bh_sharpe:.2f}")
print(f"Trend MA200 - Sharpe : {trend_sharpe:.2f}")

print(f"\nBuy & Hold - Max Drawdown : {bh_drawdown:.2%}")
print(f"Trend MA200 - Max Drawdown : {trend_drawdown:.2%}")


print(
    f"Trend Redistributed - CAGR : "
    f"{redistributed_cagr:.2%}"
)

print(
    f"Trend Redistributed - volatilité : "
    f"{redistributed_volatility:.2%}"
)

print(
    f"Trend Redistributed - Sharpe : "
    f"{redistributed_sharpe:.2f}"
)

print(
    f"Trend Redistributed - Max Drawdown : "
    f"{redistributed_drawdown:.2%}"
)



print("\n--- ROBUSTESSE DU CAP ---")

print(
    cap_results.to_string(
        index=False,
        formatters={
            "Cap": "{:.0%}".format,
            "CAGR": "{:.2%}".format,
            "Volatility": "{:.2%}".format,
            "Sharpe": "{:.2f}".format,
            "Max_Drawdown": "{:.2%}".format,
            "Average_Invested": "{:.2%}".format,
            "Average_Cash": "{:.2%}".format,
            "Daily_Turnover": "{:.4%}".format,
            "Annual_Turnover": "{:.2%}".format,
        }
    )
)

print(
    f"Poids moyen en cash : "
    f"{capped['Cash_Weight'].mean():.2%}"
)



print("\n--- PORTEFEUILLE DYNAMIQUE ---")

print(
    dynamic_results.to_string(
        index=False,
        formatters={
            "Cap": "{:.0%}".format,
            "CAGR": "{:.2%}".format,
            "Volatility": "{:.2%}".format,
            "Sharpe": "{:.2f}".format,
            "Max_Drawdown": "{:.2%}".format,
            "Daily_Turnover": "{:.4%}".format,
            "Annual_Turnover": "{:.2%}".format,
        }
    )
)