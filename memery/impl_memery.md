
6个全部完成！快速读取剩余4份分析，然后综合设计方案。

Read FundCrawler_analysis.md
Read Fund_analysis.md
6个全部完成，更新 Todo 并给出综合设计方案。

Update Todos

阅读 6 个参考项目并写分析文档

合并分析结果，与用户讨论设计方案
6个项目全部读完，现在给出综合分析和设计方案。

参考项目核心提炼
6个项目各有所长，也各有致命缺陷：

项目	最大亮点	最大问题
xalpha	FIFO持仓追踪、精确现金流建模、XIRR、完整策略框架	全靠逆向爬虫，极不稳定；交易日历手动维护
fund-strategy	引擎与UI解耦、最大本金收益率公式、分红处理完整、MACD买卖信号	无T+1延迟、纯前端无持久化
FundCrawler	AIMD自适应限流、声明式依赖图爬虫架构、晨星数据字段最全	无历史净值序列
Fund(olixu)	两库分离SQLite设计、eastmoney接口URL清晰	无估值指标、策略过于简陋
StockAnal_Sys	Flask+三层数据隔离架构、指标计算清晰	Mock数据残留、无回测
FundCombination	持仓穿透理念	脆弱爬虫、功能极残缺
设计方案
一、整体分层架构

fund_sys/
│
├── config/                  # 配置层
│   ├── settings.py          # 全局配置（DB路径、API超时等）
│   └── logging.py
│
├── data/                    # 数据层
│   ├── fetcher/             # 数据抓取（akshare为主，eastmoney补充）
│   │   ├── base.py          # 抽象接口 + 重试/限流装饰器
│   │   ├── akshare_api.py   # akshare封装（免费稳定，无需爬虫）
│   │   ├── eastmoney.py     # 东方财富补充接口
│   │   └── cached.py        # 带TTL缓存的包装层
│   ├── models/              # ORM数据模型
│   │   ├── fund_info.py     # 基金基本信息表
│   │   ├── nav_history.py   # 历史净值表
│   │   ├── index_val.py     # 指数估值表（PE/PB）
│   │   └── base.py          # SQLAlchemy Base
│   ├── repository/          # 数据仓库（DB读写封装）
│   │   ├── fund_repo.py
│   │   ├── nav_repo.py
│   │   └── valuation_repo.py
│   └── updater.py           # 增量更新调度器
│
├── strategy/                # 策略层
│   ├── indicators.py        # 指标计算（PE/PB分位、盈利收益率等）
│   ├── buy_signal.py        # 买入信号（螺丝钉E/P法、博格公式法）
│   ├── sell_signal.py       # 卖出信号
│   ├── fund_selector.py     # 选基策略（从DB拉取+多维筛选）
│   └── formulas.py          # 公式库（XIRR、年化收益率等）
│
├── shadow/                  # 影子账户层（核心）
│   ├── position.py          # FIFO持仓追踪（借鉴xalpha rem）
│   ├── cashflow.py          # 现金流表（cftable）
│   ├── portfolio.py         # 单基金影子账户
│   ├── multi_portfolio.py   # 多基金组合
│   └── report.py            # 收益报告生成
│
├── cli/                     # 命令行界面
│   ├── commands/
│   │   ├── fetch.py         # 数据拉取命令
│   │   ├── screen.py        # 选基命令
│   │   ├── shadow.py        # 影子模式命令
│   │   └── report.py        # 报告命令
│   └── main.py
│
├── tests/
├── pyproject.toml
└── README.md
二、数据层设计
数据源选择：用 akshare 替代爬虫

这是最重要的架构决策。6个参考项目的核心痛点都是"爬虫不稳定"。akshare 是专门封装中国金融数据的开源库，内部接口每周维护，能覆盖我们90%的需求：


