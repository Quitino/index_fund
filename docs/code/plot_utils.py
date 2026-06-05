"""公共绘图工具：统一字体、颜色、样式设置"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np

# ---------- 字体配置 ----------
_FONT_PATH = '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
_BOLD_PATH = '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'
fm.fontManager.addfont(_FONT_PATH)
fm.fontManager.addfont(_BOLD_PATH)

ZH_FONT   = fm.FontProperties(fname=_FONT_PATH)
ZH_BOLD   = fm.FontProperties(fname=_BOLD_PATH)

plt.rcParams.update({
    'axes.unicode_minus': False,
    'figure.dpi': 120,
    'savefig.dpi': 150,
    'savefig.bbox': 'tight',
})

# ---------- 调色板 ----------
RED    = '#E74C3C'
BLUE   = '#2980B9'
GREEN  = '#27AE60'
ORANGE = '#E67E22'
PURPLE = '#8E44AD'
GRAY   = '#95A5A6'
DARK   = '#2C3E50'
YELLOW = '#F1C40F'
TEAL   = '#16A085'

PALETTE = [BLUE, RED, GREEN, ORANGE, PURPLE, TEAL, GRAY]


def zfont(size=12, bold=False):
    """返回指定大小的中文字体属性"""
    fp = fm.FontProperties(fname=_BOLD_PATH if bold else _FONT_PATH)
    fp.set_size(size)
    return fp


def apply_zh(ax, title=None, xlabel=None, ylabel=None,
             title_size=13, label_size=11, tick_size=10):
    """统一为坐标轴设置中文标签"""
    if title:
        ax.set_title(title, fontproperties=zfont(title_size, bold=True))
    if xlabel:
        ax.set_xlabel(xlabel, fontproperties=zfont(label_size))
    if ylabel:
        ax.set_ylabel(ylabel, fontproperties=zfont(label_size))
    for tick in ax.get_xticklabels() + ax.get_yticklabels():
        tick.set_fontproperties(zfont(tick_size))


def zh_legend(ax, **kwargs):
    """设置图例中文字体"""
    leg = ax.legend(**kwargs)
    if leg:
        for text in leg.get_texts():
            text.set_fontproperties(zfont(10))
    return leg


def zh_text(ax, x, y, s, size=10, bold=False, **kwargs):
    return ax.text(x, y, s, fontproperties=zfont(size, bold=bold), **kwargs)
