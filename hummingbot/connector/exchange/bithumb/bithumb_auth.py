import hashlib
import json
import uuid
from collections import OrderedDict
from typing import Any, Dict, Optional
from urllib.parse import urlencode
import logging


from hummingbot.connector.time_synchronizer import TimeSynchronizer
from hummingbot.core.web_assistant.auth import AuthBase
from hummingbot.core.web_assistant.connections.data_types import RESTMethod, RESTRequest, WSRequest


import jwt

from hummingbot.connector.time_synchronizer import TimeSynchronizer
from hummingbot.core.web_assistant.auth import AuthBase
from hummingbot.core.web_assistant.connections.data_types import RESTRequest, WSRequest
from hummingbot.logger import HummingbotLogger


class BithumbAuth(AuthBase):
    _logger: Optional[HummingbotLogger] = None

    def __init__(self,
                 api_key: str,
                 secret_key: str,
                 time_provider: TimeSynchronizer):
        self._api_key = api_key
        self._secret_key = secret_key
        self._time_provider = time_provider

    @classmethod
    def logger(cls) -> HummingbotLogger:
        if cls._logger is None:
            cls._logger = logging.getLogger(HummingbotLogger.logger_name_for_class(cls))
        return cls._logger

    async def rest_authenticate(self, request: RESTRequest) -> RESTRequest:
        """
        Adds the server time and the signature to the request, required for authenticated interactions. It also adds
        the required parameter in the request header.
        :param request: the request to be configured for authenticated interaction
        """
        self.logger().error(f"rest_authenticate method = {request.method}")
        self.logger().error(f"rest_authenticate data = {request.data}")
        self.logger().error(f"rest_authenticate params = {request.params}")

        timestamp = int(self._time_provider.time() * 1e3)
        payload = {
            'access_key': self._api_key,
            'nonce': str(uuid.uuid4()),
            'timestamp': timestamp,
        }

        if request.method == "POST" and request.data:
            query_string = urlencode(request.data)
        elif request.method == "GET" and request.params:
            query_string = urlencode(request.params)
        else:
            query_string = None  # No data to hash

        if query_string is not None:
            hash = hashlib.sha512()
            hash.update(query_string.encode("utf-8"))
            query_hash = hash.hexdigest()

            payload["query_hash"] = query_hash
            payload["query_hash_alg"] = "SHA512"

        jwt_token = jwt.encode(payload, self._secret_key)

        request.headers["Authorization"] = f"Bearer {jwt_token}"

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