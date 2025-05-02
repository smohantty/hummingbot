import logging
import math
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from hummingbot.connector.connector_base import ConnectorBase
from hummingbot.core.data_type.common import OrderType, PriceType, TradeType
from hummingbot.core.data_type.order_candidate import OrderCandidate
from hummingbot.core.event.events import BuyOrderCompletedEvent, OrderFilledEvent, SellOrderCompletedEvent
from hummingbot.core.utils import map_df_to_str
from hummingbot.strategy.script_strategy_base import ScriptStrategyBase


@dataclass(frozen=True)
class Percent:
    value: Decimal
    def as_ratio(self) ->Decimal:
        return self.value /100.0
    
HL_ASSET_SIZE_DECIMALS = {
    'BTC': 5, 'ETH': 4, 'ATOM': 2, 'MATIC': 1, 'DYDX': 1, 'SOL': 2, 'AVAX': 2, 'BNB': 3,
    'APE': 1, 'OP': 1, 'LTC': 2, 'ARB': 1, 'DOGE': 0, 'INJ': 1, 'SUI': 1, 'kPEPE': 0,
    'CRV': 1, 'LDO': 1, 'LINK': 1, 'STX': 1, 'RNDR': 1, 'CFX': 0, 'FTM': 0, 'GMX': 2,
    'SNX': 1, 'XRP': 0, 'BCH': 3, 'APT': 2, 'AAVE': 2, 'COMP': 2, 'MKR': 4, 'WLD': 1,
    'FXS': 1, 'HPOS': 0, 'RLB': 0, 'UNIBOT': 3, 'YGG': 0, 'TRX': 0, 'kSHIB': 0, 'UNI': 1,
    'SEI': 0, 'RUNE': 1, 'OX': 0, 'FRIEND': 1, 'SHIA': 0, 'CYBER': 1, 'ZRO': 1, 'BLZ': 0,
    'DOT': 1, 'BANANA': 1, 'TRB': 2, 'FTT': 1, 'LOOM': 0, 'OGN': 0, 'RDNT': 0, 'ARK': 0,
    'BNT': 0, 'CANTO': 0, 'REQ': 0, 'BIGTIME': 0, 'KAS': 0, 'ORBS': 0, 'BLUR': 0,
    'TIA': 1, 'BSV': 2, 'ADA': 0, 'TON': 1, 'MINA': 0, 'POLYX': 0, 'GAS': 1, 'PENDLE': 0,
    'STG': 0, 'FET': 0, 'STRAX': 0, 'NEAR': 1, 'MEME': 0, 'ORDI': 2, 'BADGER': 1, 'NEO': 2,
    'ZEN': 2, 'FIL': 1, 'PYTH': 0, 'SUSHI': 1, 'ILV': 2, 'IMX': 1, 'kBONK': 0, 'GMT': 0,
    'SUPER': 0, 'USTC': 0, 'NFTI': 1, 'JUP': 0, 'kLUNC': 0, 'RSR': 0, 'GALA': 0, 'JTO': 0,
    'NTRN': 0, 'ACE': 2, 'MAV': 0, 'WIF': 0, 'CAKE': 1, 'PEOPLE': 0, 'ENS': 2, 'ETC': 2,
    'XAI': 1, 'MANTA': 1, 'UMA': 1, 'ONDO': 0, 'ALT': 0, 'ZETA': 1, 'DYM': 1, 'MAVIA': 1,
    'W': 1, 'PANDORA': 5, 'STRK': 1, 'PIXEL': 0, 'AI': 1, 'TAO': 3, 'AR': 2, 'MYRO': 0,
    'kFLOKI': 0, 'BOME': 0, 'ETHFI': 1, 'ENA': 0, 'MNT': 1, 'TNSR': 1, 'SAGA': 1, 'MERL': 0,
    'HBAR': 0, 'POPCAT': 0, 'OMNI': 2, 'EIGEN': 2, 'REZ': 0, 'NOT': 0, 'TURBO': 0,
    'BRETT': 0, 'IO': 1, 'ZK': 0, 'BLAST': 0, 'LISTA': 0, 'MEW': 0, 'RENDER': 1,
    'kDOGS': 0, 'POL': 0, 'CATI': 0, 'CELO': 0, 'HMSTR': 0, 'SCR': 1, 'NEIROETH': 0,
    'kNEIRO': 1, 'GOAT': 0, 'MOODENG': 0, 'GRASS': 1, 'PURR': 0, 'PNUT': 1, 'XLM': 0,
    'CHILLGUY': 0, 'SAND': 0, 'IOTA': 0, 'ALGO': 0, 'HYPE': 2, 'ME': 1, 'MOVE': 0,
    'VIRTUAL': 1, 'PENGU': 0, 'USUAL': 1, 'FARTCOIN': 1, 'AI16Z': 1, 'AIXBT': 0,
    'ZEREBRO': 0, 'BIO': 0, 'GRIFFAIN': 0, 'SPX': 1, 'S': 0, 'MORPHO': 1, 'TRUMP': 1,
    'MELANIA': 1, 'ANIME': 0, 'VINE': 0, 'VVV': 2, 'JELLY': 0, 'BERA': 1, 'TST': 0,
    'LAYER': 0, 'IP': 1, 'OM': 1, 'KAITO': 0, 'NIL': 0, 'PAXG': 3, 'PROMPT': 0, 'BABY': 0,
    'WCT': 0, 'HYPER': 0, 'ZORA': 0, 'INIT': 0
}    

