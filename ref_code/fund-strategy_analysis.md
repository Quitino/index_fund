# fund-strategy 项目深度分析报告

## 1. 项目定位与技术栈

### 项目定位
这是一个基金投资策略回测系统，核心价值是：无需后端数据库，纯前端通过 JSONP 借用天天基金网（eastmoney.com）的公开接口，拉取基金历史净值数据，在浏览器内完整模拟定投过程，可视化展示策略效果。

支持三类策略的组合回测：
- 定投策略（按周/按月定时定额买入）
- 止盈策略（多条件触发卖出）
- 补仓策略（基于 MACD 指标触发加仓）

### 技术栈

| 层次 | 技术 |
|------|------|
| 语言 | TypeScript |
| 框架 | React 16 + UmiJS 2（SPA，hash 路由） |
| 状态管理 | DVA（基于 Redux + React-Router，实际未大量使用 model） |
| UI 组件 | Ant Design 3 |
| 图表 | BizCharts 3（AntV G2 的 React 封装） |
| HTTP | JSONP（`window.getJSONP`，无 CORS 限制），工具脚本用 axios |
| 构建 | UmiJS 内置 Webpack |
| 数据持久化 | localStorage（策略条件、指数历史数据缓存） |

---

## 2. 整体架构

### 目录结构与模块划分

```
src/
├── app.ts                          # DVA 全局错误处理配置
├── layouts/index.tsx               # 全局布局，顶栏导航
├── pages/
│   ├── index.tsx                   # 主页：创建 InvestmentStrategy 对象，触发回测
│   ├── components/
│   │   ├── search-form.tsx         # 主搜索表单，定义 FundFormObj 接口
│   │   ├── stop-profit-form.tsx    # 止盈策略子表单
│   │   ├── buy-stragegy-form.tsx   # 补仓策略子表单
│   │   ├── saved-search.tsx        # 策略条件保存/读取（localStorage）
│   │   ├── fund-line.tsx           # 主图表容器 FundChart
│   │   ├── fund-val.tsx            # 基金收益率走势图 FundValChart
│   │   ├── rate.tsx                # 累计收益趋势图 RateChart
│   │   ├── total-amount.tsx        # 资产增长趋势图 TotalAmountChart
│   │   ├── macd.tsx                # MACD 指标图 MacdLine
│   │   ├── common-line.tsx         # 通用折线图 CommonFundLine
│   │   └── slider-chart.tsx        # 可滑动时间范围图表
│   └── compare/
│       ├── compare.tsx             # 策略对比页主组件
│       ├── compare-chart.tsx       # 策略对比图表组件
│       ├── compare-position.tsx    # 仓位对比柱状图
│       └── search-form.tsx         # 对比页选择表单
└── utils/
    ├── common.ts                   # 工具函数：dateFormat、roundToFix、getJSONP
    ├── color.ts                    # 图表配色
    └── fund-stragegy/
        ├── index.ts                # 核心引擎：InvestmentStrategy、InvestDateSnapshot
        ├── fetch-fund-data.ts      # 数据拉取：基金净值、指数数据、MACD 计算
        └── static/
            ├── shanghai.json       # 上证指数离线备用数据
            └── 景顺长城新兴成长混合260108.json  # 基金离线备用数据

tools/
├── get-fund-data-json.ts           # Node.js 离线数据下载工具（用于生成 static/ 下 json）
├── sz.csv                          # 上证指数历史 csv 原始数据
└── test.csv
```

### 数据流

