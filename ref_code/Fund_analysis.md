# Fund 项目深度分析报告

> 分析对象：`/home/root123/Documents/fund_sys/ref_code/Fund/`
> 项目作者：olixu，License：MIT，约 2020 年 6 月起开发，2021 年 4 月规划重构至 V2.0.0

---

## 1. 项目定位与整体架构

### 定位

这是一个**面向个人散户（"韭菜"）的基金辅助投资工具**，解决三个痛点：

1. 支付宝基金持仓成本明细不清晰、不可汇总分析
2. 缺乏高效的量化筛选基金方法
3. 多基金走势查看繁琐

功能定位分两块：
- **推荐系统**：每日抓取天天基金网数据，按阈值策略筛选出建议申购/赎回的基金，通过 Server酱 推送到微信
- **投资记录系统**：规划中的 Streamlit 可视化 Web 界面，用于记录每笔投资明细并做数据分析

### 版本架构演进

**V1.0.0（已实现）**

```
Fund/
├── fund/
│   ├── funddata.py       # 数据爬取模块（核心）
│   ├── recommend.py      # 推荐策略模块（核心）
│   ├── main.py           # Streamlit Web 入口
│   ├── manifest.yml      # IBM Cloud Foundry 部署配置
│   ├── Procfile          # Heroku 风格启动文件
│   └── fund.bat          # Windows 定时任务脚本
├── database/
│   └── view.sql          # 简单查询示例
└── requirements.txt      # 依赖声明
```

**V2.0.0（规划中，未完全实现）**

```
Fund/
├── fund/
│   ├── common/           # 基础组件（数据库连接、爬虫封装）
│   └── policy/           # 策略模块（量化指标、回测）
├── scripts/              # 回测整合脚本
├── web/                  # 独立 Web 可视化模块
└── database/
```

### 技术栈

| 层次 | 技术 |
|------|------|
| Web UI | Streamlit |
| 数据采集 | requests + lxml + re（正则提取 JSONP） |
| 并发爬取 | `multiprocessing.dummy.Pool`（多线程） |
| 数据存储 | SQLite（两个独立 .db 文件） |
| 数据分析 | pandas + numpy |
| 消息推送 | Server酱 HTTP API（微信公众号） |
| 部署环境 | IBM Cloud Foundry（免费 256MB 内存，1GB 存储） |

---

## 2. 数据来源与获取方式

### 数据源：天天基金网（东方财富）

所有数据均来自 **fund.eastmoney.com** 的公开接口，无需登录，无需 API Key。

### 接口一：所有基金当日净值（排名接口）

文件：`funddata.py`，方法：`get_fund_earning_perday()`

```
GET http://fund.eastmoney.com/data/rankhandler.aspx?op=ph&dt=kf&ft=all&rs=&gs=0&sc=dm&st=asc&sd=2019-05-30&ed=2020-05-30&qdii=&tabSubtype=,,,,,&pi=1&pn=10000&dx=1&v=...
```

- `pi=1&pn=10000`：第1页，每页10000条，一次加载全部基金（约1万只）
- 返回格式：JSONP 包装的 JavaScript 变量 `var rankData = {...}`
- 解析方式：用正则 `re.findall(r"var rankData = (.*?);$", response)[0]` 提取，再按逗号分割字段

每条记录包含字段（按索引顺序）：

| 索引 | 字段名 | 含义 |
|------|--------|------|
| f[0] | code | 基金代码 |
| f[3] | date | 净值日期 |
| f[4] | net_value | 单位净值 |
| f[5] | accumulative_value | 累计净值 |
| f[6] | rate_day | 日涨跌幅（%） |
| f[7] | rate_recent_week | 近一周涨跌幅（%） |
| f[8] | rate_recent_month | 近一月涨跌幅（%） |
| f[9] | rate_recent_3month | 近三月涨跌幅（%） |
| f[10] | rate_recent_6month | 近六月涨跌幅（%） |
| f[11] | rate_recent_year | 近一年涨跌幅（%） |
| f[12] | rate_recent_2year | 近两年涨跌幅（%） |
| f[13] | rate_recent_3year | 近三年涨跌幅（%） |
| f[14] | rate_from_this_year | 今年以来涨跌幅（%） |
| f[15] | rate_from_begin | 成立以来涨跌幅（%） |

### 接口二：单只基金基本信息

文件：`funddata.py`，方法：`fund_info(code)`

