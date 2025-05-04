from decimal import Decimal
from typing import Literal

from hummingbot.strategy_v2.executors.data_types import ExecutorConfigBase


class SpotGridExecutorConfig(ExecutorConfigBase):
    type: Literal["spot_grid_executor"] = "spot_grid_executor"
    connector_name: str
    trading_pair: str
    start_price: Decimal
    end_price: Decimal
    spread_percentage: Decimal
    total_amount_quote: Decimal
