import numpy as np


TRADING_DAYS = 252


def annualized_return(returns):
    return returns.mean() * TRADING_DAYS


def annualized_volatility(returns):
    return returns.std() * np.sqrt(TRADING_DAYS)


def cagr(cumulative, dates):
    years = (
        dates.iloc[-1] - dates.iloc[0]
    ).days / 365.25

    return cumulative.iloc[-1] ** (1 / years) - 1


def sharpe_ratio(returns, risk_free_rate=0.0):
    """
    Calcule un Sharpe ratio annualisé à partir des rendements journaliers.
    """

    excess_returns = returns - risk_free_rate / TRADING_DAYS

    return (
        excess_returns.mean()
        / excess_returns.std()
        * np.sqrt(TRADING_DAYS)
    )


def max_drawdown(cumulative):
    peak = cumulative.cummax()
    drawdown = cumulative / peak - 1

    return drawdown.min()