# 可以获取的关键数据（无需自己爬虫）
akshare.fund_open_fund_info_em()     # 基金基本信息（场内外、成立日期、费率、跟踪指数）
akshare.fund_open_fund_daily_em()    # 场外基金历史净值
akshare.fund_etf_fund_info_em()      # ETF历史净值
akshare.fund_open_fund_rating_em()   # 基金评级
akshare.stock_zh_index_daily()       # 指数行情（沪深300等）
akshare.stock_a_indicator_lg()       # A股PE/PB（用于指数估值）
数据库设计：


-- 基金信息表（静态，每周更新一次）
fund_info(
    code TEXT PRIMARY KEY,    -- 基金代码
    name TEXT,                -- 基金名称
    type TEXT,                -- 基金类型（股票型/混合型/债券型/指数型）
    market TEXT,              -- 场内/场外
    tracking_index TEXT,      -- 跟踪指数（指数基金专用）
    inception_date DATE,      -- 成立日期
    aum REAL,                 -- 资产规模（亿元）
    manager TEXT,             -- 基金经理
    mgmt_fee REAL,            -- 管理费率（%/年）
    custody_fee REAL,         -- 托管费率（%/年）
    purchase_status TEXT,     -- 申购状态
    updated_at DATETIME
)

-- 历史净值表（每日增量更新）
nav_history(
    code TEXT,
    date DATE,
    nav REAL,                 -- 单位净值
    acc_nav REAL,             -- 累计净值
    daily_return REAL,        -- 日涨幅（%）
    dividend REAL,            -- 分红（元/份，0表示无）
    split_ratio REAL,         -- 折算系数（1.0表示无折算）
    PRIMARY KEY (code, date)
)

-- 指数估值表（PE/PB历史，每日更新）
index_valuation(
    index_code TEXT,
    date DATE,
    pe REAL,
    pb REAL,
    pe_percentile REAL,       -- PE历史百分位（0~1）
    pb_percentile REAL,
    roe REAL,
    earnings_yield REAL,      -- 盈利收益率 = 1/PE
    PRIMARY KEY (index_code, date)
)
三、策略层设计（螺丝钉方法论）
核心公式完整实现：


# strategy/formulas.py

def earnings_yield(pe: float) -> float:
    """盈利收益率 = 1/PE，螺丝钉核心选买指标"""
    return 1.0 / pe * 100  # 返回百分比

def buy_signal_ep(pe: float) -> str:
    """盈利收益率法买卖信号"""
    ep = earnings_yield(pe)
    if ep > 10:    return "BUY"    # 开始定投
    if ep > 6.4:   return "HOLD"   # 持有
    return "SELL"                   # 分批卖出

def bogle_expected_return(
    dividend_yield: float,      # 初始股息率（%）
    pe_change_annual: float,    # 年均PE变化率（%）
    earnings_growth: float      # 年均盈利增长率（%）
) -> float:
    """博格公式：指数基金预期年复合收益率"""
    return dividend_yield + pe_change_annual + earnings_growth

def xirr(cashflows: list[tuple[date, float]], guess=0.1) -> float:
    """不规则时间间隔内部收益率（XIRR）——年化定投收益率标准算法"""
    # cashflows: [(date, amount), ...], 流出为负，流入为正
    from scipy.optimize import brentq
    t0 = min(d for d, _ in cashflows)
    def npv(rate):
        return sum(cf / (1 + rate) ** ((t - t0).days / 365.0)
                   for t, cf in cashflows)
    return brentq(npv, -0.999, 100.0)

def annualized_return(total_return: float, days: int) -> float:
    """年化收益率（复利）"""
    return (1 + total_return) ** (365 / days) - 1

def max_drawdown(nav_series: list[float]) -> float:
    """最大回撤"""
    peak = nav_series[0]
    max_dd = 0.0
    for v in nav_series:
        peak = max(peak, v)
        dd = (v - peak) / peak
        max_dd = min(max_dd, dd)
    return abs(max_dd)

def sharpe_ratio(returns: list[float], risk_free=0.03, periods=250) -> float:
    """夏普比率"""
    import numpy as np
    excess = np.array(returns) - risk_free / periods
    return np.sqrt(periods) * excess.mean() / excess.std()
