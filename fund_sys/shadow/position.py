"""FIFO 持仓追踪，用于精确计算持有天数和赎回费。"""
from datetime import date
from dataclasses import dataclass, field
from config.settings import DEFAULT_REDEEM_FEE_SHORT, DEFAULT_REDEEM_FEE_LONG, REDEEM_SHORT_DAYS


@dataclass
class Lot:
    buy_date: date
    confirm_date: date   # T+1 确认日
    shares: float
    confirm_nav: float
    fee_paid: float      # 实际支付的申购费（元）
    gross_amount: float  # 原始投入金额（含费）


@dataclass
class SellResult:
    gross_proceeds: float    # 卖出时按净值计算的总金额
    redeem_fee: float        # 赎回费
    net_proceeds: float      # 到账金额
    realized_pnl: float      # 已实现盈亏
    sold_lots: list[dict]    # 各批次明细


class FIFOPosition:
    def __init__(self):
        self.lots: list[Lot] = []

    @property
    def total_shares(self) -> float:
        return sum(l.shares for l in self.lots)

    @property
    def total_cost(self) -> float:
        return sum(l.gross_amount for l in self.lots)

    def buy(self, buy_date: date, confirm_date: date, shares: float,
            confirm_nav: float, fee_paid: float, gross_amount: float):
        self.lots.append(Lot(
            buy_date=buy_date,
            confirm_date=confirm_date,
            shares=shares,
            confirm_nav=confirm_nav,
            fee_paid=fee_paid,
            gross_amount=gross_amount,
        ))

    def sell(self, sell_date: date, shares_to_sell: float, sell_nav: float) -> SellResult:
        """FIFO 卖出，返回 SellResult。"""
        if shares_to_sell > self.total_shares:
            raise ValueError(f"卖出份额 {shares_to_sell:.4f} 超过持仓 {self.total_shares:.4f}")

        remaining = shares_to_sell
        gross_proceeds = 0.0
        redeem_fee = 0.0
        realized_pnl = 0.0
        sold_lots = []

        new_lots = []
        for lot in self.lots:
            if remaining <= 0:
                new_lots.append(lot)
                continue

            sell_shares = min(lot.shares, remaining)
            remaining -= sell_shares

            # 持有天数（从确认日算起）
            hold_days = (sell_date - lot.confirm_date).days
            fee_rate = DEFAULT_REDEEM_FEE_SHORT if hold_days < REDEEM_SHORT_DAYS else DEFAULT_REDEEM_FEE_LONG

            gross = sell_shares * sell_nav
            fee = gross * fee_rate
            net = gross - fee
            cost_basis = (sell_shares / lot.shares) * lot.gross_amount if lot.shares > 0 else 0.0
            pnl = net - cost_basis

            gross_proceeds += gross
            redeem_fee += fee
            realized_pnl += pnl

            sold_lots.append({
                "buy_date": lot.buy_date,
                "confirm_date": lot.confirm_date,
                "sell_date": sell_date,
                "shares": sell_shares,
                "buy_nav": lot.confirm_nav,
                "sell_nav": sell_nav,
                "hold_days": hold_days,
                "fee_rate": fee_rate,
                "gross": gross,
                "fee": fee,
                "net": net,
                "pnl": pnl,
            })

            if sell_shares < lot.shares:
                # 部分卖出，更新剩余
                ratio = 1 - sell_shares / lot.shares
                new_lots.append(Lot(
                    buy_date=lot.buy_date,
                    confirm_date=lot.confirm_date,
                    shares=lot.shares - sell_shares,
                    confirm_nav=lot.confirm_nav,
                    fee_paid=lot.fee_paid * ratio,
                    gross_amount=lot.gross_amount * ratio,
                ))

        self.lots = new_lots
        return SellResult(
            gross_proceeds=gross_proceeds,
            redeem_fee=redeem_fee,
            net_proceeds=gross_proceeds - redeem_fee,
            realized_pnl=realized_pnl,
            sold_lots=sold_lots,
        )

    def market_value(self, current_nav: float) -> float:
        return self.total_shares * current_nav

    def unrealized_pnl(self, current_nav: float) -> float:
        return self.market_value(current_nav) - self.total_cost
