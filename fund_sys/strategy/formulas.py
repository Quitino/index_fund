"""核心公式库：XIRR、年化收益率、最大回撤、夏普比率等。"""
from datetime import date
import numpy as np
from scipy.optimize import brentq


def xirr(cashflows: list[tuple[date, float]], guess: float = 0.1) -> float | None:
    """
    不规则时间间隔的内部收益率（年化）。
    cashflows: [(date, amount), ...], 流出为负，流入为正。
    最后一笔通常为当前市值（正数，代表清仓）。
    """
    if len(cashflows) < 2:
        return None
    t0 = min(d for d, _ in cashflows)
    days = [(d - t0).days for d, _ in cashflows]
    amounts = [cf for _, cf in cashflows]

    def npv(rate):
        return sum(a / (1 + rate) ** (t / 365.0) for t, a in zip(days, amounts))

    try:
        return brentq(npv, -0.999, 100.0, maxiter=1000)
    except (ValueError, RuntimeError):
        return None


def annualized_return(total_return: float, days: int) -> float:
    """复利年化收益率。total_return 为小数（如 0.2 代表20%）。"""
    if days <= 0:
        return 0.0
    return (1 + total_return) ** (365.0 / days) - 1


def max_drawdown(nav_series: list[float]) -> float:
    """最大回撤（返回正数，如 0.15 代表 -15%）。"""
    if not nav_series:
        return 0.0
    peak = nav_series[0]
    mdd = 0.0
    for v in nav_series:
        peak = max(peak, v)
        dd = (peak - v) / peak if peak > 0 else 0.0
        mdd = max(mdd, dd)
    return mdd


def sharpe_ratio(daily_returns: list[float], risk_free_annual: float = 0.02) -> float | None:
    """
    夏普比率（年化）。
    daily_returns: 每日收益率序列（小数，如 0.01 代表 1%）。
    """
    if len(daily_returns) < 10:
        return None
    arr = np.array(daily_returns)
    rf_daily = risk_free_annual / 250
    excess = arr - rf_daily
    std = excess.std()
    if std == 0:
        return None
    return float(np.sqrt(250) * excess.mean() / std)


def earnings_yield(pe: float) -> float:
    """盈利收益率 E/P = 1/PE，以百分比表示。"""
    if pe and pe > 0:
        return 1.0 / pe * 100
    return 0.0


def bogle_expected_return(
    dividend_yield: float,
    earnings_growth: float,
    pe_change_annual: float = 0.0,
) -> float:
    """
    博格公式预期年复合收益率（均为百分比输入，返回百分比）。
    = 初始股息率 + 盈利增长率 + PE变化贡献
    """
    return dividend_yield + earnings_growth + pe_change_annual
