import json
import os

from dotenv import load_dotenv
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware

load_dotenv()


def check_funds_location():
    pk = os.getenv("PK")

    # Setup Web3
    web3 = Web3(Web3.HTTPProvider("https://polygon-rpc.com"))
    web3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

    account = web3.eth.account.from_key(pk)
    target_address = account.address
    print(f"Checking address: {target_address}")

    # Contracts
    usdc_e_address = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"
    ctf_address = "0x4D97DCd97eC945f40cF65F87097ACe5EA0476045"

    # Check USDC.e Balance
    with open("data_updater/erc20ABI.json", "r") as file:
        erc20_abi = json.load(file)
    usdc_e_contract = web3.eth.contract(address=usdc_e_address, abi=erc20_abi)

    usdc_balance = usdc_e_contract.functions.balanceOf(target_address).call() / 10**6
    print(f"\n💰 Wallet USDC.e Balance: {usdc_balance:.2f}")

    # Check Active Orders (Funds locked in orders)
    try:
        from py_clob_client.client import ClobClient
        from py_clob_client.constants import POLYGON

        host = "https://clob.polymarket.com"
        client = ClobClient(host, key=pk, chain_id=POLYGON)
        api_creds = client.create_or_derive_api_creds()
        client.set_api_creds(api_creds)

        orders = client.get_orders()
        locked_in_orders = 0
        print(f"\n📋 Active Orders: {len(orders)}")
        for order in orders:
            # Assuming buy orders lock funds: price * size
            if order["side"] == "BUY":
                amount = float(order["price"]) * float(
                    order["original_size"]
                )  # Approximation
                locked_in_orders += amount
                print(
                    f"  - Buy Order: {order['size_matched']}/{order['original_size']} @ {order['price']} (Locked ~{amount:.2f} USDC)"
                )

        print(f"🔒 Total Locked in Orders: ~{locked_in_orders:.2f} USDC")

    except Exception as e:
        print(f"Could not check orders: {e}")

    # Check Positions (Funds converted to shares)
    try:
        import requests

        res = requests.get(
            f"https://data-api.polymarket.com/positions?user={target_address}"
        )
        if res.status_code == 200:
            positions = res.json()
            pos_value = 0
            print("\n📈 Positions:")
            for pos in positions:
                # Assuming API returns current value or similar, verifying structure
                size = float(pos.get("size", 0))
                # Need to fetch price for accurate value, but listing size for now
                asset = pos.get("asset")
                print(f"  - {asset}: {size} shares")
                # Rough estimation if price not available in this endpoint easily without more calls
                # For now just confirming existence

            # Alternative value endpoint check
            val_res = requests.get(
                f"https://data-api.polymarket.com/value?user={target_address}"
            )
            if val_res.status_code == 200:
                # The value endpoint returns a straight JSON object usually, checking structure
                data = val_res.json()
                # If it's a list, handle it, otherwise dict
                if isinstance(data, list):
                    print(f"DEBUG: Value endpoint returned list: {data}")
                else:
                    pos_value = float(data.get("value", 0))

            print(f"📈 Portfolio Value (API): {pos_value:.2f} USDC")
        else:
            print("\nCould not fetch positions.")
    except Exception as e:
        print(f"Error checking positions: {e}")

    total_accounted = (
        usdc_balance
        + (locked_in_orders if "locked_in_orders" in locals() else 0)
        + (pos_value if "pos_value" in locals() else 0)
    )
    print(f"\n💵 Total Accounted Value: ~{total_accounted:.2f} USDC")


if __name__ == "__main__":
    check_funds_location()
