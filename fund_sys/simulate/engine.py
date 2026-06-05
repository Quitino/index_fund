"""
模拟持有引擎。
支持：一次性建仓、日投、周投（每周N）、月投（每月N号）。
自动处理 T+1 确认净值（场外基金），ETF 按当日净值确认。
"""
from datetime import date, timedelta
from dataclasses import dataclass, field
import pandas as pd
from data.repository.fund_repo import get_nav_series, ensure_fund_info
from config.settings import DEFAULT_PURCHASE_FEE_OTC, DEFAULT_COMMISSION_ETF


@dataclass
class InvestPlan:
    code: str
    start_date: date
    end_date: date
    strategy: str           # "lump_sum" | "daily" | "weekly" | "monthly"
    amount: float           # 每次金额（元），一次性时为总金额
    weekday: int = 1        # 周投：1=周一 … 5=周五
    monthday: int = 1       # 月投：每月几号


def _is_etf(code: str) -> bool:
    return len(code) == 6 and code[0] in ("5", "1")


def _invest_days(plan: InvestPlan, nav_df: pd.DataFrame) -> list[date]:
    """根据策略生成投入日期列表（只在有净值的交易日）。"""
    trading_days = set(nav_df["date"].tolist())
    all_days = sorted(trading_days)

    if plan.strategy == "lump_sum":
        # 找 start_date 当日或最近下一个交易日
        for d in all_days:
            if d >= plan.start_date:
                return [d]
        return []

    result = []
    cur = plan.start_date
    while cur <= plan.end_date:
        if plan.strategy == "daily":
            if cur in trading_days:
                result.append(cur)
        elif plan.strategy == "weekly":
            if cur.isoweekday() == plan.weekday and cur in trading_days:
                result.append(cur)
        elif plan.strategy == "monthly":
            if cur.day == plan.monthday and cur in trading_days:
                result.append(cur)
            elif cur.day < plan.monthday:
                # 该月还没到投入日
                pass
            else:
                # 该月投入日已过，找最近交易日
                pass
        cur += timedelta(days=1)
    return result


def _monthly_invest_days(plan: InvestPlan, nav_df: pd.DataFrame) -> list[date]:
    """月投：每月 monthday 号，若当日非交易日则顺延到下一个交易日。"""
    trading_days = sorted(nav_df["date"].tolist())
    trading_set = set(trading_days)
    result = []
    cur = plan.start_date.replace(day=1)
    while cur <= plan.end_date:
        # 本月目标日
        try:
            target = cur.replace(day=plan.monthday)
        except ValueError:
            # monthday 超过本月天数，取月末
            import calendar
            last = calendar.monthrange(cur.year, cur.month)[1]
            target = cur.replace(day=last)

        if target < plan.start_date:
            # 推进到下月
            if cur.month == 12:
                cur = cur.replace(year=cur.year + 1, month=1)
            else:
                cur = cur.replace(month=cur.month + 1)
            continue

        if target > plan.end_date:
            break

        # 顺延到交易日
        actual = target
        while actual not in trading_set and actual <= plan.end_date:
            actual += timedelta(days=1)
        if actual in trading_set:
            result.append(actual)

        # 推进到下月
        if cur.month == 12:
            cur = cur.replace(year=cur.year + 1, month=1)
        else:
            cur = cur.replace(month=cur.month + 1)
    return result


def run_simulation(plan: InvestPlan) -> pd.DataFrame:
    """
    执行模拟，返回每日快照 DataFrame。

    columns:
        date, nav, shares_total, cost_total, market_value,
        cumulative_return, daily_pnl, invested_today
    """
    nav_df = get_nav_series(plan.code, start=plan.start_date, end=plan.end_date)
    if nav_df.empty:
        raise ValueError(f"无法获取基金 {plan.code} 的净值数据")

    is_etf = _is_etf(plan.code)
    fee_rate = DEFAULT_COMMISSION_ETF if is_etf else DEFAULT_PURCHASE_FEE_OTC

    nav_dict = dict(zip(nav_df["date"], nav_df["nav"]))
    nav_dates = sorted(nav_dict.keys())

    # 生成投入日
    if plan.strategy == "monthly":
        invest_days = set(_monthly_invest_days(plan, nav_df))
    else:
        invest_days = set(_invest_days(plan, nav_df))

    shares_total = 0.0
    cost_total = 0.0
    rows = []

    for d in nav_dates:
        nav = nav_dict[d]
        invested_today = 0.0

        if d in invest_days:
            if is_etf:
                # ETF：当日净值确认
                confirm_nav = nav
            else:
                # 场外 T+1：找下一个交易日净值
                confirm_nav = _next_nav(d, nav_dict, nav_dates)

            if confirm_nav and confirm_nav > 0:
                net_amount = plan.amount / (1 + fee_rate)
                shares_bought = net_amount / confirm_nav
                shares_total += shares_bought
                cost_total += plan.amount
                invested_today = plan.amount

        market_value = shares_total * nav
        cum_return = (market_value - cost_total) / cost_total if cost_total > 0 else 0.0
        prev_value = rows[-1]["market_value"] if rows else market_value
        daily_pnl = market_value - prev_value - invested_today

        rows.append({
            "date": d,
            "nav": nav,
            "shares_total": shares_total,
            "cost_total": cost_total,
            "market_value": market_value,
            "cumulative_return": cum_return,
            "daily_pnl": daily_pnl,
            "invested_today": invested_today,
        })

    return pd.DataFrame(rows)


def _next_nav(d: date, nav_dict: dict, nav_dates: list) -> float | None:
    """找 d 之后第一个有净值的交易日净值（T+1）。"""
    for nd in nav_dates:
        if nd > d:
            return nav_dict.get(nd)
    return nav_dict.get(d)  # 若无下一日，用当日（边界情况）
