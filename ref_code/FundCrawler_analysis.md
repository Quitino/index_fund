# FundCrawler 项目深度分析

> 分析日期：2026-06-05
> 项目路径：`/home/root123/Documents/fund_sys/ref_code/FundCrawler/`

---

## 1. 项目定位与整体架构

### 定位

FundCrawler 是一个面向中国公募基金市场的全量数据爬虫，目标是抓取天天基金网（EastMoney）和晨星中国（Morningstar CN）两个平台的基金数据，覆盖约 **21,000 只开放式基金**（含暂停申购/认购中，排除货币基金和场内 ETF），完整爬取约需 **30 分钟**。输出为单个 CSV 文件，供后续量化筛选脚本 `result_analyse.py` 消费。

### 目录结构

```
FundCrawler/
├── run.py                      # 入口：触发全量爬取
├── test_run.py                 # 冒烟测试：爬 500 只
├── result_analyse.py           # 结果分析脚本（选基逻辑）
├── crawler/
│   ├── engine.py               # 核心调度引擎（依赖图 + 并发控制）
│   ├── fetcher.py              # HTTP 客户端 + AIMD 自适应限流
│   ├── fund_context.py         # 数据载体 dataclass（21 个字段）
│   ├── target_loader.py        # 基金列表加载器（多种实现）
│   ├── writer.py               # 异步 CSV 写入器
│   └── parsers/
│       ├── __init__.py         # STEPS 声明式依赖图
│       ├── eastmoney.py        # 天天基金网解析（HTML 正则）
│       └── morningstar.py      # 晨星中国解析（JSON）
├── utils/
│   ├── constants.py            # 枚举、哨兵字符串、正则常量
│   ├── fake_ua_getter.py       # UA 池随机轮换
│   └── top_k_holder.py         # 堆结构，分析脚本 Top-K 筛选用
└── tests/
    ├── case/                   # 真实 HTTP 响应快照（无网络单测）
    └── test_*.py               # 各模块单元测试
```

### 整体架构（数据流）

```
WebTargetLoader
  └─ 天天基金净值列表接口（全量基金代码）
        │
        ▼
Engine（20 并发流水线槽位）
  ├─ Phase 1（asyncio.gather 并行）
  │    ├─ overview   → EastMoney HTML → 类型/规模/净值/公司/费率
  │    ├─ manager    → EastMoney HTML → 基金经理/任职日期
  │    └─ morningstar→ MS JSON → 晨星基金 ID（后续阶段依赖此 ID）
  │
  └─ Phase 2（morningstar 完成后触发）
       ├─ return     → MS JSON → 五/十年年化回报
       └─ risk       → MS JSON → 标准差/夏普/阿尔法/贝塔/R²
              │
              ▼
        ResultWriter → result/result.csv
```

依赖关系在 `crawler/parsers/__init__.py` 的 `STEPS` 列表中声明，`engine.py` 的 `_crawl_one()` 函数通过 `deps` 字段自动推断执行阶段，无需手写 Phase 数量。

---

## 2. 数据来源

### 来源一：天天基金网（EastMoney）

**A. 基金列表接口**

```
GET http://fund.eastmoney.com/Data/Fund_JJJZ_Data.aspx?page=1,&onlySale=0
```

- 实现文件：`crawler/target_loader.py` 的 `WebTargetLoader`
- 响应格式：自定义文本（含 JS 变量），用正则 `"[0-9]{6}",".+?"` 提取基金代码和简称
- `onlySale=0` 表示包含暂停申购的基金
- 测试用批量接口：`page=1,{limit}` 可指定返回条数

**B. 基金概况页（overview）**

```
GET http://fundf10.eastmoney.com/jbgk_{fund_code}.html
```

- 实现文件：`crawler/parsers/eastmoney.py` 的 `build_overview_url()` / `parse_overview()`
- 返回 HTML，通过正则从表格 `<th>...<td>` 结构提取字段

**C. 基金经理页（manager）**

```
GET http://fundf10.eastmoney.com/jjjl_{fund_code}.html
```