```
用户填写表单
      ↓
SearchForm.handleSubmit()
      ↓
pages/index.tsx: getFundData()
      ↓  (并行)
┌──────────────────────────────────────────────────────┐
│  getFundData(基金代码)    →  天天基金 JSONP 接口      │
│  getIndexFundData(上证)   →  东方财富 K 线接口         │
│  getIndexFundData(参考指数) →  东方财富 K 线接口       │
└──────────────────────────────────────────────────────┘
      ↓
txnByMacd()  对参考指数数据标记买卖点
      ↓
createInvestStragegy()
  → new InvestmentStrategy({...配置, onEachDay: 止盈补仓逻辑})
  → investment.buy(初始持有金额)
  → investment.fixedInvest({周期配置})   ← 主回测循环
      ↓ (每个交易日)
InvestDateSnapshot 构造 → operate() → buy()/sell()
      ↓
setState({ fundData: investment.data })
      ↓
FundChart 可视化渲染（多个子图）
```

---

## 3. 数据来源与获取方式

### 3.1 基金净值数据

来源文件：`src/utils/fund-stragegy/fetch-fund-data.ts`，函数 `getFundData()`

- 接口：`http://fund.eastmoney.com/pingzhongdata/{fundCode}.js`
- 方式：JSONP，通过动态插入 `<script>` 标签，脚本执行后数据挂载到 `window.Data_netWorthTrend`
- 字段映射：
  - `item.x` → 日期（Unix 时间戳）
  - `item.y` → 单位净值
  - `item.unitMoney` → 分红信息字符串（如 "每份基金分红0.1元" 或 "拆分：每份基金份额折算1.02份"）
- 返回结构 `FundJson`：`{ all: Record<date, FundDataItem>, bonus: Record<date, FundDataItem> }`

### 3.2 指数数据（上证 / 参考指数）

来源：`getIndexFundData()` 函数

- 接口：`//60.push2his.eastmoney.com/api/qt/stock/kline/get?secid={code}&fields2=f51,f52,f53,...&klt=101`
- 响应格式：`"2020-02-06,7386.27,7452.25,7461.18,7302.34,1936321,14723348992.00"`（日期,开,收,高,低,量,额）
- 取字段：`date`（第0位）、`val`（第2位，收盘价）
- 增量缓存：数据存入 `localStorage[secid]`，下次优先用缓存，只请求缺失时段
- 计算完 MACD 后也存入 localStorage

### 3.3 基金/指数搜索接口

- 基金搜索：`getFundInfo(key)` → `https://fundsuggest.eastmoney.com/FundSearch/api/FundSearchAPI.ashx`
- 指数搜索：`searchIndex(input)` → `//searchapi.eastmoney.com/api/suggest/get?type=14`

### 3.4 离线工具脚本

`tools/get-fund-data-json.ts`（Node.js 脚本，用 axios 调用天天基金 REST API）：
- 接口：`http://api.fund.eastmoney.com/f10/lsjz?fundCode={code}&pageIndex=1&pageSize=1000`
- 字段：`FSRQ`（日期）、`DWJZ`（净值）、`FHFCZ`（分红）
- 生成 static/ 下的 json 离线文件

---

## 4. 核心数据结构

### 4.1 FundDataItem（基金单日数据）

```typescript
// fetch-fund-data.ts
interface FundDataItem {
  date: string        // "2021-01-01"
  val: number         // 单位净值
  bonus: number       // 分红/折算值（已解析为数字）
  isBonusPortion?: boolean  // true=份额折算, false=现金分红
}
```

### 4.2 FundJson（基金完整源数据）

```typescript
interface FundJson {
  all: Record<string, FundDataItem>    // 所有交易日净值，key=日期
  bonus: Record<string, FundDataItem>  // 仅分红/折算日，key=日期
}
```

### 4.3 IndexData（指数单日数据，含 MACD 指标）

```typescript
// fetch-fund-data.ts
interface IndexData {
  date: string
  val: number
  ema12: number      // 12日指数移动平均
  ema26: number      // 26日指数移动平均
  diff: number       // DIF = EMA12 - EMA26
  dea: number        // DEA = EMA(DIFF, 9)
  macd: number       // MACD 柱 = 2 * (DIFF - DEA)
  macdPosition: number  // 当前 MACD 柱在本波段内的百分位 [0, 1]
  index?: number     // 在数组中的下标
  txnType?: 'buy'|'sell'  // 被 txnByMacd 标记的交易类型
}
```

