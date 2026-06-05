"""第10-13章配图：平台雷达、渠道费率、资金分层、行为成本"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from plot_utils import *
import matplotlib.patches as mpatches

OUT = os.path.join(os.path.dirname(__file__), '..', 'docs', 'pic')


# ─────────────────────────────────────────────────────
# 图10  各平台功能对比雷达图
# ─────────────────────────────────────────────────────
def ch10_platform_comparison():
    cats = ['数据完整性', '免费程度', '易用性', '专业深度', '社区活跃度']
    N = len(cats)
    angles = np.linspace(0, 2*np.pi, N, endpoint=False).tolist()
    angles += angles[:1]

    platforms = {
        '天天基金': ([5, 4.5, 5, 3.5, 3.5], BLUE),
        '晨星中国': ([4, 2.5, 3, 5, 2],     ORANGE),
        '雪球':     ([3.5, 4.5, 4.5, 3, 5], RED),
        'AKShare':  ([4.5, 5, 3, 4.5, 2],   GREEN),
    }

    fig, ax = plt.subplots(figsize=(7, 6.5), subplot_kw=dict(polar=True))
    for name, (vals, c) in platforms.items():
        v = vals + vals[:1]
        ax.plot(angles, v, lw=2, color=c, label=name)
        ax.fill(angles, v, color=c, alpha=0.1)

    ax.set_ylim(0, 5.5)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(cats, fontproperties=zfont(10.5))
    ax.set_yticklabels(['1','2','3','4','5'], fontproperties=zfont(7.5))

    apply_zh(ax, title='主要基金信息平台功能对比')
    zh_legend(ax, loc='upper right', bbox_to_anchor=(1.38, 1.15))
    plt.tight_layout()
    plt.savefig(f'{OUT}/ch10_platform_comparison.png')
    plt.close()
    print('✓ ch10_platform_comparison.png')


# ─────────────────────────────────────────────────────
# 图11-1  各渠道费率对比
# ─────────────────────────────────────────────────────
def ch11_fee_comparison():
    channels  = ['银行\n（不打折）', '基金直销', '天天基金\n(1折)', '支付宝', '券商\n(ETF佣金)']
    fees_eq   = [1.2, 1.0, 0.12, 0.12, 0.025]  # 股票型申购费%
    colors    = [RED, ORANGE, GREEN, GREEN, BLUE]

    fig, ax = plt.subplots(figsize=(8.5, 4.5))
    bars = ax.bar(channels, fees_eq, color=colors, edgecolor='white', lw=1.5, width=0.55)
    for bar, v in zip(bars, fees_eq):
        zh_text(ax, bar.get_x()+bar.get_width()/2, v+0.02, f'{v}%',
                size=11, bold=True, ha='center', color=DARK)

    ax.set_ylim(0, 1.5)
    apply_zh(ax, title='各渠道股票型基金申购费对比（%）',
             ylabel='申购费率（%）')
    for tick in ax.get_xticklabels():
        tick.set_fontproperties(zfont(10))
    ax.grid(axis='y', alpha=0.25)

    # 节省标注
    zh_text(ax, 0, 1.28, '← 银行渠道比1折平台', size=9, color=RED, style='italic')
    zh_text(ax, 0, 1.18, '   多花约 1080元/10万', size=9, color=RED)

    plt.tight_layout()
    plt.savefig(f'{OUT}/ch11_fee_comparison.png')
    plt.close()
    print('✓ ch11_fee_comparison.png')


# ─────────────────────────────────────────────────────
# 图11-2  购买渠道选择矩阵（散点图）
# ─────────────────────────────────────────────────────
def ch11_channel_matrix():
    channels = ['银行', '基金直销', '天天基金', '支付宝/微信', '券商(ETF)']
    ease     = [5, 3, 5, 5, 3]        # 操作便捷度
    cost     = [1, 3, 5, 4.5, 5]      # 低费率（高=好）
    colors   = [RED, ORANGE, GREEN, BLUE, PURPLE]
    sizes    = [200, 180, 300, 280, 250]

    fig, ax = plt.subplots(figsize=(7, 5.5))
    for c, e, co, cl, s in zip(channels, ease, cost, colors, sizes):
        ax.scatter(e, co, s=s, color=cl, zorder=5, edgecolors='white', lw=1.5)
        zh_text(ax, e+0.05, co+0.1, c, size=10, color=cl)

    ax.axvline(3.5, ls='--', color=GRAY, lw=1.2)
    ax.axhline(3.5, ls='--', color=GRAY, lw=1.2)
    zh_text(ax, 1.5, 1.5, '高费+繁琐\n（避免）', size=9, color=GRAY, ha='center')
    zh_text(ax, 4.5, 4.5, '低费+简便\n（最优）', size=9, color=GREEN, ha='center', bold=True)

    ax.set_xlim(1, 6); ax.set_ylim(0.5, 6)
    apply_zh(ax, title='基金购买渠道选择矩阵',
             xlabel='操作便捷度（高=好）', ylabel='费率低廉度（高=好）')
    ax.grid(alpha=0.2)
    plt.tight_layout()
    plt.savefig(f'{OUT}/ch11_channel_matrix.png')
    plt.close()
    print('✓ ch11_channel_matrix.png')


# ─────────────────────────────────────────────────────
# 图12  资金分层管理
# ─────────────────────────────────────────────────────
def ch12_money_layers():
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.set_xlim(0, 10); ax.set_ylim(0, 7.5)
    ax.set_axis_off()

    layers = [
        (5, 1.2, 7, 1.1, GREEN,  '第一层：活钱（流动性层）',
         '货币基金 / 活期存款 | 3~6个月生活费 | T+0/T+1随时取'),
        (5, 2.8, 7, 1.1, BLUE,   '第二层：稳钱（保值层）',
         '短债/纯债基金 / 定存 | 1~3年不动用 | 年化3~5%'),
        (5, 4.4, 7, 1.1, ORANGE, '第三层：投资钱（增值层）',
         '宽基指数 / 主动基金 | 3年以上不动用 | 目标年化8~12%'),
        (5, 6.0, 7, 1.1, RED,    '可选第四层：进取层（冒险资本）',
         '行业基金 / 个股 | 可全损不影响生活 | 不超过总资产5~10%'),
    ]

    percents = ['20~30%', '30~40%', '30~40%', '5~10%']
    for (cx,cy,w,h,c,title,detail), pct in zip(layers, percents):
        rect = mpatches.FancyBboxPatch((cx-w/2, cy-h/2), w, h,
                                   boxstyle='round,pad=0.1',
                                   fc=c, ec='white', lw=2, alpha=0.9, zorder=3)
        ax.add_patch(rect)
        zh_text(ax, cx, cy+0.22, title, size=11, bold=True, ha='center', color='white')
        zh_text(ax, cx, cy-0.22, detail, size=8.5, ha='center', color='white')
        zh_text(ax, cx-3.8, cy, pct, size=10, bold=True, ha='center',
                color=c, bbox=dict(fc='white', ec=c, boxstyle='round', alpha=0.9))

    zh_text(ax, 5, 7.1, '资金分层管理框架（金字塔模型）',
            size=13, bold=True, ha='center', color=DARK)
    # 箭头
    for y in [1.7, 3.35, 4.95]:
        ax.annotate('', xy=(5, y+0.05), xytext=(5, y-0.02),
                    arrowprops=dict(arrowstyle='->', color=GRAY, lw=1.5))
    plt.tight_layout(pad=0.3)
    plt.savefig(f'{OUT}/ch12_money_layers.png')
    plt.close()
    print('✓ ch12_money_layers.png')


# ─────────────────────────────────────────────────────
# 图13  行为偏差导致的收益损耗
# ─────────────────────────────────────────────────────
def ch13_behavior_cost():
    years = np.arange(0, 11)
    P = 10  # 万元
    base_ret = 0.08

    scenarios = [
        ('买入持有', base_ret,       0,     DARK),
        ('每年换仓1次', base_ret, 0.006,  BLUE),
        ('每季换仓', base_ret,   0.018,   ORANGE),
        ('每月换仓', base_ret,   0.036,   RED),
    ]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 5))
    finals = []
    for name, ret, cost, c in scenarios:
        net_ret = ret - cost
        vals = P * ((1+net_ret)**years)
        ax1.plot(years, vals, lw=2.2, color=c, label=name)
        finals.append((name, vals[-1], c))

    ax1.set_xlim(0, 10); ax1.set_ylim(0)
    apply_zh(ax1, title='频繁换仓 vs 买入持有（10万元·8%·10年）',
             xlabel='年数', ylabel='资产（万元）')
    zh_legend(ax1, fontsize=9)
    ax1.grid(alpha=0.22)

    names2, vals2, cols2 = zip(*finals)
    bars = ax2.bar(names2, vals2, color=cols2, edgecolor='white', lw=1.5, width=0.55)
    for bar, v in zip(bars, vals2):
        zh_text(ax2, bar.get_x()+bar.get_width()/2, v+0.15, f'{v:.1f}万',
                size=10, bold=True, ha='center', color=DARK)
    ax2.set_ylim(0, 24)
    apply_zh(ax2, title='10年后终值对比', ylabel='万元')
    for tick in ax2.get_xticklabels():
        tick.set_fontproperties(zfont(9))
        tick.set_rotation(10)
    ax2.grid(axis='y', alpha=0.22)

    plt.suptitle('行为成本量化——频繁换仓的隐性代价',
                 fontproperties=zfont(12, bold=True))
    plt.tight_layout()
    plt.savefig(f'{OUT}/ch13_behavior_cost.png')
    plt.close()
    print('✓ ch13_behavior_cost.png')


if __name__ == '__main__':
    ch10_platform_comparison()
    ch11_fee_comparison()
    ch11_channel_matrix()
    ch12_money_layers()
    ch13_behavior_cost()
    print('第10-13章配图全部生成完毕')
