import os
import json
from dotenv import load_dotenv
from py_clob_client.client import ClobClient
from py_clob_client.constants import POLYGON

load_dotenv()

def cancel_all_orders():
    host = "https://clob.polymarket.com"
    key = os.getenv("PK")
    chain_id = POLYGON
    
    if key is None:
        print("Error: Environment variable 'PK' cannot be found")
        return

    try:
        print("Initializing ClobClient...")
        client = ClobClient(host, key=key, chain_id=chain_id)
        api_creds = client.create_or_derive_api_creds()
        client.set_api_creds(api_creds)
        
        print("Fetching open orders...")
        orders = client.get_orders()
        
        if not orders:
            print("No open orders found.")
            return

        print(f"Found {len(orders)} open orders. Cancelling them now...")
        
        cancelled_count = 0
        for order in orders:
            order_id = order.get('id')
            asset_id = order.get('asset_id')
            side = order.get('side')
            price = order.get('price')
            size = order.get('original_size')
            
            print(f"Cancelling order: {side} {size} of asset {asset_id} at price {price}")
            
            try:
                # Cancel order by ID
                client.cancel(order_id)
                cancelled_count += 1
                print(f"Successfully cancelled order {order_id}")
            except Exception as e:
                print(f"Failed to cancel order {order_id}: {e}")
                
        print(f"\nSummary: {cancelled_count} orders cancelled out of {len(orders)} found.")
        print("Funds locked in these orders should now be returned to your wallet balance.")
        
    except Exception as ex: 
        print(f"Error occurred: {ex}")

if __name__ == "__main__":
    cancel_all_orders()

