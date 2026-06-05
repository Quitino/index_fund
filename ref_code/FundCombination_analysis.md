# FundCombination 项目深度解析

> 分析基准：读取全部源码文件（4个 .py、3个 .json、8个 .html、2个输出 csv）后整理。
> 项目地址：`/home/root123/Documents/fund_sys/ref_code/FundCombination/`

---

## 1. 项目定位与整体架构

### 定位
FundCombination 是一个**基金组合持仓透视工具**，而非最优组合求解器（没有 Markowitz 均值-方差优化，没有遗传算法等权重优化逻辑）。其核心价值在于：

1. 弥补晨星"组合透视"工具的三个缺陷：只看前十重仓、行业分类粗糙、QDII/港股持仓数据误差；
2. 将用户手工设定的组合权重与各基金前十股票/前五债券持仓合并，算出每只标的在整体组合中的真实占比；
3. 批量抓取并汇出单只基金的风险参数（标准差、夏普比、Alpha、Beta 等）。

### 整体架构

```
FundCombination/
├── input/                          # 数据输入层
│   ├── group_fund.json             # 组合配置（基金代码+权重）
│   ├── chenxingcode.json           # 基金代码→晨星专属ID 映射
│   ├── stock_info.json             # 股票/债券→一级/二级行业 映射（手工维护）
│   └── *.html                      # 从天天基金网抓取的基金详情页缓存
│
├── src/                            # 业务逻辑层（4个模块）
│   ├── IOFile.py                   # I/O工具：读 JSON、爬 HTML
│   ├── FundParameterInfo.py        # 核心数据类 FundInfo + 抓取实现
│   ├── acquire_group_fund.py       # 入口1：计算组合持仓透视
│   └── export_fund_info.py         # 入口2：导出单基金风险参数
│
└── output/                         # 结果输出层
    ├── group_position.csv/xlsx     # 组合持仓透视表（行业+股票+占比）
    └── fund_info.csv/xlsx          # 单基金参数汇总表
```

**没有前端**。输出为 CSV/XLSX 文件，在 Excel 或其他工具中查看，无 Web UI、无可视化图表代码。

---

## 2. 数据来源与获取方式

项目使用**两个来源**：

### 2.1 天天基金网（fund.eastmoney.com）

- **获取方式**：`IOFile.py` 中 `crawl_html()` 函数通过 `urllib.request.urlopen` 直接 GET 请求基金详情页。
  - URL 格式：`http://fund.eastmoney.com/{基金代码}.html`
  - 下载后以 `{基金名称}_{基金代码}.html` 保存到 `../input/` 目录。
  - 有 **12小时缓存**：文件已存在且创建时间距当前不超过 43200 秒时跳过重新下载。

- **解析方式**：`FundParameterInfo.py` 中使用 `BeautifulSoup（lxml解析器）` 解析 HTML。
  - `update_position_info_by_tiantian()`：从 `class="ui-table-hover"` 的第一个 `<table>` 提取股票持仓，从第二个 `<table>` 提取债券持仓；持仓比例用 `re.findall(r"\d+\.?\d*", ...)` 提取数字后除以 100 转为小数。
  - `update_fund_info_by_tiantian()`：从 `class="infoOfFund"` 的 div 里提取基金规模（亿元）和成立日期（`\d{4}-\d{2}-\d{2}`）。

### 2.2 晨星网（cn.morningstar.com）

- **获取方式**：`FundParameterInfo.py` 中 `update_fund_info_by_chenxing()` 使用 `selenium + ChromeDriver` 进行带登录的动态页面抓取。
  - URL 格式：`http://cn.morningstar.com/quicktake/{晨星编码}`
  - 晨星编码与基金代码之间的映射存储在 `chenxingcode.json`，格式示例：`{"005827": "0P0001E00M"}`
  - 登录逻辑：自动填入账号密码后点击 `loginGo`，获取 cookies 后复用。
  - 大量使用 `sleep(3)` 规避反爬检测。

- **解析字段**（均通过 `find_element_by_id` 等 Selenium 方法提取）：

| 字段 | 晨星页面元素 ID / Class |
|------|------------------------|
| 三个月最大回撤 | `#qt_worst .r3` |
| 股票总仓位 | class=`stock` |
| 债券总仓位 | class=`bonds` |
| 十大股票仓位占比 | `#qt_stocktab` |
| 五大债券仓位占比 | `#qt_bondstab` |
| 标准差 | `#qt_risk > li[15]` |
| 风险系数（晨星） | `#qt_risk > li[22]` |
| 夏普比 | `#qt_risk > li[29]` |
| Alpha | `#qt_riskstats > li[4]` |
| Beta | `#qt_riskstats > li[7]` |
| R² | `#qt_riskstats > li[10]` |

---

## 3. 组合构建逻辑

### 3.1 如何选基（人工配置）

