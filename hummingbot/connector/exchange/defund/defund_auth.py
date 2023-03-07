from hummingbot.core.web_assistant.auth import AuthBase
from hummingbot.core.web_assistant.connections.data_types import RESTRequest, WSJSONRequest

class DefundAuth(AuthBase):
    def __init__(self, api_key: str, secret_key: str):
        self.api_key: str = api_key
        self.secret_key: str = secret_key

    async def rest_authenticate(self, request: RESTRequest) -> RESTRequest:
        return request # pass-through

    async def ws_authenticate(self, request: WSJSONRequest) -> WSJSONRequest:
        return request  # pass-through