### 4.4 InvestmentStrategy（策略主对象）

```typescript
// utils/fund-stragegy/index.ts
class InvestmentStrategy {
  totalAmount: number        // 初始资本（不含已买入基金）
  salary: number             // 每月增量资金
  buyFeeRate: number = 0.0015   // 买入费率 0.15%
  sellFeeRate: number = 0.005   // 卖出费率 0.5%
  fundJson: FundJson         // 基金源数据
  shangZhengData: Record<string, IndexData>  // 上证数据
  indexData: Record<string, IndexData>       // 参考指数数据
  data: InvestDateSnapshot[] // 每日快照数组（回测结果）
  dataMap: Record<string, InvestDateSnapshot>  // 日期到快照的映射
  latestInvestment: InvestDateSnapshot   // 指针，上一个快照（状态传递载体）
  fixedConfig: FixedInvestOption         // 当前定投配置
  onEachDay: Function        // 每日回调（止盈/补仓逻辑注入点）
}
```

### 4.5 InvestDateSnapshot（每日持仓快照）

```typescript
class InvestDateSnapshot {
  date: string              // 当日日期
  cost: number              // 持仓成本单价（含买入费率）
  portion: number           // 持仓份额
  totalBuyAmount: number    // 累计买入金额（含手续费）
  totalSellAmount: number   // 累计卖出到账金额（扣手续费后）
  maxPrincipal: number      // 历史最大持仓成本金额（用于算累计收益率）
  leftAmount: number        // 可用资金余额

  // 计算属性（getter）
  costAmount: number        // 持仓成本金额 = cost * portion
  fundAmount: number        // 持仓市值 = curFund.val * portion
  profit: number            // 持有收益 = (curFund.val - cost) * portion
  profitRate: number        // 持有收益率 = curFund.val / cost - 1
  totalAmount: number       // 总资产 = leftAmount + fundAmount
  accumulatedProfit: number // 累计收益 = fundAmount - totalBuyAmount + totalSellAmount
  totalProfitRate: number   // 累计收益率 = accumulatedProfit / maxPrincipal
  fundGrowthRate: number    // 基金本身涨幅（含分红复投修正）
  
  // 当日操作记录
  dateBuyAmount: number     // 当日买入金额
  dateSellAmount: number    // 当日卖出金额
  curFund: FundDataItem     // 当日基金净值数据
  curBonus: FundDataItem[]  // 区间内所有分红记录
  maxAccumulatedProfit: {date, amount}  // 历史最高累计收益快照
}
```

---

## 5. 策略实现

### 5.1 定投策略

**触发条件**（`shouldFixedInvest()` in `index.ts`）：
- 按月：`new Date(date).getDate() === fixedInvestment.dateOrWeek`（每月 N 号）
- 按周：`new Date(date).getDay() === fixedInvestment.dateOrWeek`（每周星期 N）

**回测主循环**（`fixedInvest()` in `index.ts`）：
```typescript
// 从 range[0] 到 range[1]，每天步进 ONE_DAY
while(curDate <= endTime) {
  if(shouldFixedInvest()) {
    this.buy(fixedInvestment.amount, curDate)   // 定投日买入
  } else {
    this.buy(0, curDate)                         // 非定投日记录快照
  }
  this.onEachDay(curDate)  // 触发止盈/补仓回调
  curDate += ONE_DAY
}
```

**买入计算**（`InvestDateSnapshot.buy()` in `index.ts`）：
```typescript
// 1. 扣除买入手续费，计算净申购金额
netAmount = amount / (1 + buyFeeRate)     // 如: 1000 / 1.0015 ≈ 998.5元
// 2. 计算买入份额
portion = netAmount / curFund.val
// 3. 加权平均成本价
this.cost = (旧成本金额 + amount) / (旧份额 + 新份额)
// 注意：成本 = 含手续费的总投入 / 总份额
```

**工资收入**（`income()` in `index.ts`）：
- 每月 1 号（`salaryDate = 1`），`leftAmount += salary`