#@TODO Find the exact size_decimal for each coin
def normalize_price(price: Decimal, max_decimals: int, sz_decimals: int) -> Decimal:
    if price > 100000:
        px = round(price)
    else:
        px = round(float(f"{price:.5g}"), max_decimals - sz_decimals)
    return Decimal(str(px))

def normalize_quantity(quantity: Decimal, sz_decimals: int) -> Decimal:
    sz = round(quantity, sz_decimals)
    return Decimal(str(sz))


@dataclass
class GridItem:
    price: Decimal                                 # in quote currency
    quantity: Decimal                              # in base currency
    order_info: Optional[OrderCandidate] = None  # order info 
    order_id: Optional[str] = None               # order id
    order_submitted: bool = False

class GridManager:
    lowerbound = Decimal
    upperbound = Decimal
    spread_percentage = Percent(1.0)
    quote_token_amount = Decimal
    grids = []

    def __init__(self, lower_bound: Decimal , upper_bound: Decimal, quote_token_amount: Decimal, spread_percentage = Percent(1.0), size_decimals: int = 5):
        self.lowerbound = lower_bound
        self.upperbound = upper_bound
        self.quote_token_amount = quote_token_amount
        self.spread_percentage = spread_percentage
        self.size_decimals = size_decimals
        self._generate_grid()


    
    def _generate_grid(self):
        """ calculates indivisual grid value in the range[lowerbound, upperbound] and spread_percentage to
            keeps the grid spacing  constant in terms of spread_percentage"""
        
        if (self.lowerbound <= 0) or (self.upperbound <=0):
            raise ValueError("Bound must be positive")
        if self.spread_percentage.as_ratio() <= 0 :
            raise ValueError("Spread percent must be positive")
        
        if (self.quote_token_amount <= 0):
            raise ValueError("Quote currency total must be positive")
                
        ratio = self.upperbound / self.lowerbound
        num_grids = 1 + math.log(ratio) / math.log(1 + self.spread_percentage.as_ratio())
        num_grids = math.ceil(num_grids)

        if (num_grids < 2):
            raise ValueError("Number of grids must be atleast 2")
        step = pow(self.upperbound / self.lowerbound, Decimal(1) / Decimal(num_grids - 1))

        price_grid_list = [self.lowerbound * pow(step, i) for i in range(num_grids)]

        if not price_grid_list or any (p <= 0 for p in price_grid_list):
            raise ValueError("Grid Prices must be positive")
        
        quote_token_quantity_per_grid = self.quote_token_amount/ len(price_grid_list)
        
        base_token_quantity_list = [quote_token_quantity_per_grid / price for price in price_grid_list]

        if (len(price_grid_list) != len(base_token_quantity_list)):
            raise ValueError("Grid prices and base token quantity list must be of the same length")
        
        for i , price in enumerate(price_grid_list):
            self.grids.append(GridItem(normalize_price(price, 6, self.size_decimals), normalize_quantity(base_token_quantity_list[i], self.size_decimals)))

    def find_grid_index(self, order_id: str) -> int:
        return next((i for i, grid in enumerate(self.grids) if grid.order_id == order_id), -1)

    def generate_data_frame(self)-> pd.DataFrame:
        data = []
        for i, grid in enumerate(self.grids):
            order_type = "EMPTY"
            if grid.order_id is not None:
                order_type = "BUY" if grid.order_info.order_side == TradeType.BUY else "SELL"
            
            data.append({
                "index": i,
                "price": grid.price,
                "quantity": grid.quantity,
                "order_type": order_type
            })
        
        df = pd.DataFrame(data)
        return df


