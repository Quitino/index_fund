"""第9章技术分析配图：K线解析、K线形态、均线系统、量价关系、MACD、RSI+布林带"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from plot_utils import *
import matplotlib.patches as mpatches
import matplotlib.ticker as mticker

OUT = os.path.join(os.path.dirname(__file__), '..', 'docs', 'pic')


def _candle(ax, x, open_, high, low, close, width=0.4):
    """绘制单根K线"""
    color = RED if close >= open_ else BLUE
    # 实体
    rect_y = min(open_, close)
    rect_h = abs(close - open_)
    rect = plt.Rectangle((x-width/2, rect_y), width, max(rect_h, 0.002),
                          fc=color, ec=color, lw=0.5, zorder=4)
    ax.add_patch(rect)
    # 上影线
    ax.vlines(x, max(open_, close), high, color=color, lw=1.2, zorder=4)
    # 下影线
    ax.vlines(x, low, min(open_, close), color=color, lw=1.2, zorder=4)


# ─────────────────────────────────────────────────────
# 图9-1  K线结构解析
# ─────────────────────────────────────────────────────
def ch9_candlestick_anatomy():
    fig, axes = plt.subplots(1, 2, figsize=(8, 5))

    for ax, (o, h, l, c, name) in zip(axes,
        [(10, 14, 8, 13, '阳线（涨）'), (13, 15, 9, 10, '阴线（跌）')]):
        ax.set_xlim(0, 4); ax.set_ylim(6, 16.5)
        ax.set_axis_off()
        _candle(ax, 2, o, h, l, c, width=1.2)

        color = RED if c >= o else BLUE
        # 标注
        def ann(y_val, y_text, text, side='right'):
            x_arrow = 2.62 if side == 'right' else 1.38
            x_text  = 2.7  if side == 'right' else 0.0
            ax.annotate(text, xy=(x_arrow, y_val), xytext=(x_text, y_text),
                        fontproperties=zfont(9),
                        arrowprops=dict(arrowstyle='->', color=DARK, lw=1.2),
                        ha='left' if side=='right' else 'right')

        ann(h, h+0.3, f'最高价 High\n{h}', 'right')
        ann(l, l-0.3, f'最低价 Low\n{l}',  'right')
        ann(max(o,c), max(o,c)+0.2, f'收盘价 Close\n{c}' if c>=o else f'开盘价 Open\n{o}', 'left')
        ann(min(o,c), min(o,c)-0.2, f'开盘价 Open\n{o}' if c>=o else f'收盘价 Close\n{c}', 'left')

        # 上下影线标注
        ax.annotate('上影线', xy=(2.62, (h+max(o,c))/2),
                    xytext=(3.0, (h+max(o,c))/2),
                    fontproperties=zfont(8.5), color=GRAY,
                    arrowprops=dict(arrowstyle='->', color=GRAY, lw=1))
        ax.annotate('下影线', xy=(2.62, (l+min(o,c))/2),
                    xytext=(3.0, (l+min(o,c))/2),
                    fontproperties=zfont(8.5), color=GRAY,
                    arrowprops=dict(arrowstyle='->', color=GRAY, lw=1))
        ax.annotate('实体', xy=(1.4, (o+c)/2),
                    xytext=(0.2, (o+c)/2),
                    fontproperties=zfont(8.5), color=color,
                    arrowprops=dict(arrowstyle='->', color=color, lw=1))

        ax.set_title(name, fontproperties=zfont(12, bold=True),
                     color=RED if c>=o else BLUE)

    plt.suptitle('K线基本结构：开高低收（OHLC）',
                 fontproperties=zfont(13, bold=True))
    plt.tight_layout()
    plt.savefig(f'{OUT}/ch9_candlestick_anatomy.png')
    plt.close()
    print('✓ ch9_candlestick_anatomy.png')


# ─────────────────────────────────────────────────────
# 图9-2  常见K线形态
# ─────────────────────────────────────────────────────
def ch9_candlestick_patterns():
    patterns = [
        ('锤子线\n(看涨反转)', [(10,12,8,11.5),(10,12,8,11.5)], YELLOW),
        ('上吊线\n(看跌反转)', [(10,12,8,11.5),(10,12,8,11.5)], ORANGE),
        ('看涨吞没\n(多头信号)', None, GREEN),
        ('看跌吞没\n(空头信号)', None, RED),
        ('晨星\n(底部反转)', None, BLUE),
        ('暮星\n(顶部反转)', None, PURPLE),
    ]

    # 定义各形态数据 (x, open, high, low, close)
    candles_data = {
        '锤子线\n(看涨反转)': [(2, 10.5, 11.2, 8.0, 11.0)],
        '上吊线\n(看跌反转)': [(2, 10.5, 11.2, 8.0, 11.0)],  # 同形但位置含义不同
        '看涨吞没\n(多头信号)': [(1.5, 11.0, 11.5, 9.5, 10.0), (2.5, 9.0, 12.5, 8.5, 12.0)],
        '看跌吞没\n(空头信号)': [(1.5, 9.5, 11.0, 9.0, 11.0), (2.5, 11.5, 12.0, 8.5, 8.8)],
        '晨星\n(底部反转)': [(1.2, 12.0, 12.3, 11.5, 11.7),
                            (2.0, 11.0, 11.4, 10.5, 10.8),
                            (2.8, 10.5, 13.0, 10.3, 12.5)],
        '暮星\n(顶部反转)': [(1.2, 10.0, 10.5, 9.7, 10.3),
                            (2.0, 10.5, 11.2, 10.2, 10.8),
                            (2.8, 11.0, 11.2, 8.0, 8.3)],
    }
    bg_colors = {'锤子线\n(看涨反转)': (0.9,1,0.9),
                 '上吊线\n(看跌反转)': (1,0.9,0.9),
                 '看涨吞没\n(多头信号)': (0.9,1,0.9),
                 '看跌吞没\n(空头信号)': (1,0.9,0.9),
                 '晨星\n(底部反转)': (0.9,1,0.9),
                 '暮星\n(顶部反转)': (1,0.9,0.9)}

    fig, axes = plt.subplots(2, 3, figsize=(11, 6.5))
    axes = axes.flatten()

    for ax, (pname, _, pc) in zip(axes, patterns):
        cdata = candles_data[pname]
        ax.set_xlim(0.5, 3.5); ax.set_ylim(7.5, 13.5)
        ax.set_axis_off()
        ax.set_facecolor(bg_colors[pname])
        fig.patch.set_alpha(0)
        for candle in cdata:
            x, o, h, l, c = candle
            _candle(ax, x, o, h, l, c, width=0.5)
        ax.set_title(pname, fontproperties=zfont(10, bold=True))

    plt.suptitle('六种经典K线形态（背景绿=看涨信号，红=看跌信号）',
                 fontproperties=zfont(12, bold=True))
    plt.tight_layout()
    plt.savefig(f'{OUT}/ch9_candlestick_patterns.png')
    plt.close()
    print('✓ ch9_candlestick_patterns.png')


# ─────────────────────────────────────────────────────
# 图9-3  均线系统示意
# ─────────────────────────────────────────────────────
def ch9_moving_average():
    np.random.seed(12)
    n = 120
    ret = np.random.normal(0.003, 0.025, n)
    price = 100 * np.cumprod(np.concatenate([[1], 1+ret]))
    x = np.arange(n+1)

    def sma(arr, k):
        return np.array([np.nan]*k + [arr[i-k:i].mean() for i in range(k, len(arr))])

    ma5  = sma(price, 5)
    ma20 = sma(price, 20)
    ma60 = sma(price, 60)

    fig, (ax_main, ax_vol) = plt.subplots(2, 1, figsize=(11, 6), sharex=True,
                                           gridspec_kw={'height_ratios':[3,1],'hspace':0.06})

    ax_main.plot(x, price, lw=1.2, color=DARK, alpha=0.8, label='价格', zorder=3)
    ax_main.plot(x, ma5,   lw=1.5, color=RED,    label='MA5（5日）')
    ax_main.plot(x, ma20,  lw=2,   color=BLUE,   label='MA20（20日）')
    ax_main.plot(x, ma60,  lw=2.2, color=GREEN,  label='MA60（60日）')

    # 标注金叉/死叉
    cross_up = cross_down = None
    for i in range(21, n):
        if not np.isnan(ma5[i]) and not np.isnan(ma20[i]) and not np.isnan(ma5[i-1]):
            if ma5[i-1] < ma20[i-1] and ma5[i] >= ma20[i] and cross_up is None:
                cross_up = i
                ax_main.scatter(i, price[i], s=200, marker='^', color=RED, zorder=6)
                zh_text(ax_main, i+1, price[i]+1, '金叉↑', size=9, color=RED, bold=True)
            elif ma5[i-1] > ma20[i-1] and ma5[i] <= ma20[i] and cross_down is None:
                cross_down = i
                ax_main.scatter(i, price[i], s=200, marker='v', color=BLUE, zorder=6)
                zh_text(ax_main, i+1, price[i]-2, '死叉↓', size=9, color=BLUE, bold=True)

    apply_zh(ax_main, ylabel='价格（元）',
             title='均线系统示意——MA5/MA20/MA60与金叉死叉')
    zh_legend(ax_main, ncol=4, fontsize=8.5)
    ax_main.grid(alpha=0.2)

    # 简单成交量
    vol = np.abs(np.random.normal(0.5, 0.3, n+1)) * 1000
    ax_vol.bar(x, vol, color=[RED if ret[min(i,n-1)]>0 else BLUE for i in range(n+1)],
               alpha=0.6, width=1)
    apply_zh(ax_vol, xlabel='交易日', ylabel='成交量')
    ax_vol.grid(alpha=0.15)

    plt.savefig(f'{OUT}/ch9_moving_average.png')
    plt.close()
    print('✓ ch9_moving_average.png')


# ─────────────────────────────────────────────────────
# 图9-4  量价关系
# ─────────────────────────────────────────────────────
def ch9_volume_price():
    np.random.seed(33)
    n = 80
    x = np.arange(n)

    # 四段：量增价涨、量缩价涨、量增价跌、量缩价跌
    seg_len = 20
    prices, volumes = [100], [500]

    defs = [
        (0.006, 0.012, 1.3, 0.15, GREEN),  # 量增价涨
        (0.004, 0.008, 0.7, 0.1,  ORANGE), # 量缩价涨
        (-0.005, 0.012, 1.4, 0.15, RED),   # 量增价跌
        (-0.003, 0.008, 0.6, 0.1, BLUE),   # 量缩价跌
    ]
    for mu, sigma, vol_mul, vol_sigma, _ in defs:
        for _ in range(seg_len):
            r = np.random.normal(mu, sigma)
            prices.append(prices[-1]*(1+r))
            v = abs(np.random.normal(500*vol_mul, 500*vol_sigma))
            volumes.append(v)

    prices  = np.array(prices[:n+1])
    volumes = np.array(volumes[:n+1])

    seg_labels = ['量增价涨（健康上涨）', '量缩价涨（需警惕）', '量增价跌（出货信号）', '量缩价跌（筑底）']
    seg_colors = [GREEN, ORANGE, RED, BLUE]

    fig, (ax_p, ax_v) = plt.subplots(2, 1, figsize=(11, 5.5), sharex=True,
                                      gridspec_kw={'height_ratios':[2,1],'hspace':0.06})

    ax_p.plot(np.arange(n+1), prices, lw=2, color=DARK)
    for i, (lbl, c) in enumerate(zip(seg_labels, seg_colors)):
        s = i*seg_len; e = (i+1)*seg_len+1
        ax_p.axvspan(s, e-1, alpha=0.1, color=c)
        ax_p.text((s+e)/2-0.5, prices.max()*1.01, lbl, fontproperties=zfont(8.5),
                  ha='center', color=c, rotation=0)
    apply_zh(ax_p, ylabel='价格（元）')
    ax_p.grid(alpha=0.2)

    for i, (lbl, c) in enumerate(zip(seg_labels, seg_colors)):
        s = i*seg_len; e = (i+1)*seg_len+1
        ax_v.bar(np.arange(s, e), volumes[s:e], color=c, alpha=0.75, width=1)
        ax_v.axvspan(s, e-1, alpha=0.05, color=c)
    apply_zh(ax_v, xlabel='交易日', ylabel='成交量')
    ax_v.grid(alpha=0.15)

    plt.suptitle('四种典型量价关系（颜色对应不同市场阶段）',
                 fontproperties=zfont(12, bold=True))
    plt.savefig(f'{OUT}/ch9_volume_price.png')
    plt.close()
    print('✓ ch9_volume_price.png')


# ─────────────────────────────────────────────────────
# 图9-5  MACD指标
# ─────────────────────────────────────────────────────
def ch9_macd():
    np.random.seed(7)
    n = 150
    ret = np.random.normal(0.002, 0.022, n)
    price = 100 * np.cumprod(np.concatenate([[1], 1+ret]))
    x = np.arange(n+1)

    def ema(arr, k):
        alpha = 2/(k+1)
        result = [arr[0]]
        for v in arr[1:]:
            result.append(alpha*v + (1-alpha)*result[-1])
        return np.array(result)

    ema12 = ema(price, 12)
    ema26 = ema(price, 26)
    dif   = ema12 - ema26
    dea   = ema(dif, 9)
    hist  = 2*(dif - dea)

    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(11, 7.5), sharex=True,
                                         gridspec_kw={'hspace':0.06})

    # 价格图
    ax1.plot(x, price, lw=1.5, color=DARK, label='价格')
    ax1.grid(alpha=0.2)
    apply_zh(ax1, ylabel='价格（元）', title='MACD指标示意图——趋势与动量分析')
    zh_legend(ax1)

    # DIF/DEA
    ax2.plot(x, dif, lw=1.8, color=RED,  label='DIF（快线）')
    ax2.plot(x, dea, lw=1.8, color=BLUE, label='DEA（慢线/信号线）')
    ax2.axhline(0, color=GRAY, lw=1, ls='--')
    ax2.fill_between(x, dif, dea, where=dif>=dea, alpha=0.2, color=RED,  label='多头区')
    ax2.fill_between(x, dif, dea, where=dif<dea,  alpha=0.2, color=BLUE, label='空头区')

    # 标注金叉
    for i in range(1, len(dif)):
        if dif[i-1] < dea[i-1] and dif[i] >= dea[i]:
            ax2.scatter(i, dif[i], s=120, marker='^', color=RED, zorder=5)
            break
    for i in range(1, len(dif)):
        if dif[i-1] > dea[i-1] and dif[i] <= dea[i]:
            ax2.scatter(i, dif[i], s=120, marker='v', color=BLUE, zorder=5)
            break

    apply_zh(ax2, ylabel='DIF/DEA')
    zh_legend(ax2, ncol=2, fontsize=8.5)
    ax2.grid(alpha=0.15)

    # MACD柱
    colors_hist = [RED if v >= 0 else BLUE for v in hist]
    ax3.bar(x, hist, color=colors_hist, alpha=0.75, width=1)
    ax3.axhline(0, color=GRAY, lw=1, ls='--')
    apply_zh(ax3, xlabel='交易日', ylabel='MACD柱')
    ax3.grid(alpha=0.15)

    plt.savefig(f'{OUT}/ch9_macd.png')
    plt.close()
    print('✓ ch9_macd.png')


# ─────────────────────────────────────────────────────
# 图9-6  RSI与布林带
# ─────────────────────────────────────────────────────
def ch9_rsi_bollinger():
    np.random.seed(19)
    n = 150
    ret = np.random.normal(0.002, 0.022, n)
    price = 100 * np.cumprod(np.concatenate([[1], 1+ret]))
    x = np.arange(n+1)

    # 布林带
    k = 20
    ma20 = np.array([np.nan]*k + [price[i-k:i].mean() for i in range(k, n+1)])
    std20= np.array([np.nan]*k + [price[i-k:i].std()  for i in range(k, n+1)])
    ub = ma20 + 2*std20
    lb = ma20 - 2*std20

    # RSI
    def rsi(arr, period=14):
        gains = np.diff(arr).clip(min=0)
        losses = -np.diff(arr).clip(max=0)
        result = [np.nan]*period
        avg_g = gains[:period].mean(); avg_l = losses[:period].mean()
        result.append(100 if avg_l==0 else 100-100/(1+avg_g/avg_l))
        for g, l in zip(gains[period:], losses[period:]):
            avg_g = (avg_g*(period-1)+g)/period
            avg_l = (avg_l*(period-1)+l)/period
            result.append(100 if avg_l==0 else 100-100/(1+avg_g/avg_l))
        return np.array(result)

    rsi14 = rsi(price, 14)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 7), sharex=True,
                                    gridspec_kw={'hspace':0.06,'height_ratios':[3,1.5]})

    # 布林带
    ax1.plot(x, price, lw=1.5, color=DARK, label='价格', zorder=3)
    ax1.plot(x, ma20, lw=1.5, color=BLUE, ls='--', label='MA20（中轨）')
    ax1.plot(x, ub,   lw=1.5, color=RED,  ls=':',  label='上轨（+2σ）')
    ax1.plot(x, lb,   lw=1.5, color=GREEN,ls=':',  label='下轨（-2σ）')
    ax1.fill_between(x, lb, ub, alpha=0.08, color=BLUE)

    # 触及上轨/下轨标注
    for i in range(k, n+1):
        if not np.isnan(ub[i]) and price[i] >= ub[i]:
            ax1.scatter(i, price[i], s=60, color=RED, zorder=5, alpha=0.7)
        if not np.isnan(lb[i]) and price[i] <= lb[i]:
            ax1.scatter(i, price[i], s=60, color=GREEN, zorder=5, alpha=0.7)

    apply_zh(ax1, ylabel='价格（元）',
             title='布林带（上方）与RSI（下方）组合示例')
    zh_legend(ax1, ncol=4, fontsize=8.5)
    ax1.grid(alpha=0.18)

    # RSI
    ax2.plot(x[:len(rsi14)], rsi14, lw=1.8, color=PURPLE, label='RSI(14)')
    ax2.axhline(70, ls='--', color=RED,   lw=1.3, label='超买线(70)')
    ax2.axhline(30, ls='--', color=GREEN, lw=1.3, label='超卖线(30)')
    ax2.axhline(50, ls=':',  color=GRAY,  lw=1)
    ax2.fill_between(x[:len(rsi14)], 70, rsi14,
                     where=np.array(rsi14)>=70, alpha=0.2, color=RED)
    ax2.fill_between(x[:len(rsi14)], rsi14, 30,
                     where=np.array(rsi14)<=30, alpha=0.2, color=GREEN)
    ax2.set_ylim(0, 100)
    apply_zh(ax2, xlabel='交易日', ylabel='RSI')
    zh_legend(ax2, ncol=3, fontsize=8.5)
    ax2.grid(alpha=0.15)

    plt.savefig(f'{OUT}/ch9_rsi_bollinger.png')
    plt.close()
    print('✓ ch9_rsi_bollinger.png')


if __name__ == '__main__':
    ch9_candlestick_anatomy()
    ch9_candlestick_patterns()
    ch9_moving_average()
    ch9_volume_price()
    ch9_macd()
    ch9_rsi_bollinger()
    print('第9章配图全部生成完毕')
