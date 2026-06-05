"""
估值查询命令组。

fund valuation show 000300           # 单个指数详情
fund valuation all                   # 所有已知指数概览
fund valuation batch 000300 000905   # 批量多个
fund valuation category 宽基         # 按分类
"""
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from strategy.indicators import get_valuation_signal
from data.index_catalog import INDEX_CATALOG, CATEGORIES, list_by_category, list_all

console = Console()


def _signal_color(signal: str) -> str:
    return {"BUY": "green", "HOLD": "yellow", "SELL": "red"}.get(signal, "white")


def _render_valuation_table(pairs: list[tuple[str, str]], title: str):
    """批量渲染估值表格，pairs = [(code, name), ...]"""
    t = Table(title=title, box=box.ROUNDED)
    t.add_column("指数", style="cyan", min_width=8)
    t.add_column("代码", style="dim")
    t.add_column("日期", style="dim")
    t.add_column("PE", justify="right")
    t.add_column("PB", justify="right")
    t.add_column("PE百分位", justify="right")
    t.add_column("E/P%", justify="right")
    t.add_column("信号", justify="center")
    t.add_column("理由", no_wrap=False)

    for code, name in pairs:
        with console.status(f"  获取 {name}({code})..."):
            sig = get_valuation_signal(code)
        if not sig:
            t.add_row(name, code, "-", "-", "-", "-", "-", "[dim]无数据[/dim]", "")
            continue
        sc = _signal_color(sig.signal)
        t.add_row(
            name, code,
            str(sig.date),
            f"{sig.pe:.1f}" if sig.pe else "-",
            f"{sig.pb:.2f}" if sig.pb else "-",
            f"{sig.pe_percentile*100:.0f}%" if sig.pe_percentile else "-",
            f"{sig.earnings_yield_pct:.1f}%",
            f"[{sc}]{sig.signal}[/{sc}]",
            sig.reason,
        )
    console.print(t)


@click.group()
def valuation():
    """指数估值查询（支持单个/批量/分类）"""


@valuation.command("show")
@click.argument("index_code")
def val_show(index_code):
    """
    查看单个指数估值详情，例如：

    \b
    fund valuation show 000300   # 沪深300
    fund valuation show 000905   # 中证500
    """
    info = INDEX_CATALOG.get(index_code, {})
    name = info.get("name", index_code)

    with console.status(f"[bold green]获取 {name}({index_code}) 估值..."):
        sig = get_valuation_signal(index_code)

    if not sig:
        console.print(f"[red]无法获取 {index_code} 估值数据（该指数可能不在支持列表中）[/red]")
        console.print(f"[dim]支持的指数：{', '.join(INDEX_CATALOG.keys())}[/dim]")
        return

    sc = _signal_color(sig.signal)

    t = Table(title=f"指数估值详情  {name}({index_code})", show_header=False, box=box.ROUNDED)
    t.add_column("指标", style="cyan", min_width=12)
    t.add_column("数值")

    t.add_row("估值日期", str(sig.date))
    t.add_row("市盈率 PE", f"{sig.pe:.2f}" if sig.pe else "N/A")
    t.add_row("市净率 PB", f"{sig.pb:.2f}" if sig.pb else "N/A")
    t.add_row("PE历史百分位",
              f"{sig.pe_percentile*100:.1f}%（历史上有 {sig.pe_percentile*100:.0f}% 的时间 PE 比现在低）"
              if sig.pe_percentile else "N/A")
    t.add_row("盈利收益率 E/P", f"{sig.earnings_yield_pct:.2f}%  （螺丝钉核心指标）")
    t.add_row("操作信号", f"[{sc} bold]{sig.signal}[/{sc} bold]")
    t.add_row("判断依据", sig.reason)
    if sig.bogle_return:
        t.add_row("博格预期收益", f"{sig.bogle_return:.1f}% / 年（乐观估算）")

    # 信号说明
    guide = (
        "[green]E/P > 10%[/green] → BUY（低估，开始/加仓定投）\n"
        "[yellow]6.4% ~ 10%[/yellow] → HOLD（正常，持有）\n"
        "[red]E/P < 6.4%[/red] → SELL（高估，分批卖出）"
    )
    console.print(t)
    console.print(Panel(guide, title="螺丝钉E/P法说明", border_style="dim"))


@valuation.command("all")
def val_all():
    """查看所有支持指数的估值概览"""
    pairs = list_all()
    _render_valuation_table(pairs, "全部指数估值概览")


@valuation.command("batch")
@click.argument("codes", nargs=-1, required=True)
def val_batch(codes):
    """
    批量查询多个指数，例如：

    \b
    fund valuation batch 000300 000905 000852 000016
    """
    pairs = []
    for code in codes:
        info = INDEX_CATALOG.get(code, {})
        pairs.append((code, info.get("name", code)))
    _render_valuation_table(pairs, f"批量估值查询（{len(pairs)} 个指数）")


@valuation.command("category")
@click.argument("category", type=click.Choice(CATEGORIES + ["全部"]), default="全部")
def val_category(category):
    """
    按分类查看估值，例如：

    \b
    fund valuation category 宽基
    fund valuation category 红利
    fund valuation category 全部
    """
    if category == "全部":
        pairs = list_all()
    else:
        pairs = list_by_category(category)

    if not pairs:
        console.print(f"[red]分类 '{category}' 下无指数[/red]")
        return
    _render_valuation_table(pairs, f"{category} 指数估值")