```
GET http://fundf10.eastmoney.com/jbgk_{code}.html
```

- 返回 HTML 页面，用 lxml 的 XPath 解析表格
- 提取字段：基金全称、类型、发行日期、成立日期/规模、资产规模、份额规模、管理公司、托管银行、基金经理、利润情况、管理费率、托管费率、业绩比较基准、跟踪标的

### 接口三：单只基金完整历史净值

文件：`funddata.py`，方法：`fund_history(code)`

```
GET http://api.fund.eastmoney.com/f10/lsjz?callback=jQuery...&fundCode={code}&pageIndex=1&pageSize=20000
Referer: http://fundf10.eastmoney.com
```

- `pageSize=20000`：一次性加载最多两万条历史记录（覆盖基金成立至今全部日期）
- 返回 JSONP 格式，用正则 `re.findall(r'\((.*?)\)$', response)[0]` 剥离回调后 JSON 解析
- 历史记录字段：`FSRQ`（日期）、`DWJZ`（单位净值）、`LJJZ`（累计净值）、`JZZZL`（日涨幅）
- 注意：历史接口**只有日期、净值、累计净值、日涨幅**，其他区间涨幅字段存空字符串

### 爬取策略

- **历史数据**（`get_past_data()`）：先调用 `get_fund_earning_perday()` 获取全量基金 code 列表，然后按 100 只为一批，对每批用 `ThreadPool(thread)` 多线程并发爬取详情 + 历史净值，每批写入一次数据库
- **增量更新**（`get_new_data()`）：仅调用 `get_fund_earning_perday(only_code=False)` 更新排名接口返回的当日数据（使用 `insert or replace` 覆盖）
- **失败重试**：`detail()` 方法在 `fund_info()` 或 `fund_history()` 返回 False 时循环 `time.sleep(3)` 重试

---

## 3. 核心数据结构与存储

### 存储方案：两个独立 SQLite 文件

| 文件 | 路径 | 内容 |
|------|------|------|
| `fundinfo.db` | `../database/fundinfo.db` | 基金基本信息，单表 `info` |
| `fundhistory.db` | `../database/fundhistory.db` | 所有基金历史净值，每只基金一张独立表（以基金代码命名） |

### 表一：`info`（`fundinfo.db`）

```sql
create table if not exists info(
    code text primary key,        -- 基金代码（如 001588）
    full_name text,               -- 基金全称
    fund_url text,                -- 天天基金详情页 URL
    tpye text,                    -- 基金类型（注：字段名拼写错误，应为 type）
    publish_date text,            -- 发行日期
    setup_date_and_scale text,    -- 成立日期/规模
    asset_scale text,             -- 资产规模
    amount_scale text,            -- 份额规模
    company text,                 -- 基金管理公司
    company_url text,
    bank text,                    -- 托管银行
    bank_url text,
    manager text,                 -- 基金经理
    manager_url text,
    profit_situation text,        -- 利润情况
    management_feerate text,      -- 管理费率
    trustee_feerate text,         -- 托管费率
    standard_compared text,       -- 业绩比较基准
    followed_target text          -- 跟踪标的
);
```

### 表二：`{code}`（`fundhistory.db`，每只基金一张表）

```sql
create table if not exists "{code}"(
    date text primary key,            -- 净值日期，格式 YYYY-MM-DD
    net_value text,                   -- 单位净值
    accumulative_value text,          -- 累计净值
    rate_day text,                    -- 日涨跌幅（%）
    rate_recent_week text,            -- 近一周涨跌幅
    rate_recent_month text,           -- 近一月涨跌幅
    rate_recent_3month text,          -- 近三月涨跌幅
    rate_recent_6month text,          -- 近六月涨跌幅
    rate_recent_year text,            -- 近一年涨跌幅
    rate_recent_2year text,           -- 近两年涨跌幅
    rate_recent_3year text,           -- 近三年涨跌幅
    rate_from_this_year text,         -- 今年以来涨跌幅
    rate_from_begin text              -- 成立以来涨跌幅
);
```

- **主键**：`date`，配合 `insert or ignore` / `insert or replace` 实现去重与覆盖
- 所有数值字段存储为 `text` 类型，读取时由 pandas 的 `apply(pd.to_numeric, errors='ignore')` 转换
- 历史数据量：作者测试时全量约 400MB+（约1万只基金 × 若干年历史）

### 数据完整性检查