### 5.2 止盈策略

止盈逻辑在 `pages/index.tsx` 的 `onEachDay` 回调中，所有条件需同时满足：

```typescript
if(
  level > formData.fundPosition/100        // 条件1：仓位 > 设定值（默认70%）
  && curSzIndex.val > formData.shCompositeIndex  // 条件2：上证指数 > 设定点位（默认3000）
  && (!formData.sellAtTop || latestInvestment.maxAccumulatedProfit.date === latestInvestment.date)  
                                            // 条件3（可选）：累计收益处于历史新高
  && (!formData.sellMacdPoint || curReferIndex.txnType === 'sell')  
                                            // 条件4（可选）：参考指数MACD达到卖出临界点
  && latestInvestment.profitRate > (formData.profitRate/100)  // 条件5：持有收益率 > 设定值（默认5%）
) {
  const sellAmount = sellUnit==='amount' ? sellNum : (sellNum/100 * fundAmount)
  this.sell(sellAmount, dateStr)
}
```

- `level` = `fundAmount / totalAmount`（当前仓位）
- "收益新高"判断：`maxAccumulatedProfit.date === latestInvestment.date`，即今天的累计收益等于历史最大值对应的日期

**卖出计算**（`InvestDateSnapshot.sell()` in `index.ts`）：
```typescript
// 按金额卖出时，转换为份额
portion = txn.amount / curFund.val
// 实际到账金额（扣手续费）
txn.amount = curFund.val * portion * (1 - sellFeeRate)
// 更新持仓
this.portion -= sellTxn.portion
this.leftAmount += sellTxn.amount       // 到账金额加回可用资金
this.totalSellAmount += sellTxn.amount  // 累计到账金额
```

注意：卖出后**持仓成本单价不变**，这与"先进先出"不同，项目只保留整体加权均价。

### 5.3 补仓策略（基于 MACD）

**触发条件**：
```typescript
if(formData.buyMacdPoint && curReferIndex.txnType === 'buy') {
  const buyAmount = buyAmountPercent <= 100 
    ? Math.round(latestInvestment.leftAmount * buyAmountPercent / 100)
    : buyAmountPercent   // >100视为固定金额
  this.buy(buyAmount, dateStr)
}
```

- 补仓金额 = 剩余可用资金 × 补仓百分比（默认20%）

### 5.4 分红/拆分处理

在每日 `operate()` 中处理：
```typescript
if(this.isBonus) {
  if(this.curFund.isBonusPortion) {
    // 份额折算（拆分）：如折算比例1.02，份额*1.02，成本/1.02（净值等比调整）
    this.cost = this.cost / this.curFund.bonus
    this.portion = this.portion * this.curFund.bonus
  } else {
    // 现金分红再投入（红利复投模式）：分红后净值下降，份额增加以保持市值不变
    this.cost = this.cost * curFund.val / (curFund.val + curFund.bonus)
    this.portion = this.portion * (curFund.val + curFund.bonus) / curFund.val
  }
}
```
分红日禁止买卖，仅更新成本和份额。

---

## 6. 影子/回测模式

### 6.1 回测原理

项目采用**完全历史重放**方式。无真实交易，全程只操作内存对象 `InvestmentStrategy`：

1. 时间轴驱动：`fixedInvest()` 按日步进，每天创建一个 `InvestDateSnapshot`
2. 非交易日处理：`getFundByDate()` 递归往前查找最近有效净值，保证每天都有数据
3. 日间状态传递：每个 `InvestDateSnapshot` 在构造时从 `fundStrategy.latestInvestment` 继承上一日的 `cost`、`portion`、`leftAmount` 等，并在 `operate()` 末尾将 `latestInvestment = this`

### 6.2 数据填充机制

