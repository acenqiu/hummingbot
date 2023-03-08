import asyncio
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

from bidict import bidict

from hummingbot.connector.constants import s_decimal_NaN
from hummingbot.connector.exchange.defund import (
    defund_constants as CONSTANTS,
    defund_utils,
    defund_web_utils as web_utils,
)
from hummingbot.connector.exchange.defund.defund_api_order_book_data_source import DefundAPIOrderBookDataSource
from hummingbot.connector.exchange.defund.defund_api_user_stream_data_source import DefundAPIUserStreamDataSource
from hummingbot.connector.exchange.defund.defund_auth import DefundAuth
from hummingbot.connector.exchange_py_base import ExchangePyBase
from hummingbot.connector.trading_rule import TradingRule
from hummingbot.connector.utils import TradeFillOrderDetails, combine_to_hb_trading_pair
from hummingbot.core.data_type.common import OrderType, TradeType
from hummingbot.core.data_type.in_flight_order import InFlightOrder, OrderUpdate, TradeUpdate
from hummingbot.core.data_type.order_book_tracker_data_source import OrderBookTrackerDataSource
from hummingbot.core.data_type.trade_fee import DeductedFromReturnsTradeFee, TokenAmount, TradeFeeBase
from hummingbot.core.data_type.user_stream_tracker_data_source import UserStreamTrackerDataSource
from hummingbot.core.event.events import MarketEvent, OrderFilledEvent
from hummingbot.core.utils.async_utils import safe_gather
from hummingbot.core.web_assistant.connections.data_types import RESTMethod
from hummingbot.core.web_assistant.web_assistants_factory import WebAssistantsFactory

if TYPE_CHECKING:
    from hummingbot.client.config.config_helpers import ClientConfigAdapter

s_logger = None

class DefundExchange(ExchangePyBase):
    
    web_utils = web_utils

    def __init__(self,
                 client_config_map: "ClientConfigAdapter",
                 defund_api_key: str,
                 defund_secret_key: str,
                 trading_pairs: Optional[List[str]] = None,
                 trading_required: bool = True,
                 ):
        self.api_key = defund_api_key
        self.secret_key = defund_secret_key
        self._trading_required = trading_required
        self._trading_pairs = trading_pairs
        
        super().__init__(client_config_map)

    @property
    def authenticator(self):
        return DefundAuth(self.api_key, self.secret_key)

    @property
    def name(self) -> str:
        return CONSTANTS.EXCHANGE_NAME

    @property
    def rate_limits_rules(self):
        return CONSTANTS.RATE_LIMITS

    @property
    def domain(self):
        return ""

    @property
    def client_order_id_max_length(self):
        return CONSTANTS.MAX_ID_LEN

    @property
    def client_order_id_prefix(self):
        return CONSTANTS.CLIENT_ID_PREFIX

    @property
    def trading_rules_request_path(self):
        return CONSTANTS.EXCHANGE_INFO_PATH_URL

    @property
    def trading_pairs_request_path(self):
        return CONSTANTS.EXCHANGE_INFO_PATH_URL

    @property
    def check_network_request_path(self):
        return CONSTANTS.PING_PATH_URL

    @property
    def trading_pairs(self):
        return self._trading_pairs

    @property
    def is_cancel_request_in_exchange_synchronous(self) -> bool:
        return False

    @property
    def is_trading_required(self) -> bool:
        return self._trading_required

    def supported_order_types(self):
        return [OrderType.LIMIT, OrderType.LIMIT_MAKER]

    async def get_all_pairs_prices(self) -> List[Dict[str, str]]:
        return []
    
    def _is_request_exception_related_to_time_synchronizer(self, request_exception: Exception):
        return False

    def _create_web_assistants_factory(self) -> WebAssistantsFactory:
        return web_utils.build_api_factory(
            throttler=self._throttler,
            time_synchronizer=self._time_synchronizer,
            auth=self._auth)

    def _create_order_book_data_source(self) -> OrderBookTrackerDataSource:
        return DefundAPIOrderBookDataSource(
            trading_pairs=self._trading_pairs,
            connector=self,
            api_factory=self._web_assistants_factory
        )

    def _create_user_stream_data_source(self) -> UserStreamTrackerDataSource:
        return DefundAPIUserStreamDataSource(
            auth=self._auth,
            connector=self,
            api_factory=self._web_assistants_factory)

    def _get_fee(self,
                 base_currency: str,
                 quote_currency: str,
                 order_type: OrderType,
                 order_side: TradeType,
                 amount: Decimal,
                 price: Decimal = s_decimal_NaN,
                 is_maker: Optional[bool] = None) -> TradeFeeBase:
        is_maker = order_type is OrderType.LIMIT_MAKER
        return DeductedFromReturnsTradeFee(percent=self.estimate_fee_pct(is_maker))

    def _initialize_trading_pair_symbols_from_exchange_info(self, exchange_info: Dict[str, Any]):
        mapping = bidict()
        self._set_trading_pair_symbol_map(mapping)

    async def _place_order(self,
                           order_id: str,
                           trading_pair: str,
                           amount: Decimal,
                           trade_type: TradeType,
                           order_type: OrderType,
                           price: Decimal,
                           **kwargs) -> Tuple[str, float]:
        return "", 0

    async def _place_cancel(self, order_id: str, tracked_order: InFlightOrder):
        """
        This implementation specific function is called by _cancel, and returns True if successful
        """
        return False

    async def _get_last_traded_price(self, trading_pair: str) -> float:
        return 0

    async def _update_balances(self):
        local_asset_names = set(self._account_balances.keys())
        remote_asset_names = set()

        fund_info = await self._api_request(
            path_url=CONSTANTS.FUND_INFO_PATH_URL,
            is_auth_required=True)

        balances = fund_info["tokenBalances"]
        for balance_entry in balances:
            asset_name = balance_entry["symbol"]
            free_balance = Decimal(balance_entry["balanceWithUnit"])
            total_balance = free_balance
            self._account_available_balances[asset_name] = free_balance
            self._account_balances[asset_name] = total_balance
            remote_asset_names.add(asset_name)

        asset_names_to_remove = local_asset_names.difference(remote_asset_names)
        for asset_name in asset_names_to_remove:
            del self._account_available_balances[asset_name]
            del self._account_balances[asset_name]

    async def _update_trading_rules(self):
        ...

    async def _format_trading_rules(self, raw_trading_pair_info: List[Dict[str, Any]]) -> List[TradingRule]:
        trading_rules = []
        return trading_rules

    async def _update_trading_fees(self):
        """
        Update fees information from the exchange
        """
        pass

    async def _request_order_update(self, order: InFlightOrder) -> Dict[str, Any]:
        return {}

    async def _request_order_fills(self, order: InFlightOrder) -> Dict[str, Any]:
        return {}

    async def _all_trade_updates_for_order(self, order: InFlightOrder) -> List[TradeUpdate]:
        trade_updates = []

        return trade_updates

    async def _request_order_status(self, tracked_order: InFlightOrder) -> OrderUpdate:
        raise NotImplementedError

    async def _user_stream_event_listener(self):
        raise NotImplementedError