**基金选择完全由用户手工决定**，没有任何量化筛选逻辑。用户在 `input/group_fund.json` 中配置如下结构：

```json
[
  {"ID": "005827", "name": "易方达蓝筹精选", "proportion": 0.18},
  {"ID": "519772", "name": "交银新生活力灵活", "proportion": 0.16},
  ...
]
```

示例组合为 8 只基金，涵盖：
- 主动权益（易方达蓝筹精选、交银新生活力、兴全合润）
- 行业主题（中欧医疗创新、汇添富消费）
- 综合混合（工银战略转型）
- QDII（华安纳斯达克100、汇添富全球移动互联）

### 3.2 权重分配

权重同样完全人工设定，无优化算法。`IOFile.py` 中 `read_group_fund_json()` 有一个**硬约束校验**：

```python
percent_sum = 0.0
for i in range(len(group_fund_info)):
    percent_sum += group_fund_info[i]["proportion"]
if abs(1 - percent_sum) > 0.01:
    print("fund propotion sum is not 100% and sum is :", percent_sum)
    import sys
    sys.exit()
```

若所有基金权重之和偏离 1.0 超过 0.01，程序退出。示例权重分布：0.18 + 0.16 + 0.10 + 0.09 + 0.10 + 0.11 + 0.13 + 0.13 = 1.00。

### 3.3 组合持仓合并公式

核心计算在 `acquire_group_fund.py` 的 `manage_group_fund()` 函数：

**对每只基金 i，其每个持仓标的 k 在组合层面的贡献为：**

```
组合持仓[k] += 基金i在组合中的权重[i] × 基金i中标的k的仓位比例[i][k]
```

代码实现：

```python
for key in mixed_position.keys():        # key = 标的名称
    if key not in group_position.keys():
        group_position[key] = group_proportion * mixed_position[key]
    else:
        group_position[key] += group_proportion * mixed_position[key]
```

其中 `mixed_position` 是将 `stock_position_proportion`（股票）和 `bond_position_propotion`（债券）合并成的一个字典，仓位比例已在解析时除以 100 转为小数（如 3.5% → 0.035）。

**注意**：该方法计算的是"天天基金网前十持仓"对组合的加权贡献，而非全仓穿透。每只基金披露的股票仓位数据通常只覆盖前十大，合计未必等于该基金总股票仓位，因此组合所有标的仓位加总通常远小于 1（约 30%~50%）。

---

## 4. 策略指标计算

**本项目不自行计算任何指标**，所有指标均直接从晨星网抓取显示值，不含任何公式实现。下面记录各指标的定义和晨星网数据来源：

### 4.1 指标来源一览

| 指标名 | 变量名 | 晨星数据位置 | 说明 |
|--------|--------|-------------|------|
| 三个月最大回撤 | `three_month_retracement` | `#qt_worst .r3` | 过去3个月的最大净值回撤，晨星直接展示 |
| 标准差 | `risk_assessment["standard_deviation"]` | `#qt_risk > li[15]` | 收益率的年化标准差（波动率），晨星计算 |
| 风险系数 | `risk_assessment["risk_coefficient"]` | `#qt_risk > li[22]` | 晨星自定义风险评分 |
| 夏普比 | `risk_assessment["sharpby"]` | `#qt_risk > li[29]` | 超额收益/标准差，晨星计算 |
| Alpha | `risk_statistics["alpha"]` | `#qt_riskstats > li[4]` | 相对基准的超额收益 |
| Beta | `risk_statistics["beta"]` | `#qt_riskstats > li[7]` | 相对基准的系统风险敏感度 |
| R² | `risk_statistics["r_square"]` | `#qt_riskstats > li[10]` | 基金收益与基准指数相关系数的平方 |
| 股票总仓位 | `stock_total_position["stock_total_position"]` | class=`stock` | 基金股票资产占净资产比例 |
| 债券总仓位 | `bond_total_position["bond_total_position"]` | class=`bonds` | 基金债券资产占净资产比例 |
| 十大股票仓位 | `stock_total_position["ten_stock_position"]` | `#qt_stocktab` | 前十大股票占净资产比例（集中度） |

### 4.2 指标字段说明（理论公式）

代码仅存储和展示晨星提供的值，以下是各指标的标准计算方式（供参考）：

- **年化标准差（波动率）**：
  ```
  σ = std(日收益率) × sqrt(250)   # 基于日收益率
  # 或 sqrt(12) 基于月收益率
  ```

- **夏普比率**：
  ```
  Sharpe = (R_fund - R_f) / σ
  # R_fund 为基金年化收益，R_f 为无风险收益率，σ 为年化标准差
  ```

- **最大回撤**：
  ```
  MaxDrawdown = max[(峰值净值 - 随后最低净值) / 峰值净值]
  # 项目中仅有3个月最大回撤，不是全区间
  ```

