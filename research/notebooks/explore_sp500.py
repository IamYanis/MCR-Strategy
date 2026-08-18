import pandas as pd
import matplotlib.pyplot as plt

from src.signals.trend import moving_average_signal
from src.portfolio.backtest import run_backtest
from src.risk.metrics import (
    annualized_return,
    annualized_volatility,
    cagr,
    sharpe_ratio,
    max_drawdown,
)

# Charger les données du S&P 500
sp500 = pd.read_csv(
    "data/raw/sp500.csv",
    parse_dates=["Date"]
)

# Afficher les premières lignes
print(sp500.head())

# Afficher les dimensions du tableau
print("\nDimensions :", sp500.shape)

# Afficher les colonnes
print("\nColonnes :", sp500.columns)

#-----------------------

# Calcul du rendement journalier
sp500["Return"] = sp500["Close"].pct_change()

print("\nPremiers rendements :")
print(sp500[["Date", "Close", "Return"]].head(10))

#-----------------------

sp500["Cumulative"] = (1 + sp500["Return"]).cumprod()

#-----------------------

# Signal de tendance basé sur la moyenne mobile
sp500 = moving_average_signal(sp500, window=200)

print("\nPrix et moyenne mobile 200 jours :")
print(sp500[["Date", "Close", "MA200", "Signal200"]].tail(10))

# Backtest de la stratégie MA200
sp500 = run_backtest(sp500, signal_column="Signal200")

print("\nDernières lignes de la stratégie :")
print(
    sp500[
        [
            "Date",
            "Close",
            "MA200",
            "Signal200",
            "Position",
            "Return",
            "Strategy_Return",
            "Strategy_Cumulative",
        ]
    ].tail(10)
)




#-----------------------
# PERFORMANCE

buy_hold_annual_return = annualized_return(sp500["Return"])
strategy_annual_return = annualized_return(sp500["Strategy_Return"])

buy_hold_volatility = annualized_volatility(sp500["Return"])
strategy_volatility = annualized_volatility(sp500["Strategy_Return"])

buy_hold_cagr = cagr(
    sp500["Cumulative"],
    sp500["Date"]
)

strategy_cagr = cagr(
    sp500["Strategy_Cumulative"],
    sp500["Date"]
)

buy_hold_sharpe = sharpe_ratio(
    sp500["Return"]
)

strategy_sharpe = sharpe_ratio(
    sp500["Strategy_Return"]
)

print("\n--- PERFORMANCE ---")

print(f"Buy & Hold - rendement annualisé : {buy_hold_annual_return:.2%}")
print(f"MA200      - rendement annualisé : {strategy_annual_return:.2%}")

print(f"\nBuy & Hold - volatilité : {buy_hold_volatility:.2%}")
print(f"MA200      - volatilité : {strategy_volatility:.2%}")

print(f"\nBuy & Hold - CAGR : {buy_hold_cagr:.2%}")
print(f"MA200      - CAGR : {strategy_cagr:.2%}")

print(f"\nBuy & Hold - Sharpe : {buy_hold_sharpe:.2f}")
print(f"MA200      - Sharpe : {strategy_sharpe:.2f}")


#-----------------------
# MAX DRAWDOWN

buy_hold_max_drawdown = max_drawdown(
    sp500["Cumulative"]
)

strategy_max_drawdown = max_drawdown(
    sp500["Strategy_Cumulative"]
)

print("\n--- MAX DRAWDOWN ---")

print(f"Buy & Hold : {buy_hold_max_drawdown:.2%}")
print(f"MA200      : {strategy_max_drawdown:.2%}")

#-----------------------

plt.figure(figsize=(12, 6))

plt.plot(sp500["Date"], sp500["Close"], label="S&P 500")
plt.plot(sp500["Date"], sp500["MA200"], label="Moyenne mobile 200 jours")

plt.title("S&P 500 et moyenne mobile 200 jours")
plt.xlabel("Date")
plt.ylabel("Niveau de l'indice")
plt.legend()

#plt.show()

#-----------------------

plt.figure(figsize=(12, 6))

plt.plot(
    sp500["Date"],
    sp500["Cumulative"],
    label="Buy & Hold"
)

plt.plot(
    sp500["Date"],
    sp500["Strategy_Cumulative"],
    label="MA200 Strategy"
)

plt.title("MA200 Strategy vs Buy & Hold")
plt.xlabel("Date")
plt.ylabel("Valeur de 1 unité investie")
plt.legend()


plt.show()