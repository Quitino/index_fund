# xalpha 基金投资框架深度分析

> 基于源码版本 0.12.3，逐文件精读后整理。

---

## 1. 项目定位与整体框架

### 1.1 定位

xalpha 是一个面向个人投资者的**基金全流程管理框架**，核心能力：
- 基金/指数/个股/外汇/大宗商品历史数据统一获取
- 精确到分的投资账单解析与现金流模拟（支持分红、折算、赎回费分段计算）
- 多基金组合的影子账户（虚拟持仓）管理与净值计算
- 策略生成（定投、网格、技术指标）+ 回测
- QDII/ETF T-0 实时净值预测
- PE/PB 历史估值分析、可转债定价

### 1.2 模块分层

```
xalpha/
├── cons.py          基础工具层：日历、时间、XIRR公式、HTTP重试装饰器
├── exceptions.py    异常定义层
├── provider.py      数据源认证层：聚宽(jqdatasdk)注册、代理设置
│
├── info.py          信息层（核心）：fundinfo/mfundinfo/cashinfo/indexinfo
│   └── 继承 indicator (Mixin)
├── indicator.py     量化指标层：MA/EMA/MACD/RSI/KDJ/Sharpe/Beta 等
├── universal.py     通用数据获取层：get_daily/get_rt/get_bar，20+ 数据源适配
├── realtime.py      实时数据（部分已 deprecated）
├── misc.py          杂项爬虫（可转债状态、集思录等），接口不稳定
│
├── record.py        记账单层：record(场外CSV)/irecord(场内CSV)
├── remain.py        持仓余量追踪层：先进先出的 rem 数据结构
├── trade.py         交易模拟层：trade/itrade，cftable/remtable
├── multiple.py      组合管理层：mul/mulfix/imul
├── evaluate.py      多标的对比分析层
│
├── policy.py        策略生成层：buyandhold/scheduled/grid/indicator_cross 等
├── backtest.py      动态回测框架层：BTE 基类 + 子类继承
├── toolbox.py       高级工具箱：PEBHistory/QDIIPredict/CBCalculator/Compare 等
│
├── caldate.csv      A股交易日历（需每年更新）
└── holiday.json     海外各市场节假日
```

**分层依赖关系**（从下到上）：
```
cons/exceptions/provider
     ↓
remain / indicator
     ↓
info (fundinfo/mfundinfo/cashinfo)  ←  universal (get_daily/get_rt)
     ↓
record
     ↓
trade   →  multiple
     ↓         ↓
  policy     evaluate
     ↓
  backtest / toolbox
```

---

## 2. 数据来源与获取方式

### 2.1 主要数据源

| 数据源 | URL/域名 | 数据内容 | 获取方式 |
|---|---|---|---|
| 天天基金(东方财富) | `fund.eastmoney.com` | 基金历史净值、费率、基本信息 | JS 文件解析 + BeautifulSoup HTML解析 |
| 天天基金(东方财富) | `fundf10.eastmoney.com` | 基金持仓（股票/债券）、报告 | HTML表格解析 |
| 雪球 | `stock.xueqiu.com` / `xueqiu.com` | A/H/美股日K线、实时行情、PE/PB | JSON API（需 cookie token） |
| 英为财情 | `cn.investing.com` | 全球指数/外汇/大宗商品历史数据 | POST 表单请求 |
| 中国货币网 | `chinamoney.com.cn` | 人民币汇率中间价 | POST JSON API |
| 聚宽(jqdatasdk) | SDK 接口 | 指数PE/PB/成分股权重、财务数据 | `jqdatasdk` Python SDK（需认证） |
| 富途 | `futunn.com` | 港/美股历史行情 | JSON API |
| 英国金融时报 | `markets.ft.com` | 海外指数历史数据 | JSON API |
| 标普全球 | `spglobal.com` | 标普系列指数 | Excel 文件下载 |
| 彭博 | `bloomberg.com` | 金融数据（试验性支持，易被封） | JSON API |
| 申万行业研究所 | `hysec.com` | 申万行业指数历史PE/PB | 聚宽 SDK |
| 国证指数 | `cnindex.com.cn` | 国证系列指数 | JSON API |
| 集思录 | `jisilu.cn` | 可转债详情（利率表、评级、转股价） | HTML BeautifulSoup解析 |
| 易盛商品 | `esunny.com.cn` | 商品指数 | CSV 下载 |
| 中港互认基金 | `overseas.1234567.com.cn` | 港股互认基金净值、分红 | JSON API |

