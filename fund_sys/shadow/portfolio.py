"""
影子账户：追踪真实持仓，输入买入/卖出记录，计算当前盈亏状态。
"""
from datetime import date, timedelta
from dataclasses import dataclass, field
import pandas as pd
from shadow.position import FIFOPosition
from data.repository.fund_repo import get_nav_series
from strategy.formulas import xirr, max_drawdown, annualized_return
from config.settings import DEFAULT_PURCHASE_FEE_OTC, DEFAULT_COMMISSION_ETF


def _is_etf(code: str) -> bool:
    return len(code) == 6 and code[0] in ("5", "1")


@dataclass
class TradeRecord:
    """一笔买入或卖出记录（用户手动录入）。"""
    trade_date: date
    action: str          # "buy" | "sell"
    amount: float        # 买入：投入金额（元）；卖出：卖出份额
    nav: float = None    # 用户可指定净值，否则从DB查询


class ShadowPortfolio:
    def __init__(self, code: str, fee_rate: float = None):
        self.code = code
        self.is_etf = _is_etf(code)
        self.fee_rate = fee_rate or (DEFAULT_COMMISSION_ETF if self.is_etf else DEFAULT_PURCHASE_FEE_OTC)
        self.position = FIFOPosition()
        self.trades: list[TradeRecord] = []
        self._nav_cache: dict[date, float] = {}

    def _get_nav(self, d: date) -> float | None:
        if not self._nav_cache:
            nav_df = get_nav_series(self.code)
            self._nav_cache = dict(zip(nav_df["date"], nav_df["nav"]))
        return self._nav_cache.get(d)

    def _confirm_nav(self, trade_date: date) -> tuple[date, float]:
        """场外 T+1 确认净值，ETF 当日。"""
        if self.is_etf:
            nav = self._get_nav(trade_date)
            return trade_date, nav
        # 找下一个交易日
        d = trade_date + timedelta(days=1)
        for _ in range(10):
            nav = self._get_nav(d)
            if nav:
                return d, nav
            d += timedelta(days=1)
        return trade_date, self._get_nav(trade_date)

    def add_buy(self, trade_date: date, amount: float, nav: float = None):
        """录入一笔买入。amount 为实际投入元数（含申购费）。"""
        confirm_date, confirm_nav = (trade_date, nav) if nav else self._confirm_nav(trade_date)
        if not confirm_nav:
            raise ValueError(f"无法获取 {self.code} 在 {confirm_date} 的净值")

        fee_paid = amount * self.fee_rate
        net_amount = amount - fee_paid
        shares = net_amount / confirm_nav

        self.position.buy(
            buy_date=trade_date,
            confirm_date=confirm_date,
            shares=shares,
            confirm_nav=confirm_nav,
            fee_paid=fee_paid,
            gross_amount=amount,
        )
        self.trades.append(TradeRecord(trade_date=trade_date, action="buy", amount=amount, nav=confirm_nav))

    def add_sell(self, trade_date: date, shares: float, nav: float = None):
        """录入一笔卖出。shares 为卖出份额。"""
        sell_nav = nav or self._get_nav(trade_date)
        if not sell_nav:
            raise ValueError(f"无法获取 {self.code} 在 {trade_date} 的净值")
        result = self.position.sell(trade_date, shares, sell_nav)
        self.trades.append(TradeRecord(trade_date=trade_date, action="sell", amount=shares, nav=sell_nav))
        return result

    def snapshot(self, as_of: date = None) -> dict:
        """当前（或指定日期）持仓快照。"""
        nav_date = as_of or date.today()
        current_nav = self._get_nav(nav_date)
        # 向前找最近交易日
        if not current_nav:
            for offset in range(1, 8):
                current_nav = self._get_nav(nav_date - timedelta(days=offset))
                if current_nav:
                    break

        if not current_nav:
            return {"error": "无法获取当前净值"}

        mv = self.position.market_value(current_nav)
        cost = self.position.total_cost
        shares = self.position.total_shares
        pnl = mv - cost
        cum_return = pnl / cost if cost > 0 else 0.0

        # XIRR
        cashflows = [(-t.amount, t.trade_date) for t in self.trades if t.action == "buy"]
        cashflows_typed = [(-t.amount, t.trade_date) for t in self.trades if t.action == "buy"]
        xirr_cfs = [(-t.amount, t.trade_date) for t in self.trades if t.action == "buy"]
        xirr_input = [(t.trade_date, -t.amount) for t in self.trades if t.action == "buy"]
        xirr_input.append((nav_date, mv))
        xirr_rate = xirr(xirr_input)

        # 持有天数（从第一笔买入算起）
        buy_trades = [t for t in self.trades if t.action == "buy"]
        hold_days = (nav_date - buy_trades[0].trade_date).days if buy_trades else 0

        return {
            "code": self.code,
            "as_of": nav_date,
            "current_nav": current_nav,
            "shares": shares,
            "cost_total": cost,
            "market_value": mv,
            "pnl": pnl,
            "cumulative_return_pct": cum_return * 100,
            "annualized_return_pct": annualized_return(cum_return, hold_days) * 100 if hold_days > 0 else 0.0,
            "xirr_pct": xirr_rate * 100 if xirr_rate is not None else None,
            "hold_days": hold_days,
            "lots_count": len(self.position.lots),
        }

    def nav_curve(self, start: date = None, end: date = None) -> pd.DataFrame:
        """返回持仓期间每日市值曲线。"""
        buy_dates = [t.trade_date for t in self.trades if t.action == "buy"]
        if not buy_dates:
            return pd.DataFrame()
        curve_start = start or min(buy_dates)
        curve_end = end or date.today()
        nav_df = get_nav_series(self.code, start=curve_start, end=curve_end)
        if nav_df.empty:
            return pd.DataFrame()

        rows = []
        running_shares = 0.0
        running_cost = 0.0
        buy_idx = 0
        sorted_buys = sorted([(t.trade_date, t.amount, t.nav) for t in self.trades if t.action == "buy"])

        for _, row in nav_df.iterrows():
            d = row["date"]
            nav = row["nav"]
            # 累加当日及之前的买入
            while buy_idx < len(sorted_buys) and sorted_buys[buy_idx][0] <= d:
                _, amt, bnav = sorted_buys[buy_idx]
                if bnav:
                    net = amt * (1 - self.fee_rate)
                    running_shares += net / bnav
                    running_cost += amt
                buy_idx += 1

            mv = running_shares * nav
            rows.append({
                "date": d,
                "nav": nav,
                "market_value": mv,
                "cost_total": running_cost,
                "pnl": mv - running_cost,
                "return_pct": (mv - running_cost) / running_cost * 100 if running_cost > 0 else 0.0,
            })

        return pd.DataFrame(rows)
