import hashlib
import json
import uuid
from collections import OrderedDict
from typing import Any, Dict
from urllib.parse import urlencode

from hummingbot.connector.time_synchronizer import TimeSynchronizer
from hummingbot.core.web_assistant.auth import AuthBase
from hummingbot.core.web_assistant.connections.data_types import RESTMethod, RESTRequest, WSRequest


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

    async def rest_authenticate(self, request: RESTRequest) -> RESTRequest:
        """
        Adds the server time and the signature to the request, required for authenticated interactions. It also adds
        the required parameter in the request header.
        :param request: the request to be configured for authenticated interaction
        """
        hash = hashlib.sha512()

        if request.method == RESTMethod.POST:
            hash.update(urlencode(json.loads(request.data)).encode())
        else:
            hash.update(urlencode(request.params).encode())

        query_hash = hash.hexdigest()

        timestamp = int(self._time_provider.time() * 1e3)

        payload = {
            'access_key': self.api_key,
            'nonce': str(uuid.uuid4()),
            'timestamp': timestamp,
            'query_hash': query_hash,
            'query_hash_alg': 'SHA512',
        }

        jwt_token = jwt.encode(payload, self._secret_key)
        authorization_token = 'Bearer {}'.format(jwt_token)

        headers = {}
        if request.headers is not None:
            headers.update(request.headers)
        headers.update({'Authorization': authorization_token})
        request.headers = headers


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