from datetime import date
import click
from rich.console import Console
from rich.table import Table
from shadow.portfolio import ShadowPortfolio
from shadow.checker import check_stop_profit

console = Console()

# 内存中维护影子账户（会话级，正式版可持久化到DB）
_portfolios: dict[str, ShadowPortfolio] = {}


def _get_portfolio(code: str) -> ShadowPortfolio:
    if code not in _portfolios:
        _portfolios[code] = ShadowPortfolio(code)
    return _portfolios[code]


@click.group()
def shadow():
    """影子账户（跟踪真实持仓）"""


@shadow.command("buy")
@click.argument("code")
@click.option("--date", "trade_date", required=True, help="买入日期 YYYY-MM-DD")
@click.option("--amount", required=True, type=float, help="投入金额（元）")
@click.option("--nav", default=None, type=float, help="指定净值（留空从DB查）")
def shadow_buy(code, trade_date, amount, nav):
    """录入买入记录，例如：fund shadow buy 510300 --date 2024-01-15 --amount 10000"""
    p = _get_portfolio(code)
    p.add_buy(date.fromisoformat(trade_date), amount, nav=nav)
    console.print(f"[green]已录入买入：{code} {trade_date} {amount:,.2f} 元[/green]")


@shadow.command("sell")
@click.argument("code")
@click.option("--date", "trade_date", required=True, help="卖出日期 YYYY-MM-DD")
@click.option("--shares", required=True, type=float, help="卖出份额")
@click.option("--nav", default=None, type=float, help="指定净值（留空从DB查）")
def shadow_sell(code, trade_date, shares, nav):
    """录入卖出记录"""
    p = _get_portfolio(code)
    result = p.add_sell(date.fromisoformat(trade_date), shares, nav=nav)
    console.print(f"[green]已录入卖出：{code} {shares:.4f}份 | "
                  f"到账 {result.net_proceeds:,.2f} 元 | "
                  f"实现盈亏 {result.realized_pnl:+,.2f} 元[/green]")


@shadow.command("status")
@click.argument("code")
@click.option("--date", "as_of", default=None, help="查询日期（默认今天）")
def shadow_status(code, as_of):
    """查看当前持仓状态"""
    p = _get_portfolio(code)
    as_of_date = date.fromisoformat(as_of) if as_of else None
    snap = p.snapshot(as_of=as_of_date)

    if "error" in snap:
        console.print(f"[red]{snap['error']}[/red]")
        return

    t = Table(title=f"影子账户快照 {code} ({snap['as_of']})", show_header=False)
    t.add_column("指标", style="cyan")
    t.add_column("数值")

    sign = "+" if snap["pnl"] >= 0 else ""
    color = "green" if snap["pnl"] >= 0 else "red"
    xirr_str = f"{snap['xirr_pct']:+.1f}%" if snap.get("xirr_pct") else "N/A"

    t.add_row("当前净值", f"{snap['current_nav']:.4f}")
    t.add_row("持仓份额", f"{snap['shares']:,.4f}")
    t.add_row("持仓成本", f"¥ {snap['cost_total']:,.2f}")
    t.add_row("当前市值", f"¥ {snap['market_value']:,.2f}")
    t.add_row("累计盈亏", f"[{color}]{sign}¥ {snap['pnl']:,.2f} ({sign}{snap['cumulative_return_pct']:.1f}%)[/{color}]")
    t.add_row("年化收益", f"{snap['annualized_return_pct']:+.1f}%")
    t.add_row("XIRR", xirr_str)
    t.add_row("持有天数", str(snap["hold_days"]))
    t.add_row("持仓批次", str(snap["lots_count"]))
    console.print(t)


@shadow.command("check")
@click.argument("code")
@click.option("--index", "index_code", default=None, help="跟踪指数代码（如 000300）")
@click.option("--stop-profit-xirr", default=15.0, type=float, show_default=True, help="止盈XIRR阈值（%）")
@click.option("--stop-loss-dd", default=20.0, type=float, show_default=True, help="止损最大回撤阈值（%）")
def shadow_check(code, index_code, stop_profit_xirr, stop_loss_dd):
    """止盈止损综合判断"""
    p = _get_portfolio(code)
    result = check_stop_profit(
        p, index_code=index_code,
        stop_profit_xirr=stop_profit_xirr,
        stop_loss_drawdown=stop_loss_dd,
    )

    action_color = {"HOLD": "yellow", "SELL_PARTIAL": "red", "SELL_ALL": "bold red", "BUY_MORE": "green"}.get(result.action, "white")
    console.print(f"\n[bold]止盈止损判断：{code}[/bold]")
    console.print(f"  建议操作：[{action_color}]{result.action}[/{action_color}]")
    for r in result.reasons:
        console.print(f"  • {r}")

    if result.pe:
        console.print(f"\n  估值快照：PE={result.pe:.1f}  "
                      f"E/P={result.earnings_yield_pct:.1f}%  "
                      f"PE百分位={result.pe_percentile*100:.0f}%" if result.pe_percentile else "")
    console.print(f"  持仓收益：XIRR={result.xirr_pct:+.1f}%  累计={result.cumulative_return_pct:+.1f}%  最大回撤={result.max_drawdown_pct:.1f}%\n" if result.xirr_pct else "")
