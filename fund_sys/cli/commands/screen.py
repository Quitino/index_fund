"""
基金筛选命令。

fund screen --index 000300               # 跟踪沪深300的全部基金
fund screen --index 000300 --top 5       # 费率最低5只
fund screen --index 000300 --type etf    # 只看ETF
fund screen --index 000300 --type otc    # 只看场外联接基金
fund screen --signal BUY                 # 当前处于低估的所有指数下的基金
fund screen --name 消费                  # 名称含"消费"的基金
"""
import click
import akshare as ak
import pandas as pd
from rich.console import Console
from rich.table import Table
from rich import box

from data.index_catalog import INDEX_CATALOG, find_funds_by_index
from strategy.indicators import get_valuation_signal

console = Console()


def _load_index_fund_df() -> pd.DataFrame:
    """加载全量被动指数型场外基金列表。"""
    with console.status("正在获取指数基金列表..."):
        df = ak.fund_info_index_em(symbol="全部", indicator="被动指数型")
    df = df.rename(columns={
        "基金代码": "code", "基金名称": "name",
        "手续费": "fee", "单位净值": "nav",
        "近1年": "return_1y", "近3年": "return_3y", "今年来": "return_ytd",
    })
    df["market"] = "OTC"
    return df


def _load_etf_df() -> pd.DataFrame:
    """加载 ETF 列表（仅代码和名称，实时数据）。"""
    with console.status("正在获取 ETF 列表..."):
        df = ak.fund_etf_spot_em()
    df = df.rename(columns={"代码": "code", "名称": "name", "涨跌幅": "daily_pct"})
    df["market"] = "ETF"
    df["fee"] = "0.03%"  # 佣金近似
    df["nav"] = df.get("最新价", pd.Series(dtype=float))
    return df[["code", "name", "market", "fee", "nav"]]


def _parse_fee(s) -> float:
    """将费率字符串（'0.15%'）转为浮点数（0.0015）。"""
    try:
        return float(str(s).replace("%", "").strip()) / 100
    except Exception:
        return 999.0


def _render_fund_table(df: pd.DataFrame, title: str, top: int = None):
    if df.empty:
        console.print(f"[yellow]未找到符合条件的基金[/yellow]")
        return

    # 按手续费排序
    df = df.copy()
    df["_fee_num"] = df["fee"].apply(_parse_fee)
    df = df.sort_values("_fee_num")

    if top:
        df = df.head(top)

    t = Table(title=title, box=box.ROUNDED)
    t.add_column("代码", style="cyan", min_width=8)
    t.add_column("名称", min_width=20)
    t.add_column("类型", style="dim")
    t.add_column("手续费", justify="right")

    has_1y = "return_1y" in df.columns
    has_3y = "return_3y" in df.columns
    has_ytd = "return_ytd" in df.columns

    if has_ytd:
        t.add_column("今年来%", justify="right")
    if has_1y:
        t.add_column("近1年%", justify="right")
    if has_3y:
        t.add_column("近3年%", justify="right")

    for _, r in df.iterrows():
        row = [str(r["code"]), str(r["name"]), str(r["market"]), str(r["fee"])]
        if has_ytd:
            v = r.get("return_ytd")
            row.append(_color_pct(v))
        if has_1y:
            v = r.get("return_1y")
            row.append(_color_pct(v))
        if has_3y:
            v = r.get("return_3y")
            row.append(_color_pct(v))
        t.add_row(*row)

    console.print(t)
    console.print(f"[dim]共 {len(df)} 只，按手续费升序排列[/dim]")


def _color_pct(v) -> str:
    try:
        f = float(v)
        color = "green" if f >= 0 else "red"
        return f"[{color}]{f:+.1f}[/{color}]"
    except Exception:
        return str(v) if v else "-"


# ──────────────────────────────────────────────
# 命令定义
# ──────────────────────────────────────────────

@click.group()
def screen():
    """基金筛选（按指数/名称/信号）"""


@screen.command("index")
@click.argument("index_code")
@click.option("--type", "fund_type", type=click.Choice(["all", "etf", "otc"]), default="all",
              show_default=True, help="基金类型")
