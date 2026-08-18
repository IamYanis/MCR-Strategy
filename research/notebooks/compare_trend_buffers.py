import pandas as pd

from src.signals.trend import moving_average_buffer_signal


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


print("\n--- ROBUSTESSE DU BUFFER MA200 ---")

for buffer in BUFFERS:

    print(f"\nBUFFER : {buffer:.0%}")

    total_changes = 0

    for market in MARKETS:

        data = pd.read_csv(
            f"data/raw/{market}.csv",
            parse_dates=["Date"]
        )

        data = moving_average_buffer_signal(
            data,
            window=200,
            buffer=buffer,
        )

        signal_column = (
            f"Signal200_B{int(buffer * 100)}"
        )

        changes = (
            data[signal_column]
            .diff()
            .abs()
            .fillna(0)
            .sum()
        )

        total_changes += changes

        print(
            f"{market:12s}: "
            f"{changes:4.0f} changements"
        )

    print(
        f"TOTAL       : "
        f"{total_changes:.0f} changements"
    )