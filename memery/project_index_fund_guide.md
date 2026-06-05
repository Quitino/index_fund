---
name: index-fund-guide-project
description: 《指数基金投资指南》笔记项目——原书位置、笔记结构、配图脚本等基本信息
metadata:
  type: project
---

# 指数基金投资指南笔记项目

**Why:** 用户希望将《指数基金投资指南》（面向程序员的13章教程）整理成意简言赅的核心笔记，配合配图，方便后续继续讨论。

**How to apply:** 后续讨论时直接引用本笔记结构，不需要重新读取原书。

## 原书位置
`/home/root123/Documents/fund_investment/docs/` — 共13章 + 3附录，Markdown格式

## 笔记输出目录
`/home/root123/Documents/index_fund_investment/`
- `docs/` — 核心笔记（index.md + 3个章节笔记文件）
- `docs/pic/` — 37张配图（PNG，150dpi）
- `code/` — 7个Python绘图脚本
- `memery/` — 本项目记忆文件

## 笔记文件结构
- `docs/index.md` — 汇总索引 + 公式速查 + 配图索引
- `docs/notes_ch1_ch4.md` — 第1-4章：通胀/复利/市场/基金概念/分类
- `docs/notes_ch5_ch9.md` — 第5-9章：指数基金/主动基金选法/策略/风险/技术分析
- `docs/notes_ch10_ch13.md` — 第10-13章：信息平台/开户/组合实战/心理陷阱

## 绘图技术栈
- Python matplotlib，中文字体：Noto Sans CJK Regular
  (`/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc`)
- 通过 `code/plot_utils.py` 统一管理字体/颜色/辅助函数

## 状态（2026-06-05）
- 笔记和配图已全部完成（13章全覆盖）
- 附录A/B/C尚未整理（推荐书单、术语速查、常用公式）
- 可后续深化：真实数据回测、具体基金筛选实操