@click.option("--top", type=int, default=None, help="取费率最低的前N只")
def screen_index(index_code, fund_type, top):
    """
    筛选跟踪某指数的基金，按手续费升序，例如：

    \b
    fund screen index 000300              # 沪深300全部基金
    fund screen index 000300 --type etf   # 只看ETF
    fund screen index 000300 --top 5      # 费率最低5只
    """
    info = INDEX_CATALOG.get(index_code)
    if not info:
        console.print(f"[red]不支持的指数代码 {index_code}[/red]")
        console.print(f"[dim]支持：{', '.join(INDEX_CATALOG.keys())}[/dim]")
        return

    name = info["name"]
    frames = []

    if fund_type in ("all", "etf"):
        etf_df = _load_etf_df()
        matched = etf_df[etf_df["name"].apply(
            lambda n: any(kw in str(n) for kw in info["keywords"])
        )]
        frames.append(matched)

    if fund_type in ("all", "otc"):
        otc_df = _load_index_fund_df()
        otc_df = otc_df.rename(columns={"name": "基金名称"})
        matched_otc = find_funds_by_index(otc_df, index_code)
        matched_otc = matched_otc.rename(columns={"基金名称": "name"})
        frames.append(matched_otc)

    if not frames:
        console.print("[yellow]未找到基金[/yellow]")
        return

    combined = pd.concat(frames, ignore_index=True)
    title = f"跟踪 {name}({index_code}) 的基金"
    if top:
        title += f"（费率最低前{top}只）"

    _render_fund_table(combined, title, top=top)

    # 附带当前估值信号
    sig = get_valuation_signal(index_code)
    if sig:
        sc = {"BUY": "green", "HOLD": "yellow", "SELL": "red"}.get(sig.signal, "white")
        console.print(
            f"\n[dim]当前估值：PE={sig.pe:.1f}  E/P={sig.earnings_yield_pct:.1f}%  "
            f"信号=[/{sc}][{sc} bold]{sig.signal}[/{sc} bold][dim]  {sig.reason}[/dim]"
        )


@screen.command("name")
@click.argument("keyword")
@click.option("--top", type=int, default=20, show_default=True)
def screen_name(keyword, top):
    """
    按名称关键词筛选基金，例如：

    \b
    fund screen name 消费
    fund screen name 医疗 --top 10
    fund screen name 新能源
    """
    otc_df = _load_index_fund_df()
    matched = otc_df[otc_df["name"].str.contains(keyword, na=False)]
    _render_fund_table(matched, f"名称含「{keyword}」的基金", top=top)


@screen.command("signal")
@click.argument("signal_type", type=click.Choice(["BUY", "HOLD", "SELL"]))
def screen_signal(signal_type):
    """
    列出当前处于指定信号的所有指数及其代表性基金，例如：

    \b
    fund screen signal BUY    # 所有低估指数
    fund screen signal SELL   # 所有高估指数
    """
    sc = {"BUY": "green", "HOLD": "yellow", "SELL": "red"}[signal_type]
    console.print(f"\n[bold]当前 [{sc}]{signal_type}[/{sc}] 信号的指数：[/bold]\n")

    hit_indexes = []
    for code, info in INDEX_CATALOG.items():
        sig = get_valuation_signal(code)
        if sig and sig.signal == signal_type:
            hit_indexes.append((code, info["name"], sig))

    if not hit_indexes:
        console.print(f"[dim]当前没有处于 {signal_type} 信号的指数[/dim]")
        return

    t = Table(box=box.ROUNDED)
    t.add_column("指数", style="cyan")
    t.add_column("代码")
    t.add_column("PE", justify="right")
    t.add_column("PE百分位", justify="right")
    t.add_column("E/P%", justify="right")
    t.add_column("判断依据")

    for code, name, sig in hit_indexes:
        t.add_row(
            name, code,
            f"{sig.pe:.1f}" if sig.pe else "-",
            f"{sig.pe_percentile*100:.0f}%" if sig.pe_percentile else "-",
            f"{sig.earnings_yield_pct:.1f}%",
            sig.reason,
        )
    console.print(t)
    console.print(f"\n共 {len(hit_indexes)} 个指数处于 {signal_type} 区间")
