from typing import Dict, Optional
import json
import httpx
import os
from dotenv import load_dotenv
from loguru import logger
from fastapi import HTTPException
from datetime import datetime


load_dotenv()

import logging

# Configure the logger
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class BlockchainService:
    def __init__(self):
        self.rpc_url = f"http://{os.getenv('MULTICHAIN_HOST', 'localhost')}:{os.getenv('MULTICHAIN_PORT', '7189')}"
        self.headers = {'Content-Type': 'application/json'}
        
        # Basic Auth for MultiChain
        rpc_user = os.getenv('MULTICHAIN_USER', 'multichainrpc')
        rpc_pass = os.getenv('MULTICHAIN_PASS', '')
        self.auth = (rpc_user, rpc_pass)

        self.initialized = False
        logger.error(f"I am called with {self.rpc_url}")

    async def _rpc_call(self, method: str, params: list = None) -> Dict:
        """Make RPC call to MultiChain node with better error handling"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                logger.debug(f"Making RPC call: {method} with params {params}")
                response = await client.post(
                    self.rpc_url,
                    json={
                        'method': method,
                        'params': params or [],
                        'id': 1,
                    },
                    headers=self.headers,
                    auth=self.auth
                )
                
                logger.debug(f"RPC response: {response.text}")  # Log full response text
                if response.status_code == 200:
                    result = response.json()
                    if 'error' in result and result['error']:
                        logger.error(f"RPC Error: {result['error']}")
                        return None
                    return result['result']
                else:
                    logger.error(f"HTTP Error: {response.status_code} - {response.text}")
                    return None
        except httpx.RequestError as e:
            logger.error(f"Request error occurred: {e}")
        except Exception as e:
            logger.error(f"Unexpected error occurred: {e}")
        return None

    async def init_stream(self) -> bool:
        """Initialize the products stream with better error handling"""
        try:
            if self.initialized:
                return True

            # Test connection first
            info = await self._rpc_call('getinfo')
            if not info:
                logger.warning("Could not connect to MultiChain. Running in offline mode.")
                return False

            # Check if stream exists
            streams = await self._rpc_call('liststreams')
            if streams is None:
                logger.warning("Could not list streams. Running in offline mode.")
                return False

            if not any(s['name'] == 'products' for s in streams):
                result = await self._rpc_call('create', ['stream', 'products', True])
                if result:
                    await self._rpc_call('subscribe', ['products'])
                    logger.info("Products stream created and subscribed")
                else:
                    logger.warning("Failed to create products stream")
                    return False

            self.initialized = True
            return True

        except Exception as e:
            logger.error(f"Stream initialization failed: {str(e)}")
            return False
        
    async def store_product(self, product_data: Dict) -> Optional[str]:
        """
        Store product data in blockchain
        Returns: Transaction ID if successful, None otherwise
        """
        try:
            # Prepare data for blockchain storage
            blockchain_data = {
                "product_id": product_data.get("id"),
                "name": product_data.get("product_name"),
                "supplier_id": product_data.get("supplier_id"),
                "timestamp": datetime.utcnow().isoformat(),
                "price": str(product_data.get("price")),
                "ingredients": product_data.get("ingredients"),
                "category": product_data.get("category"),
                "label": product_data.get("label")
            }

            # Convert data to hex for blockchain storage
            data_hex = json.dumps(blockchain_data).encode('utf-8').hex()

            # Store in blockchain using streams
            key = f"product_{product_data.get('id')}"
            result = await self._rpc_call(
                'publish', 
                [
                    'products',  # stream name
                    key,         # key
                    data_hex     # data in hex
                ]
            )

            if result:
                logger.info(f"Product stored in blockchain. TxID: {result}")
                return result
            else:
                logger.error("Failed to store product in blockchain")
                return None

        except Exception as e:
            logger.error(f"Error storing product in blockchain: {str(e)}")
            return None