`buy()` / `sell()` 方法会自动填充两次调用之间的空白日期：
```typescript
// 如果 buy(date) 与上次 buy 之间有间隔，自动补充中间每天的快照
while(cur > latestInvestDate) {
  this.pushData(this.getSnapshotInstance(latestInvestDate).buy(0))
  latestInvestDate += ONE_DAY
}
```

### 6.3 对比模式

`pages/compare/compare.tsx` 的 `CompareStragegyChart` 通过：
1. 从 localStorage 读取已保存的多套策略条件（`allSavedCondition`）
2. 为每套条件独立创建 `App` 实例，并行执行 `getFundData()`
3. 合并结果，通过 `CompareChart` 在同一图表上叠加多条曲线
4. 额外计算仓位指标：`avgPos`（平均仓位）、`maxPos`（最大仓位）、`profitPerInvest`（收益/平均仓位）

---

## 7. 关键公式

### 7.1 买入成本公式

买入手续费扣除后净申购金额：
```
净申购金额 = 买入金额 / (1 + buyFeeRate)     // buyFeeRate = 0.0015
买入份额 = 净申购金额 / 当日净值
新成本单价 = (旧成本金额 + 本次买入金额含费) / (旧份额 + 新份额)
```

### 7.2 卖出到账公式

```
卖出份额 = 指定金额 / 当日净值
实际到账 = 当日净值 × 卖出份额 × (1 - sellFeeRate)   // sellFeeRate = 0.005
```

### 7.3 持有收益率

```
profitRate = curFund.val / cost - 1
```

### 7.4 持有收益

```
profit = (curFund.val - cost) × portion
```

### 7.5 累计收益

```
accumulatedProfit = fundAmount - totalBuyAmount + totalSellAmount
                  = (当前净值 × 份额) - (累计投入) + (累计卖出到账)
```

### 7.6 累计收益率（最大本金法）

参考自 https://sspai.com/post/53061
```
totalProfitRate = accumulatedProfit / maxPrincipal
```
`maxPrincipal` 是历史上 `costAmount`（持仓成本金额）的最大值，只增不减（卖出不影响），反映"最多时投入了多少本金"。

### 7.7 年化收益率（复利）

```typescript
// annualizedRate getter in InvestmentStrategy
rangeYear = (endDate - startDate) / ONE_DAY / 365
fundGrowth = (1 + endFund.fundGrowthRate)^(1/rangeYear) - 1
totalProfit = (1 + endFund.totalProfitRate)^(1/rangeYear) - 1
```

### 7.8 基金涨幅（含分红修正）

普通情况：
```
fundGrowthRate = (当前净值 - 起始净值) / 起始净值
```

含现金分红修正（累乘分红系数）：
```
fundGrowthRate = (当前净值 / 起始净值) × ∏[(分红点净值 + 分红额) / 分红点净值] - 1
```

含份额折算修正：
```
fundGrowthRate = (当前净值 / 起始净值) × ∏[折算比例] - 1
```

### 7.9 MACD 计算公式

来源：`fetch-fund-data.ts` 中的 `calcMACD()` 和 `EMA()` 函数

```
EMA(n) = (2 × 当日收盘 + (n-1) × 前日EMA(n)) / (n+1)
首日EMA = 首日收盘价

DIF = EMA(12) - EMA(26)
DEA = EMA(DIF, 9)            // 即 EMA9
MACD柱 = 2 × (DIF - DEA)
```

### 7.10 MACD 百分位计算

`calcMacdPosition()` in `fetch-fund-data.ts`：
1. 将 MACD 序列按正负分组（每次穿零为一组）
2. 组内每日 `macdPosition = |当日MACD| / 组内最大|MACD|`
3. 百分位越高，说明该波段能量越充足（接近峰值）

### 7.11 MACD 买卖信号逻辑

`txnByMacd()` in `fetch-fund-data.ts`：
1. 对每个 MACD 波段（正波段=红柱区，负波段=绿柱区）
2. 在波段内寻找峰值后第一个 macd < 峰值 × sellPosition（卖出临界比） 的点
3. 该点标记 `txnType = 'sell'`（正波段）或 `txnType = 'buy'`（负波段）
4. 若波段内未达到临界点，则临界点设为下一波段首日（黄金/死亡交叉时）