- **Alpha（Jensen's Alpha）**：
  ```
  α = R_fund - [R_f + β × (R_benchmark - R_f)]
  ```

- **Beta**：
  ```
  β = Cov(R_fund, R_benchmark) / Var(R_benchmark)
  ```

- **R²**：
  ```
  R² = [Corr(R_fund, R_benchmark)]²
  ```

### 4.3 输出格式

`export_fund_info.py` 将所有参数写入 `output/fund_info.csv`，列顺序：
`代码, 规模, 基龄(成立日期), 3月回撤, 标准差, 风险系数, 夏普比, 阿尔法, 贝塔, R平方, 股仓, 债仓, 十股, 五债`

---

## 5. 定投/影子模式

**本项目不包含定投逻辑、影子持仓模式或任何动态再平衡机制。**

- 没有定投金额/频率/日期设定
- 没有基于估值指标（如 PE、PB）的变额定投
- 没有组合追踪模式（记录实际持仓与目标权重的偏离）
- 没有交易信号生成

项目是一次性快照分析工具：每次运行时抓取当前数据，输出当前状态的组合透视，不做历史对比或时序管理。

---

## 6. 可视化实现

**本项目无可视化代码**，没有任何图表生成逻辑：

- 没有 matplotlib、seaborn、plotly、echarts 等图表库
- 没有 HTML 报告生成
- 没有 Dashboard 或 Web 界面

输出仅为 CSV 和 XLSX 文件（`fund_info.csv`、`group_position.csv` 及对应 xlsx），均为表格数据，需要用户自行在 Excel 或其他工具中制图。

---

## 7. 可借鉴点与局限性

### 7.1 可借鉴点

**架构层面：**
- `IOFile.py` 与业务逻辑分离的设计清晰，I/O 统一收口，便于替换数据源。
- `FundInfo` 类设计合理，字段分组（基础信息/天天数据/晨星数据）、来源注释清楚，可直接扩展。
- 12小时 HTML 缓存机制（`time.time() - os.stat(...).st_mtime > 3600 * 12`）避免重复请求，思路值得复用。
- `read_group_fund_json()` 中的权重和校验（`abs(1 - percent_sum) > 0.01`）是一个简单且实用的输入校验范式。

**数据层面：**
- `stock_info.json` 设计：股票名称 → [一级行业, 二级行业] 的手工映射，细化到 A股申万二级行业 + 港股行业 + 美股行业，实际覆盖约 100 只标的，是一份有参考价值的行业分类样本。
- `chenxingcode.json` 维护基金代码与晨星 ID 的映射关系，解决了两个数据源编码体系不一致的问题，类似 symbol_mapping 设计模式。
- 组合穿透的核心公式（`组合持仓 = Σ 基金权重 × 基金内标的持仓比例`）正确且简洁，可直接用于自建系统。

**工程细节：**
- BeautifulSoup `findAll("table", {"class": "ui-table-hover"})[0/1]` 按索引区分股债持仓表的方式，适用于天天基金网页面结构相对固定的场景。
- `mixed_position = stock.copy(); mixed_position.update(bond)` 合并股债字典后统一遍历，代码简洁。

### 7.2 局限性

**数据覆盖：**
- 仓位穿透只到"前十股票 + 前五债券"，未披露的持仓不可见，组合全貌不完整。
- `stock_info.json` 完全手工维护，缺少自动更新机制；新增持仓标的需手动添加行业信息，否则输出为 `default/default`。

**指标计算：**
- 所有风险指标（标准差、夏普、Alpha、Beta、R²）全部依赖晨星网现成数据，不自行计算，无法定制时间窗口、基准指数、无风险利率等参数。
- 没有收益率时间序列，无法计算组合层面的整体波动率或最大回撤（只有单基金的3个月回撤）。

**工程健壮性：**
- `update_fund_info_by_chenxing()` 中账号密码明文写在代码里（已用 `*` 替代，但框架暴露），不符合安全规范。
- Selenium 依赖大量 `sleep(3)` 硬等待，既慢又脆弱，无 WebDriverWait 显式等待。
- 晨星解析用 `find_elements_by_xpath('li').pop(15/22/29...)` 硬编码下标，页面结构变化后立即失效，维护成本极高。
- 无异常处理（try/except），任何单个基金抓取失败会导致整批中断。
- `find_element_by_id`、`find_element_by_class_name` 等 Selenium API 已在新版中废弃（需改为 `find_element(By.ID, ...)`）。
- 不支持增量更新；每次运行覆盖写输出文件（`open(..., 'w')`），无历史记录。

**功能缺失：**
- 无组合优化（无法求"最优权重"）
- 无回测框架（无法验证策略历史表现）
- 无定投/再平衡
- 无前端/可视化
- 无基金数量、权重上下界等约束
- `institution_propotion`（机构持仓占比）和 `morningstar_evaluation`（晨星评级）字段已定义但标注"无法获取"，为未完成功能。