- 实现文件：`crawler/parsers/eastmoney.py` 的 `build_manager_url()` / `parse_manager()`
- 返回 HTML，提取"现任基金经理简介"段落

### 来源二：晨星中国（Morningstar CN）

晨星接口坐落在 **CloudFront WAF** 之后，缺少 `Accept` / `Accept-Language` 请求头会返回 403 或超时，是本项目反爬绕过的核心难点。

**A. 基金搜索接口（morningstar）**

```
GET https://www.morningstar.cn/handler/fundsearch.ashx?q={fund_code}&limit=1
```

- 实现文件：`crawler/parsers/morningstar.py` 的 `build_morningstar_url()` / `parse_morningstar()`
- 返回 JSON 数组，取第一个元素的 `FundClassId` 字段（如 `0P00011NK0`）
- 此 ID 是 Phase 2 两个接口的必需参数

示例响应（`tests/case/MORNINGSTAR.json`）：
```json
[
  {
    "FundClassId": "0P00011NK0",
    "Symbol": "000457",
    "FundName": "摩根核心成长股票A",
    "ShortFundName": "",
    "CategoryId": "qdii"
  }
]
```

**B. 基金回报接口（return）**

```
GET https://www.morningstar.cn/handler/quicktake.ashx?command=return&fcid={morningstar_fund_id}
```

- 实现文件：`crawler/parsers/morningstar.py` 的 `build_return_url()` / `parse_return()`
- 返回 JSON，结构为 `CurrentReturn.Return[]`，按 `Name` 字段匹配
- 仅提取 `"五年回报（年化）"` 和 `"十年回报（年化）"` 两项（其余项如一月/三月/一年等被忽略）

**C. 风险评估接口（risk）**

```
GET https://www.morningstar.cn/handler/quicktake.ashx?command=rating&fcid={morningstar_fund_id}
```

- 实现文件：`crawler/parsers/morningstar.py` 的 `build_risk_url()` / `parse_risk()`
- 返回 JSON，包含两个数组：
  - `RiskAssessment[]`：标准差（%）、夏普比率（按 `Year5`/`Year10`）
  - `RiskStats[]`：阿尔法系数（%）、贝塔系数、R平方（按 `ToInd`，即相对于基准指数）
- 若接口返回字面量 `"null"` 或 Python `None`，统一用 `NO_DATA` 填充所有风险字段

---

## 3. 数据存储方式

### 输出文件

- 路径：`result/result.csv`（目录不存在时自动创建）
- 格式：UTF-8 编码 CSV，带表头行
- 实现：`crawler/writer.py` 的 `ResultWriter` 类

### 并发安全写入

`ResultWriter` 使用 `asyncio.Lock` 保护 CSV 文件句柄，所有 `await writer.write(ctx)` 调用序列化执行，避免行交错。文件在第一次写入时懒初始化（`_ensure_open()`），程序退出前调用 `await writer.close()` 显式 flush 和关闭。

### 哨兵字符串机制

CSV 中空值不用空字符串，而用三类哨兵区分语义：

| 哨兵值 | 含义 |
|--------|------|
| `NO_DATA` | 数据源明确返回无数据（如费率显示 `---`） |
| `DATA_ERROR` | 爬取失败或字段从未被赋值（`getattr` 返回 `None`） |
| `DATA_IGNORE` | 数据源存在但本项目忽略（如管理费率链接跳转场景 `<a`） |

分析脚本 `result_analyse.py` 通过 `_SKIP = {"NO_DATA", "DATA_ERROR", "DATA_IGNORE"}` 统一过滤。

### 断点续传

`RetryTargetLoader`（`crawler/target_loader.py`）在 `result/result.csv` 存在时，读取已完成的基金代码并从待爬列表中剔除，支持中断后继续爬取。

---

## 4. 爬虫实现细节

### 请求方式

- 全异步：Python 3.14 + `asyncio` + `aiohttp`
- 全局连接池：`aiohttp.TCPConnector(limit=0, limit_per_host=50)`，无全局上限，每域名最多 50 连接
- 所有请求 GET 方式，无 POST 或 Cookie 依赖

