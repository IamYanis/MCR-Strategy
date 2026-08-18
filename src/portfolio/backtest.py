def run_backtest(data, signal_column):
    """
    Backtest simple d'une stratégie long / cash.

    signal_column :
        1 = investi
        0 = hors du marché
    """

    data = data.copy()

    # La position du jour dépend du signal de la veille
    data["Position"] = data[signal_column].shift(1)

    # Rendement de la stratégie
    data["Strategy_Return"] = (
        data["Position"] * data["Return"]
    )

    # Performance cumulée
    data["Strategy_Cumulative"] = (
        1 + data["Strategy_Return"]
    ).cumprod()

    return data