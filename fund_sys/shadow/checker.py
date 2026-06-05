"""止盈止损判断器：综合 E/P 信号 + XIRR + 最大回撤阈值。"""
from datetime import date
from dataclasses import dataclass
from shadow.portfolio import ShadowPortfolio
from strategy.indicators import get_valuation_signal
from data.repository.fund_repo import ensure_fund_info


@dataclass
class StopCheckResult:
    code: str
    as_of: date
    # 估值信号
    valuation_signal: str | None    # BUY / HOLD / SELL
    earnings_yield_pct: float | None
    pe: float | None
    pe_percentile: float | None
    # 收益状态
    xirr_pct: float | None
    cumulative_return_pct: float
    max_drawdown_pct: float
    # 综合建议
    action: str          # HOLD / SELL_PARTIAL / SELL_ALL / BUY_MORE
    reasons: list[str]


def check_stop_profit(
    portfolio: ShadowPortfolio,
    index_code: str = None,
    stop_profit_xirr: float = 15.0,    # XIRR 超过此值考虑止盈（%）
    stop_loss_drawdown: float = 20.0,   # 最大回撤超过此值触发预警（%）
    as_of: date = None,
) -> StopCheckResult:
    """
    综合判断是否应该止盈/止损/加仓。
    """
    snap = portfolio.snapshot(as_of=as_of)
    nav_curve = portfolio.nav_curve()

    # 估值信号
    val_signal = None
    ep = None
    pe = None
    pe_pct = None

    if not index_code:
        # 尝试从基金信息获取跟踪指数
        info = ensure_fund_info(portfolio.code)
        if info:
            index_code = info.tracking_index

    if index_code:
        vs = get_valuation_signal(index_code, as_of=as_of)
        if vs:
            val_signal = vs.signal
            ep = vs.earnings_yield_pct
            pe = vs.pe
            pe_pct = vs.pe_percentile

    xirr_pct = snap.get("xirr_pct")
    cum_return = snap.get("cumulative_return_pct", 0.0)

    # 最大回撤
    mdd = 0.0
    if not nav_curve.empty:
        from strategy.formulas import max_drawdown
        mdd = max_drawdown(nav_curve["market_value"].tolist()) * 100

    # 综合判断
    reasons = []
    action = "HOLD"

    if val_signal == "SELL":
        reasons.append(f"估值偏高：E/P={ep:.1f}% < 6.4%")
        action = "SELL_PARTIAL"

    if xirr_pct and xirr_pct >= stop_profit_xirr:
        reasons.append(f"XIRR={xirr_pct:.1f}% 已超止盈线 {stop_profit_xirr}%")
        action = "SELL_PARTIAL" if action == "HOLD" else "SELL_ALL"

    if mdd >= stop_loss_drawdown:
        reasons.append(f"最大回撤={mdd:.1f}% 超预警线 {stop_loss_drawdown}%，注意风险")

    if val_signal == "BUY":
        if action == "HOLD":
            action = "BUY_MORE"
            reasons.append(f"估值低廉：E/P={ep:.1f}% > 10%，可考虑加仓")

    if not reasons:
        reasons.append("无明显信号，继续持有")

    return StopCheckResult(
        code=portfolio.code,
        as_of=as_of or date.today(),
        valuation_signal=val_signal,
        earnings_yield_pct=ep,
        pe=pe,
        pe_percentile=pe_pct,
        xirr_pct=xirr_pct,
        cumulative_return_pct=cum_return,
        max_drawdown_pct=mdd,
        action=action,
        reasons=reasons,
    )