### 2.2 统一获取接口 (`universal.py`)

核心函数 `get_daily(code, start, end, prev)` 实现了一套**代码前缀路由**机制：

```python
# 代码前缀路由逻辑（get_daily 内部 codedict 映射）
"SH"/"SZ"  → get_historical_fromxq()        # 雪球沪深股
"HK"       → get_historical_fromxq()        # 雪球港股
"F"        → get_fund()                     # 天天基金（场外基金净值）
"T"        → get_fund() 取 totvalue        # 场外基金累计净值
"M"        → mfundinfo().price              # 货币基金
"indices/" → get_historical_fromcninvesting() # 英为全球指数
"currencies/" → get_historical_fromcninvesting() # 英为外汇
"commodities/" → get_historical_fromcninvesting() # 英为大宗
"USD/CNY"等 → get_rmb()                    # 中国货币网人民币中间价
"peb-"     → 聚宽 get_peb_range()          # PE/PB 历史
"sw-"      → 聚宽申万行业PE/PB数据
"teb-"     → 聚宽指数总盈利总净资产
"pt-"      → 天天基金资产配置比例
```

### 2.3 数据存储方式

支持两种后端，通过 `xa.set_backend()` 配置：
- **CSV 文件**：每个基金一个 `.csv` 文件，文件首行存储 JSON 元信息（费率、赎回费分段等），第2行起为日期净值表
- **SQL 数据库**：通过 SQLAlchemy，表名为 `xa{代码}`，逻辑同上
- **内存缓存**：`lru_cache` 和 `lru_cache_time` 装饰器对高频调用缓存（如 `get_token`、`get_industry_fromxq`）

增量更新逻辑在 `fundinfo.update()` 中实现：比较已存储的最后日期和今日，按差量天数分页请求天天基金 API，避免全量重拉。

---

## 3. 核心数据结构

### 3.1 info 层（`info.py`）

#### `basicinfo`（抽象基类）
继承 `indicator` Mixin。核心属性：
- `self.price`：`pd.DataFrame`，列为 `date | netvalue | totvalue | comment`
  - `netvalue`：单位净值
  - `totvalue`：累计净值
  - `comment`：正数为分红金额（元/份），负数为折算系数（如 -1.5 表示折算为 1.5 倍）
- `self.rate`：申购费率（百分比，如 1.5 表示 1.5%）
- `self.feeinfo`：赎回费分段描述列表，如 `["小于7天","1.50%","大于等于7天","0.00%"]`
- `self.segment`：赎回费数值分段，如 `[[0,7],[7]]`

#### `fundinfo`（场外基金）
在 `basicinfo` 基础上增加：
- `self.segment` / `self.feeinfo`：通过 `_piecewise()` 解析赎回费HTML为数值分段
- `self.purchase_status`：申购状态（正常/暂停/限大额）
- `self.specialdate`：分红/折算日列表
- `self.fenhongdate` / `self.zhesuandate`：分别记录分红和折算日期

核心方法：
- `shengou(value, date, fee=None)` → `(实际确认日, -申购金额, 获得份额)`：模拟申购，考虑申购费和净值
- `shuhui(share, date, rem, fee=None)` → `(实际确认日, 赎回金额, -赎回份额)`：模拟赎回，根据持仓时间 `rem` 逐批计算赎回费
- `feedecision(day)` → 赎回费率（%）：按持有天数查分段赎回费

申购份额计算（`_shengoucal`）：
```
净申购金额 = round(申购金额 / (1 + 申购费率/100))
申购份额   = round(净申购金额 / 当日净值)
```

#### `mfundinfo`（货币基金）
将万份收益率累乘转为拟净值序列，`price.netvalue` 从 1 开始递增。

#### `cashinfo`（虚拟现金）
用于 `mulfix` 中平衡进出资金。以恒定日利率（默认 0.0001，约 3.65% 年化）复利构造净值序列。

### 3.2 remain 层（`remain.py`）

`rem` 是一个 `[[date, shares], ...]` 的嵌套列表，记录**各批次买入的剩余份额**（FIFO 先进先出）。

