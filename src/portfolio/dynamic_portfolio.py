import pandas as pd


def run_dynamic_portfolio(
    data,
    markets,
    max_weight,
):
    """
    Simule un portefeuille trend multi-assets.

    Le portefeuille est rebalancé uniquement lorsque
    l'ensemble des signaux change.
    """

    data = data.copy()

    weight_columns = [
        f"{market}_weight"
        for market in markets
    ]

    # Poids détenus au départ
    current_weights = {
        market: 0.0
        for market in markets
    }

    current_cash_weight = 1.0

    previous_signals = None

    portfolio_returns = []
    turnovers = []

    for _, row in data.iterrows():

        current_signals = tuple(
            row[f"{market}_signal"]
            for market in markets
        )

        # ---------------------------------
        # Rebalancement si les signaux changent

        if current_signals != previous_signals:

            active_markets = [
                market
                for market in markets
                if row[f"{market}_signal"] == 1
            ]

            active_count = len(active_markets)

            target_weights = {
                market: 0.0
                for market in markets
            }

            if active_count > 0:

                equal_weight = 1 / active_count

                asset_weight = min(
                    equal_weight,
                    max_weight
                )

                for market in active_markets:
                    target_weights[market] = asset_weight

            target_cash_weight = (
                1 - sum(target_weights.values())
            )

            # Turnover du rebalancement
            turnover = sum(
                abs(
                    target_weights[market]
                    - current_weights[market]
                )
                for market in markets
            )

            turnover += abs(
                target_cash_weight
                - current_cash_weight
            )

            turnover /= 2

            current_weights = target_weights
            current_cash_weight = target_cash_weight

        else:
            turnover = 0.0

        # ---------------------------------
        # Rendement du portefeuille

        portfolio_return = (
            current_cash_weight
            * row["Cash_Return"]
        )

        for market in markets:

            portfolio_return += (
                current_weights[market]
                * row[f"{market}_return"]
            )

        portfolio_returns.append(
            portfolio_return
        )

        turnovers.append(
            turnover
        )

        previous_signals = current_signals

    data["Portfolio_Return"] = portfolio_returns
    data["Turnover"] = turnovers

    return data