四、影子账户层（最核心）
借鉴 xalpha 的 FIFO rem 设计，但简化且正确处理 T+1：


# shadow/position.py  ——  FIFO持仓追踪

@dataclass
class Lot:
    """一批次买入记录"""
    buy_date: date       # 确认买入日（T+1）
    shares: float        # 份额
    nav: float           # 买入净值
    cost_per_share: float # 含申购费的成本单价

class FIFOPosition:
    """先进先出持仓队列，用于精确计算持有天数和赎回费"""
    def __init__(self):
        self.lots: list[Lot] = []
    
    def buy(self, confirm_date, shares, nav, cost_per_share):
        self.lots.append(Lot(confirm_date, shares, nav, cost_per_share))
    
    def sell(self, sell_date, shares_to_sell, fee_schedule) -> dict:
        """
        FIFO卖出，返回：
        - proceeds: 到账金额
        - sold_lots: 各批次卖出详情（用于计算赎回费）
        - realized_pnl: 已实现盈亏
        """
        ...

# shadow/portfolio.py  ——  单基金影子账户

class ShadowPortfolio:
    def __init__(self, code: str, start_date: date, amount_per_day: float):
        self.code = code
        self.start_date = start_date
        self.amount_per_day = amount_per_day
        self.position = FIFOPosition()
        self.cashflow: list[CashflowEntry] = []
    
    def simulate(self, end_date: date) -> pd.DataFrame:
        """
        从start_date到end_date逐日模拟定投
        返回每日快照DataFrame，列：
        date | nav | shares | cost_amount | market_value | 
        daily_pnl | cumulative_pnl | cumulative_return | xirr
        """
        for day in trading_days(self.start_date, end_date):
            nav = self._get_nav(day)
            # T+1：今天买，明天确认
            if self._is_invest_day(day):
                confirm_day = next_trading_day(day)
                confirm_nav = self._get_nav(confirm_day)
                net_amount = self.amount_per_day / (1 + self.purchase_fee)
                shares = net_amount / confirm_nav
                self.position.buy(confirm_day, shares, confirm_nav, ...)
                self.cashflow.append(...)
            
            # 处理分红（现金分红 or 红利再投资）
            if dividend := self._get_dividend(day):
                self._process_dividend(day, dividend)
            
            # 记录当日快照
            snapshot = self._daily_snapshot(day, nav)
            ...
    
    def check_stop_profit(self, current_date: date) -> dict:
        """检查是否达到止盈条件（盈利收益率法）"""
        index_pe = self._get_index_pe(current_date)
        ep = 1.0 / index_pe * 100
        xirr_rate = self._calc_xirr(current_date)
        return {
            "earnings_yield": ep,
            "signal": "SELL" if ep < 6.4 else "HOLD",
            "xirr": xirr_rate,
            "max_drawdown": self._max_drawdown(),
            "cumulative_return": self._cumulative_return()
        }
五、关键设计决策需要你确认
读完代码后，有几个关键问题需要你来决定：

Q1：数据源优先级
推荐用 akshare（稳定、免费、无爬虫风险）作为主数据源。但akshare有个局限：PE/PB历史分位数据不够完整，需要配合中证指数官网。你接受用akshare吗？还是要自己写爬虫更灵活？

Q2：数据库

方案A：SQLite（轻量，单文件，无需部署，够用）
方案B：PostgreSQL（更强大，支持并发写入，适合后续扩展）
推荐SQLite，个人使用完全够用，后期迁移也容易。你怎么看？
Q3：影子模式的"复刻基金公司计算"
基金公司的计算规则：买入T+1确认净值，赎回T+3到账，申购费率一般场外1折（0.15%），赎回费持有7天内1.5%、7天以上0%。这些规则我会按天天基金实际规则实现。但你目前是场内ETF还是场外基金？ 两者规则有差异（ETF是实时成交价，场外是次日净值）。

Q4：第一阶段功能范围
建议分三期：

