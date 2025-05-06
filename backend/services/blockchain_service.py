from typing import Dict, List, Optional
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
        self.rpc_url = f"http://{os.getenv('MULTICHAIN_HOST', 'localhost')}:{os.getenv('MULTICHAIN_PORT', '7188')}"
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
        """Initialize both products and orders streams"""
        try:
            if self.initialized:
                return True

            # Test connection first
            info = await self._rpc_call('getinfo')
            if not info:
                logger.warning("Could not connect to MultiChain. Running in offline mode.")
                return False

            # Check if streams exist
            streams = await self._rpc_call('liststreams')
            if streams is None:
                logger.warning("Could not list streams. Running in offline mode.")
                return False

            # Initialize products stream
            if not any(s['name'] == 'products' for s in streams):
                result = await self._rpc_call('create', ['stream', 'products', True])
                if result:
                    await self._rpc_call('subscribe', ['products'])
                    logger.info("Products stream created and subscribed")
                else:
                    logger.warning("Failed to create products stream")
                    return False

            # Initialize orders stream
            if not any(s['name'] == 'orders' for s in streams):
                result = await self._rpc_call('create', ['stream', 'orders', True])
                if result:
                    await self._rpc_call('subscribe', ['orders'])
                    logger.info("Orders stream created and subscribed")
                else:
                    logger.warning("Failed to create orders stream")
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
        
    async def store_order(self, order_data: dict) -> Optional[str]:
        """Store order data in blockchain"""
        try:
            # Clean and prepare order data
            clean_data = {}
            for k, v in order_data.items():
                if not k.startswith('_'):
                    if isinstance(v, datetime):
                        clean_data[k] = v.isoformat()
                    elif isinstance(v, (int, float, bool, str)):
                        clean_data[k] = v
                    else:
                        clean_data[k] = str(v)
            
            blockchain_data = {
                'type': 'order',
                'action': 'create',
                'data': clean_data,
                'timestamp': datetime.utcnow().isoformat()
            }

            # Convert to JSON string first, then to hex
            json_str = json.dumps(blockchain_data)
            data_hex = json_str.encode('utf-8').hex()
            
            # Store in blockchain using orders stream
            key = f"order_{clean_data.get('id')}"
            result = await self._rpc_call(
                'publish',
                ['orders', key, data_hex]
            )

            if result:
                logger.info(f"Order stored in blockchain. TxID: {result}")
                return result
            
            logger.error("Failed to store order in blockchain")
            return None

        except Exception as e:
            logger.error(f"Failed to store order in blockchain: {str(e)}")
            return None

    async def update_order(self, order_data: dict) -> Optional[str]:
        """Update order data in blockchain"""
        try:
            # Clean and prepare order data
            clean_data = {}
            for k, v in order_data.items():
                if not k.startswith('_'):
                    if isinstance(v, datetime):
                        clean_data[k] = v.isoformat()
                    elif isinstance(v, (int, float, bool, str)):
                        clean_data[k] = v
                    else:
                        clean_data[k] = str(v)
            
            blockchain_data = {
                'type': 'order',
                'action': 'update',
                'data': clean_data,
                'timestamp': datetime.utcnow().isoformat()
            }

            # Convert to JSON string first, then to hex
            json_str = json.dumps(blockchain_data)
            data_hex = json_str.encode('utf-8').hex()
            
            # Store in orders stream with unique key
            key = f"order_{clean_data.get('id')}_update_{datetime.utcnow().timestamp()}"
            result = await self._rpc_call(
                'publish',
                ['orders', key, data_hex]
            )

            if result:
                logger.info(f"Order update stored in blockchain. TxID: {result}")
                return result
            
            logger.error("Failed to store order update in blockchain")
            return None

        except Exception as e:
            logger.error(f"Failed to update order in blockchain: {str(e)}")
            return None
        
    async def get_order_history(self, order_identifier: str) -> List[dict]:
        """
        Get order history from blockchain
        Args:
            order_identifier: Can be either an order ID (int) or transaction hash (str)
        """
        try:
            all_items = []
            
            # Check if identifier is a transaction hash
            if isinstance(order_identifier, str) and len(order_identifier) == 64:
                # Get transaction directly
                tx_data = await self._rpc_call(
                    'gettxoutdata',
                    [order_identifier]
                )
                if tx_data:
                    all_items = [{'data': tx_data, 'txid': order_identifier}]
            else:
                # Treat as order ID
                order_id = str(order_identifier)
                # Get original order
                items = await self._rpc_call(
                    'liststreamkeyitems',
                    ['orders', f"order_{order_id}"]
                ) or []
                
                # Get updates
                update_items = await self._rpc_call(
                    'liststreamkeyitems',
                    ['orders', f"order_{order_id}_update"]
                ) or []
                
                all_items = items + update_items

            if not all_items:
                logger.warning(f"No blockchain records found for identifier: {order_identifier}")
                return []

            order_history = []
            for item in all_items:
                try:
                    # Validate and decode data
                    if not item.get('data') or not isinstance(item.get('data'), str):
                        logger.warning(f"Invalid data format in item: {item}")
                        continue

                    data = bytes.fromhex(item['data']).decode('utf-8')
                    parsed_data = json.loads(data)

                    if not isinstance(parsed_data, dict):
                        logger.warning(f"Invalid parsed data structure: {parsed_data}")
                        continue

                    # Handle both direct transaction data and stream items
                    action = parsed_data.get('action', 'unknown')
                    details = parsed_data.get('data', parsed_data)  # Fall back to full data if no 'data' field

                    history_entry = {
                        'transaction_hash': str(item['txid']),
                        'timestamp': datetime.fromtimestamp(float(item.get('time', datetime.utcnow().timestamp()))).isoformat(),
                        'action': str(action),
                        'details': dict(details)
                    }
                    order_history.append(history_entry)

                except (ValueError, json.JSONDecodeError) as e:
                    logger.error(f"Data parsing error: {str(e)}")
                    continue
                except Exception as e:
                    logger.error(f"Unexpected error processing item: {str(e)}")
                    continue

            return sorted(order_history, key=lambda x: x['timestamp'])

        except Exception as e:
            logger.error(f"Failed to fetch order history: {str(e)}")
            return []