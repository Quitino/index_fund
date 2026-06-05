"""模拟持有收益报告生成。"""
from datetime import date
import pandas as pd
from strategy.formulas import xirr, max_drawdown, sharpe_ratio, annualized_return


def build_report(df: pd.DataFrame, code: str, plan_desc: str) -> dict:
    """
    从模拟快照 DataFrame 生成完整收益报告。
    返回结构化 dict，供 CLI 渲染。
    """
    if df.empty:
        return {}

    last = df.iloc[-1]
    first = df.iloc[0]

    cost_total = last["cost_total"]
    market_value = last["market_value"]
    pnl = market_value - cost_total
    cum_return = last["cumulative_return"]

    # XIRR 现金流构建：买入为负，期末市值为正
    cashflows = []
    cumulative_invested = 0.0
    for _, r in df.iterrows():
        if r["invested_today"] > 0:
            cashflows.append((r["date"], -r["invested_today"]))
            cumulative_invested += r["invested_today"]
    cashflows.append((last["date"], market_value))
    xirr_rate = xirr(cashflows)

    # 最大回撤（基于每日市值）
    mdd = max_drawdown(df["market_value"].tolist())

    # 夏普比率（基于每日收益率）
    daily_returns = df["market_value"].pct_change().dropna().tolist()
    sharpe = sharpe_ratio(daily_returns)

    # 持有天数
    hold_days = (last["date"] - first["date"]).days or 1
    ann_return = annualized_return(cum_return, hold_days)

    # 买入持有对比：若一次性在 start_date 买入，收益如何
    start_nav = first["nav"]
    end_nav = last["nav"]
    buy_hold_return = (end_nav - start_nav) / start_nav if start_nav > 0 else 0.0

    # 投入次数
    invest_count = int((df["invested_today"] > 0).sum())

    return {
        "code": code,
        "plan": plan_desc,
        "start_date": first["date"],
        "end_date": last["date"],
        "hold_days": hold_days,
        "invest_count": invest_count,
        "cost_total": cost_total,
        "market_value": market_value,
        "pnl": pnl,
        "cumulative_return_pct": cum_return * 100,
        "annualized_return_pct": ann_return * 100,
        "xirr_pct": xirr_rate * 100 if xirr_rate is not None else None,
        "max_drawdown_pct": mdd * 100,
        "sharpe": sharpe,
        "buy_hold_return_pct": buy_hold_return * 100,
        "vs_buy_hold_pct": (cum_return - buy_hold_return) * 100,
        "df": df,
    }


def format_report(r: dict) -> str:
    """将报告 dict 格式化为终端文本。"""
    if not r:
        return "无数据"

    sign = "+" if r["pnl"] >= 0 else ""
    xirr_str = f"{r['xirr_pct']:+.1f}%" if r["xirr_pct"] is not None else "N/A"
    sharpe_str = f"{r['sharpe']:.2f}" if r["sharpe"] is not None else "N/A"
    vs_str = f"{r['vs_buy_hold_pct']:+.1f}%（{'超越' if r['vs_buy_hold_pct'] >= 0 else '跑输'}买入持有）"

    return f"""
╔══════════════════════════════════════════════╗
  模拟持有报告：{r['code']}  {r['plan']}
╠══════════════════════════════════════════════╣
  区间：{r['start_date']} → {r['end_date']}（{r['hold_days']}天）
  投入次数：{r['invest_count']} 次
  累计投入：{r['cost_total']:>12,.2f} 元
  当前市值：{r['market_value']:>12,.2f} 元
  累计盈亏：{sign}{r['pnl']:>10,.2f} 元（{sign}{r['cumulative_return_pct']:.1f}%）
──────────────────────────────────────────────
  年化收益：{r['annualized_return_pct']:+.1f}%
  XIRR：    {xirr_str}
  最大回撤：{r['max_drawdown_pct']:.1f}%
  夏普比率：{sharpe_str}
──────────────────────────────────────────────
  买入持有：{r['buy_hold_return_pct']:+.1f}%
  对比：    {vs_str}
╚══════════════════════════════════════════════╝""".strip()
