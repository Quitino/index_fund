"""
批量下载命令，对 data/batch_downloader.py 的 CLI 封装。

fund batch etf                        # 下载所有ETF历史净值
fund batch index                      # 下载所有指数型场外基金
fund batch index --index 000300       # 只下载跟踪沪深300的基金
fund batch update                     # 增量更新DB中已有数据
fund batch status                     # 查看DB当前数据概况
"""
import click
from rich.console import Console
from rich.table import Table
from rich import box

console = Console()


@click.group()
def batch():
    """批量下载历史净值"""


@batch.command("etf")
@click.option("--dry-run", is_flag=True, help="只预览数量，不实际下载")
@click.option("--no-skip", is_flag=True, help="强制重下，忽略已有数据")
def batch_etf(dry_run, no_skip):
    """下载所有 ETF 历史净值（约1500只，预计40分钟）"""
    from data.batch_downloader import get_etf_list, batch_download, estimate_time, estimate_size_mb
    import akshare as ak
    with console.status("获取 ETF 列表..."):
        codes = get_etf_list()

    console.print(f"[bold]目标：所有 ETF ({len(codes)} 只)[/bold]")
    console.print(f"预计时间：{estimate_time(len(codes))}")
    console.print(f"预计数据量：{estimate_size_mb(len(codes))} MB")

    if dry_run:
        console.print(f"\n[dim][dry-run] 前10个代码: {codes[:10]}[/dim]")
        return

    if not click.confirm("\n确认开始下载？"):
        return

    result = batch_download(codes, skip_existing=not no_skip)
    _print_result(result)


@batch.command("index")
@click.option("--index", "index_code", default=None, help="指定跟踪指数代码（如 000300），留空下载全部指数型基金")
@click.option("--dry-run", is_flag=True)
@click.option("--no-skip", is_flag=True)
def batch_index(index_code, dry_run, no_skip):
    """
    下载指数型场外基金历史净值，例如：

    \b
    fund batch index                     # 全部指数型（约4000只，预计3小时）
    fund batch index --index 000300      # 只下载跟踪沪深300的基金（约140只，5分钟）
    fund batch index --index 000905      # 中证500
    """
    from data.batch_downloader import (
        get_index_fund_list, get_funds_by_index,
        batch_download, estimate_time, estimate_size_mb
    )
    from data.index_catalog import INDEX_CATALOG

    if index_code:
        info = INDEX_CATALOG.get(index_code)
        if not info:
            console.print(f"[red]不支持的指数代码 {index_code}[/red]")
            console.print(f"[dim]支持：{', '.join(INDEX_CATALOG.keys())}[/dim]")
            return
        with console.status(f"获取跟踪 {info['name']} 的基金列表..."):
            codes = get_funds_by_index(index_code)
        desc = f"跟踪 {info['name']}({index_code}) 的基金（{len(codes)} 只）"
    else:
        with console.status("获取全量指数型基金列表..."):
            codes = get_index_fund_list()
        desc = f"全部指数型场外基金（{len(codes)} 只）"

    console.print(f"[bold]目标：{desc}[/bold]")
    console.print(f"预计时间：{estimate_time(len(codes))}")
    console.print(f"预计数据量：{estimate_size_mb(len(codes))} MB")

    if dry_run:
        console.print(f"\n[dim][dry-run] 前10个代码: {codes[:10]}[/dim]")
        return

    if not click.confirm("\n确认开始下载？"):
        return

    result = batch_download(codes, skip_existing=not no_skip)
    _print_result(result)


@batch.command("update")
def batch_update():
    """增量更新 DB 中已有数据的所有基金（补全缺失的最新净值）"""
    from data.batch_downloader import get_existing_codes, batch_download, estimate_time

    with console.status("读取 DB 中已有基金..."):
        codes = get_existing_codes()

    if not codes:
        console.print("[yellow]DB 中暂无基金数据，请先运行 fund batch etf 或 fund batch index[/yellow]")
        return

    console.print(f"[bold]增量更新 {len(codes)} 只基金[/bold]")
    console.print(f"预计时间（最长）：{estimate_time(len(codes))}")
    console.print("[dim]已是最新的基金会自动跳过[/dim]\n")

    result = batch_download(codes, skip_existing=True)
    _print_result(result)


@batch.command("status")
def batch_status():
    """查看 DB 中净值数据的当前概况"""
    import sqlite3
    from config.settings import DB_PATH

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("SELECT COUNT(DISTINCT code) FROM nav_history")
    fund_count = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM nav_history")
    row_count = cur.fetchone()[0]

    cur.execute("SELECT MIN(date), MAX(date) FROM nav_history")
    min_date, max_date = cur.fetchone()

    cur.execute("""
        SELECT code, COUNT(*) as cnt, MIN(date) as start, MAX(date) as end
        FROM nav_history GROUP BY code ORDER BY cnt DESC LIMIT 10
    """)
    top10 = cur.fetchall()

    cur.execute("""
        SELECT code, MAX(date) as latest FROM nav_history
        GROUP BY code ORDER BY latest ASC LIMIT 5
    """)
    stale5 = cur.fetchall()
    conn.close()

    # 文件大小
    import os
    size_mb = os.path.getsize(DB_PATH) / 1024 / 1024

    console.print(f"\n[bold]DB 数据概况[/bold]  ({DB_PATH})\n")
    t = Table(show_header=False, box=box.SIMPLE)
    t.add_column("", style="cyan")
    t.add_column("")
    t.add_row("基金数量", str(fund_count))
    t.add_row("净值条数", f"{row_count:,}")
    t.add_row("日期范围", f"{min_date} ~ {max_date}")
    t.add_row("DB 文件大小", f"{size_mb:.1f} MB")
    console.print(t)

    if top10:
        t2 = Table(title="数据最多的10只基金", box=box.ROUNDED)
        t2.add_column("代码", style="cyan")
        t2.add_column("条数", justify="right")
        t2.add_column("起始日期")
        t2.add_column("最新日期")
        for code, cnt, start, end in top10:
            t2.add_row(code, str(cnt), str(start), str(end))
        console.print(t2)

    if stale5:
        console.print("\n[yellow]最旧的5只基金（可能需要更新）：[/yellow]")
        for code, latest in stale5:
            console.print(f"  {code}  最新: {latest}")


def _print_result(result: dict):
    color = "green" if result["fail"] == 0 else "yellow"
    console.print(f"\n[{color} bold]完成！[/{color} bold]  "
                  f"成功 {result['success']}  跳过 {result['skip']}  失败 {result['fail']}")
    if result["fail_codes"]:
        console.print(f"[red]失败代码（前20）：{result['fail_codes'][:20]}[/red]")
        from pathlib import Path
        Path("failed_codes.txt").write_text("\n".join(result["fail_codes"]))
        console.print("[dim]失败代码已写入 failed_codes.txt[/dim]")
