import asyncio
import logging
from decimal import Decimal
from typing import Union

from hummingbot.connector.connector_base import ConnectorBase
from hummingbot.core.data_type.common import PriceType
from hummingbot.core.event.events import (
    BuyOrderCompletedEvent,
    BuyOrderCreatedEvent,
    MarketOrderFailureEvent,
    OrderCancelledEvent,
    OrderFilledEvent,
    SellOrderCompletedEvent,
    SellOrderCreatedEvent,
)
from hummingbot.logger import HummingbotLogger
from hummingbot.strategy.script_strategy_base import ScriptStrategyBase
from hummingbot.strategy_v2.executors.executor_base import ExecutorBase
from hummingbot.strategy_v2.executors.spot_grid_executor.data_types import SpotGridExecutorConfig
from hummingbot.strategy_v2.models.base import RunnableStatus


class SpotGridExecutor(ExecutorBase):
    _logger = None

    @classmethod
    def logger(cls) -> HummingbotLogger:
        if cls._logger is None:
            cls._logger = logging.getLogger(__name__)
        return cls._logger

    def __init__(self, strategy: ScriptStrategyBase, config: SpotGridExecutorConfig,
                 update_interval: float = 1.0, max_retries: int = 10):
        """
        Initialize the PositionExecutor instance.

        :param strategy: The strategy to be used by the PositionExecutor.
        :param config: The configuration for the PositionExecutor, subclass of PositionExecutoConfig.
        :param update_interval: The interval at which the PositionExecutor should be updated, defaults to 1.0.
        :param max_retries: The maximum number of retries for the PositionExecutor, defaults to 5.
        """
        self.config: SpotGridExecutorConfig = config
        super().__init__(strategy=strategy, config=config, connectors=[config.connector_name],
                         update_interval=update_interval)
        self.trading_rules = self.get_trading_rules(self.config.connector_name, self.config.trading_pair)

        self._current_retries = 0
        self._max_retries = max_retries

    async def control_task(self):
        """
        This method is responsible for controlling the task based on the status of the executor.

        :return: None
        """
        if self.status == RunnableStatus.RUNNING:
            self.logger().error("Spot Grid Executor is running")
        elif self.status == RunnableStatus.SHUTTING_DOWN:

            self.logger().error("Spot Grid Executor is shutting down")
        self.evaluate_max_retries()

    def early_stop(self, keep_position: bool = False):
        """
        This method allows strategy to stop the executor early.

        :return: None
        """
        self._status = RunnableStatus.SHUTTING_DOWN

    async def control_shutdown_process(self):
        """
        Control the shutdown process of the executor, handling held positions separately
        """
        await self._sleep(5.0)

    async def validate_sufficient_balance(self):
        mid_price = self.get_price(self.config.connector_name, self.config.trading_pair, PriceType.MidPrice)
        total_amount_base = self.config.total_amount_quote / mid_price
        self.logger().error(f"Total amount base: {total_amount_base}")

    async def on_start(self):
        """
        This method is responsible for starting the executor and validating if the position is expired. The base method
        validates if there is enough balance to place the open order.

        :return: None
        """
        await super().on_start()
        self.update_metrics()

    def update_metrics(self):
        self.logger().error("Update metrics not yet implemented")

    def evaluate_max_retries(self):
        """
        This method is responsible for evaluating the maximum number of retries to place an order and stop the executor
        if the maximum number of retries is reached.

        :return: None
        """
        if self._current_retries > self._max_retries:
            self.stop()

    def update_tracked_orders_with_order_id(self, order_id: str):
        """
        This method is responsible for updating the tracked orders with the information from the InFlightOrder, using
        the order_id as a reference.

        :param order_id: The order_id to be used as a reference.
        :return: None
        """
        pass

    def process_order_created_event(self, _, market, event: Union[BuyOrderCreatedEvent, SellOrderCreatedEvent]):
        """
        This method is responsible for processing the order created event. Here we will update the TrackedOrder with the
        order_id.
        """
        self.update_tracked_orders_with_order_id(event.order_id)

    def process_order_filled_event(self, _, market, event: OrderFilledEvent):
        """
        This method is responsible for processing the order filled event. Here we will update the value of
        _total_executed_amount_backup, that can be used if the InFlightOrder
        is not available.
        """
        self.update_tracked_orders_with_order_id(event.order_id)

    def process_order_completed_event(self, _, market, event: Union[BuyOrderCompletedEvent, SellOrderCompletedEvent]):
        """
        This method is responsible for processing the order completed event. Here we will check if the id is one of the
        tracked orders and update the state
        """
        self.update_tracked_orders_with_order_id(event.order_id)

    def process_order_canceled_event(self, _, market: ConnectorBase, event: OrderCancelledEvent):
        """
        This method is responsible for processing the order canceled event
        """
        pass

    def process_order_failed_event(self, _, market, event: MarketOrderFailureEvent):
        """
        This method is responsible for processing the order failed event. Here we will add the InFlightOrder to the
        failed orders list.
        """
        pass

    def get_net_pnl_pct(self) -> Decimal:
        """
        Calculate the net pnl percentage

        :return: The net pnl percentage.
        """
        return Decimal("0")

    def get_net_pnl_quote(self) -> Decimal:
        """
        Returns the net profit or loss in quote currency.
        """
        return Decimal("0")

    def get_cum_fees_quote(self) -> Decimal:
        """
        Returns the cumulative fees in quote currency.
        """
        return Decimal("0")

    async def _sleep(self, delay: float):
        """
        This method is responsible for sleeping the executor for a specific time.

        :param delay: The time to sleep.
        :return: None
        """
        await asyncio.sleep(delay)