### 反爬策略

**1. UA 随机轮换（`utils/fake_ua_getter.py`）**

`FakeUA` 类维护 17 条真实浏览器 UA 字符串（Chrome/Firefox/Edge/Safari/Opera，Windows/macOS），每次请求通过 `singleton_fake_ua.get_random_ua()` 随机选取一条注入 `User-Agent` 请求头。

**2. 完整浏览器请求头（`crawler/fetcher.py` 的 `_BASE_HEADERS`）**

晨星接口由 CloudFront WAF 校验，缺少以下任意头部将被拒绝（403 或连接超时）：
```python
{
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}
```

**3. AIMD 自适应并发限流（`crawler/fetcher.py` 的 `RateController`）**

每个目标域名配置独立的 `RateController` 实例：

| 实例 | 初始并发 | 最小并发 | 调整窗口 | 超时 | 重试次数 |
|------|---------|---------|---------|------|---------|
| `_eastmoney` | 20 | 1 | 0.5s | 10s | 3 |
| `_ms_search` | 3 | 1 | 1.0s | 8s | 2 |
| `_ms_quicktake` | 5 | 3 | 1.0s | 12s | 2 |

AIMD 规则（每调整窗口执行一次 `_adjust()`）：
- 失败率 ≥ 20%：`cur_rate × 0.75`（乘法减，快速降速）
- 失败率 < 20% 且有流量：`cur_rate + 1`（加法增，缓慢扩容）
- 无流量：保持不变

`phase` 参数决定使用哪个晨星限流器：Phase 1（morningstar 搜索）用 `_ms_search`，Phase 2（quicktake return/risk）用 `_ms_quicktake`（因接口更慢，初始并发设为 5）。

**4. 指数退避重试**

重试间隔 = `1.5 ** attempt` 秒（第 1 次重试等 1s，第 2 次 1.5s，第 3 次 2.25s）。速率记录只在**最终结果**上调用 `rc.record()`，避免重试中间失败被误计入失败统计，防止不必要的降速。

### 解析逻辑

**天天基金（HTML 正则解析，`crawler/parsers/eastmoney.py`）**

不使用 BeautifulSoup，直接用 `re.compile` 匹配 HTML 片段：

- `_fund_type_re`：匹配 `基金类型</th><td>...</td></tr>` 之间的内容
- `_fund_size_re`：匹配 `资产规模` 字段，支持 `---`（NO_DATA）和带千分号数字（如 `1,234.56` 亿）
- `_fund_value_re`：匹配 `单位净值：` 后的数字
- `_management_fee_re`：特殊处理 `<a` 开头场景（DATA_IGNORE，表示费率通过链接另行说明）

**晨星中国（JSON 解析，`crawler/parsers/morningstar.py`）**

直接 `json.loads()` 后按字段名取值：
- `parse_morningstar`：取 `data[0]['FundClassId']`
- `parse_return`：遍历 `CurrentReturn.Return[]`，按 `Name` 字段精确匹配 `"五年回报（年化）"` 和 `"十年回报（年化）"`
- `parse_risk`：分别遍历 `RiskAssessment[]` 和 `RiskStats[]`，按 `Name` 匹配具体指标，取 `Year5`/`Year10`/`ToInd` 值

---

## 5. 数据字段说明

`FundContext` dataclass（`crawler/fund_context.py`）和 CSV 输出列（`crawler/writer.py` 的 `_COLUMNS`）完全对应，共 21 列：

