"""第1-2章配图：通胀侵蚀、复利对比、风险收益散点、股票vs债券走势、金融市场结构"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from plot_utils import *

OUT = os.path.join(os.path.dirname(__file__), '..', 'docs', 'pic')
os.makedirs(OUT, exist_ok=True)

# ─────────────────────────────────────────────────────
# 图1-1  通货膨胀侵蚀购买力
# ─────────────────────────────────────────────────────
def ch1_inflation_erosion():
    years = np.arange(0, 31)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    rates = [0.02, 0.03, 0.05, 0.07]
    labels = ['通胀率 2%', '通胀率 3%', '通胀率 5%', '通胀率 7%']
    colors = [GREEN, BLUE, ORANGE, RED]
    for r, lbl, c in zip(rates, labels, colors):
        pv = 100 * (1 - r) ** years
        ax.plot(years, pv, lw=2.2, color=c, label=lbl)

    ax.axhline(50, ls='--', color=GRAY, lw=1)
    zh_text(ax, 30.3, 50, '50元', size=9, color=GRAY, va='center')
    ax.fill_between(years, 0, 100 * (1-0.07)**years, alpha=0.07, color=RED)
    ax.set_xlim(0, 30); ax.set_ylim(0, 105)
    apply_zh(ax, title='通货膨胀对购买力的侵蚀（初始 100 元）',
             xlabel='年数', ylabel='实际购买力（元）')
    zh_legend(ax, loc='upper right')
    ax.annotate('7%通胀→30年后\n仅剩约12元', xy=(30, 12.3),
                xytext=(22, 25), fontproperties=zfont(9),
                arrowprops=dict(arrowstyle='->', color=RED, lw=1.4),
                color=RED)
    ax.grid(alpha=0.25)
    plt.tight_layout()
    plt.savefig(f'{OUT}/ch1_inflation_erosion.png')
    plt.close()
    print('✓ ch1_inflation_erosion.png')


# ─────────────────────────────────────────────────────
# 图1-2  复利 vs 单利（40年）
# ─────────────────────────────────────────────────────
def ch1_compound_interest():
    years = np.arange(0, 41)
    P = 10
    r = 0.08
    compound = P * (1 + r) ** years
    simple   = P * (1 + r * years)

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(years, compound, lw=2.5, color=RED,  label='复利（年化8%）')
    ax.plot(years, simple,   lw=2.5, color=BLUE, label='单利（年化8%）', ls='--')
    ax.fill_between(years, simple, compound, alpha=0.12, color=RED)

    ax.annotate(f'复利：≈{compound[-1]:.0f}万', xy=(40, compound[-1]),
                xytext=(32, compound[-1]-30), fontproperties=zfont(10, bold=True),
                color=RED, arrowprops=dict(arrowstyle='->', color=RED, lw=1.3))
    ax.annotate(f'单利：≈{simple[-1]:.0f}万', xy=(40, simple[-1]),
                xytext=(32, simple[-1]+15), fontproperties=zfont(10),
                color=BLUE, arrowprops=dict(arrowstyle='->', color=BLUE, lw=1.3))

    ax.set_xlim(0, 40); ax.set_ylim(0)
    apply_zh(ax, title='复利 vs 单利——10万元·年化8%·40年增长对比',
             xlabel='年数', ylabel='资产（万元）')
    zh_legend(ax, loc='upper left')
    ax.grid(alpha=0.25)
    plt.tight_layout()
    plt.savefig(f'{OUT}/ch1_compound_interest.png')
    plt.close()
    print('✓ ch1_compound_interest.png')


# ─────────────────────────────────────────────────────
# 图1-3  各类资产风险收益散点
# ─────────────────────────────────────────────────────
def ch1_risk_return():
    assets = ['货币基金', '纯债基金', '混合型基金', '指数基金', '主动股票基金', '个股（示意）']
    risk   = [0.5,  3.5,  11,  18,   22,  35]
    ret    = [2.5,  4.0,   7,  10,   11,  14]
    sizes  = [180,  160,  160, 200,  160, 140]
    cols   = [GREEN, TEAL, BLUE, ORANGE, RED, PURPLE]

    fig, ax = plt.subplots(figsize=(7.5, 4.8))
    for a, x, y, s, c in zip(assets, risk, ret, sizes, cols):
        ax.scatter(x, y, s=s, color=c, zorder=5, edgecolors='white', lw=1.2)
        offset = (1.2, 0.3)
        zh_text(ax, x + offset[0], y + offset[1], a, size=9.5, color=c)

    # 有效前沿虚线
    xf = np.linspace(0.3, 40, 200)
    yf = 1.5 + 3.5 * np.log1p(xf * 0.18)
    ax.plot(xf, yf, ls='--', color=GRAY, lw=1.5, label='风险-收益参考线')

    apply_zh(ax, title='各类资产风险-收益分布（示意）',
             xlabel='年化波动率（%）', ylabel='预期年化收益率（%）')
    ax.set_xlim(-2, 45); ax.set_ylim(0, 18)
    ax.grid(alpha=0.22)
    plt.tight_layout()
    plt.savefig(f'{OUT}/ch1_risk_return.png')
    plt.close()
    print('✓ ch1_risk_return.png')


# ─────────────────────────────────────────────────────
# 图2-1  金融市场结构
# ─────────────────────────────────────────────────────
def ch2_market_structure():
    fig, ax = plt.subplots(figsize=(9, 5.5))
    ax.set_xlim(0, 10); ax.set_ylim(0, 8)
    ax.set_axis_off()

    def box(cx, cy, w, h, color, label, sublabel='', fontsize=11):
        rect = plt.Rectangle((cx-w/2, cy-h/2), w, h,
                              fc=color, ec='white', lw=2, alpha=0.9, zorder=3)
        ax.add_patch(rect)
        zh_text(ax, cx, cy+(0.12 if sublabel else 0), label, size=fontsize,
                bold=True, ha='center', va='center', color='white')
        if sublabel:
            zh_text(ax, cx, cy-0.35, sublabel, size=8.5, ha='center', va='center', color='white')

    # 投资者
    box(2, 6.8, 2.5, 0.9, BLUE, '投资者（你）', '出资购买基金份额')
    # 基金公司
    box(5, 6.8, 2.5, 0.9, PURPLE, '基金公司', '发行管理基金')
    # 托管银行
    box(8, 6.8, 2.5, 0.9, TEAL, '托管银行', '独立保管资金')
    # 各市场
    markets = [('股票市场', 1.3, 4.2, RED),
               ('债券市场', 3.5, 4.2, ORANGE),
               ('货币市场', 5.7, 4.2, GREEN),
               ('海外市场', 7.9, 4.2, BLUE)]
    for name, cx, cy, c in markets:
        box(cx, cy, 2.0, 0.85, c, name)

    # 底部资产类型
    box(5, 2.1, 7, 0.85, GRAY, '投资收益流回投资者（净值上涨 / 分红）', fontsize=10)

    # 箭头
    def arrow(x1,y1,x2,y2,c=DARK):
        ax.annotate('', xy=(x2,y2), xytext=(x1,y1),
                    arrowprops=dict(arrowstyle='->', color=c, lw=1.6), zorder=4)

    arrow(3.25,6.8, 3.75,6.8)  # 投资者→基金
    arrow(6.25,6.8, 6.75,6.8)  # 基金→托管
    for cx in [1.3,3.5,5.7,7.9]:
        arrow(5, 6.35, cx, 4.62)
    for cx in [1.3,3.5,5.7,7.9]:
        arrow(cx, 3.77, 5, 2.54)

    zh_text(ax, 5, 7.6, '金融市场整体结构', size=14, bold=True,
            ha='center', va='center', color=DARK)
    plt.tight_layout(pad=0.5)
    plt.savefig(f'{OUT}/ch2_market_structure.png')
    plt.close()
    print('✓ ch2_market_structure.png')


# ─────────────────────────────────────────────────────
# 图2-2  沪深300行业构成（饼图）
# ─────────────────────────────────────────────────────
def ch2_index_composition():
    industries = ['金融', '消费（食品饮料）', '医药生物', '信息技术', '工业', '新能源/材料', '其他']
    weights    = [24, 17, 12, 11, 10, 10, 16]
    colors     = [BLUE, RED, GREEN, ORANGE, PURPLE, TEAL, GRAY]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 5))
    wedges, texts, autotexts = ax1.pie(
        weights, colors=colors, autopct='%1.0f%%',
        startangle=140, pctdistance=0.78,
        wedgeprops=dict(edgecolor='white', lw=1.8)
    )
    for t in autotexts:
        t.set_fontproperties(zfont(9, bold=True))
        t.set_color('white')
    for t in texts:
        t.set_text('')

    leg = ax1.legend(wedges, industries, loc='lower left',
                     bbox_to_anchor=(-0.15, -0.12), ncol=2)
    for t in leg.get_texts():
        t.set_fontproperties(zfont(9))
    apply_zh(ax1, title='沪深300行业权重分布（示意）')

    # 横条图
    sorted_data = sorted(zip(weights, industries, colors), reverse=True)
    w2, n2, c2 = zip(*sorted_data)
    bars = ax2.barh(n2, w2, color=c2, edgecolor='white', lw=1)
    for bar, v in zip(bars, w2):
        ax2.text(v + 0.5, bar.get_y() + bar.get_height()/2,
                 f'{v}%', va='center', fontproperties=zfont(9))
    for tick in ax2.get_yticklabels():
        tick.set_fontproperties(zfont(10))
    for tick in ax2.get_xticklabels():
        tick.set_fontproperties(zfont(9))
    apply_zh(ax2, title='各行业权重（%）', xlabel='权重（%）')
    ax2.set_xlim(0, 30); ax2.grid(axis='x', alpha=0.3)

    plt.suptitle('沪深300指数成分行业分布（示意数据）',
                 fontproperties=zfont(13, bold=True), y=1.01)
    plt.tight_layout()
    plt.savefig(f'{OUT}/ch2_index_composition.png')
    plt.close()
    print('✓ ch2_index_composition.png')


# ─────────────────────────────────────────────────────
# 图2-3  股票 vs 债券5年净值走势
# ─────────────────────────────────────────────────────
def ch2_stock_vs_bond():
    np.random.seed(42)
    n = 60  # 月
    months = np.arange(n)

    # 股票：趋势向上+大波动
    stock_ret = np.random.normal(0.008, 0.05, n)
    stock = 100 * np.cumprod(1 + stock_ret)

    # 债券：小趋势+小波动
    bond_ret = np.random.normal(0.003, 0.008, n)
    bond  = 100 * np.cumprod(1 + bond_ret)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 6), sharex=True,
                                    gridspec_kw={'hspace': 0.08})

    ax1.plot(months, stock, lw=2, color=RED, label='股票型基金（示意）')
    ax1.fill_between(months, 100, stock, where=stock >= 100,
                     alpha=0.15, color=RED)
    ax1.fill_between(months, 100, stock, where=stock < 100,
                     alpha=0.15, color=BLUE)
    ax1.axhline(100, ls='--', color=GRAY, lw=1)
    apply_zh(ax1, ylabel='净值（元）')
    zh_legend(ax1)
    ax1.grid(alpha=0.2)

    ax2.plot(months, bond, lw=2, color=GREEN, label='债券型基金（示意）')
    ax2.fill_between(months, 100, bond, alpha=0.12, color=GREEN)
    ax2.axhline(100, ls='--', color=GRAY, lw=1)
    apply_zh(ax2, xlabel='月份', ylabel='净值（元）')
    zh_legend(ax2)
    ax2.grid(alpha=0.2)

    # 统计
    zh_text(ax1, 55, stock.min()+3,
            f'最大回撤: {((stock.min()-stock[:stock.argmin()].max())/stock[:stock.argmin()].max()*100):.1f}%',
            size=9, color=DARK)
    zh_text(ax2, 55, bond.min()-1.5,
            f'债基波动低，年化约{(bond[-1]/bond[0]-1)*12/n*100:.1f}%',
            size=9, color=DARK)

    plt.suptitle('股票型基金 vs 债券型基金净值走势对比（5年模拟）',
                 fontproperties=zfont(13, bold=True))
    plt.savefig(f'{OUT}/ch2_stock_vs_bond.png')
    plt.close()
    print('✓ ch2_stock_vs_bond.png')


if __name__ == '__main__':
    ch1_inflation_erosion()
    ch1_compound_interest()
    ch1_risk_return()
    ch2_market_structure()
    ch2_index_composition()
    ch2_stock_vs_bond()
    print('第1-2章配图全部生成完毕')
