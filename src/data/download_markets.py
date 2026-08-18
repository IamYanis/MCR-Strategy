import os
import yfinance as yf


MARKETS = {
    "sp500": "^GSPC",
    "nasdaq": "^IXIC",
    "europe": "^STOXX50E",
    "treasuries": "IEF",
    "gold": "GC=F",
    "oil": "CL=F",
    "usd": "DX-Y.NYB",
    "cash_rate": "^IRX",
}


def download_market(name, ticker, start="2000-01-01"):
    print(f"\nTéléchargement de {name} ({ticker})...")

    data = yf.download(
        ticker,
        start=start,
        auto_adjust=False,
        progress=False,
    )

    # yfinance peut retourner des colonnes MultiIndex.
    # Pour un seul ticker, on supprime le niveau ticker.
    if data.columns.nlevels > 1:
        data.columns = data.columns.get_level_values(0)

    data = data.reset_index()

    os.makedirs("data/raw", exist_ok=True)

    path = f"data/raw/{name}.csv"
    data.to_csv(path, index=False)

    print(f"{len(data)} observations sauvegardées dans {path}")


def download_all_markets():
    for name, ticker in MARKETS.items():
        download_market(name, ticker)


if __name__ == "__main__":
    download_all_markets()