- `buy(rem, share, date)` → 新 rem：追加新买入批次，同一天合并
- `sell(rem, share, date)` → `(soldrem, newrem)`：从最早买入批次开始扣减
- `trans(rem, coef, date)` → 新 rem：基金折算时按系数调整各批次份额

**作用**：精确计算赎回费（每批次持有天数不同），实现 FIFO 赎回逻辑。

### 3.3 trade 层（`trade.py`）

#### `trade`（场外交易）
核心数据结构：
- `self.cftable`：现金流量表，`date | cash | share`
  - `cash` 负值=买入现金流出，正值=卖出/分红现金流入
  - `share` 正值=份额增加（买入/分红再投），负值=份额减少（卖出/折算）
- `self.remtable`：每次变更后的余量表，`date | rem`（rem 同 remain.py 结构）

`_arrange()` → `_addrow()` 循环调用：驱动账单 `status` 逐行转化为 cftable/remtable。特殊处理：
- 申购：调用 `aim.shengou()` 计算实际份额
- 赎回：调用 `aim.shuhui()` 结合 rem 计算赎回费
- 分红：按 `comment` 列值和 `dividend_label` 决定现金分红或再投份额
- 折算：按 `comment` 负值调整份额和 rem

#### `itrade`（场内交易）
不依赖 `fundinfo`，直接读取价格，`cftable` 直接由账单记录的成交价和份额计算。

### 3.4 record 层（`record.py`）

#### `record`（场外记账单）
读取 CSV 格式账单（matrix 或 list 两种格式），生成 `self.status`：
- matrix 格式：行=日期，列=基金代码，值=申购金额（正）/赎回份额（负）
- 编码约定（精妙设计）：
  - 小数第二位为 5 且当日为分红日 → 标记分红再投
  - 绝对值在 (0, 0.005] 的负数 → 表示按比例赎回（0.005=全部赎回）
  - 小数第三位为 5 → 自定义申购费/赎回费标记，之后数字为费率

#### `irecord`（场内记账单）
五列格式：`date | code | value | share | fee`，直接记录实际成交价、份额、手续费。

### 3.5 multiple 层（`multiple.py`）

#### `mul`（多基金组合）
- `fundtradeobj`：trade 对象元组
- `totcftable`：汇总所有基金的总现金流量表
- 核心方法：`combsummary(date)` 输出各基金当日汇总报表
- `get_stock_holdings()` 穿透持仓：根据季报持仓比例计算组合底层等效股票

#### `mulfix`（封闭式组合，净值计算用）
在 `mul` 基础上引入 `cashinfo` 平衡资金，使总现金流量表仅有初始投入一行，从而可计算整体净值曲线，进而使用 `indicator` Mixin 的所有量化指标。

---

## 4. 策略相关（`policy.py`）

所有策略类继承 `policy`，核心机制：遍历 `[start, end]` 日期，每天调用 `status_gen(date)` 生成交易信号（正数=买入金额，负数=卖出比例），最终汇成 `self.status` 传给 `mul` 进行回测。

### 4.1 内置策略

| 类名 | 策略逻辑 | 关键参数 |
|---|---|---|
| `buyandhold` | 起始日全仓买入，持有到底 | - |
| `scheduled` | 固定日期定额买入 | `times`（日期列表），`totmoney` |
| `scheduled_tune` | 定期不定额：按净值分段调整买入金额 | `piece=[(净值上限,倍数),...]` |
| `scheduled_window` | 滑动窗口定投：比较当前与窗口均值，跌越多买越多 | `window`, `piece`, `method` |
| `grid` | 网格策略：按跌幅分批建仓，按涨幅分批卖出 | `buypercent`, `sellpercent` |
| `indicator_cross` | 双均线（或任意两指标）交叉买入/卖出 | `col=('netvalue','MA10')` |
| `indicator_points` | 多阈值分段建仓/卖出 | `col`, `buy`, `sell` 阈值列表 |

**网格策略 `grid.status_gen` 细节**：
- 买点：价格从上跌穿 `buypts[i]` 且当前仓位 <= i → 买入 `totmoney/division`
- 卖点：价格从下穿 `sellpts[j]` 且仓位 > j → 卖出 `-1/pos` 比例（按份额均分）
- 卖出以份额为基准（而非金额），所以每次卖出份额略少于对应买入，实现更多收益

