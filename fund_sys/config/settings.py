from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "db"
DATA_DIR.mkdir(exist_ok=True)

DB_PATH = DATA_DIR / "fund.db"
DB_URL = f"sqlite:///{DB_PATH}"

# 数据更新 TTL（秒）
NAV_TTL = 6 * 3600       # 净值缓存6小时
INFO_TTL = 7 * 24 * 3600  # 基金信息缓存7天
VAL_TTL = 6 * 3600        # 估值缓存6小时

# akshare 请求间隔（秒），避免触发限流
REQUEST_DELAY = 0.3

# 费率默认值（可被基金信息表覆盖）
DEFAULT_PURCHASE_FEE_OTC = 0.0015   # 场外申购费（1折后 0.15%）
DEFAULT_REDEEM_FEE_SHORT = 0.015    # 持有<7天赎回费
DEFAULT_REDEEM_FEE_LONG = 0.0       # 持有>=7天赎回费
DEFAULT_COMMISSION_ETF = 0.0003     # ETF佣金（单边）

REDEEM_SHORT_DAYS = 7               # 短期赎回天数阈值
