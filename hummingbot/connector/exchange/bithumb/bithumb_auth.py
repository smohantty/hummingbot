import hashlib
import hmac
import json
import time
import uuid
from typing import Dict

import jwt

from hummingbot.connector.time_synchronizer import TimeSynchronizer
from hummingbot.core.web_assistant.auth import AuthBase
from hummingbot.core.web_assistant.connections.data_types import RESTRequest, WSRequest


class BithumbAuth(AuthBase):
    def __init__(self,
                 api_key: str,
                 secret_key: str,
                 time_provider: TimeSynchronizer):
        self._api_key = api_key
        self._secret_key = secret_key
        self._time_provider = time_provider

    def _generate_signature(self, params: Dict) -> str:
        """
        Generates authentication signature for API requests
        """
        encoded_params = json.dumps(params).encode()
        signature = hmac.new(self._secret_key.encode(),
                             encoded_params,
                             hashlib.sha512).hexdigest()
        return signature

    async def rest_authenticate(self, request: RESTRequest) -> RESTRequest:
        """
        Adds authentication to REST request
        """
        headers = {
            "Api-Key": self._api_key,
            "Api-Sign": self._generate_signature(request.params),
            "Api-Nonce": str(int(time.time() * 1000))
        }
        request.headers = headers
        return request

    async def ws_authenticate(self, request: WSRequest) -> WSRequest:
        """
        Adds authentication to WebSocket request
        """
        nonce = str(uuid.uuid4())
        timestamp = str(int(time.time() * 1000))

        payload = {
            "apiKey": self._api_key,
            "nonce": nonce,
            "timestamp": timestamp
        }

        token = jwt.encode(payload, self._secret_key, algorithm="HS256")

        request.payload["token"] = token
        return request