| CSV 列名 | FundContext 属性 | 数据来源 | 说明 |
|---------|----------------|---------|------|
| 基金代码 | `fund_code` | EastMoney 列表 | 6位数字 |
| 基金简称 | `fund_name` | EastMoney 列表 | |
| (晨星)基金代码 | `morningstar_fund_id` | 晨星搜索 | 如 `0P00011NK0` |
| 基金类型 | `fund_type` | EastMoney overview | 如 `混合型-偏股`、`指数型-股票`、`债券型` |
| 资产规模(亿) | `fund_size` | EastMoney overview | 净资产规模，单位亿元 |
| 基金管理人 | `fund_company` | EastMoney overview | 基金管理公司名称 |
| 基金净值 | `fund_value` | EastMoney overview | 最新单位净值 |
| 基金经理(最近连续最长任职) | `fund_manager` | EastMoney manager | 当前在任经理姓名 |
| 基金经理的上任时间 | `date_of_appointment` | EastMoney manager | ISO 格式日期，如 `2026-02-14` |
| 管理费率(每年) | `management_fee_rate` | EastMoney overview | 如 `0.80%`，可能为 `DATA_IGNORE` |
| 托管费率(每年) | `custody_fee_rate` | EastMoney overview | 如 `0.20%` |
| 销售服务费率(每年) | `sales_service_fee_rate` | EastMoney overview | ETF 联接等有此费用 |
| 五年回报(年化) | `annualized_return_five_year` | 晨星 return | 百分比数字，如 `7.34828` |
| 十年回报(年化) | `annualized_return_ten_year` | 晨星 return | 成立不足10年的基金为 `NO_DATA` |
| 标准差(五年%) | `standard_deviation_five_years` | 晨星 risk | 如 `18.26328` |
| 标准差(十年%) | `standard_deviation_ten_years` | 晨星 risk | |
| 夏普比率(五年) | `sharp_rate_five_years` | 晨星 risk | 如 `0.44460` |
| 夏普比率(十年) | `sharp_rate_ten_years` | 晨星 risk | |
| 阿尔法系数(相对于基准指数%) | `alpha_to_ind` | 晨星 risk | 相对于基准指数的超额收益 |
| 贝塔系数(相对于基准指数) | `beta_to_ind` | 晨星 risk | 系统性风险暴露 |
| R平方(相对于基准指数) | `r_squared_to_ind` | 晨星 risk | 与基准相关性，0-100 |

**注意**：RETURN.json 中还包含月/季/半年/一年/二年/三年回报数据，但 `parse_return()` 仅提取五年和十年年化回报，其余数据被丢弃。

---

## 6. 策略相关（选基逻辑）

本项目爬虫部分本身不含选基策略，策略逻辑完全集中在 `result_analyse.py` 的 `analyse()` 函数，处理已爬取的 CSV 结果。

### 筛选流程（`result_analyse.py`）

`analyse(fund_filter, tenure_day_filter)` 接受两个过滤函数：

**Step 1：类型/规模过滤（`fund_filter`）**

按基金名称、基金类型和资产规模过滤，例如：
- 纯债：`"债券型" in ftype and "纯债" in name and size > 10`，排除 C/Y 份额
- 国内指数/混合：`"指数型" in ftype and "海外股票" not in ftype` 或 `"混合型" in ftype and "偏债" not in ftype`

**Step 2：经理任职年限过滤（`tenure_day_filter`）**

通过 `date_of_appointment` 计算当前经理已任职天数，例如：
- 纯债：> 7 年
- 指数/混合：> 10 年

**Step 3：夏普前 10% + R² > 60 筛选**

使用 `TopKHolder`（`utils/top_k_holder.py` 的小顶堆实现）从第二步结果中取十年夏普前 10% 的基金，同时要求 `R² > 60`（表示与基准相关性足够高，阿尔法有统计意义）。

**Step 4：阿尔法选基（扣费）**

从第三步结果中，按 `阿尔法系数 - 年总费率`（管理费+托管费+销售服务费）降序取前 3，排除 `DATA_IGNORE` 费率（费率数据不可靠的基金）。

**Step 5：年化回报选基（扣费）**

从第二步结果中，按 `十年年化回报 - 年总费率` 降序取前 3，并与第四步比较，输出"年化好但阿尔法差"的基金（可能是 Beta 驱动而非真实选股能力）。

### 预设分析场景

`result_analyse.py` 的 `__main__` 部分预设了三个分析场景：

