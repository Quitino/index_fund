"""估值指标计算：螺丝钉 E/P 法买卖信号。"""
from dataclasses import dataclass
from data.repository.fund_repo import get_index_valuation
from strategy.formulas import earnings_yield, bogle_expected_return


@dataclass
class ValuationSignal:
    index_code: str
    date: object
    pe: float
    pb: float
    pe_percentile: float
    earnings_yield_pct: float
    signal: str          # BUY / HOLD / SELL
    reason: str
    bogle_return: float | None = None


def get_valuation_signal(index_code: str, as_of=None) -> ValuationSignal | None:
    """
    螺丝钉盈利收益率法买卖信号：
    E/P > 10%  → BUY（买入/加仓）
    6.4% ~ 10% → HOLD（持有）
    < 6.4%     → SELL（分批卖出）
    """
    val = get_index_valuation(index_code, as_of=as_of)
    if not val:
        return None

    ep = earnings_yield(val["pe"]) if val["pe"] else 0.0

    if ep > 10:
        signal, reason = "BUY", f"E/P={ep:.1f}% > 10%，低估区间，建议买入"
    elif ep >= 6.4:
        signal, reason = "HOLD", f"E/P={ep:.1f}%，正常区间，持有"
    else:
        signal, reason = "SELL", f"E/P={ep:.1f}% < 6.4%，高估区间，建议卖出"

    bogle = None
    if val.get("dividend_yield") and ep > 0:
        bogle = bogle_expected_return(
            dividend_yield=val["dividend_yield"],
            earnings_growth=ep,  # 用盈利收益率近似替代
        )

    return ValuationSignal(
        index_code=index_code,
        date=val["date"],
        pe=val["pe"],
        pb=val["pb"],
        pe_percentile=val.get("pe_percentile"),
        earnings_yield_pct=ep,
        signal=signal,
        reason=reason,
        bogle_return=bogle,
    )


def pe_percentile_signal(pe_percentile: float) -> str:
    """PE百分位法辅助信号（用于无E/P数据的基金）。"""
    if pe_percentile <= 0.1:
        return "BUY"
    if pe_percentile <= 0.3:
        return "ACCUMULATE"
    if pe_percentile >= 0.9:
        return "SELL"
    if pe_percentile >= 0.7:
        return "REDUCE"
    return "HOLD"