class FixedGrid(ScriptStrategyBase):
    # Parameters to modify -----------------------------------------
    coin = "HYPE"
    trading_pair = f"{coin}-USDC"
    exchange = "hyperliquid"
    grid_price_lower_bound = Decimal(18)
    grid_price_upper_bound = Decimal(19.35)
    grid_spread_in_percentage = Percent(0.6)
    quote_token_total_amount = Decimal(350)
    # Optional ----------------------
    rebalance_order_type = "limit"
    rebalance_order_spread = Decimal(0.02)
    rebalance_order_refresh_time = 60.0
    grid_orders_refresh_time = 3600000.0
    price_source = PriceType.MidPrice
    # ----------------------------------------------------------------

    # Hyperliquid specific parameters
    TICK_SIZE = Decimal('0.0001')  # 0.01% tick size
    LOT_SIZE = Decimal('0.0001')   # 0.01% lot size

    markets = {exchange: {trading_pair}}
    grid_manager = None
    initialized = False

    def __init__(self, connectors: Dict[str, ConnectorBase]):
        super().__init__(connectors)

        try:
            self.grid_manager = GridManager(self.grid_price_lower_bound, 
                                            self.grid_price_upper_bound, 
                                            self.quote_token_total_amount, 
                                            self.grid_spread_in_percentage,
                                            size_decimals=HL_ASSET_SIZE_DECIMALS[self.coin])
        except ValueError as e:
            self.log_with_clock(logging.ERROR, str(e))
            self.notify_hb_app_with_timestamp(str(e))
            return


    def on_tick(self):
        if not self.initialized:
            self.initialized = True
            current_price = self.connectors[self.exchange].get_price_by_type(self.trading_pair, self.price_source)

            for griditem in self.grid_manager.grids:
                if current_price > griditem.price:
                    griditem.order_info = OrderCandidate(trading_pair=self.trading_pair, is_maker=True, order_type=OrderType.LIMIT,
                                                        order_side=TradeType.BUY, amount=griditem.quantity, price=griditem.price)
                else:
                    griditem.order_info = OrderCandidate(trading_pair=self.trading_pair, is_maker=True, order_type=OrderType.LIMIT,
                                                        order_side=TradeType.SELL, amount=griditem.quantity, price=griditem.price)
                    
        # delay order submission to avoid order submission failure due to backend rate limit
        for griditem in self.grid_manager.grids:
            if not griditem.order_submitted:
                griditem.order_id = self.place_order(self.exchange, griditem.order_info)
                griditem.order_submitted = True
                break
    


    def did_fill_order(self, event: OrderFilledEvent):
        msg = (f"{event.trade_type.name} {round(event.amount, 2)} {event.trading_pair} {self.exchange} at {round(event.price, 2)}")
        self.log_with_clock(logging.INFO, msg)
        self.notify_hb_app_with_timestamp(msg)

    def did_complete_buy_order(self, event: BuyOrderCompletedEvent):
        grid_index = self.grid_manager.find_grid_index(event.order_id)
        if (grid_index == -1):
            msg = (f"Buy order completed: {event.order_id} but grid index not found")
            self.log_with_clock(logging.ERROR, msg)
            self.notify_hb_app_with_timestamp(msg)
            return
        
        msg = (f"Buy order completed: {event.order_id} at index {grid_index}")
        self.log_with_clock(logging.INFO, msg)
        self.notify_hb_app_with_timestamp(msg)

        
        self.grid_manager.grids[grid_index].order_id = None

        if (grid_index == len(self.grid_manager.grids) - 1):
            msg = (f"Buy order completed: {event.order_id} but grid index is the last grid")
            self.log_with_clock(logging.ERROR, msg)
            self.notify_hb_app_with_timestamp(msg)
            return
        
        gridItem = self.grid_manager.grids[grid_index + 1]
        
        #place sell order if not already placed
        if (gridItem.order_id is None):
            gridItem.order_info = OrderCandidate(trading_pair=self.trading_pair, is_maker=True, order_type=OrderType.LIMIT,
                                            order_side=TradeType.SELL, amount=gridItem.quantity, price=gridItem.price)
            gridItem.order_submitted = True
            gridItem.order_id = self.place_order(self.exchange, gridItem.order_info)

            msg = (f"Placed next Sell order at index {grid_index + 1}")
            self.log_with_clock(logging.INFO, msg)
            self.notify_hb_app_with_timestamp(msg)
        else:
            msg = (f"Sell order already placed at index {grid_index + 1}")
            self.log_with_clock(logging.INFO, msg)
            self.notify_hb_app_with_timestamp(msg)


    def did_complete_sell_order(self, event: SellOrderCompletedEvent):
        grid_index = self.grid_manager.find_grid_index(event.order_id)
        if (grid_index == -1):
            msg = (f"Sell order completed: {event.order_id} but grid index not found")
            self.log_with_clock(logging.ERROR, msg)
            self.notify_hb_app_with_timestamp(msg)
            return
        
        msg = (f"Sell order completed: {event.order_id} at index {grid_index}")
        self.log_with_clock(logging.INFO, msg)
        self.notify_hb_app_with_timestamp(msg)

        
        self.grid_manager.grids[grid_index].order_id = None

        if (grid_index == 0):
            msg = (f"Sell order completed: {event.order_id} but grid index is the first grid")
            self.log_with_clock(logging.ERROR, msg)
            self.notify_hb_app_with_timestamp(msg)
            return
        
        gridItem = self.grid_manager.grids[grid_index - 1]
        
        #place sell order if not already placed
        if (gridItem.order_id is None):
            gridItem.order_info = OrderCandidate(trading_pair=self.trading_pair, is_maker=True, order_type=OrderType.LIMIT,
                                            order_side=TradeType.BUY, amount=gridItem.quantity, price=gridItem.price)
            gridItem.order_submitted = True
            gridItem.order_id = self.place_order(self.exchange, gridItem.order_info)

            msg = (f"Placed next Buy order at index {grid_index - 1}")
            self.log_with_clock(logging.INFO, msg)
            self.notify_hb_app_with_timestamp(msg)
        else:
            msg = (f"Buy order already placed at index {grid_index - 1}")
            self.log_with_clock(logging.INFO, msg)
            self.notify_hb_app_with_timestamp(msg)
            

    def place_order(self, connector_name: str, order: OrderCandidate) -> str:
        if order.order_side == TradeType.SELL:
            return self.sell(connector_name=connector_name, trading_pair=order.trading_pair, amount=order.amount,
                      order_type=order.order_type, price=order.price)
        elif order.order_side == TradeType.BUY:
            return self.buy(connector_name=connector_name, trading_pair=order.trading_pair, amount=order.amount,
                     order_type=order.order_type, price=order.price)

    def format_status(self) -> str:
        """
         Displays the status of the fixed grid strategy
         Returns status of the current strategy on user balances and current active orders.
         """
        if not self.ready_to_trade:
            return "Market connectors are not ready."

        lines = []
        warning_lines = []
        warning_lines.extend(self.network_warning(self.get_market_trading_pair_tuples()))

        balance_df = self.get_balance_df()
        lines.extend(["", "  Balances:"] + ["    " + line for line in balance_df.to_string(index=False).split("\n")])

        # Add grid information
        grid_df = map_df_to_str(self.grid_manager.generate_data_frame())
        lines.extend(["", "  Grid:"] + ["    " + line for line in grid_df.to_string(index=False).split("\n")])

        try:
            df = self.active_orders_df()
            lines.extend(["", "  Orders:"] + ["    " + line for line in df.to_string(index=False).split("\n")])
        except ValueError:
            lines.extend(["", "  No active maker orders."])

        warning_lines.extend(self.balance_warning(self.get_market_trading_pair_tuples()))
        if len(warning_lines) > 0:
            lines.extend(["", "*** WARNINGS ***"] + warning_lines)
        return "\n".join(lines)

    def cancel_active_orders(self):
        """
        Cancels active orders
        """
        for order in self.get_active_orders(connector_name=self.exchange):
            self.cancel(self.exchange, order.trading_pair, order.client_order_id)
