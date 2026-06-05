---
name: lsd-book-notes
description: 银行螺丝钉《指数基金投资指南》笔记项目——核心策略、文件位置、方便后续接着讨论
metadata:
  type: project
---

# 银行螺丝钉《指数基金投资指南》笔记（2026-06-05）

**Why:** 用户希望将螺丝钉这本书整理成核心笔记，结合之前的程序员教程笔记，图文结合方便后续继续讨论。

## PDF原书位置
`/home/root123/Documents/index_fund_investment/pdf/指数基金投资指南.pdf`（中信出版社，银行螺丝钉著）

## 笔记输出
`/home/root123/Documents/index_fund_investment/`
- `docs/lsd_index.md` — 汇总索引（公式/买卖速查/配图索引/两书对比）
- `docs/lsd_ch1_ch2.md` — 第1~2章：资产观/复利/指数基金三大优势
- `docs/lsd_ch3_ch4.md` — 第3~4章：常见指数品种/四大估值方法/买卖策略
- `docs/lsd_ch5_ch6.md` — 第5~6章：懒人定投法/三种定投计划模板
- `docs/lsd_ch7_ch8.md` — 第7~8章：家庭资产配置金字塔/7大心理关卡
- `docs/pic/lsd_*.png` — 19张配图（Python生成，Noto CJK字体）
- `code/plot_lsd_ch1_ch4.py` — 第1~4章绘图脚本（9张图）
- `code/plot_lsd_ch5_ch8.py` — 第5~8章绘图脚本（10张图）

## 本书核心策略（方便后续直接引用）

### 怎么选（估值策略）
- 盈利收益率法（E/P）：E/P > 10% 买入，< 6.4% 卖出
  适用：上证50、红利指数、H股指数等盈利稳定品种
- 博格公式法（PE）：PE处历史低位买入，高位卖出
  适用：沪深300、中证500、消费、医药等成长型指数
- 博格公式变种（PB）：PB处历史低位买入
  适用：证券、银行、金融、地产等周期性行业

### 怎么买（懒人定投法）
- E/P > 10%：继续定投
- E/P 6.4%~10%：暂停定投，持有
- E/P < 6.4%：分批卖出（分10份，每次卖1份）

### 博格公式
年复合收益率 ≈ 初始股息率 + 年均PE变化率 + 年均盈利增长率

## How to apply
后续讨论时引用 `docs/lsd_index.md` 作为起点，不需重读PDF。
