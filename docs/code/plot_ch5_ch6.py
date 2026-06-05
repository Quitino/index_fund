"""第5-6章配图：指数累计收益、PE历史走势、PE/PB象限、主动vs被动胜率、经理雷达、规模效应"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from plot_utils import *
import matplotlib.patches as mpatches

OUT = os.path.join(os.path.dirname(__file__), '..', 'docs', 'pic')


# ─────────────────────────────────────────────────────
# 图5-1  主要指数累计收益对比
# ─────────────────────────────────────────────────────
def ch5_index_comparison():
    np.random.seed(7)
    months = np.arange(0, 121)  # 10年

    def sim_index(annual_ret, annual_vol):
        m_ret = annual_ret/12
        m_vol = annual_vol/np.sqrt(12)
        r = np.random.normal(m_ret, m_vol, len(months))
        return 100 * np.cumprod(np.concatenate([[1], 1+r]))

    indices = [
        ('沪深300',    0.09, 0.20, BLUE),
        ('中证500',    0.11, 0.26, RED),
        ('创业板指',   0.12, 0.34, ORANGE),
        ('标普500(QDII)', 0.13, 0.18, GREEN),
        ('纳斯达克100', 0.15, 0.24, PURPLE),
    ]

    fig, ax = plt.subplots(figsize=(10, 5.5))
    for name, ret, vol, c in indices:
        vals = sim_index(ret, vol)
        ax.plot(months, vals[:len(months)], lw=2, color=c, label=name)

    ax.axhline(100, ls='--', color=GRAY, lw=1)
    ax.set_xlim(0, 120)
    apply_zh(ax, title='主要指数10年累计净值对比（模拟数据）',
             xlabel='月份', ylabel='累计净值（起始=100）')
    zh_legend(ax, loc='upper left', ncol=2)
    ax.grid(alpha=0.22)
    plt.tight_layout()
    plt.savefig(f'{OUT}/ch5_index_comparison.png')
    plt.close()
    print('✓ ch5_index_comparison.png')


# ─────────────────────────────────────────────────────
# 图5-2  PE历史走势（均值回归）
# ─────────────────────────────────────────────────────
def ch5_index_pe_history():
    np.random.seed(3)
    n = 180
    t = np.arange(n)
    mean_pe = 13
    pe = mean_pe + 5*np.sin(t*2*np.pi/60) + np.random.normal(0, 2, n)
    pe = np.clip(pe, 7, 30)
    sigma = pe.std()

    fig, ax = plt.subplots(figsize=(10, 4.8))
    ax.plot(t, pe, lw=1.5, color=BLUE, label='沪深300 PE')
    ax.axhline(mean_pe, ls='--', color=DARK, lw=1.8, label=f'历史均值 {mean_pe}x')
    ax.axhline(mean_pe + sigma, ls=':', color=RED, lw=1.5, label=f'+1σ ({mean_pe+sigma:.1f}x)')
    ax.axhline(mean_pe - sigma, ls=':', color=GREEN, lw=1.5, label=f'-1σ ({mean_pe-sigma:.1f}x)')

    ax.fill_between(t, mean_pe-sigma, pe,
                    where=pe < mean_pe-sigma, alpha=0.25, color=GREEN)
    ax.fill_between(t, pe, mean_pe+sigma,
                    where=pe > mean_pe+sigma, alpha=0.25, color=RED)

    # 标注买入/警惕区
    zh_text(ax, 5, mean_pe-sigma-1.5, '低估区 → 适合买入', size=9, color=GREEN, bold=True)
    zh_text(ax, 5, mean_pe+sigma+0.5, '高估区 → 需谨慎', size=9, color=RED, bold=True)

    ax.set_xlim(0, n); ax.set_ylim(4, 32)
    apply_zh(ax, title='沪深300 市盈率（PE）历史走势与均值回归（模拟示意）',
             xlabel='月份', ylabel='市盈率（倍）')
    zh_legend(ax, loc='upper right')
    ax.grid(alpha=0.2)
    plt.tight_layout()
    plt.savefig(f'{OUT}/ch5_index_pe_history.png')
    plt.close()
    print('✓ ch5_index_pe_history.png')


# ─────────────────────────────────────────────────────
# 图5-3  PE/PB估值象限
# ─────────────────────────────────────────────────────
def ch5_pe_pb_quadrant():
    indices = [
        ('上证50', 8.5, 0.8, BLUE),
        ('沪深300', 12, 1.3, DARK),
        ('中证500', 20, 2.0, ORANGE),
        ('创业板指', 35, 4.5, RED),
        ('中证红利', 7, 0.7, GREEN),
        ('标普500',  22, 4.0, PURPLE),
        ('恒生指数', 9, 1.0, TEAL),
    ]
    fig, ax = plt.subplots(figsize=(8, 6))

    for name, pe, pb, c in indices:
        ax.scatter(pe, pb, s=200, color=c, zorder=5, edgecolors='white', lw=1.5)
        zh_text(ax, pe+0.5, pb+0.08, name, size=10, color=c)

    # 象限线
    ax.axvline(16, ls='--', color=GRAY, lw=1.2)
    ax.axhline(1.5, ls='--', color=GRAY, lw=1.2)

    # 象限标签
    kw = dict(ha='center', va='center', size=9, color=GRAY,
              bbox=dict(fc='white', ec=GRAY, alpha=0.7, boxstyle='round'))
    zh_text(ax,  8, 3.5, '低PE高PB\n（轻资产高溢价）', **kw)
    zh_text(ax, 28, 3.5, '高PE高PB\n（高估区，需谨慎）', **kw)
    zh_text(ax,  8, 0.5, '低PE低PB\n（低估区★推荐）', **{**kw, 'color':GREEN})
    zh_text(ax, 28, 0.5, '高PE低PB\n（成长或价值陷阱）', **kw)

    ax.set_xlim(3, 40); ax.set_ylim(0.2, 5.5)
    apply_zh(ax, title='主要指数 PE/PB 估值象限（模拟示意）',
             xlabel='市盈率 PE（倍）', ylabel='市净率 PB（倍）')
    ax.grid(alpha=0.15)
    plt.tight_layout()
    plt.savefig(f'{OUT}/ch5_pe_pb_quadrant.png')
    plt.close()
    print('✓ ch5_pe_pb_quadrant.png')


# ─────────────────────────────────────────────────────
# 图5-4  主动基金vs指数基金胜率随时间下降
# ─────────────────────────────────────────────────────
def ch5_active_vs_passive():
    periods = ['1年', '2年', '3年', '5年', '7年', '10年']
    x = [1, 2, 3, 5, 7, 10]
    win_rates = [42, 38, 35, 27, 20, 15]

    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    ax.bar(periods, win_rates, color=[BLUE if w>30 else ORANGE if w>20 else RED for w in win_rates],
           edgecolor='white', lw=1.5, width=0.6)
    ax.axhline(50, ls='--', color=GRAY, lw=1.5, label='50%（随机水平）')
    ax.axhline(25, ls=':', color=ORANGE, lw=1.5, label='25%')

    for i, (p, w) in enumerate(zip(periods, win_rates)):
        zh_text(ax, p, w+1, f'{w}%', size=11, bold=True, ha='center', color=DARK)

    ax.set_ylim(0, 60)
    apply_zh(ax, title='不同持有期内，主动基金跑赢指数的概率',
             xlabel='持有期', ylabel='胜率（%）')
    zh_legend(ax)
    ax.grid(axis='y', alpha=0.22)
    for tick in ax.get_xticklabels():
        tick.set_fontproperties(zfont(11))
    plt.tight_layout()
    plt.savefig(f'{OUT}/ch5_active_vs_passive.png')
    plt.close()
    print('✓ ch5_active_vs_passive.png')


# ─────────────────────────────────────────────────────
# 图6-1  基金经理风格雷达图
# ─────────────────────────────────────────────────────
def ch6_manager_style():
    cats = ['年化收益', '波动控制', '换手率\n（低=好）', '回撤控制', '持仓集中度\n（低=分散）']
    N = len(cats)
    angles = np.linspace(0, 2*np.pi, N, endpoint=False).tolist()
    angles += angles[:1]

    growth = [4.5, 2.5, 3.0, 2.5, 4.0]  # 成长型：高收益高波动
    value  = [3.5, 4.5, 2.0, 4.5, 2.5]  # 价值型：低换手低回撤
    growth += growth[:1]; value += value[:1]

    fig, ax = plt.subplots(figsize=(6.5, 5.5), subplot_kw=dict(polar=True))
    ax.plot(angles, growth, color=RED,  lw=2.2, label='成长型基金经理')
    ax.fill(angles, growth, color=RED,  alpha=0.18)
    ax.plot(angles, value,  color=BLUE, lw=2.2, label='价值型基金经理')
    ax.fill(angles, value,  color=BLUE, alpha=0.18)

    ax.set_ylim(0, 5.5)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(cats, fontproperties=zfont(10))
    ax.set_yticklabels(['1','2','3','4','5'], fontproperties=zfont(7))

    apply_zh(ax, title='成长型 vs 价值型基金经理风格对比')
    zh_legend(ax, loc='upper right', bbox_to_anchor=(1.35, 1.15))
    plt.tight_layout()
    plt.savefig(f'{OUT}/ch6_manager_style.png')
    plt.close()
    print('✓ ch6_manager_style.png')


# ─────────────────────────────────────────────────────
# 图6-2  基金规模与收益散点（10-100亿最优）
# ─────────────────────────────────────────────────────
def ch6_fund_size_effect():
    np.random.seed(22)
    n = 200
    sizes = np.exp(np.random.uniform(np.log(0.5), np.log(500), n))

    def ret_fn(s):
        # 规模在10-100亿时收益最优
        if s < 5:    base = 8
        elif s < 10: base = 9.5
        elif s < 100: base = 11
        elif s < 200: base = 9
        else:         base = 7
        return base + np.random.normal(0, 3)

    rets = np.array([ret_fn(s) for s in sizes])

    fig, ax = plt.subplots(figsize=(8.5, 5))
    sc = ax.scatter(sizes, rets, s=30, alpha=0.55,
                    c=np.clip(rets, 0, 20), cmap='RdYlGn', edgecolors='none')
    plt.colorbar(sc, ax=ax, label='').set_label('年化收益率', fontproperties=zfont(9))

    ax.axvspan(10, 100, alpha=0.12, color=GREEN)
    zh_text(ax, 35, 19, '最优区间\n10~100亿', size=10, bold=True,
            ha='center', color=GREEN)
    ax.axvline(10,  ls='--', color=GREEN, lw=1.5)
    ax.axvline(100, ls='--', color=GREEN, lw=1.5)

    ax.set_xscale('log')
    ax.set_xlim(0.3, 600); ax.set_ylim(-5, 25)
    apply_zh(ax, title='偏股混合型基金：规模 vs 近3年年化收益（模拟数据）',
             xlabel='基金规模（亿元，对数轴）', ylabel='近3年年化收益率（%）')
    ax.grid(alpha=0.2)
    plt.tight_layout()
    plt.savefig(f'{OUT}/ch6_fund_size_effect.png')
    plt.close()
    print('✓ ch6_fund_size_effect.png')


# ─────────────────────────────────────────────────────
# 图6-3  主动基金筛选SOP流程图
# ─────────────────────────────────────────────────────
def ch6_selection_flow():
    steps = [
        ('①确定目标', '投资期 ≥3年\n偏股混合型', DARK),
        ('②初步过滤', '成立≥3年\n规模10-100亿\n晨星≥3星', TEAL),
        ('③经理考察', '任职≥3年\n在管≤3只\n最大回撤≤30%', PURPLE),
        ('④业绩验证', '5年年化跑赢\n基准≥3%\n夏普比率≥1', BLUE),
        ('⑤持仓分析', '前十大≤60%\n行业符合预期\n风格一致', ORANGE),
        ('⑥规模/费率', '规模未急剧扩大\n管理费核实', RED),
        ('⑦最终决策', '满足15/21项\n→纳入候选', GREEN),
    ]

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.set_xlim(0, 11); ax.set_ylim(0, 5.5)
    ax.set_axis_off()

    for i, (title, detail, c) in enumerate(steps):
        cx = 1.3 + i * 1.4
        rect = mpatches.FancyBboxPatch((cx-0.6, 1.2), 1.2, 2.8,
                                   boxstyle='round,pad=0.08',
                                   fc=c, ec='white', lw=2, alpha=0.9, zorder=3)
        ax.add_patch(rect)
        zh_text(ax, cx, 3.65, title, size=9.5, bold=True, ha='center', color='white')
        for j, line in enumerate(detail.split('\n')):
            zh_text(ax, cx, 2.9-j*0.45, line, size=8, ha='center', color='white')

        if i < len(steps)-1:
            ax.annotate('', xy=(cx+0.7, 2.6), xytext=(cx+0.6, 2.6),
                        arrowprops=dict(arrowstyle='->', color=GRAY, lw=1.6), zorder=4)

    zh_text(ax, 5.5, 5.0, '主动基金筛选 SOP（7步流程）',
            size=13, bold=True, ha='center', color=DARK)
    plt.tight_layout(pad=0.5)
    plt.savefig(f'{OUT}/ch6_selection_flow.png')
    plt.close()
    print('✓ ch6_selection_flow.png')


if __name__ == '__main__':
    ch5_index_comparison()
    ch5_index_pe_history()
    ch5_pe_pb_quadrant()
    ch5_active_vs_passive()
    ch6_manager_style()
    ch6_fund_size_effect()
    ch6_selection_flow()
    print('第5-6章配图全部生成完毕')
