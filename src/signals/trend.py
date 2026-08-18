#moving_average_signal()
#        ↓
#signal classique
#Close > MA200

#moving_average_buffer_signal()
#        ↓
#signal avec hystérésis
#entrée > MA200 + buffer
#sortie < MA200 - buffer



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

def moving_average_buffer_signal(
    data,
    window=200,
    buffer=0.01,
    ):
    """
    Crée un signal de tendance avec zone tampon autour
    de la moyenne mobile.

    Exemple avec buffer=0.01 :
    - entrée si Close > MA * 1.01
    - sortie si Close < MA * 0.99
    - entre les deux, on garde le signal précédent
    """

    data = data.copy()

    ma_column = f"MA{window}"
    signal_column = f"Signal{window}_B{int(buffer * 100)}"

    data[ma_column] = (
        data["Close"]
        .rolling(window=window)
        .mean()
    )

    upper_band = data[ma_column] * (1 + buffer)
    lower_band = data[ma_column] * (1 - buffer)

    signal = 0
    signals = []

    for close, upper, lower in zip(
        data["Close"],
        upper_band,
        lower_band,
    ):

        if close > upper:
            signal = 1

        elif close < lower:
            signal = 0

        signals.append(signal)

    data[signal_column] = signals

    return data