**`scheduled_window` 计算逻辑**：
```python
base_value = AVG/MAX/MIN(window 内的净值)
change_pct = (当前净值 - base_value) / base_value * 100
# 按 piece 阈值决定买入倍数
```

### 4.2 动态回测框架（`backtest.py`）

`BTE`（BackTestEnvironment）提供面向对象的策略编写方式：
```python
class MyStrategy(BTE):
    def prepare(self):
        # 初始化变量
        pass
    def run(self, date):
        # 每个交易日调用
        if some_condition(date):
            self.buy("F100032", 1000, date)
        elif other_condition(date):
            self.sell("F100032", 100, date)
```
- `self.buy(code, value, date)` / `self.sell(code, share, date)`：动态追加交易记录并重新计算 cftable
- `get_current_mul()` / `get_current_mulfix()` → 获取当前组合的 mul/mulfix 对象进行分析
- `backtest()` 循环 `pd.bdate_range()` 内所有国内交易日执行 `run()`

---

## 5. 影子/回测模式

### 5.1 影子持仓模拟（核心机制）

xalpha 最核心的设计是**精确的影子账户**：给定历史账单 CSV，完全按照真实基金规则（申购费、赎回费分段、分红处理、份额折算）重算每一笔现金流，确保与实盘完全对应。

`trade._addrow()` 内部逻辑：
1. 读取 `status` 中下一个有交易记录的日期
2. 若该日在 `price` 表中无净值（非开市日），顺延到下一开市日
3. 遇到分红日（`fenhongdate`）：根据 `dividend_label` 和账单标记，决定现金分红或份额再投
4. 遇到折算日（`zhesuandate`）：调用 `remain.trans()` 按折算系数放大每批次份额
5. 记录新 `[date, cash, share]` 行到 `cftable`，记录新 `[date, rem]` 到 `remtable`

### 5.2 收益计算

`trade.dailyreport(date)` 计算：
```python
totinput  = -sum(cash < 0)   # 总申购金额
totoutput = +sum(cash > 0)   # 分红+赎回现金
currentshare = sum(share)    # 当前持仓份额
currentcash  = currentshare * 当日净值
unitcost = (totinput - totoutput) / currentshare  # 持仓均价
ereturn  = currentcash + totoutput - totinput     # 总收益额
returnrate = ereturn / bottleneck(cftable) * 100  # 简单收益率
```

其中 `bottleneck(cftable)` = 历史累计现金流的最大净流出值（历史最大占用资金），比总申购金额更准确地反映资金使用峰值。

### 5.3 mulfix 净值曲线生成

`mulfix.unitvalue(date)` = 各基金当日总值 / `totmoney`，每天计算一次，即可得到完整净值曲线，之后可套用 `indicator` 所有量化指标（Sharpe、最大回撤、Beta 等）。

---

## 6. 关键公式

### 6.1 XIRR（不规则时间间隔内部收益率）

定义在 `cons.py`：

```python
def xnpv(rate, cashflows):
    # cashflows: [(date, amount), ...]，流出为负，流入为正
    t0 = min(date)
    NPV = sum(cf / (1 + rate) ** ((t - t0).days / 365.0)
              for (t, cf) in cashflows)
    return NPV

def xirr(cashflows, guess=0.1):
    # 用牛顿法求解 xnpv(r, cf) = 0
    return scipy.optimize.newton(lambda r: xnpv(r, cashflows), guess)
```

使用位置：`trade.xirrrate(date)` → `xirrcal(cftable, trades, date)`：
1. 提取 `cftable` 中的历史现金流 `(date, cash)` 列表
2. 追加一笔虚拟清仓：`(date, 当日持仓市值)` 作为正流入
3. 求解 XIRR，即年化内部收益率

### 6.2 申购份额计算

```python
def _shengoucal(sg, sgf, value, label):
    jsg = round(sg / (1 + sgf/100))      # 扣申购费后净申购金额
    share = round(jsg / value, label)    # label=1 四舍五入，label=2 截尾
    return (jsg, share)
```

### 6.3 赎回金额计算（FIFO + 分段赎回费）

