import yfinance as yf


sp500 = yf.download(
    "^GSPC",
    start="2000-01-01",
    auto_adjust=False,
    multi_level_index=False
)

print(sp500.head())

sp500.to_csv("data/raw/sp500.csv")

print("\nDonnées sauvegardées dans data/raw/sp500.csv")