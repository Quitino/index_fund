import click
from rich.console import Console
from rich.table import Table
from data.repository.fund_repo import ensure_fund_info, ensure_nav_history, get_nav_series

console = Console()


@click.group()
def fetch():
    """数据拉取命令"""


@fetch.command("info")
@click.argument("code")
def fetch_info(code):
    """拉取基金基本信息，例如：fund fetch info 510300"""
    with console.status(f"[bold green]拉取 {code} 基本信息..."):
        info = ensure_fund_info(code)

    if not info:
        console.print(f"[red]未找到基金 {code}[/red]")
        return

    t = Table(title=f"基金信息 {code}", show_header=False)
    t.add_column("字段", style="cyan")
    t.add_column("值")
    fields = [
        ("代码", info.code), ("名称", info.name), ("类型", info.fund_type),
        ("市场", info.market), ("跟踪指数", info.tracking_index),
        ("规模(亿)", f"{info.aum:.2f}" if info.aum else "N/A"),
        ("管理费(%)", f"{info.mgmt_fee*100:.2f}" if info.mgmt_fee else "N/A"),
        ("申购费(%)", f"{info.purchase_fee*100:.3f}" if info.purchase_fee else "N/A"),
        ("成立日期", str(info.inception_date) if info.inception_date else "N/A"),
    ]
    for k, v in fields:
        t.add_row(k, str(v) if v else "N/A")
    console.print(t)


@fetch.command("nav")
@click.argument("code")
def fetch_nav(code):
    """拉取并更新历史净值，例如：fund fetch nav 510300"""
    with console.status(f"[bold green]拉取 {code} 历史净值..."):
        ensure_nav_history(code)
        df = get_nav_series(code)

    if df.empty:
        console.print(f"[red]未能获取 {code} 净值数据[/red]")
        return

    console.print(f"[green]已获取 {len(df)} 条净值记录（{df['date'].iloc[0]} ~ {df['date'].iloc[-1]}）[/green]")

    # 显示最近5条
    t = Table(title=f"最近净值 {code}")
    for col in ["date", "nav", "acc_nav", "daily_return"]:
        t.add_column(col)
    for _, r in df.tail(5).iterrows():
        t.add_row(str(r["date"]), f"{r['nav']:.4f}", f"{r['acc_nav']:.4f}", f"{r['daily_return']:.2f}%")
    console.print(t)
