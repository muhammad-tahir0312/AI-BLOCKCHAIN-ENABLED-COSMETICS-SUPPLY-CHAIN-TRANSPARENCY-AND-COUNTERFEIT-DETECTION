# main_blockchain.py

from datetime import datetime
from multichain_client import MultiChainClient

# Load your AI model from previous steps
from your_ai_module import predict_counterfeit

# 1. Initialize client
client = MultiChainClient(
    rpc_user="multichainrpc",
    rpc_password="<your‐password>",
    rpc_host="127.0.0.1",
    rpc_port=8571,
    chain_name="cosmeticsChain"
)

# 2. Register a new product
def register_product(product_id: str, metadata: dict):
    """ metadata: {name, category, price, ingredients, timestamp} """
    client.publish("products", product_id, metadata)
    print(f"[Chain] Registered product {product_id}")

# 3. Log a shipment event
def log_shipment(product_id: str, location: dict, stage: str):
    event = {
        "product_id": product_id,
        "stage": stage,            # e.g. "manufacture","transit","QC","delivery"
        "location": location,      # {"lat":..., "lng":...}
        "timestamp": datetime.utcnow().isoformat()
    }
    client.publish("shipments", product_id, event)
    print(f"[Chain] Shipment event for {product_id}: {stage}")

# 4. Analyze & Flag anomalies
def analyze_and_flag(product_id: str, metadata: dict):
    """Use your existing AI model to predict counterfeit."""
    result = predict_counterfeit(
        metadata["product_name"],
        metadata["ingredients"],
        metadata["price"],
        metadata["category"]
    )
    if result["is_counterfeit"] or result["probability"] > 0.5:
        alert = {
            "product_id": product_id,
            "score": result["probability"],
            "timestamp": datetime.utcnow().isoformat()
        }
        client.publish("anomalies", product_id, alert)
        print(f"[Chain] Anomaly flagged for {product_id}: {alert['score']:.2f}")
    else:
        print(f"[AI] {product_id} passed: {result['probability']:.2f}")

# 5. Consumer verification
def verify_product(product_id: str):
    # Fetch registration
    prod_hist = client.list_stream_key_items("products", product_id)
    ship_hist = client.list_stream_key_items("shipments", product_id)
    anomalies = client.list_stream_key_items("anomalies", product_id)
    # Decode hex data
    def decode(item):
        return bytes.fromhex(item["data"]).decode()
    print("=== Product History ===")
    for item in prod_hist:
        print("Registered:", decode(item))
    print("=== Shipments ===")
    for item in ship_hist:
        print("Event:", decode(item))
    print("=== Anomalies ===")
    for item in anomalies:
        print("Alert:", decode(item))

# 6. Example end‐to‐end sequence
if __name__ == "__main__":
    # Suppose you have a product dict from your test set:
    product = {
        "product_id": "SKU12345",
        "product_name": "HydraBoost Serum",
        "category": "moisturizer",
        "price": 29.99,
        "ingredients": "water,glycerin,dimethicone,phenoxyethanol,...",
        "timestamp": datetime.utcnow().isoformat()
    }

    # Register on chain
    register_product(product["product_id"], product)

    # Log some shipments
    log_shipment(product["product_id"], {"lat":24.86,"lng":67.01}, "manufacture")
    log_shipment(product["product_id"], {"lat":23.02,"lng":72.45}, "transit")

    # Run AI check & flag if needed
    analyze_and_flag(product["product_id"], product)

    # Later, consumer verification
    verify_product(product["product_id"])