---

## 8. 可借鉴的优点与局限性

### 优点

**架构设计层面：**
1. **核心引擎与 UI 完全解耦**：`InvestmentStrategy` 和 `InvestDateSnapshot` 是纯计算逻辑，不依赖 React，可独立测试和复用
2. **策略可注入**：`onEachDay` 回调模式，止盈/补仓逻辑由外部注入，便于扩展新策略
3. **快照链式结构**：每日快照继承上一快照的所有状态，既保留历史轨迹，又支持任意时间点查询

**公式准确性：**
4. **分红处理完整**：分现金和份额折算两种情况都处理了，并正确修正了 `fundGrowthRate`
5. **累计收益率用最大本金法**：比简单用"总投入"更合理，避免了频繁卖出后分母收缩导致收益率虚高的问题
6. **年化收益率用复利公式**：`(1+r)^(1/year) - 1`，标准化便于不同时间段比较
7. **买入费率扣除合理**：模拟了真实申购的净申购金额计算

**工程实践：**
8. **指数数据增量缓存**：localStorage 中保存全量历史指数数据，仅增量拉取，减少重复请求
9. **策略条件保存**：localStorage 持久化策略配置，方便多策略对比
10. **多策略并行回测**：对比页用 `Promise.all` 并行执行各策略回测

### 局限性

**策略层面：**
1. **卖出后成本价不变**：真实场景中卖出高价份额后应更新平均成本，项目直接保持原成本，可能导致后续收益率计算偏差
2. **无滑点模拟**：假设每笔交易均能按当日净值成交，实际上基金是 T+1 确认净值
3. **无最低申购限制**：买入金额可以为任意正数，真实基金有最低申购份额限制
4. **补仓策略只支持 MACD**：未支持基于估值（PE/PB 百分位）、均线等其他常见补仓条件
5. **止盈只支持线性卖出**：无法模拟网格止盈、分级止盈等更复杂策略

**数据层面：**
6. **无分红税处理**：股票型基金分红需缴纳红利税，项目未计入
7. **依赖第三方 JSONP 接口**：天天基金接口未公开，随时可能失效（已在注释里标记过接口调整）
8. **历史净值精度**：`val` 直接取接口返回值（number），未处理浮点精度问题（虽有 `roundToFix` 但不彻底）
9. **无通货膨胀调整**：不同年份的收益率未折算为实际购买力

**工程层面：**
10. **无单元测试**：`__tests__` 目录基本为空，核心 `InvestmentStrategy` 未覆盖测试
11. **MACD 参数硬编码**：EMA 周期 12、26、9 硬编码，不可配置
12. **onEachDay 回调 `this` 绑定问题**：回调用 `this` 但作为普通函数传入，依赖 `pages/index.tsx` 中特殊的 `onEachDay(this: InvestmentStrategy, ...)` 类型标注，实际运行时需要依赖调用上下文正确

---

## 9. 关键文件速查

| 文件 | 核心内容 |
|------|---------|
| `src/utils/fund-stragegy/index.ts` | `InvestmentStrategy`（回测引擎）、`InvestDateSnapshot`（日快照），所有买卖/收益计算公式 |
| `src/utils/fund-stragegy/fetch-fund-data.ts` | 数据拉取、MACD 计算（`calcMACD`、`txnByMacd`）、EMA 公式 |
| `src/pages/index.tsx` | 整体编排：并行拉取数据 → 创建策略 → 触发回测，`onEachDay` 注入止盈/补仓逻辑 |
| `src/pages/components/search-form.tsx` | `FundFormObj` 接口（所有用户输入参数定义）|
| `src/pages/compare/compare.tsx` | 多策略并行回测与对比，`ChartSnapshot` 类型 |
| `tools/get-fund-data-json.ts` | Node.js 离线数据下载工具，字段含义注释最清晰 |
