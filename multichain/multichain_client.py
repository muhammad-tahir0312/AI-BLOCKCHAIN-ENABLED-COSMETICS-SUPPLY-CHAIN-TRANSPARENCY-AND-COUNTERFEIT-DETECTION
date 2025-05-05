import requests
import json
import base64
from typing import Any, Dict, List, Optional

class MultiChainClient:
    def __init__(self,
                 rpc_user: str,
                 rpc_password: str,
                 rpc_host: str = "172.24.160.1",
                 rpc_port: int  =  7188,
                 chain_name: str = "cosmeticsChain"):
        self.url = f"http://{rpc_host}:{rpc_port}"
        auth_str = f"{rpc_user}:{rpc_password}".encode()
        self.auth = base64.b64encode(auth_str).decode()

    def _rpc(self, method: str, params: List[Any] = []) -> Any:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Basic {self.auth}"
        }
        payload = {
            "method": method,
            "params": params,
            "id": "python-client",
            "chain_name": None
        }
        resp = requests.post(self.url, data=json.dumps(payload), headers=headers)
        resp.raise_for_status()
        result = resp.json()
        if result.get("error"):
            raise Exception(result["error"])
        return result["result"]

    def publish(self, stream: str, key: str, data: Dict[str, Any]) -> str:
        """Publish JSON data (auto‐hex‐encoded) under a given key."""
        hex_data = data if isinstance(data, str) else json.dumps(data)
        hex_data = hex_data.encode().hex()
        return self._rpc("publish", [stream, key, hex_data])

    def list_stream_key_items(self,
                              stream: str,
                              key: str,
                              count: int = 100) -> List[Dict[str,Any]]:
        """Retrieve up to `count` items for a given key."""
        return self._rpc("liststreamkeyitems", [stream, key, False, count])

    def list_stream_items(self, stream: str) -> List[Dict[str,Any]]:
        """Retrieve all items in a stream."""
        return self._rpc("liststreamitems", [stream, False, 1000])