`check_databases()` 方法：检查 `fundhistory.db` 是否存在且文件大小 > 400MB，作为"历史数据完整"的判断依据（阈值较粗糙）。

---

## 4. 推荐/筛选逻辑（选基策略）

### 入口

文件：`recommend.py`，函数：`recom(para1, para2, para3)`

### 数据准备流程

1. 从 `fundhistory.db` 的 `sqlite_master` 中获取所有表名（即所有基金代码）
2. 以**当天日期** `datetime.datetime.now().date()` 为 key，查询每只基金当日的净值记录
3. 将所有记录汇总为 pandas DataFrame，列名为中文

### 三参数筛选策略

```python
record = df[(df['最近一年涨跌幅'] > para1) & (df['最近一年涨跌幅'] < 1000)]
record1 = record[record['最近一周涨跌幅'] < para2]   # 建议申购
record2 = record[record['最近一周涨跌幅'] > para3]   # 建议赎回
```

| 参数 | 默认值 | 含义 |
|------|--------|------|
| `para1` | 50 | 近一年涨幅下限，过滤表现差的基金 |
| `para2` | -5.0 | 近一周跌幅阈值，跌幅超过此值则建议申购（逢跌买入） |
| `para3` | 5.0 | 近一周涨幅阈值，涨幅超过此值则建议赎回（逢涨卖出） |

**筛选逻辑语义**（逢低买入、逢高卖出）：

- **建议申购**：近一年涨幅 > 50%（优质基金）且 近一周涨跌幅 < -5%（近期回调）
- **建议赎回**：近一年涨幅 > 50%（持仓的优质基金）且 近一周涨跌幅 > 5%（近期过热）

### 推送方式

通过 Server酱 HTTP API 将申购/赎回基金代码列表以 Markdown 格式推送到微信：

```python
requests.post(url="https://sc.ftqq.com/{SCKEY}.send", data={'text': '今日基金推荐', 'desp': buy + sell})
```

---

## 5. 策略指标（涨幅等的计算方式）

### 指标来源

**本项目不自行计算涨幅指标**，所有涨幅数据直接来自天天基金网接口：

| 指标 | 数据来源接口 | 计算主体 |
|------|------------|---------|
| 日涨跌幅 | 排名接口 `rate_day` 字段 / 历史接口 `JZZZL` | 天天基金网 |
| 近一周/一月/三月/六月涨跌幅 | 排名接口 | 天天基金网 |
| 近一年/两年/三年涨跌幅 | 排名接口 | 天天基金网 |
| 今年以来/成立以来涨跌幅 | 排名接口 | 天天基金网 |

**项目本身无 PE/PB/夏普比率/最大回撤等指标的计算实现**，这些属于 V2.0.0 的 TODO 项。

### V2.0.0 规划的量化策略优化方向（来自 README TODO）

1. 优化现有基于阈值的量化策略指标
2. 增加"当前值占历史估值的百分位"指标（分位值策略）
3. 增加基金实时估值接口（当日盘中估算）
4. 基于美股/A股历史数据预测未来走势（ML 方向）

### 涨幅计算的隐含公式（天天基金网标准）

虽然代码未自行实现，但接口返回的涨幅字段遵循标准公式：

```
日涨跌幅(%) = (当日单位净值 - 前日单位净值) / 前日单位净值 × 100
区间涨跌幅(%) = (区间末单位净值 - 区间初单位净值) / 区间初单位净值 × 100
```

---

## 6. 定投/回测模式

### 当前版本（V1.0.0）

**无定投和回测功能实现**，V1.0.0 仅有：
- 爬取全量历史净值数据（`get_past_data`）
- 基于当日快照的阈值筛选策略（`recom`）

### V2.0.0 规划

README 明确提到以下规划模块（代码目录结构已设计但未实现）：

```
fund/
├── common/    # 数据库连接、爬虫基础组件
└── policy/    # 策略模块（结合 scripts 进行回测整合）
scripts/       # 回测整合脚本
```

回测模块的设计思路是：利用已存储的完整历史净值数据（从基金成立至今），在 `policy` 模块中编写策略，通过 `scripts` 模块对历史数据运行策略，验证效果。

**但截至代码快照时间，以上模块均未有实现代码存在。**

---

## 7. 关键公式

### 7.1 申购筛选条件

