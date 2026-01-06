import os
import json
import time
from dotenv import load_dotenv
from py_clob_client.client import ClobClient
from py_clob_client.clob_types import OrderArgs
from py_clob_client.constants import POLYGON
from web3 import Web3
import requests

load_dotenv()

def sell_all():
    host = "https://clob.polymarket.com"
    key = os.getenv("PK")
    chain_id = POLYGON
    
    if key is None:
        print("Error: PK not found")
        return

    try:
        print("Initializing Client...")
        client = ClobClient(host, key=key, chain_id=chain_id)
        api_creds = client.create_or_derive_api_creds()
        client.set_api_creds(api_creds)
        
        # Derive address from PK just to be safe
        web3 = Web3()
        account = web3.eth.account.from_key(key).address
        print(f"Checking positions for: {account}")
        
        res = requests.get(f'https://data-api.polymarket.com/positions?user={account}')
        if res.status_code != 200:
            print("Failed to fetch positions API")
            return
            
        positions = res.json()
        if not positions:
            print("No positions found.")
            return

        print(f"Found {len(positions)} positions. Starting liquidation...")

        for pos in positions:
            asset_id = pos.get('asset')
            size = float(pos.get('size', 0))
            
            if size < 1: # Ignore dust
                continue
                
            print(f"\nProcessing Asset: {asset_id}, Size: {size}")
            
            # Get Orderbook to find best bid
            orderbook = client.get_order_book(asset_id)
            if not orderbook.bids:
                print("No bids available! Cannot sell.")
                continue
                
            # Sell at best bid to ensure execution
            best_bid = float(orderbook.bids[0].price)
            print(f"Best Bid Price: {best_bid}")
            
            # Create Sell Order
            order_args = OrderArgs(
                price=best_bid,
                size=size,
                side="SELL",
                token_id=asset_id
            )
            
            try:
                signed_order = client.create_order(order_args)
                resp = client.post_order(signed_order)
                print(f"✅ SELL Order Sent! ID: {resp.get('orderID')}")
            except Exception as e:
                print(f"❌ Sell failed: {e}")
                
            time.sleep(1) # Prevent rate limit

        print("\nAll positions processed. Check your USDC balance.")

    except Exception as ex: 
        print(f"Critical Error: {ex}")

if __name__ == "__main__":
    sell_all()

