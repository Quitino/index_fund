"""
《指数基金投资指南》银行螺丝钉
第5-8章配图：懒人定投法、定投计划、家庭配置、心理建设
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from plot_utils import *
import matplotlib.patches as mpatches

OUT = os.path.join(os.path.dirname(__file__), '..', 'docs', 'pic')
os.makedirs(OUT, exist_ok=True)

# ─────────────────────────────────────────────────────
# 图5-1  懒人定投法核心流程
# ─────────────────────────────────────────────────────
def lsd_ch5_lazy_dip_flow():
    fig, ax = plt.subplots(figsize=(10, 5.5))
    ax.set_xlim(0, 11); ax.set_ylim(0, 7); ax.set_axis_off()

    def rbox(cx, cy, w, h, c, lines):
        rect = mpatches.FancyBboxPatch((cx-w/2, cy-h/2), w, h,
                                        boxstyle='round,pad=0.1',
                                        fc=c, ec='white', lw=2, alpha=0.92, zorder=3)
        ax.add_patch(rect)
        if isinstance(lines, str): lines = [lines]
        step = h / (len(lines)+1)
        for i, l in enumerate(lines):
            s = 11 if i == 0 else 9
            zh_text(ax, cx, cy+h/2-step*(i+1), l, size=s,
                    bold=(i==0), ha='center', va='center', color='white')

    def arr(x1,y1,x2,y2,lbl=''):
        ax.annotate('', xy=(x2,y2), xytext=(x1,y1),
                    arrowprops=dict(arrowstyle='->', color=DARK, lw=1.8), zorder=4)
        if lbl:
            zh_text(ax, (x1+x2)/2-0.15, (y1+y2)/2+0.12, lbl, size=9, color=DARK)

    rbox(2.0, 5.8, 3.5, 1.0, DARK,   ['第一步：选指数', '挑选适合投资的指数基金'])
    rbox(5.5, 5.8, 3.5, 1.0, BLUE,   ['第二步：看估值', '判断是否处于低估区域'])
    rbox(9.0, 5.8, 1.6, 1.0, RED,    ['不低估', '暂停/持有'])

    rbox(5.5, 3.8, 3.5, 1.0, GREEN,  ['第三步：定投买入', '每月固定日期，分批建仓'])
    rbox(5.5, 1.8, 3.5, 1.0, ORANGE, ['第四步：估值止盈', 'E/P<6.4% 或 PE进高估区，分批卖'])

    arr(3.75, 5.8, 4.75, 5.8)
    arr(7.25, 5.8, 8.2, 5.8)   # →不低估
    arr(5.5, 5.3, 5.5, 4.3, '低估，开始')
    arr(5.5, 3.3, 5.5, 2.3)

    # 循环箭头
    ax.annotate('', xy=(2.0, 5.3), xytext=(5.5, 1.3),
                arrowprops=dict(arrowstyle='->', color=TEAL, lw=1.8,
                                connectionstyle='arc3,rad=0.35'), zorder=4)
    zh_text(ax, 3.0, 3.0, '重新开始\n下一轮', size=9, color=TEAL, ha='center')

    zh_text(ax, 5.5, 6.8, '懒人定投法核心流程',
            size=14, bold=True, ha='center', color=DARK)
    plt.tight_layout(pad=0.5)
    plt.savefig(f'{OUT}/lsd_ch5_lazy_dip_flow.png')
    plt.close()
    print('✓ lsd_ch5_lazy_dip_flow.png')


# ─────────────────────────────────────────────────────
# 图5-2  定投收益率年复合：配合估值 vs 无脑定投
# ─────────────────────────────────────────────────────
def lsd_ch5_dip_vs_blind():
    np.random.seed(42)
    months = np.arange(0, 145)
    # 指数净值模拟（含两次牛熊）
    pts = [1.0]
    for i in range(144):
        if i < 30:  pts.append(pts[-1] * (1 + np.random.normal(0.005, 0.04)))
        elif i < 50:pts.append(pts[-1] * (1 + np.random.normal(-0.02, 0.06)))
        elif i < 80:pts.append(pts[-1] * (1 + np.random.normal(0.015, 0.05)))
        elif i < 100:pts.append(pts[-1]*(1+np.random.normal(-0.015,0.06)))
        else:       pts.append(pts[-1] * (1 + np.random.normal(0.01, 0.04)))
    pts = np.array(pts)

    # 估值（PE，简化）
    pe = 10 + 8*np.sin(months*2*np.pi/60) + np.random.normal(0, 1.5, len(months))
    ep = 1/pe * 100  # 盈利收益率%

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6.5), sharex=True,
                                    gridspec_kw={'hspace':0.06, 'height_ratios':[2,1]})

    ax1.plot(months, pts, lw=2, color=DARK, label='指数净值')
    # 标注定投区间
    invest_mask = ep > 10
    ax1.fill_between(months, pts.min(), pts, where=invest_mask,
                     alpha=0.2, color=GREEN, label='盈利收益率>10%（定投区）')
    ax1.fill_between(months, pts.min(), pts, where=ep < 6.4,
                     alpha=0.2, color=RED, label='盈利收益率<6.4%（卖出区）')
    apply_zh(ax1, ylabel='净值', title='懒人定投法：结合估值择机定投（绿色买入，红色卖出）')
    zh_legend(ax1, ncol=3, fontsize=9)
    ax1.grid(alpha=0.18)

    ax2.plot(months, ep, lw=1.8, color=BLUE, label='盈利收益率（%）')
    ax2.axhline(10, ls='--', color=GREEN, lw=1.5, label='10%（开始定投）')
    ax2.axhline(6.4, ls='--', color=RED, lw=1.5, label='6.4%（停止定投）')
    ax2.fill_between(months, 6.4, ep, where=ep >= 10, alpha=0.2, color=GREEN)
    ax2.fill_between(months, 0, ep, where=ep < 6.4, alpha=0.15, color=RED)
    ax2.set_ylim(0, 20)
    apply_zh(ax2, xlabel='月份', ylabel='盈利收益率（%）')
    zh_legend(ax2, ncol=3, fontsize=9)
    ax2.grid(alpha=0.15)
    plt.savefig(f'{OUT}/lsd_ch5_dip_vs_blind.png')
    plt.close()
    print('✓ lsd_ch5_dip_vs_blind.png')


# ─────────────────────────────────────────────────────
# 图5-3  提高定投收益的5个小技巧
# ─────────────────────────────────────────────────────
def lsd_ch5_five_tips():
    fig, ax = plt.subplots(figsize=(10, 5.5))
    ax.set_xlim(0, 11); ax.set_ylim(0, 7); ax.set_axis_off()

    tips = [
        (1.8, 5.5, GREEN,  '技巧1：只投低估值\n盈利收益率>10%才投'),
        (5.5, 5.5, BLUE,   '技巧2：分散多只\n同时投2~3只低估指数'),
        (9.2, 5.5, ORANGE, '技巧3：发薪日定投\n工资到账立即扣款，防止乱花'),
        (1.8, 2.8, RED,    '技巧4：越跌越买\n低估时可适当加大定投金额'),
        (5.5, 2.8, PURPLE, '技巧5：坚守纪律\n不追涨、不停投、熊市是朋友'),
    ]

    for cx, cy, c, text in tips:
        circle = plt.Circle((cx, cy), 1.8, fc=c, ec='white', lw=2, alpha=0.88, zorder=3)
        ax.add_patch(circle)
        lines = text.split('\n')
        zh_text(ax, cx, cy+0.35, lines[0], size=10.5, bold=True,
                ha='center', va='center', color='white')
        zh_text(ax, cx, cy-0.4, lines[1], size=9, ha='center', va='center', color='white')

    zh_text(ax, 5.5, 6.7, '提高定投收益的5个小技巧',
            size=14, bold=True, ha='center', color=DARK)
    plt.tight_layout(pad=0.3)
    plt.savefig(f'{OUT}/lsd_ch5_five_tips.png')
    plt.close()
    print('✓ lsd_ch5_five_tips.png')


# ─────────────────────────────────────────────────────
# 图5-4  定投年复合收益率计算示意
# ─────────────────────────────────────────────────────
def lsd_ch5_annualized_return():
    # XIRR简化：月均收益→年复合
    total_invested = 120  # 120月×1000元
    # 不同策略最终值
    scenarios = [
        ('无脑定投', 182000),
        ('估值定投\n（上证50）', 380000),
        ('估值定投\n（红利指数）', 395000),
    ]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 5))

    # 左：终值对比
    names, vals = zip(*scenarios)
    cols3 = [GRAY, RED, ORANGE]
    bars = ax1.bar(names, [v/1000 for v in vals], color=cols3, edgecolor='white', lw=1.5, width=0.55)
    for bar, v in zip(bars, vals):
        zh_text(ax1, bar.get_x()+bar.get_width()/2, v/1000+3,
                f'{v//1000}万', size=11, bold=True, ha='center', color=DARK)
    ax1.axhline(120, ls='--', color=BLUE, lw=1.5, label='总本金12万')
    ax1.set_ylim(0, 450)
    apply_zh(ax1, title='10年定投（每月1000元）终值对比', ylabel='终值（千元）')
    zh_legend(ax1)
    for tick in ax1.get_xticklabels():
        tick.set_fontproperties(zfont(9.5))
    ax1.grid(axis='y', alpha=0.22)

    # 右：对应年复合收益率
    annual_r = [12.3, 29.27, 29.9]
    bars2 = ax2.bar(names, annual_r, color=cols3, edgecolor='white', lw=1.5, width=0.55)
    for bar, v in zip(bars2, annual_r):
        zh_text(ax2, bar.get_x()+bar.get_width()/2, v+0.6,
                f'{v}%', size=11, bold=True, ha='center', color=DARK)
    ax2.set_ylim(0, 36)
    apply_zh(ax2, title='年复合收益率对比', ylabel='年复合收益率（%）')
    for tick in ax2.get_xticklabels():
        tick.set_fontproperties(zfont(9.5))
    ax2.grid(axis='y', alpha=0.22)

    plt.suptitle('估值定投 vs 无脑定投：收益差距一目了然',
                 fontproperties=zfont(12, bold=True))
    plt.tight_layout()
    plt.savefig(f'{OUT}/lsd_ch5_annualized_return.png')
    plt.close()
    print('✓ lsd_ch5_annualized_return.png')


# ─────────────────────────────────────────────────────
# 图6-1  三种定投计划对比（养老/上班族/教育）
# ─────────────────────────────────────────────────────
def lsd_ch6_three_plans():
    plans = [
        ('养老定投计划', [('货币/债券', 30, GREEN), ('上证50/红利', 50, RED), ('H股/恒生', 20, BLUE)]),
        ('上班族加薪计划', [('货币基金', 20, GREEN), ('沪深300', 40, RED), ('中证500', 25, ORANGE), ('纳斯达克', 15, PURPLE)]),
        ('子女教育计划', [('货币/短债', 25, GREEN), ('沪深300', 35, RED), ('医药/消费', 25, TEAL), ('标普500', 15, BLUE)]),
    ]

    fig, axes = plt.subplots(1, 3, figsize=(12, 5))
    for ax, (title, components) in zip(axes, plans):
        sizes  = [c[1] for c in components]
        colors_= [c[2] for c in components]
        labels = [f'{c[0]}\n{c[1]}%' for c in components]
        wedges, texts, autotexts = ax.pie(
            sizes, colors=colors_,
            autopct='%1.0f%%', startangle=90,
            wedgeprops=dict(edgecolor='white', lw=2),
            pctdistance=0.72
        )
        for t in autotexts:
            t.set_fontproperties(zfont(9.5, bold=True)); t.set_color('white')
        for t in texts: t.set_text('')

        leg = ax.legend(wedges, [c[0] for c in components],
                        loc='lower center', bbox_to_anchor=(0.5, -0.22),
                        prop=zfont(8.5), ncol=2)
        ax.set_title(title, fontproperties=zfont(11, bold=True))

    plt.suptitle('三种定投计划资产配置方案',
                 fontproperties=zfont(13, bold=True), y=1.02)
    plt.tight_layout()
    plt.savefig(f'{OUT}/lsd_ch6_three_plans.png')
    plt.close()
    print('✓ lsd_ch6_three_plans.png')


# ─────────────────────────────────────────────────────
# 图7-1  货币基金 vs 债券基金 vs 银行存款对比
# ─────────────────────────────────────────────────────
def lsd_ch7_fund_types_compare():
    categories = ['安全性', '流动性', '收益性', '门槛\n（低=好）', '适合场景']
    N = len(categories)
    angles = np.linspace(0, 2*np.pi, N, endpoint=False).tolist()
    angles += angles[:1]

    products = {
        '银行活期存款': ([3, 5, 1, 5, 2], GRAY),
        '货币基金\n（余额宝等）': ([5, 5, 2.5, 5, 4], GREEN),
        '纯债基金':  ([4, 3, 3.5, 4, 3.5], BLUE),
        '混合偏债': ([3.5, 2.5, 4, 3.5, 3], ORANGE),
    }

    fig, ax = plt.subplots(figsize=(7, 6.5), subplot_kw=dict(polar=True))
    for name, (vals, c) in products.items():
        v = vals + vals[:1]
        ax.plot(angles, v, lw=2.2, color=c, label=name)
        ax.fill(angles, v, color=c, alpha=0.1)

    ax.set_ylim(0, 5.5)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, fontproperties=zfont(10.5))
    ax.set_yticklabels(['1','2','3','4','5'], fontproperties=zfont(7))
    apply_zh(ax, title='货币基金/债券基金/银行存款五维对比')
    zh_legend(ax, loc='upper right', bbox_to_anchor=(1.4, 1.15))
    plt.tight_layout()
    plt.savefig(f'{OUT}/lsd_ch7_fund_types_compare.png')
    plt.close()
    print('✓ lsd_ch7_fund_types_compare.png')


# ─────────────────────────────────────────────────────
# 图7-2  家庭资产配置金字塔
# ─────────────────────────────────────────────────────
def lsd_ch7_asset_pyramid():
    fig, ax = plt.subplots(figsize=(8.5, 5.5))
    ax.set_xlim(0, 10); ax.set_ylim(0, 7); ax.set_axis_off()

    layers = [
        (5, 1.2, 9, 1.1, GREEN,  '基础层：流动性资产（20~30%）',
         '货币基金 | 短债基金 | 随取随用'),
        (5, 2.85, 7.8, 1.1, BLUE,  '稳健层：固定收益类（30~40%）',
         '纯债基金 | 定期存款 | 年化3~5%'),
        (5, 4.5, 6.2, 1.1, ORANGE, '增值层：股票指数基金（30~40%）',
         '宽基指数定投 | 低估时买入 | 3年+不动'),
        (5, 6.1, 4.0, 0.85, RED,  '进取层：行业/个股（≤10%）',
         '可全损 | 高风险高收益'),
    ]

    for cx, cy, w, h, c, title, detail in layers:
        rect = mpatches.FancyBboxPatch((cx-w/2, cy-h/2), w, h,
                                        boxstyle='round,pad=0.08',
                                        fc=c, ec='white', lw=2, alpha=0.9, zorder=3)
        ax.add_patch(rect)
        zh_text(ax, cx, cy+0.22, title, size=11, bold=True, ha='center', color='white')
        zh_text(ax, cx, cy-0.25, detail, size=8.5, ha='center', color='white')

    zh_text(ax, 5, 6.75, '家庭资产配置金字塔',
            size=14, bold=True, ha='center', color=DARK)
    plt.tight_layout(pad=0.5)
    plt.savefig(f'{OUT}/lsd_ch7_asset_pyramid.png')
    plt.close()
    print('✓ lsd_ch7_asset_pyramid.png')


# ─────────────────────────────────────────────────────
# 图8-1  复利从哪里来（三大来源分解）
# ─────────────────────────────────────────────────────
def lsd_ch8_return_sources():
    fig, ax = plt.subplots(figsize=(9, 5))
    years = np.arange(0, 31)
    P = 10

    # 三个收益来源的累积贡献
    div_yield = 0.02      # 股息率
    pe_change = -0.005    # 市盈率变化
    earnings_g = 0.12     # 盈利增长

    total_r = div_yield + pe_change + earnings_g  # ≈11.5%
    total   = P * (1+total_r)**years
    # 分解：仅股息、仅盈利、仅PE变化
    div_only = P * (1+div_yield)**years
    earn_only= P * (1+earnings_g)**years
    pe_only  = P * (1+pe_change)**years

    ax.plot(years, total,     lw=2.5, color=RED,    label=f'合计（约{total_r*100:.0f}%）≈三者之和')
    ax.plot(years, earn_only, lw=2,   color=ORANGE, ls='--', label=f'仅盈利增长（{earnings_g*100:.0f}%）')
    ax.plot(years, div_only,  lw=2,   color=GREEN,  ls=':',  label=f'仅股息（{div_yield*100:.0f}%）')
    ax.plot(years, pe_only,   lw=1.8, color=BLUE,   ls='-.', label=f'仅PE变化（{pe_change*100:.1f}%，低估买入优势）')

    ax.fill_between(years, P, total, alpha=0.1, color=RED)
    ax.set_xlim(0, 30); ax.set_ylim(0)
    apply_zh(ax, title='博格公式：指数基金收益的三大来源分解（10万元·30年）',
             xlabel='年数', ylabel='资产（万元）')
    zh_legend(ax, fontsize=9)
    ax.grid(alpha=0.2)

    zh_text(ax, 28, total[-1]*0.87,
            f'30年后\n≈{total[-1]:.0f}万', size=10, bold=True, color=RED, ha='center')
    plt.tight_layout()
    plt.savefig(f'{OUT}/lsd_ch8_return_sources.png')
    plt.close()
    print('✓ lsd_ch8_return_sources.png')


# ─────────────────────────────────────────────────────
# 图8-2  长期投资的心理关卡——典型行为偏差
# ─────────────────────────────────────────────────────
def lsd_ch8_psychology_traps():
    fig, ax = plt.subplots(figsize=(10, 5.5))
    ax.set_xlim(0, 11); ax.set_ylim(0, 7); ax.set_axis_off()

    traps = [
        (1.5, 5.5, RED,    '追涨杀跌', '看到涨才买，\n跌了就割肉'),
        (4.0, 5.5, ORANGE, '低估不敢买', '市场大跌时\n反而不敢定投'),
        (6.5, 5.5, PURPLE, '看到上涨\n不下手', '等跌了再买，\n结果越等越高'),
        (9.0, 5.5, BLUE,   '定投双核制', '估值+纪律，\n两个核都要有'),
        (1.5, 2.8, TEAL,   '有恒产者\n有恒心', '持有资产的人\n才能长期坚守'),
        (4.0, 2.8, GREEN,  '买指数=\n买国运', '相信国家发展\n就相信指数'),
        (6.5, 2.8, RED,    '最倒霉的\n定投者', '即使买在高点\n长期持有也赚'),
        (9.0, 2.8, DARK,   '复利时间轴', '80%收益在\n20%时间里出现'),
    ]

    for cx, cy, c, title, detail in traps:
        rect = mpatches.FancyBboxPatch((cx-1.3, cy-1.1), 2.6, 2.2,
                                        boxstyle='round,pad=0.1',
                                        fc=c, ec='white', lw=1.8, alpha=0.88, zorder=3)
        ax.add_patch(rect)
        zh_text(ax, cx, cy+0.5, title, size=11, bold=True, ha='center', color='white')
        zh_text(ax, cx, cy-0.3, detail, size=9, ha='center', color='white')

    zh_text(ax, 5.5, 6.7, '第8章：长期投资的心理关卡与应对',
            size=13, bold=True, ha='center', color=DARK)
    plt.tight_layout(pad=0.3)
    plt.savefig(f'{OUT}/lsd_ch8_psychology_traps.png')
    plt.close()
    print('✓ lsd_ch8_psychology_traps.png')


# ─────────────────────────────────────────────────────
# 图8-3  "最倒霉的定投者"——高点买入长期持有仍赚钱
# ─────────────────────────────────────────────────────
def lsd_ch8_worst_investor():
    np.random.seed(99)
    n = 120
    months = np.arange(n)
    # 先涨到高点，再大跌，再慢牛
    pts = [1.0]
    for i in range(119):
        if i < 20:   pts.append(pts[-1]*(1+np.random.normal(0.04, 0.04)))   # 急涨
        elif i < 40: pts.append(pts[-1]*(1+np.random.normal(-0.025, 0.05))) # 大跌
        elif i < 60: pts.append(pts[-1]*(1+np.random.normal(-0.005, 0.04))) # 继续跌
        else:        pts.append(pts[-1]*(1+np.random.normal(0.01, 0.03)))   # 慢牛
    pts = np.array(pts)

    # 最倒霉：第20个月（高点）开始定投，每月500元
    start = 20
    total_cost = 0
    total_units = 0
    cost_line, units_line = [np.nan]*start, [np.nan]*start
    for i in range(start, n):
        total_cost  += 500
        total_units += 500 / pts[i]
        cost_line.append(total_cost / 500 * pts[i] * 0 + total_cost)  # 仅做参考
        units_line.append(total_units * pts[i])

    cost_arr = np.array(cost_line, dtype=float)
    val_arr  = np.array(units_line, dtype=float)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6.5), sharex=True,
                                    gridspec_kw={'hspace':0.06, 'height_ratios':[2,1]})

    ax1.plot(months, pts, lw=2, color=DARK, label='指数净值')
    ax1.scatter([20], [pts[20]], s=200, marker='v', color=RED, zorder=6)
    zh_text(ax1, 22, pts[20]+0.1, '最倒霉：高点开始定投', size=9, color=RED, bold=True)
    ax1.grid(alpha=0.2)
    apply_zh(ax1, ylabel='净值', title='"最倒霉的定投者"——买在高点长期坚持的结果')
    zh_legend(ax1)

    ax2.plot(months[start:], val_arr[start:]/cost_arr[start:]-1,
             lw=2, color=GREEN, label='持仓收益率')
    ax2.axhline(0, ls='--', color=GRAY, lw=1.2)
    ax2.fill_between(months[start:], 0, val_arr[start:]/cost_arr[start:]-1,
                     where=val_arr[start:]/cost_arr[start:] > 1,
                     alpha=0.2, color=GREEN, label='盈利区域')
    ax2.fill_between(months[start:], 0, val_arr[start:]/cost_arr[start:]-1,
                     where=val_arr[start:]/cost_arr[start:] < 1,
                     alpha=0.2, color=RED, label='亏损区域')
    apply_zh(ax2, xlabel='月份', ylabel='累计收益率')
    zh_legend(ax2, ncol=3, fontsize=9)
    ax2.grid(alpha=0.15)
    plt.savefig(f'{OUT}/lsd_ch8_worst_investor.png')
    plt.close()
    print('✓ lsd_ch8_worst_investor.png')


if __name__ == '__main__':
    lsd_ch5_lazy_dip_flow()
    lsd_ch5_dip_vs_blind()
    lsd_ch5_five_tips()
    lsd_ch5_annualized_return()
    lsd_ch6_three_plans()
    lsd_ch7_fund_types_compare()
    lsd_ch7_asset_pyramid()
    lsd_ch8_return_sources()
    lsd_ch8_psychology_traps()
    lsd_ch8_worst_investor()
    print('第5-8章（螺丝钉版）配图全部生成完毕')
