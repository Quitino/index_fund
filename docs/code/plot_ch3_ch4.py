"""第3-4章配图：运作结构、NAV计算、费率侵蚀、基金类型风险收益、ETF对比、决策树"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from plot_utils import *
import matplotlib.patches as mpatches

OUT = os.path.join(os.path.dirname(__file__), '..', 'docs', 'pic')


# ─────────────────────────────────────────────────────
# 图3-1  基金运作结构
# ─────────────────────────────────────────────────────
def ch3_fund_structure():
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.set_xlim(0, 10); ax.set_ylim(0, 7)
    ax.set_axis_off()

    def box(cx, cy, w, h, color, lines):
        rect = plt.Rectangle((cx-w/2, cy-h/2), w, h,
                              fc=color, ec='white', lw=2, alpha=0.92, zorder=3, )
        ax.add_patch(rect)
        if isinstance(lines, str):
            lines = [lines]
        step = h / (len(lines) + 1)
        for i, line in enumerate(lines):
            size = 11 if i == 0 else 9
            bold = i == 0
            zh_text(ax, cx, cy + h/2 - step*(i+1), line,
                    size=size, bold=bold, ha='center', va='center', color='white')

    def arrow(x1,y1,x2,y2,label='',c=DARK):
        ax.annotate('', xy=(x2,y2), xytext=(x1,y1),
                    arrowprops=dict(arrowstyle='->', color=c, lw=1.8), zorder=4)
        if label:
            mx, my = (x1+x2)/2, (y1+y2)/2
            zh_text(ax, mx+0.15, my, label, size=8.5, color=c)

    box(1.5, 5.5, 2.4, 1.2, BLUE,   ['投资者（你）', '出资方'])
    box(5.0, 5.5, 2.4, 1.2, PURPLE, ['基金公司', '发行+管理基金'])
    box(8.5, 5.5, 2.4, 1.2, TEAL,   ['托管银行', '独立保管资金'])
    box(1.5, 2.8, 2.4, 1.2, RED,    ['股票市场', '权益资产'])
    box(5.0, 2.8, 2.4, 1.2, ORANGE, ['债券市场', '固定收益'])
    box(8.5, 2.8, 2.4, 1.2, GREEN,  ['货币市场', '流动性资产'])
    box(5.0, 0.8, 6.0, 0.85, GRAY,  ['净值变动→投资者盈亏（按份额比例）'])

    arrow(2.7, 5.5, 3.8, 5.5, '申购资金')
    arrow(6.2, 5.5, 7.3, 5.5, '交易指令+监督')
    arrow(5.0, 4.9, 1.5, 3.4, '买卖股票')
    arrow(5.0, 4.9, 5.0, 3.4, '买卖债券')
    arrow(5.0, 4.9, 8.5, 3.4, '流动性管理')
    arrow(5.0, 2.4, 5.0, 1.25, '收益回流')

    zh_text(ax, 5.0, 6.7, '基金运作结构', size=14, bold=True,
            ha='center', va='center', color=DARK)
    plt.tight_layout(pad=0.5)
    plt.savefig(f'{OUT}/ch3_fund_structure.png')
    plt.close()
    print('✓ ch3_fund_structure.png')


# ─────────────────────────────────────────────────────
# 图3-2  NAV计算示意
# ─────────────────────────────────────────────────────
def ch3_nav_calculation():
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.set_xlim(0, 10); ax.set_ylim(0, 6)
    ax.set_axis_off()

    def box(cx, cy, w, h, color, lines, text_color='white'):
        rect = plt.Rectangle((cx-w/2, cy-h/2), w, h,
                              fc=color, ec='white', lw=1.5, alpha=0.9, zorder=3)
        ax.add_patch(rect)
        if isinstance(lines, str): lines = [lines]
        step = h / (len(lines)+1)
        for i, l in enumerate(lines):
            s = 10 if i == 0 else 8.5
            b = (i == 0)
            zh_text(ax, cx, cy+h/2-step*(i+1), l,
                    size=s, bold=b, ha='center', va='center', color=text_color)

    # 资产构成
    items = [('腾讯', '3200万', RED),
             ('茅台', '2800万', ORANGE),
             ('宁德', '1500万', PURPLE),
             ('债券', '1800万', GREEN),
             ('现金', '700万',  BLUE)]
    ys = [5.0, 4.1, 3.2, 2.3, 1.4]
    for (name, val, c), y in zip(items, ys):
        box(2.0, y, 2.8, 0.75, c, [name, val])

    # 总资产
    box(5.8, 3.2, 2.2, 1.2, DARK, ['总资产', '10,000 万元'])

    # NAV
    box(8.5, 3.2, 2.2, 1.2, BLUE, ['单位净值', '1.0000 元/份'])

    # 分母
    box(8.5, 1.4, 2.2, 0.85, GRAY, ['总份额：10,000 万份'], 'white')

    def arrow(x1,y1,x2,y2,label=''):
        ax.annotate('', xy=(x2,y2), xytext=(x1,y1),
                    arrowprops=dict(arrowstyle='->', color=DARK, lw=1.6), zorder=4)
        if label:
            zh_text(ax, (x1+x2)/2+0.15, (y1+y2)/2, label, size=9, color=DARK)

    for y in ys:
        arrow(3.4, y, 4.7, 3.2)
    arrow(6.9, 3.2, 7.4, 3.2, 'NAV =')
    arrow(8.5, 2.6, 8.5, 2.3, '÷')

    zh_text(ax, 5, 5.6, '净值（NAV）= 基金总资产 ÷ 总份额', size=12, bold=True,
            ha='center', va='center', color=DARK)
    plt.tight_layout(pad=0.5)
    plt.savefig(f'{OUT}/ch3_nav_calculation.png')
    plt.close()
    print('✓ ch3_nav_calculation.png')


# ─────────────────────────────────────────────────────
# 图3-3  费率侵蚀20年收益
# ─────────────────────────────────────────────────────
def ch3_fee_impact():
    years = np.arange(0, 21)
    P = 10  # 万元
    r = 0.08
    fees   = [0, 0.005, 0.01, 0.015, 0.025]
    labels = ['无费率（基准）', '0.5%（指数ETF）', '1.0%（指数基金）',
              '1.5%（主动基金）', '2.5%（高费率）']
    colors = [DARK, GREEN, BLUE, ORANGE, RED]
    styles = ['-', '-', '--', '--', ':']

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.8))

    finals = []
    for f, lbl, c, ls in zip(fees, labels, colors, styles):
        vals = P * ((1 + r - f) ** years)
        ax1.plot(years, vals, lw=2.2, color=c, label=lbl, ls=ls)
        finals.append(vals[-1])

    ax1.set_xlim(0, 20); ax1.set_ylim(0)
    apply_zh(ax1, title='10万元·年化8%·不同费率20年增长',
             xlabel='年数', ylabel='资产（万元）')
    zh_legend(ax1, fontsize=8.5)
    ax1.grid(alpha=0.22)

    # 柱图
    bars = ax2.bar(labels, finals, color=colors, edgecolor='white', lw=1.5)
    for bar, v in zip(bars, finals):
        zh_text(ax2, bar.get_x()+bar.get_width()/2, v+0.3,
                f'{v:.1f}万', size=9, bold=True, ha='center', color=DARK)
    ax2.set_ylim(0, 52)
    apply_zh(ax2, title='20年后终值对比（万元）', ylabel='万元')
    for tick in ax2.get_xticklabels():
        tick.set_fontproperties(zfont(8.5))
        tick.set_rotation(15)
    ax2.grid(axis='y', alpha=0.22)

    plt.suptitle('费率对长期收益的侵蚀效应',
                 fontproperties=zfont(13, bold=True))
    plt.tight_layout()
    plt.savefig(f'{OUT}/ch3_fee_impact.png')
    plt.close()
    print('✓ ch3_fee_impact.png')


# ─────────────────────────────────────────────────────
# 图4-1  各类基金风险收益气泡图
# ─────────────────────────────────────────────────────
def ch4_fund_types_risk():
    types   = ['货币基金', '纯债基金', '混合偏债', '混合偏股', '指数基金', '股票基金', 'QDII', 'REITs']
    risk    = [0.4,  3,    7,    13,   17,   22,   20,   9]
    ret     = [2.5,  4,    5.5,   9,   10,   12,   11,   6]
    scale   = [5000, 1200, 800,  1500, 2000, 1200, 500,  300]  # 规模气泡
    colors  = [GREEN, TEAL, BLUE, ORANGE, RED, PURPLE, DARK, YELLOW]

    fig, ax = plt.subplots(figsize=(9, 5.5))
    for a, x, y, s, c in zip(types, risk, ret, scale, colors):
        ax.scatter(x, y, s=s, color=c, alpha=0.78, zorder=5,
                   edgecolors='white', lw=1.5)
        offset_x = 0.8 if x < 10 else -1.5 if x > 18 else 0.8
        offset_y = 0.35
        zh_text(ax, x+offset_x, y+offset_y, a, size=9.5, color=c)

    ax.annotate('', xy=(22, 12), xytext=(0.4, 2.5),
                arrowprops=dict(arrowstyle='->', color=GRAY, lw=1.5,
                                connectionstyle='arc3,rad=-0.25'))
    zh_text(ax, 11, 5.5, '风险↑ → 收益↑', size=10, color=GRAY, style='italic')

    ax.set_xlim(-2, 28); ax.set_ylim(0, 15)
    apply_zh(ax, title='各类基金风险-收益分布（气泡大小代表市场规模）',
             xlabel='年化波动率（%）', ylabel='预期年化收益率（%）')
    ax.grid(alpha=0.22)
    plt.tight_layout()
    plt.savefig(f'{OUT}/ch4_fund_types_risk.png')
    plt.close()
    print('✓ ch4_fund_types_risk.png')


# ─────────────────────────────────────────────────────
# 图4-2  ETF vs 场外基金五维对比
# ─────────────────────────────────────────────────────
def ch4_etf_vs_ofs():
    categories = ['费率低', '交易灵活', '透明度', '入门门槛\n（低=好）', '操作简便']
    N = len(categories)
    angles = np.linspace(0, 2*np.pi, N, endpoint=False).tolist()
    angles += angles[:1]

    etf  = [5, 5, 4.5, 2, 3]  # 门槛低=2（门槛较高）
    ofs  = [3.5, 2, 3.5, 5, 5]
    etf  += etf[:1]; ofs += ofs[:1]

    fig, ax = plt.subplots(figsize=(6.5, 5.5), subplot_kw=dict(polar=True))
    ax.plot(angles, etf, color=RED, lw=2, label='ETF（场内）')
    ax.fill(angles, etf, color=RED, alpha=0.18)
    ax.plot(angles, ofs, color=BLUE, lw=2, label='场外指数基金')
    ax.fill(angles, ofs, color=BLUE, alpha=0.18)

    ax.set_ylim(0, 5.5)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, fontproperties=zfont(10))
    for tick in ax.get_yticklabels():
        tick.set_fontproperties(zfont(8))
    ax.set_yticklabels(['1','2','3','4','5'], fontproperties=zfont(7))

    apply_zh(ax, title='ETF vs 场外指数基金五维对比')
    zh_legend(ax, loc='upper right', bbox_to_anchor=(1.3, 1.15))
    plt.tight_layout()
    plt.savefig(f'{OUT}/ch4_etf_vs_ofs.png')
    plt.close()
    print('✓ ch4_etf_vs_ofs.png')


# ─────────────────────────────────────────────────────
# 图4-3  基金类型决策树（文字流程图）
# ─────────────────────────────────────────────────────
def ch4_decision_tree():
    fig, ax = plt.subplots(figsize=(11, 6.5))
    ax.set_xlim(0, 11); ax.set_ylim(0, 7)
    ax.set_axis_off()

    def rbox(cx, cy, w, h, color, text, fontsize=10, text_color='white'):
        rect = mpatches.FancyBboxPatch((cx-w/2, cy-h/2), w, h,
                                   boxstyle='round,pad=0.05',
                                   fc=color, ec='white', lw=1.5, zorder=3)
        ax.add_patch(rect)
        if isinstance(text, str): text = [text]
        step = h/(len(text)+1)
        for i, t in enumerate(text):
            s = fontsize if i==0 else fontsize-1.5
            b = (i==0)
            zh_text(ax, cx, cy+h/2-step*(i+1), t,
                    size=s, bold=b, ha='center', va='center', color=text_color)

    def arr(x1,y1,x2,y2,label='',lc=DARK):
        ax.annotate('', xy=(x2,y2), xytext=(x1,y1),
                    arrowprops=dict(arrowstyle='->', color=lc, lw=1.5), zorder=4)
        if label:
            zh_text(ax, (x1+x2)/2-0.4, (y1+y2)/2+0.08, label, size=8.5, color=lc)

    # 顶部：投资期限
    rbox(5.5, 6.2, 2.8, 0.75, DARK, '我应该买哪类基金？', fontsize=12)

    # 三条路：< 1年 / 1-3年 / > 3年
    rbox(1.5, 4.8, 2.0, 0.7, GRAY, ['投资期限', '< 1年'], 9)
    rbox(5.5, 4.8, 2.0, 0.7, GRAY, ['投资期限', '1-3年'], 9)
    rbox(9.5, 4.8, 2.0, 0.7, GRAY, ['投资期限', '> 3年'], 9)

    arr(5.5, 5.82, 1.5, 5.15, '短期'); arr(5.5, 5.82, 5.5, 5.15, '中期'); arr(5.5, 5.82, 9.5, 5.15, '长期')

    # 短期结果
    rbox(1.5, 3.6, 2.2, 0.9, GREEN,  ['✓ 货币基金', '短债基金'])

    # 中期：保守/进取
    rbox(4.5, 3.6, 1.7, 0.7, TEAL,   '保守型', 9)
    rbox(6.5, 3.6, 1.7, 0.7, ORANGE, '进取型', 9)
    arr(5.5, 4.45, 4.5, 3.95); arr(5.5, 4.45, 6.5, 3.95)
    rbox(4.5, 2.55, 2.0, 0.85, TEAL,  ['✓ 纯债基金', '混合偏债'])
    rbox(6.5, 2.55, 2.0, 0.85, ORANGE,['✓ 混合偏股', 'QDII基金'])
    arr(4.5, 3.25, 4.5, 2.97); arr(6.5, 3.25, 6.5, 2.97)

    # 长期：被动/主动/分红
    rbox(8.3, 3.6, 1.5, 0.68, BLUE, '被动投资', 9)
    rbox(9.7, 3.6, 1.5, 0.68, RED,  '主动管理', 9)
    rbox(9.0, 2.55, 1.5, 0.68, PURPLE, '稳定分红', 9)
    arr(9.5, 4.45, 8.3, 3.94); arr(9.5, 4.45, 9.7, 3.94)
    rbox(8.3, 1.7, 1.8, 0.85, BLUE, ['✓ 宽基ETF', '沪深300等'])
    rbox(10.1,1.7, 1.8, 0.85, RED,  ['✓ 主动基金', '精选经理'])
    rbox(9.0, 1.7, 0.1, 0, PURPLE, ''); rbox(9.0, 1.4, 1.8, 0.7, PURPLE, '✓ REITs')
    arr(8.3, 3.26, 8.3, 2.12); arr(9.7, 3.26, 10.1, 2.12); arr(9.0, 3.26, 9.0, 1.75)

    arr(1.5, 4.45, 1.5, 4.05)

    plt.suptitle('基金类型选择决策树', fontproperties=zfont(14, bold=True), y=0.97)
    plt.tight_layout(pad=0.3)
    plt.savefig(f'{OUT}/ch4_decision_tree.png')
    plt.close()
    print('✓ ch4_decision_tree.png')


if __name__ == '__main__':
    ch3_fund_structure()
    ch3_nav_calculation()
    ch3_fee_impact()
    ch4_fund_types_risk()
    ch4_etf_vs_ofs()
    ch4_decision_tree()
    print('第3-4章配图全部生成完毕')
