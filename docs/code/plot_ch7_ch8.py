"""第7-8章配图：定投平均成本、资产配置有效前沿、再平衡、追涨杀跌陷阱、最大回撤、夏普比率、仓位管理"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from plot_utils import *
import matplotlib.patches as mpatches

OUT = os.path.join(os.path.dirname(__file__), '..', 'docs', 'pic')


# ─────────────────────────────────────────────────────
# 图7-1  定投平均成本效应
# ─────────────────────────────────────────────────────
def ch7_dca_effect():
    months = np.arange(13)
    # 净值：先跌后涨
    nav = np.array([1.00, 0.92, 0.85, 0.78, 0.72, 0.75, 0.80, 0.90, 1.00, 1.05, 1.12, 1.18, 1.20])

    monthly = 500
    shares_dca = 0
    cost_dca   = 0
    share_list, cost_list = [0], [0]
    for n in nav[1:]:
        s = monthly / n
        shares_dca += s
        cost_dca   += monthly
        share_list.append(shares_dca)
        cost_list.append(cost_dca)

    # 一次性买入（第0月）
    lump_shares = 6000 / nav[0]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 6.5), sharex=True,
                                    gridspec_kw={'hspace': 0.08, 'height_ratios': [3,2]})

    ax1.plot(months, nav, lw=2.5, color=DARK, label='基金净值')
    avg_cost = np.array([cost_list[i]/share_list[i] if share_list[i]>0 else nav[0]
                         for i in range(len(months))])
    ax1.plot(months, avg_cost, lw=2, color=RED, ls='--', label='定投平均成本')
    ax1.axhline(nav[0], ls=':', color=BLUE, lw=1.5, label=f'一次性买入价 {nav[0]}元')
    ax1.fill_between(months, avg_cost, nav, where=nav>=avg_cost,
                     alpha=0.15, color=GREEN, label='浮盈区域')
    ax1.fill_between(months, avg_cost, nav, where=nav<avg_cost,
                     alpha=0.12, color=RED)
    apply_zh(ax1, ylabel='净值（元）')
    zh_legend(ax1, fontsize=9)
    ax1.grid(alpha=0.2); ax1.set_ylim(0.55, 1.35)

    dca_vals  = [s * n for s, n in zip(share_list, nav)]
    lump_vals = [lump_shares * n for n in nav]
    ax2.plot(months, dca_vals,  lw=2, color=RED,  label=f'定投终值 {dca_vals[-1]:.0f}元')
    ax2.plot(months, lump_vals, lw=2, color=BLUE, ls='--', label=f'一次性买入终值 {lump_vals[-1]:.0f}元')
    ax2.axhline(6000, ls=':', color=GRAY, lw=1.2)
    zh_text(ax2, 0.3, 6050, '6000元本金线', size=8.5, color=GRAY)
    ax2.set_ylim(3000, 8500)
    apply_zh(ax2, xlabel='月份', ylabel='资产价值（元）')
    zh_legend(ax2, fontsize=9)
    ax2.grid(alpha=0.2)

    plt.suptitle('定投平均成本效应——下跌时买更多份额，摊低成本',
                 fontproperties=zfont(12, bold=True))
    plt.savefig(f'{OUT}/ch7_dca_effect.png')
    plt.close()
    print('✓ ch7_dca_effect.png')


# ─────────────────────────────────────────────────────
# 图7-2  股债配置比例 风险收益散点+有效前沿
# ─────────────────────────────────────────────────────
def ch7_asset_allocation():
    ratios = [0, 20, 40, 50, 60, 80, 100]
    labels = ['全债(0:100)', '股20:债80', '股40:债60',
              '平衡(50:50)', '股60:债40', '股80:债20', '全股(100:0)']
    # 收益递增，波动递增但非线性
    rets = [4.0, 5.0, 6.0, 6.5, 7.2, 8.2, 9.0]
    risks= [4.5, 6.0, 8.0, 9.5, 11.5, 15.0, 18.0]
    sharpe = [(r-3)/v for r, v in zip(rets, risks)]
    colors = plt.cm.RdYlGn(np.linspace(0.15, 0.85, len(ratios)))

    fig, ax = plt.subplots(figsize=(8.5, 5.5))
    for x, y, lbl, c, sp in zip(risks, rets, labels, colors, sharpe):
        sc = ax.scatter(x, y, s=200, color=c, zorder=5, edgecolors='white', lw=1.5)
        zh_text(ax, x+0.3, y+0.1, lbl, size=9, color=DARK)

    # 有效前沿曲线（平滑）
    x_ef = np.linspace(4, 19, 100)
    y_ef = 3 + 0.5*np.sqrt(x_ef) + 0.02*x_ef
    ax.plot(x_ef, y_ef, ls='--', color=GRAY, lw=1.5, label='有效前沿')

    # 最佳夏普点
    best_idx = np.argmax(sharpe)
    ax.scatter(risks[best_idx], rets[best_idx], s=350, marker='*',
               color=YELLOW, zorder=6, edgecolors=DARK, lw=1)
    zh_text(ax, risks[best_idx]+0.5, rets[best_idx]-0.5, '★最优夏普比率', size=9.5,
            color=DARK, bold=True)

    ax.set_xlim(2, 22); ax.set_ylim(2, 11)
    apply_zh(ax, title='不同股债配置比例的风险收益特征',
             xlabel='年化波动率（%）', ylabel='预期年化收益率（%）')
    zh_legend(ax)
    ax.grid(alpha=0.22)
    plt.tight_layout()
    plt.savefig(f'{OUT}/ch7_asset_allocation.png')
    plt.close()
    print('✓ ch7_asset_allocation.png')


# ─────────────────────────────────────────────────────
# 图7-3  再平衡示意
# ─────────────────────────────────────────────────────
def ch7_rebalance():
    years = ['初始', '1年后\n（未再平衡）', '再平衡后']
    stocks = [60, 72, 60]
    bonds  = [40, 28, 40]

    fig, axes = plt.subplots(1, 3, figsize=(9, 4.5))
    colors_map = {'股票基金': RED, '债券基金': BLUE}

    for ax, yr, s, b in zip(axes, years, stocks, bonds):
        wedges, texts, autotexts = ax.pie(
            [s, b], colors=[RED, BLUE],
            autopct='%1.0f%%', startangle=90,
            wedgeprops=dict(edgecolor='white', lw=2),
            pctdistance=0.7
        )
        for t in autotexts:
            t.set_fontproperties(zfont(11, bold=True))
            t.set_color('white')
        apply_zh(ax, title=yr)

    axes[0].set_title('初始配置', fontproperties=zfont(11, bold=True))
    axes[1].set_title('1年后（股票涨）\n股72% 债28%', fontproperties=zfont(10))
    axes[2].set_title('再平衡后\n恢复60:40', fontproperties=zfont(10))

    # 图例
    from matplotlib.patches import Patch
    patches = [Patch(color=RED, label='股票基金'), Patch(color=BLUE, label='债券基金')]
    fig.legend(handles=patches, loc='lower center', ncol=2,
               prop=zfont(10), bbox_to_anchor=(0.5, -0.05))

    # 箭头
    fig.text(0.37, 0.5, '市场波动\n仓位漂移', ha='center', va='center',
             fontproperties=zfont(9), color=ORANGE,
             bbox=dict(fc=ORANGE, alpha=0.15, boxstyle='rarrow,pad=0.3'))
    fig.text(0.63, 0.5, '再平衡\n高卖低买', ha='center', va='center',
             fontproperties=zfont(9), color=GREEN,
             bbox=dict(fc=GREEN, alpha=0.15, boxstyle='larrow,pad=0.3'))

    plt.suptitle('再平衡操作示意——强制执行"高卖低买"',
                 fontproperties=zfont(12, bold=True), y=1.02)
    plt.tight_layout()
    plt.savefig(f'{OUT}/ch7_rebalance.png')
    plt.close()
    print('✓ ch7_rebalance.png')


# ─────────────────────────────────────────────────────
# 图7-4  追涨杀跌陷阱
# ─────────────────────────────────────────────────────
def ch7_chase_trap():
    np.random.seed(55)
    months = np.arange(25)
    # 基金净值
    nav = np.array([1.00, 1.05, 1.12, 1.20, 1.28, 1.30, 1.25, 1.15, 1.05,
                    0.92, 0.78, 0.72, 0.70, 0.75, 0.85, 0.95, 1.05, 1.15,
                    1.10, 1.05, 0.95, 0.85, 0.82, 0.78, 0.80])

    # 散户操作
    events = [
        (5,  nav[5],  '追涨\n买入\n1.30', RED,    '^', 12),
        (11, nav[11], '恐慌\n割肉\n0.72', BLUE,   'v', 12),
        (17, nav[17], '再次\n追入\n1.15', RED,    '^', 12),
        (22, nav[22], '再次\n止损\n0.85', BLUE,   'v', 12),
    ]

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(months, nav, lw=2.5, color=DARK, zorder=3, label='基金净值')
    ax.axhline(1.0, ls=':', color=GRAY, lw=1)

    for m, n, lbl, c, mk, sz in events:
        ax.scatter(m, n, s=sz*15, color=c, marker=mk, zorder=5, edgecolors='white', lw=1.5)
        offset = 0.05 if mk == '^' else -0.12
        zh_text(ax, m, n+offset, lbl, size=8.5, color=c, ha='center', bold=True)

    # 持有不动
    ax.annotate(f'持有不动收益：+{(nav[-1]/nav[0]-1)*100:.0f}%',
                xy=(24, nav[-1]), xytext=(18, 1.4),
                fontproperties=zfont(10, bold=True), color=GREEN,
                arrowprops=dict(arrowstyle='->', color=GREEN, lw=1.5))

    # 散户结果
    buy1 = 1.30; sell1 = 0.72; buy2 = 1.15; sell2 = 0.85
    total_loss = ((sell1/buy1 - 1) + (sell2/buy2 - 1)) * 50  # 概念上
    zh_text(ax, 12, 0.62, f'散户追涨杀跌两轮操作\n累计损失约 -15%', size=9.5,
            color=RED, ha='center', bold=True,
            bbox=dict(fc=RED, alpha=0.1, boxstyle='round'))

    ax.set_xlim(0, 24); ax.set_ylim(0.55, 1.55)
    apply_zh(ax, title='追涨杀跌陷阱——同一只基金，不同操作，结果迥异',
             xlabel='月份', ylabel='净值（元）')
    ax.grid(alpha=0.2)
    plt.tight_layout()
    plt.savefig(f'{OUT}/ch7_chase_trap.png')
    plt.close()
    print('✓ ch7_chase_trap.png')


# ─────────────────────────────────────────────────────
# 图8-1  最大回撤示意
# ─────────────────────────────────────────────────────
def ch8_drawdown():
    np.random.seed(9)
    months = np.arange(62)
    ret = np.random.normal(0.007, 0.05, 61)
    nav = 1.0 * np.cumprod(np.concatenate([[1], 1+ret]))

    # 计算最大回撤
    peak_idx, trough_idx = 0, 0
    max_dd = 0
    running_peak = nav[0]
    rp_idx = 0
    for i in range(1, len(nav)):
        if nav[i] > running_peak:
            running_peak = nav[i]; rp_idx = i
        dd = (nav[i] - running_peak) / running_peak
        if dd < max_dd:
            max_dd = dd; peak_idx = rp_idx; trough_idx = i

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(months, nav, lw=2, color=BLUE, label='基金净值')

    # 标注最大回撤区域
    ax.fill_between(months[peak_idx:trough_idx+1],
                    nav[peak_idx:trough_idx+1],
                    nav[peak_idx], alpha=0.25, color=RED, label=f'最大回撤区间')
    ax.annotate(f'峰值: {nav[peak_idx]:.2f}',
                xy=(months[peak_idx], nav[peak_idx]),
                xytext=(months[peak_idx]-5, nav[peak_idx]+0.08),
                fontproperties=zfont(9.5), color=DARK,
                arrowprops=dict(arrowstyle='->', color=DARK, lw=1.2))
    ax.annotate(f'谷值: {nav[trough_idx]:.2f}',
                xy=(months[trough_idx], nav[trough_idx]),
                xytext=(months[trough_idx]+2, nav[trough_idx]-0.12),
                fontproperties=zfont(9.5), color=RED,
                arrowprops=dict(arrowstyle='->', color=RED, lw=1.2))

    mid_m = (months[peak_idx] + months[trough_idx]) // 2
    mid_n = (nav[peak_idx] + nav[trough_idx]) / 2
    zh_text(ax, mid_m+2, mid_n, f'最大回撤\n{max_dd*100:.1f}%', size=10, bold=True,
            color=RED, ha='left',
            bbox=dict(fc=RED, alpha=0.12, boxstyle='round'))

    apply_zh(ax, title='基金净值最大回撤示意图',
             xlabel='月份', ylabel='净值（元）')
    zh_legend(ax); ax.grid(alpha=0.2)
    plt.tight_layout()
    plt.savefig(f'{OUT}/ch8_drawdown.png')
    plt.close()
    print('✓ ch8_drawdown.png')


# ─────────────────────────────────────────────────────
# 图8-2  夏普比率对比
# ─────────────────────────────────────────────────────
def ch8_sharpe_comparison():
    funds = ['基金A\n高收益高波动', '基金B\n中收益低波动', '基金C\n低收益低波动']
    rets  = [18, 12, 6.5]
    vols  = [28, 10, 5]
    rf    = 2.5
    sharpes = [(r-rf)/v for r, v in zip(rets, vols)]
    colors  = [RED, GREEN, BLUE]

    fig, axes = plt.subplots(1, 3, figsize=(11, 5), gridspec_kw={'wspace': 0.35})

    # 柱1：收益率
    ax1 = axes[0]
    bars = ax1.bar(funds, rets, color=colors, edgecolor='white', lw=1.5, width=0.5)
    for bar, v in zip(bars, rets):
        zh_text(ax1, bar.get_x()+bar.get_width()/2, v+0.3, f'{v}%', size=11, bold=True,
                ha='center', color=DARK)
    apply_zh(ax1, title='年化收益率（%）', ylabel='%')
    ax1.set_ylim(0, 23)
    for tick in ax1.get_xticklabels(): tick.set_fontproperties(zfont(9))

    # 柱2：波动率
    ax2 = axes[1]
    bars2 = ax2.bar(funds, vols, color=colors, edgecolor='white', lw=1.5, width=0.5)
    for bar, v in zip(bars2, vols):
        zh_text(ax2, bar.get_x()+bar.get_width()/2, v+0.4, f'{v}%', size=11, bold=True,
                ha='center', color=DARK)
    apply_zh(ax2, title='年化波动率（%）', ylabel='%')
    ax2.set_ylim(0, 35)
    for tick in ax2.get_xticklabels(): tick.set_fontproperties(zfont(9))

    # 柱3：夏普
    ax3 = axes[2]
    bars3 = ax3.bar(funds, sharpes, color=colors, edgecolor='white', lw=1.5, width=0.5)
    for bar, v in zip(bars3, sharpes):
        zh_text(ax3, bar.get_x()+bar.get_width()/2, v+0.02, f'{v:.2f}', size=11, bold=True,
                ha='center', color=DARK)
    ax3.axhline(1.0, ls='--', color=GRAY, lw=1.5)
    zh_text(ax3, 2.45, 1.02, '≥1=优秀', size=8.5, color=GRAY)
    apply_zh(ax3, title='夏普比率（越高越好）', ylabel='夏普比率')
    ax3.set_ylim(0, 1.4)
    for tick in ax3.get_xticklabels(): tick.set_fontproperties(zfont(9))

    plt.suptitle('夏普比率：衡量单位风险的超额收益（无风险利率=2.5%）',
                 fontproperties=zfont(12, bold=True))
    plt.savefig(f'{OUT}/ch8_sharpe_comparison.png')
    plt.close()
    print('✓ ch8_sharpe_comparison.png')


# ─────────────────────────────────────────────────────
# 图8-3  仓位管理
# ─────────────────────────────────────────────────────
def ch8_position_sizing():
    types = ['保守型', '平衡型', '进取型']
    components = {
        '权益基金': [25, 50, 70],
        '债券基金': [45, 35, 20],
        '货币基金\n（应急）': [25, 10, 5],
        '现金缓冲': [5, 5, 5],
    }
    colors_map = [RED, BLUE, GREEN, GRAY]

    fig, axes = plt.subplots(1, 3, figsize=(10, 4.5))
    for ax, t in zip(axes, range(3)):
        vals  = [components[k][t] for k in components]
        names = list(components.keys())
        wedges, texts, autotexts = ax.pie(
            vals, colors=colors_map,
            autopct='%1.0f%%', startangle=90,
            wedgeprops=dict(edgecolor='white', lw=2),
            pctdistance=0.72
        )
        for autot in autotexts:
            autot.set_fontproperties(zfont(9.5, bold=True))
            autot.set_color('white')
        ax.set_title(types[t], fontproperties=zfont(12, bold=True))

    from matplotlib.patches import Patch
    patches = [Patch(color=c, label=n.replace('\n','')) for n, c in zip(components, colors_map)]
    fig.legend(handles=patches, loc='lower center', ncol=4, prop=zfont(9),
               bbox_to_anchor=(0.5, -0.06))
    plt.suptitle('不同风险类型投资者的仓位配置方案',
                 fontproperties=zfont(12, bold=True), y=1.02)
    plt.tight_layout()
    plt.savefig(f'{OUT}/ch8_position_sizing.png')
    plt.close()
    print('✓ ch8_position_sizing.png')


if __name__ == '__main__':
    ch7_dca_effect()
    ch7_asset_allocation()
    ch7_rebalance()
    ch7_chase_trap()
    ch8_drawdown()
    ch8_sharpe_comparison()
    ch8_position_sizing()
    print('第7-8章配图全部生成完毕')