```python
# fundinfo.shuhui 内部
soldrem, _ = rm.sell(rem, share, date)    # FIFO 切出本次卖出的各批次
for d, s in soldrem:
    holding_days = (row.date - d).days
    fee = feedecision(holding_days) / 100  # 查分段赎回费率
    value += round(s * row.netvalue * (1 - fee))
```

### 6.4 波动率（年化）

```python
# indicator.py
volatility = std(daily_returns) * sqrt(250)   # 250 个交易日
```

### 6.5 Sharpe 比率

```python
sharpe = (total_annualized_return - riskfree) / algorithm_volatility
# riskfree 默认 0.0371724（≈3.72% 年化，对应 cashinfo 默认日利率）
```

### 6.6 Beta / Alpha

```python
beta  = Cov(fund_daily_ret, benchmark_daily_ret) / Var(benchmark_daily_ret)
alpha = rp - (riskfree + beta * (rm - riskfree))   # Jensen's Alpha
```

### 6.7 货币基金净值序列

```python
# mfundinfo._basic_init
netvalue[0] = 1
for daily_rate_per_10000 in ratel:
    netvalue.append(netvalue[-1] * (1 + daily_rate * 1e-4))
```

### 6.8 可转债定价（`toolbox.py`）

**债券价值**（`cb_bond_value`）：
```python
# 将未来各期利息和到期赎回金额折现
NPV = xnpv(bond_discount_rate, future_cashflows)
```

**期权价值**（`BlackScholes`）：
```python
d1 = (ln(S/K) + (r + v²/2)*t) / (v*sqrt(t))
d2 = d1 - v*sqrt(t)
call_option = S*N(d1) - K*e^(-r*t)*N(d2)
# 最终转股期权价值 = call_option * 100 / zgj（转股价）
```

**总价值** = 债券价值 + 期权价值

### 6.9 QDII 净值预测（`toolbox.py`）

T-1 净值预测（`QDIIPredict.get_t1`）：
```python
t1_delta = 1 + evaluate_fluctuation(hdict, yesterday)
# evaluate_fluctuation: 遍历 hdict（持仓标的+权重），每个标的取昨日涨跌幅
# 汇率转换：各标的涨跌幅 * 当日 CNY 汇率变化
t1_value = t2_value * t1_delta
```

T-0 实时净值预测（`QDIIPredict.get_t0`）：
```python
for code, weight in t0dict.items():
    c = weight/100 * get_rt(code)["current"] / lastclose
    if currency_code:
        c *= daily_currency_change
    n += c
t0_value = t1_value * n
```

---

## 7. 可借鉴的优点与局限性

### 7.1 可借鉴的优点

**1. 精确的现金流建模**
`record → trade → cftable/remtable` 这套设计非常精妙：用 CSV 账单驱动整个模拟引擎，一次性处理申购费、赎回费、分红（现金/再投）、折算等所有基金特殊事件。这是其他同类工具极少做到的细节精度。

**2. 先进先出的 rem 数据结构**（`remain.py`）
仅用一个嵌套列表加三个函数（`buy/sell/trans`），干净地实现了 FIFO 持仓追踪，使赎回费按持有天数精准计算成为可能。这一模块内聚性强，可独立移植。

**3. 统一的通用数据获取接口**（`universal.py` 的 `get_daily`/`get_rt`）
通过代码前缀路由+多数据源备用的设计，实现了"一行拿到任意金融产品历史数据"的目标。`lru_cache_time` 装饰器实现 TTL 缓存，兼顾性能与数据新鲜度。

**4. 增量 IO 设计**（`basicinfo.update()`）
读缓存 → 计算增量天数 → 只请求增量数据 → 追加写入，避免反复全量拉取，极大提升了效率，在个人项目中值得借鉴。

**5. 账单编码设计的巧妙性**
在 `record.py` 中，用同一个数字的小数位编码不同含义（第二位 5=分红再投标记，第三位 5=自定义费率），极大压缩了 CSV 账单的复杂度，同时保持向后兼容。

**6. policy 和 BTE 的策略框架设计**
`policy` 用 `status_gen(date)` 单日决策接口抽象了所有策略，`BTE` 通过子类化提供更灵活的动态回测，两者的设计都遵循"开闭原则"，易于扩展新策略。

