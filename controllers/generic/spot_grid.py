from decimal import Decimal
from typing import Dict, List, Set

from pydantic import Field

from hummingbot.data_feed.candles_feed.data_types import CandlesConfig
from hummingbot.strategy_v2.controllers import ControllerBase, ControllerConfigBase
from hummingbot.strategy_v2.executors.data_types import ConnectorPair
from hummingbot.strategy_v2.executors.grid_executor.data_types import GridExecutorConfig
from hummingbot.strategy_v2.models.executor_actions import CreateExecutorAction, ExecutorAction
from hummingbot.strategy_v2.models.executors_info import ExecutorInfo


class SpotGridConfig(ControllerConfigBase):
    """
    Configuration required to run the SpotGrid strategy for one connector and trading pair.
    """
    controller_type: str = "generic"
    controller_name: str = "spot_grid"
    candles_config: List[CandlesConfig] = []

    connector_name: str = Field(
        default="binance",
        json_schema_extra={
            "prompt": "Enter the connector name (e.g., binance): ",
            "prompt_on_new": True}
    )
    trading_pair: str = Field(
        default="SOL-USDC",
        json_schema_extra={
            "prompt": "Enter the trading pair to trade on (e.g., SOL-USDT): ",
            "prompt_on_new": True}
    )

    start_price: Decimal = Field(
        default=Decimal("140"),
        json_schema_extra={
            "prompt": "Enter the start price (e.g., 140): ",
            "prompt_on_new": True}
    )

    end_price: Decimal = Field(
        default=Decimal("160"),
        json_schema_extra={
            "prompt": "Enter the end price (e.g., 160): ",
            "prompt_on_new": True}
    )

    spread_percentage: Decimal = Field(
        default=Decimal("1"),
        json_schema_extra={
            "prompt": "Enter the spread percentage (e.g., for 1% enter 1): ",
            "prompt_on_new": True}
    )

    total_amount_quote: Decimal = Field(
        default=Decimal("100"),
        json_schema_extra={
            "prompt": "Enter the total amount in quote asset (eg., USDC , KRW) to use for trading (e.g., 100): ",
            "prompt_on_new": True}
    )

    def update_markets(self, markets: Dict[str, Set[str]]) -> Dict[str, Set[str]]:
        if self.connector_name not in markets:
            markets[self.connector_name] = set()
        markets[self.connector_name].add(self.trading_pair)
        return markets


class SpotGrid(ControllerBase):
    def __init__(self, config: SpotGridConfig, *args, **kwargs):
        super().__init__(config, *args, **kwargs)
        self.config = config
        self.connector = self.initialize_rate_sources()

    def initialize_rate_sources(self):
        self.market_data_provider.initialize_rate_sources([ConnectorPair(connector_name=self.config.connector_name,
                                                                         trading_pair=self.config.trading_pair)])

    def active_executors(self) -> List[ExecutorInfo]:
        return [
            executor for executor in self.executors_info
            if executor.is_active
        ]

    def determine_executor_actions(self) -> List[ExecutorAction]:
        if len(self.active_executors()) == 0:
            return [CreateExecutorAction(
                controller_id=self.config.id,
                executor_config=GridExecutorConfig(
                    timestamp=self.market_data_provider.time(),
                    connector_name=self.config.connector_name,
                    trading_pair=self.config.trading_pair,
                    start_price=self.config.start_price,
                    end_price=self.config.end_price,
                    spread_percentage=self.config.spread_percentage,
                    total_amount_quote=self.config.total_amount_quote
                ))]
        return []

    async def update_processed_data(self):
        pass

    def to_format_status(self) -> List[str]:
        status = []
        status.append("Place Holder for Spot Grid")
        return status