| 场景 | 类型要求 | 规模 | 经理任职 |
|------|---------|------|---------|
| 纯债基金 | 债券型 + 名称含"纯债" | > 10 亿 | > 7 年 |
| 国内指数/混合 | 国内指数型或偏股混合型 | > 10 亿 | > 10 年 |
| 全部基金比较 | 无类型限制 | > 10 亿 | > 5 年 |

---

## 7. 可借鉴的数据获取方法与局限性

### 可借鉴的方法

**1. 基金列表接口（无需解析详情页）**

天天基金网的列表接口一次性返回全部 21,000+ 基金的代码和名称，极为高效：
```
http://fund.eastmoney.com/Data/Fund_JJJZ_Data.aspx?page=1,&onlySale=0
```
可借鉴用于快速建立本地基金代码库。

**2. 晨星 quicktake 接口是高质量数据源**

`quicktake.ashx?command=return` 和 `command=rating` 返回结构化 JSON，包含多时间窗口回报、风险指标和星级评级，是目前公开可访问的最完整基金风险数据来源之一。绕过 CloudFront WAF 的关键是设置完整的 `Accept` + `Accept-Language` 请求头。

**3. AIMD 自适应限流思路**

每域名独立限流控制器，失败触发降速、成功触发提速，相比固定速率配置更稳健，特别适合晨星这类反爬策略随时间/并发量变化的目标站。

**4. 声明式依赖图（STEPS）**

将爬取步骤抽象为 `Step(name, build_url, parse, deps)` 的列表，引擎自动推断并行阶段。添加新数据源只需向 `STEPS` 追加一个 `Step`，无需修改引擎代码。

**5. 哨兵字符串区分数据状态**

`NO_DATA / DATA_ERROR / DATA_IGNORE` 三态区分比直接用空值更有利于下游分析（可以准确判断是"数据源本来就没有"还是"爬取失败需要重跑"）。

### 局限性

**1. 仅爬取静态快照，不含历史净值序列**

每次爬取只获取当前净值（`fund_value`），不含历史净值曲线。若需回测或绘制走势图，需对接其他接口（如天天基金的历史净值 API）。

**2. 晨星仅取五年和十年回报**

`parse_return()` 跳过了 RETURN.json 中存在的月/季/半年/一年/二年/三年回报，以及 `MonthEndReturn` 月末数据和同类排名（`ReturnRank`/`ReturnCatSize`），这些数据对短期趋势判断有价值。

**3. 风险指标仅取相对于基准指数（`ToInd`），忽略相对于同类（`ToCat`）**

RISK.json 中每个指标都有 `ToInd`（相对基准）和 `ToCat`（相对同类）两个维度，`parse_risk()` 只取了 `ToInd`，同类排名未被采集。

**4. 基金经理逻辑存在注释中的复杂性**

`constants.py` 注释说明：经理字段取"最近连续最长任职"的经理，但 `parse_manager()` 实际只取 `现任基金经理简介` 中的第一位经理（正则匹配 `re.compile(r'现任基金经理简介[\s\S]+?姓名：[\s\S]+?<a.+?>(.+?)</a>')`），对多经理共管基金（A+B→B→B+C 场景）未做特殊处理。

**5. 无法获取 ETF/场内基金数据**

`WebTargetLoader` 的接口参数 `onlySale=0` 过滤了货币基金和场内基金，这类基金数据需走不同接口。

**6. 晨星接口存在不稳定性**

晨星 CloudFront WAF 的反爬策略会随时间变化。代码注释中已提示"Morningstar starts conservative"，项目 README 也有"202605 重大代码修改"警告并提供回退分支（`PreviousReleaseVersion`），说明接口规则变化风险较高。

**7. 费率字段可能为 DATA_IGNORE**

部分基金（通常为 C 类份额或特殊结构基金）的管理费率以链接形式呈现（HTML 中以 `<a` 开头），`parse_overview()` 将其标记为 `DATA_IGNORE`，下游分析脚本需过滤此类记录，导致数据覆盖有损失。

**8. 无代理/IP 轮换**

当前仅依靠 UA 轮换和 AIMD 限流绕过反爬，无 IP 池支持。大规模并发场景下若触发 IP 封禁，需外加代理中间层。
