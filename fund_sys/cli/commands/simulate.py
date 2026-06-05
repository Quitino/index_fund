from datetime import date
import click
from rich.console import Console
from simulate.engine import InvestPlan, run_simulation
from simulate.report import build_report, format_report

console = Console()


@click.group()
def simulate():
    """模拟持有回测"""


@simulate.command("run")
@click.argument("code")
@click.option("--start", required=True, help="开始日期，格式 YYYY-MM-DD")
@click.option("--end", default=None, help="结束日期，默认今天")
@click.option("--strategy", type=click.Choice(["lump_sum", "daily", "weekly", "monthly"]),
              default="monthly", show_default=True)
@click.option("--amount", required=True, type=float, help="每次投入金额（元），一次性时为总金额")
@click.option("--weekday", default=1, type=int, help="周投：1=周一…5=周五", show_default=True)
@click.option("--monthday", default=1, type=int, help="月投：每月几号", show_default=True)
def simulate_run(code, start, end, strategy, amount, weekday, monthday):
    """
    模拟持有，例如：

    \b
    fund simulate run 510300 --start 2020-01-01 --strategy monthly --amount 1000
    fund simulate run 510300 --start 2020-01-01 --strategy lump_sum --amount 50000
    fund simulate run 510300 --start 2020-01-01 --strategy weekly --amount 500 --weekday 3
    """
    start_date = date.fromisoformat(start)
    end_date = date.fromisoformat(end) if end else date.today()

    plan = InvestPlan(
        code=code,
        start_date=start_date,
        end_date=end_date,
        strategy=strategy,
        amount=amount,
        weekday=weekday,
        monthday=monthday,
    )

    strategy_desc = {
        "lump_sum": f"一次性投入 {amount:,.0f} 元",
        "daily": f"每日定投 {amount:,.0f} 元",
        "weekly": f"每周{weekday}定投 {amount:,.0f} 元",
        "monthly": f"每月{monthday}号定投 {amount:,.0f} 元",
    }[strategy]

    with console.status(f"[bold green]模拟 {code} {strategy_desc}..."):
        try:
            df = run_simulation(plan)
            report = build_report(df, code, strategy_desc)
        except Exception as e:
            console.print(f"[red]模拟失败：{e}[/red]")
            return

    console.print(format_report(report))
