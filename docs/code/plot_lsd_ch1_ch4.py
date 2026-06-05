"""
《指数基金投资指南》银行螺丝钉
第1-4章配图：资产类型对比、指数基金三大优势、宽基指数特点、估值方法图解
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from plot_utils import *
import matplotlib.patches as mpatches

OUT = os.path.join(os.path.dirname(__file__), '..', 'docs', 'pic')
os.makedirs(OUT, exist_ok=True)

# ─────────────────────────────────────────────────────
# 图1-1  1802~2002年各类资产增值对比（西格尔数据复现）
# ─────────────────────────────────────────────────────
def lsd_ch1_asset_comparison():
    assets  = ['黄金', '短期债券', '长期债券', '股票']
    values  = [4.52, 281, 1778, 704997]
    colors  = [YELLOW, TEAL, BLUE, RED]

    fig, ax = plt.subplots(figsize=(8.5, 5.5))
    bars = ax.bar(assets, values, color=colors, edgecolor='white', lw=1.8, width=0.55)
    ax.set_yscale('log')

    for bar, v in zip(bars, values):
        label = f'${v:,}' if v >= 1000 else f'${v}'
        ax.text(bar.get_x()+bar.get_width()/2, v*1.5, label,
                fontproperties=zfont(11, bold=True), ha='center', color=bar.get_facecolor())

    apply_zh(ax, title='1802~2002年，1美元投入各类资产200年后的价值（西格尔数据）',
             xlabel='投资类别', ylabel='终值（美元，对数轴）')
    for tick in ax.get_xticklabels():
        tick.set_fontproperties(zfont(12))
    ax.grid(axis='y', alpha=0.25)
    ax.set_ylim(1, 5e6)

    zh_text(ax, '股票', 704997*3, '股票200年上涨\n约70万倍！',
            size=10, bold=True, color=RED, ha='center')
    plt.tight_layout()
    plt.savefig(f'{OUT}/lsd_ch1_asset_comparison.png')
    plt.close()
    print('✓ lsd_ch1_asset_comparison.png')


# ─────────────────────────────────────────────────────
# 图1-2  复利计算公式示意——终值 = 本金×(1+r)^n
# ─────────────────────────────────────────────────────
def lsd_ch1_compound_power():
    years = np.arange(0, 41)
    P = 10  # 万元
    scenarios = [
        ('年化5%（低收益）',  0.05, BLUE),
        ('年化10%（中收益）', 0.10, GREEN),
        ('年化13%（高收益）', 0.13, RED),
        ('年化20%（巴菲特）', 0.20, PURPLE),
    ]

    fig, ax = plt.subplots(figsize=(9, 5))
    for lbl, r, c in scenarios:
        v = P * (1+r)**years
        ax.plot(years, v, lw=2.2, color=c, label=f'{lbl}  →40年≈{v[-1]:.0f}万')

    ax.set_xlim(0, 40); ax.set_ylim(0)
    apply_zh(ax, title='复利的威力——10万元在不同年化收益率下40年的增长',
             xlabel='年数', ylabel='资产（万元）')
    zh_legend(ax, loc='upper left', fontsize=9.5)
    ax.grid(alpha=0.2)

    # 公式标注
    zh_text(ax, 21, 220, r'终值 = 本金 × (1 + r)ⁿ', size=11, bold=True,
            color=DARK, bbox=dict(fc='white', ec=DARK, boxstyle='round', alpha=0.8))
    plt.tight_layout()
    plt.savefig(f'{OUT}/lsd_ch1_compound_power.png')
    plt.close()
    print('✓ lsd_ch1_compound_power.png')


# ─────────────────────────────────────────────────────
# 图2-1  指数基金三大优势示意
# ─────────────────────────────────────────────────────
def lsd_ch2_three_advantages():
    fig, axes = plt.subplots(1, 3, figsize=(12, 5))

    # 优势1：长生不老（新陈代谢示意）
    ax = axes[0]
    ax.set_xlim(0, 10); ax.set_ylim(0, 8); ax.set_axis_off()
    def box(cx, cy, w, h, c, text, fsize=10):
        r = plt.Rectangle((cx-w/2, cy-h/2), w, h, fc=c, ec='white', lw=1.5, alpha=0.9, zorder=3)
        ax.add_patch(r)
        zh_text(ax, cx, cy, text, size=fsize, bold=True, ha='center', va='center', color='white')
    box(5, 6.5, 8, 0.9, RED, '指数（不断更新成分股）', 11)
    for i, (name, c) in enumerate([('衰落公司', GRAY), ('新龙头', GREEN), ('老龙头', BLUE),
                                     ('新兴企业', ORANGE), ('稳健企业', TEAL)]):
        cx = 1.5 + i * 1.8
        box(cx, 4.5, 1.5, 0.75, c, name, 8)
    zh_text(ax, 5, 3.2, '↑ 踢出弱者，纳入强者', size=9.5, ha='center', color=DARK)
    zh_text(ax, 5, 2.2, '指数理论上与国家同寿命', size=10, bold=True, ha='center', color=RED)
    ax.set_title('优势一：长生不老', fontproperties=zfont(12, bold=True))

    # 优势2：长期上涨（恒生指数53年增长）
    ax2 = axes[1]
    np.random.seed(42)
    n = 53
    y = np.array([100])
    for _ in range(n):
        y = np.append(y, y[-1] * (1 + np.random.normal(0.08, 0.25)))
    ax2.fill_between(range(n+1), y, alpha=0.2, color=RED)
    ax2.plot(range(n+1), y, lw=2, color=RED)
    ax2.axhline(100, ls='--', color=GRAY, lw=1)
    apply_zh(ax2, xlabel='年份', ylabel='指数点位（起始=100）',
             title='优势二：长期上涨（示意）')
    zh_text(ax2, n*0.6, y.max()*0.85, f'53年涨约200倍\n（含分红约600倍）',
            size=9.5, bold=True, color=RED, ha='center',
            bbox=dict(fc=RED, alpha=0.12, boxstyle='round'))
    ax2.grid(alpha=0.2)

    # 优势3：成本低（管理费对比）
    ax3 = axes[2]
    types = ['普通\n主动基金', '指数基金\n（平均）', '指数ETF\n（主流）']
    fees  = [1.5, 0.69, 0.15]
    cols  = [RED, ORANGE, GREEN]
    bars3 = ax3.bar(types, fees, color=cols, edgecolor='white', lw=1.5, width=0.55)
    for bar, v in zip(bars3, fees):
        zh_text(ax3, bar.get_x()+bar.get_width()/2, v+0.03,
                f'{v}%', size=11, bold=True, ha='center', color=DARK)
    ax3.set_ylim(0, 2)
    apply_zh(ax3, title='优势三：成本低（年管理费）', ylabel='管理费率（%/年）')
    for tick in ax3.get_xticklabels():
        tick.set_fontproperties(zfont(9))
    ax3.grid(axis='y', alpha=0.3)

    plt.suptitle('指数基金三大核心优势——长生不老·长期上涨·成本低',
                 fontproperties=zfont(13, bold=True))
    plt.tight_layout()
    plt.savefig(f'{OUT}/lsd_ch2_three_advantages.png')
    plt.close()
    print('✓ lsd_ch2_three_advantages.png')


# ─────────────────────────────────────────────────────
# 图2-2  看指数点数投资不靠谱（点数长期上涨示意）
# ─────────────────────────────────────────────────────
def lsd_ch2_index_points_wrong():
    np.random.seed(7)
    years = np.arange(1990, 2031)
    n = len(years)
    pts = [100]
    for _ in range(n-1):
        pts.append(pts[-1] * (1 + np.random.normal(0.08, 0.3)))
    pts = np.array(pts)

    fig, ax = plt.subplots(figsize=(9, 4.8))
    ax.plot(years, pts, lw=2, color=DARK)
    ax.axhline(2000, ls='--', color=RED, lw=1.8, label='固定卖点：2000点')
    ax.axhline(500,  ls='--', color=GREEN, lw=1.8, label='固定买点：500点')

    ax.fill_between(years, 500, pts, where=pts < 500, alpha=0.25, color=GREEN)
    ax.fill_between(years, pts, 2000, where=pts > 2000, alpha=0.2, color=RED)

    zh_text(ax, 2015, pts.max()*0.92, '❌ 固定点位策略在长期上涨的\n    指数面前会失效（刻舟求剑）',
            size=10, color=RED, bold=True,
            bbox=dict(fc=RED, alpha=0.1, boxstyle='round'))

    ax.set_xlim(years[0], years[-1])
    apply_zh(ax, title='为何看指数点数投资不靠谱——点数长期单向上涨',
             xlabel='年份', ylabel='指数点位')
    zh_legend(ax); ax.grid(alpha=0.2)
    plt.tight_layout()
    plt.savefig(f'{OUT}/lsd_ch2_index_points_wrong.png')
    plt.close()
    print('✓ lsd_ch2_index_points_wrong.png')


# ─────────────────────────────────────────────────────
# 图3-1  国内主要宽基指数特点对比（雷达图）
# ─────────────────────────────────────────────────────
def lsd_ch3_broad_index_radar():
    cats = ['大盘覆盖', '分散程度', '成长弹性', '波动性\n（低=好）', '历史收益']
    N = len(cats)
    angles = np.linspace(0, 2*np.pi, N, endpoint=False).tolist()
    angles += angles[:1]

    indices = {
        '上证50':  [5, 2, 2, 4, 3.5],
        '沪深300': [4.5, 3.5, 3, 3.5, 4],
        '中证500': [2.5, 4.5, 4, 2.5, 4.5],
        '创业板指': [1.5, 3, 5, 1.5, 4.5],
        '红利指数': [3.5, 3, 2.5, 4, 3.5],
    }
    colors_ = [BLUE, RED, GREEN, ORANGE, TEAL]

    fig, ax = plt.subplots(figsize=(7, 6), subplot_kw=dict(polar=True))
    for (name, vals), c in zip(indices.items(), colors_):
        v = vals + vals[:1]
        ax.plot(angles, v, lw=2, color=c, label=name)
        ax.fill(angles, v, color=c, alpha=0.07)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(cats, fontproperties=zfont(10.5))
    ax.set_yticklabels(['1','2','3','4','5'], fontproperties=zfont(7))
    ax.set_ylim(0, 5.5)
    apply_zh(ax, title='国内主要宽基指数特点对比')
    zh_legend(ax, loc='upper right', bbox_to_anchor=(1.38, 1.15))
    plt.tight_layout()
    plt.savefig(f'{OUT}/lsd_ch3_broad_index_radar.png')
    plt.close()
    print('✓ lsd_ch3_broad_index_radar.png')


# ─────────────────────────────────────────────────────
# 图3-2  A股各行业指数2004-2017年表现对比
# ─────────────────────────────────────────────────────
def lsd_ch3_industry_performance():
    industries = ['医药', '必需消费', '金融', '可选消费', '电信',
                  '信息', '工业', '材料', '公共事业', '能源']
    points = [9383, 9042, 6000, 5080, 5050, 3800, 3100, 2700, 2450, 2018]
    colors_ = [RED if p > 5000 else ORANGE if p > 3000 else GRAY for p in points]

    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.bar(industries, points, color=colors_, edgecolor='white', lw=1.5, width=0.65)
    for bar, v in zip(bars, points):
        zh_text(ax, bar.get_x()+bar.get_width()/2, v+100, f'{v:,}',
                size=9.5, bold=True, ha='center', color=DARK)

    ax.axhline(1000, ls='--', color=GRAY, lw=1.2)
    zh_text(ax, 0, 1100, '起始1000点', size=9, color=GRAY)
    ax.set_ylim(0, 11000)
    apply_zh(ax, title='2004年底至2017年5月，中证800各行业指数表现（起始均为1000点）',
             ylabel='指数点位')
    for tick in ax.get_xticklabels():
        tick.set_fontproperties(zfont(10))
    ax.grid(axis='y', alpha=0.22)

    from matplotlib.patches import Patch
    patches = [Patch(color=RED, label='优秀行业（>5000）'),
               Patch(color=ORANGE, label='一般行业（3000-5000）'),
               Patch(color=GRAY, label='较差行业（<3000）')]
    fig.legend(handles=patches, loc='upper right', prop=zfont(9),
               bbox_to_anchor=(0.98, 0.95))
    plt.tight_layout()
    plt.savefig(f'{OUT}/lsd_ch3_industry_performance.png')
    plt.close()
    print('✓ lsd_ch3_industry_performance.png')


# ─────────────────────────────────────────────────────
# 图4-1  四大估值指标对比说明
# ─────────────────────────────────────────────────────
def lsd_ch4_valuation_methods():
    fig, axes = plt.subplots(2, 2, figsize=(11, 7.5))
    axes = axes.flatten()

    # PE：市盈率概念
    ax1 = axes[0]
    ax1.set_xlim(0, 10); ax1.set_ylim(0, 6); ax1.set_axis_off()
    rect1 = plt.Rectangle((0.5, 3.5), 9, 2, fc=BLUE, ec='white', lw=2, alpha=0.85, zorder=3)
    ax1.add_patch(rect1)
    zh_text(ax1, 5, 4.5, 'PE（市盈率）= 市值 ÷ 盈利', size=13, bold=True, ha='center', color='white')
    zh_text(ax1, 5, 3.0, '理解：以当前盈利速度，多少年回本', size=11, ha='center', color=DARK)
    zh_text(ax1, 5, 2.2, 'PE < 10  →  低估，适合买入', size=10, ha='center', color=GREEN, bold=True)
    zh_text(ax1, 5, 1.5, 'PE > 20  →  高估，谨慎', size=10, ha='center', color=RED, bold=True)
    zh_text(ax1, 5, 0.7, '⚠ 盈利不稳定时（周期/亏损行业）不适用', size=9, ha='center', color=GRAY)
    ax1.set_title('①  市盈率（PE）', fontproperties=zfont(12, bold=True))

    # 盈利收益率
    ax2 = axes[1]
    ax2.set_xlim(0, 10); ax2.set_ylim(0, 6); ax2.set_axis_off()
    rect2 = plt.Rectangle((0.5, 3.5), 9, 2, fc=GREEN, ec='white', lw=2, alpha=0.85, zorder=3)
    ax2.add_patch(rect2)
    zh_text(ax2, 5, 4.5, '盈利收益率 = 盈利 ÷ 市值 = 1/PE', size=12, bold=True, ha='center', color='white')
    zh_text(ax2, 5, 3.0, '格雷厄姆策略核心指标', size=11, ha='center', color=DARK)
    zh_text(ax2, 5, 2.2, '盈利收益率 > 10%  →  开始定投', size=10, ha='center', color=GREEN, bold=True)
    zh_text(ax2, 5, 1.5, '盈利收益率 < 6.4%  →  分批卖出', size=10, ha='center', color=RED, bold=True)
    zh_text(ax2, 5, 0.7, '适用：盈利稳定的价值类指数', size=9, ha='center', color=GRAY)
    ax2.set_title('②  盈利收益率（E/P）', fontproperties=zfont(12, bold=True))

    # 市净率PB
    ax3 = axes[2]
    ax3.set_xlim(0, 10); ax3.set_ylim(0, 6); ax3.set_axis_off()
    rect3 = plt.Rectangle((0.5, 3.5), 9, 2, fc=ORANGE, ec='white', lw=2, alpha=0.85, zorder=3)
    ax3.add_patch(rect3)
    zh_text(ax3, 5, 4.5, 'PB（市净率）= 市值 ÷ 净资产', size=13, bold=True, ha='center', color='white')
    zh_text(ax3, 5, 3.0, '理解：以几折价格买入账面资产', size=11, ha='center', color=DARK)
    zh_text(ax3, 5, 2.2, 'PB < 1  →  低于账面价值，极度低估', size=10, ha='center', color=GREEN, bold=True)
    zh_text(ax3, 5, 1.5, '适用：银行、证券等周期性行业', size=10, ha='center', color=BLUE)
    zh_text(ax3, 5, 0.7, 'ROE = 净利润 / 净资产（越高越好）', size=9, ha='center', color=GRAY)
    ax3.set_title('③  市净率（PB）', fontproperties=zfont(12, bold=True))

    # 博格公式
    ax4 = axes[3]
    ax4.set_xlim(0, 10); ax4.set_ylim(0, 6); ax4.set_axis_off()
    rect4 = plt.Rectangle((0.5, 3.5), 9, 2, fc=PURPLE, ec='white', lw=2, alpha=0.85, zorder=3)
    ax4.add_patch(rect4)
    zh_text(ax4, 5, 4.5, '博格公式：年复合收益 = 初始股息率', size=11, bold=True, ha='center', color='white')
    zh_text(ax4, 5, 4.0, '+ 年均PE变化率 + 年均盈利增长率', size=11, bold=True, ha='center', color='white')
    zh_text(ax4, 5, 3.0, '揭示指数收益的三个来源', size=11, ha='center', color=DARK)
    zh_text(ax4, 5, 2.2, '低PE买入 → PE回归均值时获收益', size=10, ha='center', color=GREEN, bold=True)
    zh_text(ax4, 5, 1.5, '高股息率 → 分红再投入的复利效应', size=10, ha='center', color=BLUE)
    zh_text(ax4, 5, 0.7, '盈利长期增长 → 国运驱动的根本', size=9, ha='center', color=GRAY)
    ax4.set_title('④  博格公式法', fontproperties=zfont(12, bold=True))

    plt.suptitle('指数基金估值四大方法——怎么判断"便宜"还是"贵"',
                 fontproperties=zfont(13, bold=True))
    plt.tight_layout()
    plt.savefig(f'{OUT}/lsd_ch4_valuation_methods.png')
    plt.close()
    print('✓ lsd_ch4_valuation_methods.png')


# ─────────────────────────────────────────────────────
# 图4-2  盈利收益率策略回测对比（有策略 vs 无脑定投）
# ─────────────────────────────────────────────────────
def lsd_ch4_earnings_yield_strategy():
    strategies = ['上证50\n（无脑定投）', '上证50\n（盈利收益率）',
                  '红利指数\n（无脑定投）', '红利指数\n（盈利收益率）']
    returns = [12.3, 29.27, 13.07, 29.9]
    colors_ = [BLUE, RED, TEAL, ORANGE]

    fig, ax = plt.subplots(figsize=(8.5, 5))
    bars = ax.bar(strategies, returns, color=colors_, edgecolor='white', lw=1.8, width=0.55)
    for bar, v in zip(bars, returns):
        zh_text(ax, bar.get_x()+bar.get_width()/2, v+0.5,
                f'{v}%', size=12, bold=True, ha='center', color=DARK)

    ax.axhline(10, ls='--', color=GRAY, lw=1.5, label='参考基准10%')
    ax.set_ylim(0, 36)
    apply_zh(ax, title='2004~2015年回测：盈利收益率策略 vs 无脑定投（年复合收益率）',
             ylabel='年复合收益率（%）')
    zh_legend(ax)
    for tick in ax.get_xticklabels():
        tick.set_fontproperties(zfont(10))
    ax.grid(axis='y', alpha=0.22)

    # 注解
    zh_text(ax, 1, 31.5, '提升约2倍！', size=10, bold=True,
            color=RED, ha='center',
            bbox=dict(fc=RED, alpha=0.12, boxstyle='round'))
    plt.tight_layout()
    plt.savefig(f'{OUT}/lsd_ch4_earnings_yield_strategy.png')
    plt.close()
    print('✓ lsd_ch4_earnings_yield_strategy.png')


# ─────────────────────────────────────────────────────
# 图4-3  指数基金估值策略选择矩阵
# ─────────────────────────────────────────────────────
def lsd_ch4_strategy_matrix():
    fig, ax = plt.subplots(figsize=(10, 5.5))
    ax.set_xlim(0, 10); ax.set_ylim(0, 6.5); ax.set_axis_off()

    def cell(cx, cy, w, h, c, title, detail, tsize=10):
        rect = mpatches.FancyBboxPatch((cx-w/2, cy-h/2), w, h,
                                        boxstyle='round,pad=0.1',
                                        fc=c, ec='white', lw=1.8, alpha=0.92, zorder=3)
        ax.add_patch(rect)
        zh_text(ax, cx, cy+0.28, title, size=tsize, bold=True, ha='center', color='white')
        zh_text(ax, cx, cy-0.25, detail, size=8.5, ha='center', color='white')

    cell(1.8, 5.0, 3.2, 1.2, RED, '盈利稳定的价值指数',
         '上证50、沪深红利、中证红利、H股等')
    cell(5.0, 5.0, 3.2, 1.2, GREEN, '成长型指数',
         '沪深300、中证500、创业板、消费、医药')
    cell(8.2, 5.0, 3.2, 1.2, ORANGE, '强周期性指数',
         '证券、银行、金融、地产')

    cell(1.8, 3.2, 3.2, 1.2, RED, '用盈利收益率法',
         '买：E/P > 10%；卖：E/P < 6.4%')
    cell(5.0, 3.2, 3.2, 1.2, GREEN, '用博格公式法（PE）',
         '买：PE处历史低位；卖：PE处历史高位')
    cell(8.2, 3.2, 3.2, 1.2, ORANGE, '用博格公式法（PB）',
         '买：PB处历史低位；卖：PB处历史高位')

    cell(5.0, 1.4, 9.5, 0.95, DARK,
         '困境指数（长期亏损）→ 直接放弃，无需分析', '')

    def arrow(x1, y1, x2, y2):
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle='->', color=GRAY, lw=1.5), zorder=4)

    for cx in [1.8, 5.0, 8.2]:
        arrow(cx, 4.4, cx, 3.8)

    zh_text(ax, 5.0, 6.2, '指数基金估值策略选择矩阵',
            size=14, bold=True, ha='center', color=DARK)
    plt.tight_layout(pad=0.3)
    plt.savefig(f'{OUT}/lsd_ch4_strategy_matrix.png')
    plt.close()
    print('✓ lsd_ch4_strategy_matrix.png')


if __name__ == '__main__':
    lsd_ch1_asset_comparison()
    lsd_ch1_compound_power()
    lsd_ch2_three_advantages()
    lsd_ch2_index_points_wrong()
    lsd_ch3_broad_index_radar()
    lsd_ch3_industry_performance()
    lsd_ch4_valuation_methods()
    lsd_ch4_earnings_yield_strategy()
    lsd_ch4_strategy_matrix()
    print('第1-4章（螺丝钉版）配图全部生成完毕')