**7. `mulfix` 封闭系统设计**
引入 `cashinfo` 作为现金账户，将开放系统（资金任意进出）转化为封闭系统，使得净值计算和风险指标计算成为可能，是一个聪明的工程设计。

### 7.2 局限性

**1. 数据源极度依赖爬虫，极度不稳定**
几乎所有数据源都是逆向的第三方爬虫（英为、雪球、天天基金等），任何网站改版都会导致解析失败。项目历史上已出现多次数据源崩溃的情况（`indexinfo` 的 163 数据源已废弃，`get_ri_status` 的 richvest 已改版），README 中也承认集思录的 QDII 功能已"合规原因下架"。

**2. 交易日历需手动更新**
`caldate.csv` 需要每年更新（`cons.py` 的 `calendar_selfcheck` 有警告提醒），但无自动更新机制，连网更新因 GitHub 访问问题在国内无法工作。

**3. 无法精确支持按金额赎回的净值型基金**
`value_label=1`（按金额赎回）在注释中明确说明"只能完美支持货币基金"，净值型基金由于买入价和赎回价不同，金额赎回时份额存在误差。

**4. QDII 基金处理的复杂性**
QDII 基金净值更新存在 T+1 或 T+2 的延迟，`fundinfo` 注释中提醒"默认昨日的函数可能出现问题"。QDII 预测本身依赖外部持仓配置文件（`holdings.py`），需要用户手动维护，不自动更新。

**5. 同日多笔交易无法精确处理**
`_addrow` 中注释明确："多笔买入只能在 csv 上合并记录，由此可能引起份额计算 0.01 的误差"，"同一日既有卖也有买不现实"，这是架构层面的限制。

**6. 性能问题**
`mulfix._pricegenerate()` 需要对每个交易日调用 `unitvalue(date)`，对于时间跨度长的组合，初始化会非常慢（O(N) 次全量查询）。`v_positions_history` 同样对所有日期全量计算，无法实时响应。

**7. 可视化依赖特定版本的 pyecharts**
`requirements.txt` 中 `pyecharts==1.7.1` 固定版本，与新版本可能不兼容，限制了可视化的可维护性。

**8. 海外基金（FOF、QDII持仓穿透）支持不完整**
`get_fund_holdings` 注释："天天基金无法自动处理海外基金持仓，暂未兼容 FOF 的国内基金持仓"，组合穿透对 QDII 和 FOF 基金仓位无法准确展示。

**9. `rem` 数据结构脆弱**
`trade.py` 中注释："the design on data remtable is disaster, it is very dangerous"，rem 的嵌套列表结构在某些边界情况（如节假日申购顺延恰好到折算日）下可能产生未预期的行为。

---

## 附：关键函数速查

| 功能 | 文件 | 函数/类 |
|---|---|---|
| 获取基金历史净值 | `info.py` | `fundinfo.__init__` → `_basic_init` |
| 增量更新净值 | `info.py` | `fundinfo.update()` |
| 获取基金持仓明细 | `info.py` | `get_fund_holdings(code, year, season)` |
| 通用历史行情获取 | `universal.py` | `get_daily(code, start, end)` |
| 实时行情获取 | `universal.py` | `get_rt(code)` |
| 解析账单 CSV | `record.py` | `record(path)` / `irecord(path)` |
| 模拟单基金交易 | `trade.py` | `trade(infoobj, status)` |
| 多基金组合管理 | `multiple.py` | `mul(status=record_obj)` |
| XIRR 计算 | `cons.py` / `trade.py` | `xirr(cashflows)` / `trade.xirrrate(date)` |
| PE/PB 历史估值 | `toolbox.py` | `PEBHistory(code)` |
| QDII 净值预测 | `toolbox.py` | `QDIIPredict(code, positions=True)` |
| 定投策略生成 | `policy.py` | `scheduled(infoobj, totmoney, times)` |
| 网格策略回测 | `policy.py` | `grid(infoobj, buypercent, sellpercent, ...)` |
| 动态回测框架 | `backtest.py` | `BTE` 子类化 |
| 可转债定价 | `toolbox.py` | `CBCalculator(code).analyse()` |
| 量化指标 | `indicator.py` | `indicator.sharpe()`, `.max_drawdown()`, `.beta()` 等 |
| 余量持仓追踪 | `remain.py` | `buy/sell/trans` |
