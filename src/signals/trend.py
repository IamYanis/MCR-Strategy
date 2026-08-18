def moving_average_signal(data, window=200):
    """
    Crée un signal de tendance basé sur une moyenne mobile.

    Signal = 1 si le prix est au-dessus de la moyenne mobile.
    Signal = 0 sinon.
    """

    data = data.copy()

    ma_column = f"MA{window}"
    signal_column = f"Signal{window}"

    data[ma_column] = data["Close"].rolling(window=window).mean()

    data[signal_column] = (
        data["Close"] > data[ma_column]
    ).astype(int)

    return data