```
满足申购条件 ⟺ 近一年涨跌幅 ∈ (para1, 1000) AND 近一周涨跌幅 < para2
默认数值：近一年涨跌幅 > 50% AND 近一周涨跌幅 < -5%
```

### 7.2 赎回筛选条件

```
满足赎回条件 ⟺ 近一年涨跌幅 ∈ (para1, 1000) AND 近一周涨跌幅 > para3
默认数值：近一年涨跌幅 > 50% AND 近一周涨跌幅 > 5%
```

### 7.3 数据库完整性判断

```
is_complete ⟺ EXISTS(../database/fundhistory.db) AND filesize > 400 MB
```

（来自 `check_databases()`，粗糙但实用的快速检查）

### 7.4 历史数据批量分割

文件：`funddata.py`，方法：`code_split(codes, n=100)`

```python
for i in range(0, len(codes), n):
    yield codes[i:i+n]
```

每批 100 只基金，每批完成后才写入数据库，控制内存占用。

---

## 8. 可借鉴点与局限性

### 可借鉴点

#### 8.1 接口设计简洁可靠
天天基金网 `rankhandler.aspx` 接口一次性返回全量基金当日数据，`pageSize=10000` 的参数设计有效。历史净值接口 `pageSize=20000` 覆盖全量历史，无需分页翻页，极大简化了爬取逻辑。

#### 8.2 两库分离设计
`fundinfo.db`（静态信息）和 `fundhistory.db`（时序数据）分离存储，避免单库膨胀，逻辑清晰。每只基金独立一张表，查询单只基金历史极快。

#### 8.3 多线程批量爬取 + 批量写库
`ThreadPool` + `pool.map_async()` + 批次收集 SQL 语句后统一 `write2sql()` 的模式，减少数据库 I/O 次数，适合一次性全量爬取场景。

#### 8.4 insert or ignore / insert or replace 去重
历史数据用 `insert or ignore`（不覆盖已有），当日数据用 `insert or replace`（覆盖更新），设计合理。

#### 8.5 参数化推荐策略
`recom(para1, para2, para3)` 将策略阈值外置为参数，Streamlit UI 中暴露为 `st.number_input` 可调旋钮，用户无需改代码即可调整策略。

#### 8.6 逢低买入逢高卖出的简洁策略框架
用近一年涨幅做基金质量过滤器，再用近一周涨跌幅做时机判断，逻辑简单直观，适合个人投资者使用。

### 局限性

#### 8.1 指标过于单一，缺乏风险维度
策略仅依赖涨幅阈值，完全没有回撤、波动率、夏普比率、最大回撤等风险指标，可能选出高收益高风险的基金。

#### 8.2 涨幅指标直接取用第三方，无验证
所有区间涨幅均来自天天基金网接口，未做独立计算和校验。若接口数据有误，策略直接失效。

#### 8.3 无 PE/PB 估值分位判断
未实现 TODO 中提到的"当前值占历史估值的百分位"（即常见的宽基指数估值百分位策略），对于指数基金而言这是更稳健的买入时机判断方法。

#### 8.4 数据库表结构有拼写错误
`info` 表中字段名 `tpye` 是 `type` 的拼写错误，后续扩展查询时需注意。

#### 8.5 无回测验证
策略从未经过历史回测，阈值（50%、-5%、5%）纯粹经验设定，缺乏数据支撑。

#### 8.6 推荐结果无排序/评分
筛选结果只是满足条件的基金列表，未按综合评分排序，用户无法区分优先级。

#### 8.7 并发写库存在线程安全问题
`funddata.py` 中 `pool.map_async(self.detail, i)` 多线程并发修改 `self.sql1` 和 `self.sql2` 列表，Python 的 GIL 虽然在一定程度上保护了列表 append，但整体设计并非线程安全（如 `self.sql1=[]` 清空操作），潜在数据丢失风险。

#### 8.8 IBM CF 存储易失
README 注记：IBM Cloud Foundry 重启后数据库会丢失（CF 的 ephemeral filesystem），作者注意到此问题但未解决，生产可靠性存疑。

#### 8.9 当日数据依赖晚间净值更新
`recom()` 以 `datetime.now().date()` 查询当日净值，但天天基金网净值通常在晚 9-10 点后才更新，必须在此之后运行才有意义（fund.bat 也注明建议晚 11-12 点运行）。

#### 8.10 无定投计划和复利计算
完全没有定投模拟、复利收益计算等功能，不能支持定期定额策略评估。