P1（核心）：数据拉取+存储 + 影子模式 + 止盈止损判断
P2（策略）：PE/PB估值 + 选基策略 + 多基金对比
P3（增强）：Web界面 + 组合管理 + 报告导出
你觉得这个框架方向对吗？有什么需要调整的？确认后我们就开始写代码。

还需要有模拟持有，假设我选择持有后，可能是一次性建仓，可能是定投，周投月投，然后看收益分析
明白了，把模拟持有单独明确为一个模块，它和影子模式的区别是：

模式	定位	用途
模拟持有	假设从历史某天开始买，回测收益	"如果我这样买，结果会怎样"
影子模式	跟踪真实已持有仓位，计算实时盈亏+止盈止损判断	"我现在买的这笔，该不该卖"
完整功能模块确认

fund_sys/
│
├── data/           # 数据层
│   ├── fetcher/    → akshare拉基金信息、历史净值、指数PE/PB
│   ├── models/     → fund_info / nav_history / index_valuation
│   └── updater     → 增量更新调度
│
├── strategy/       # 策略层
│   ├── indicators  → PE/PB分位、盈利收益率E/P、夏普、最大回撤
│   ├── buy_signal  → 螺丝钉E/P法、博格公式法 买卖信号
│   ├── fund_selector → 从DB多维度筛选基金
│   └── formulas    → XIRR、年化收益率、最大回撤等公式
│
├── simulate/       # 模拟持有（NEW，回测性质）
│   ├── engine.py   → 逐日模拟引擎（支持一次性/日投/周投/月投）
│   ├── snapshot.py → 每日快照（持仓市值/成本/盈亏/收益率）
│   └── report.py   → 收益分析报告（XIRR、最大回撤、夏普、与持有不动对比）
│
├── shadow/         # 影子模式（跟踪真实仓位）
│   ├── position.py → FIFO持仓追踪（精确持有天数 → 赎回费）
│   ├── portfolio.py → 单基金影子账户（T+1确认净值、分红处理）
│   └── checker.py  → 止盈止损判断（E/P信号 + XIRR + 回撤阈值）
│
└── cli/            # 命令行交互
模拟持有的核心逻辑

用户输入：
  - 基金代码（如 510300）
  - 开始日期（如 2023-01-01）
  - 策略：
      ① 一次性建仓：总金额 N 元
      ② 定投：
          - 频率：日投 / 周投（每周X） / 月投（每月X号）
          - 每次金额：M 元
  - 结束日期（默认今天）

系统输出：
  ┌─────────────────────────────────────┐
  │ 模拟持有报告：沪深300ETF 510300     │
  │ 策略：月投 1000元，2023-01-01起     │
  ├─────────────────────────────────────┤
  │ 累计投入：     24,000 元            │
  │ 当前市值：     28,543 元            │
  │ 累计收益：     +4,543 元 (+18.9%)   │
  │ 年化收益(XIRR)：+12.3%             │
  │ 最大回撤：     -15.2%              │
  │ 夏普比率：      0.87               │
  │ 买入持有对比：  -2.1%（定投跑输）   │
  ├─────────────────────────────────────┤
  │ [图表] 每日净值曲线 vs 累计成本线   │
  │ [图表] 每日收益率走势               │
  └─────────────────────────────────────┘
三个问题的我的建议，你确认一下
Q1 数据源：用 akshare，PE/PB历史分位从中证指数官网补充（akshare也有封装）。不用手写爬虫，稳定可靠。→ 建议确认

Q2 数据库：SQLite，够用，零部署成本。→ 建议确认

Q3 场内/场外：模拟和影子模式都支持两种，自动识别代码判断：

510300 这类5开头ETF → 场内，实时价格，佣金约0.03%，无申购赎回费
000300 这类6位纯数字 → 场外，T+1净值确认，申购0.1%（1折后），持有7天以内赎回1.5%
确认方向没问题，我现在开始写代码。先完成 P1 核心功能（数据层 + 模拟持有 + 影子模式基础），能跑通后再加策略层。开始？