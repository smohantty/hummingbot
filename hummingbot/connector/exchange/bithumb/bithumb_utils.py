from decimal import Decimal
from typing import Any, Dict

from pydantic import ConfigDict, Field, SecretStr

from hummingbot.client.config.config_data_types import BaseConnectorConfigMap
from hummingbot.core.data_type.trade_fee import TradeFeeSchema

CENTRALIZED = True
EXAMPLE_PAIR = "KRW-BTC"

DEFAULT_FEES = TradeFeeSchema(
    maker_percent_fee_decimal=Decimal("0.001"),
    taker_percent_fee_decimal=Decimal("0.001"),
    buy_percent_fee_deducted_from_returns=True
)


def is_exchange_information_valid(exchange_info: Dict[str, Any]) -> bool:
    """
    Verifies if a trading pair is enabled to operate with based on its exchange information
    :param exchange_info: the exchange information for a trading pair
    :return: True if the trading pair is enabled, False otherwise
    """
    return exchange_info.get("trade_status", None) == "trading"


def is_pair_information_valid(pair_info: Dict[str, Any]) -> bool:
    """
    Verifies if a trading pair is enabled to operate with based on its market information

    :param pair_info: the market information for a trading pair

    :return: True if the trading pair is enabled, False otherwise
    """
    # Bithumb returns trading pairs with status and order_min parameters
    # We consider a pair valid if it's active for trading and has a minimum order size
    status = pair_info.get("status", "").lower()
    order_min = pair_info.get("order_min", 0)

    return status == "active" and order_min > 0


def convert_from_exchange_trading_pair(exchange_trading_pair: str) -> str:
    """
    Convert a trading pair from exchange format (KRW-BTC) to HB format (BTC-KRW)
    :param exchange_trading_pair: Trading pair in exchange format
    :return: Trading pair in Hummingbot format
    """
    if "_" in exchange_trading_pair:
        # Handle old format for backward compatibility
        base, quote = exchange_trading_pair.split("_")
        return f"{base}-{quote}"
    elif "-" in exchange_trading_pair:
        # Bithumb format is QUOTE-BASE (e.g. KRW-BTC)
        # Hummingbot format is BASE-QUOTE (e.g. BTC-KRW)
        quote, base = exchange_trading_pair.split("-")
        return f"{base}-{quote}"
    return exchange_trading_pair


def convert_to_exchange_trading_pair(hb_trading_pair: str) -> str:
    """
    Convert a trading pair from HB format (BTC-KRW) to exchange format (KRW-BTC)
    :param hb_trading_pair: Trading pair in Hummingbot format
    :return: Trading pair in exchange format
    """
    base, quote = hb_trading_pair.split("-")
    # Bithumb format is QUOTE-BASE (e.g. KRW-BTC)
    return f"{quote}-{base}"


class BithumbConfigMap(BaseConnectorConfigMap):
    connector: str = "bithumb"
    bithumb_api_key: SecretStr = Field(
        default=...,
        json_schema_extra={
            "prompt": lambda cm: "Enter your Bithumb API key",
            "is_secure": True,
            "is_connect_key": True,
            "prompt_on_new": True,
        }
    )
    bithumb_api_secret: SecretStr = Field(
        default=...,
        json_schema_extra={
            "prompt": lambda cm: "Enter your Bithumb API secret",
            "is_secure": True,
            "is_connect_key": True,
            "prompt_on_new": True,
        }
    )
    model_config = ConfigDict(title="bithumb")


KEYS = BithumbConfigMap.model_construct()
