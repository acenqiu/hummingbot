from hummingbot.core.api_throttler.data_types import RateLimit

EXCHANGE_NAME = "defund"
CLIENT_ID_PREFIX = "defund"
MAX_ID_LEN = 32

DEFAULT_DOMAIN = ""

REST_URL = "https://beta-api.defund.io/external/"

# Public API endpoints
EXCHANGE_INFO_PATH_URL = "automation_orders/exchange_info"
FUND_INFO_PATH_URL = "funds/0xCe9ab1a2C75447451B2E5c9639d4640B6c50043E"
PING_PATH_URL = "/ping"


RATE_LIMITS = [
  RateLimit(EXCHANGE_INFO_PATH_URL, limit=10, time_interval=60),
  RateLimit(FUND_INFO_PATH_URL, limit=10, time_interval=60)
]