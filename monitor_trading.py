import os

from dotenv import load_dotenv
from py_clob_client.client import ClobClient
from py_clob_client.constants import POLYGON

load_dotenv()


def monitor_status():
    host = "https://clob.polymarket.com"
    key = os.getenv("PK")
    chain_id = POLYGON

    if key is None:
        print("Error: PK not found")
        return

    try:
        print("\n--- Connecting to Polymarket ---")
        client = ClobClient(host, key=key, chain_id=chain_id)
        api_creds = client.create_or_derive_api_creds()
        client.set_api_creds(api_creds)

        # 1. Check Open Orders (当前挂单)
        print("\n=== 📋 Open Orders (当前挂单) ===")
        orders = client.get_orders()

        if not orders:
            print("No open orders found.")
        else:
            for order in orders:
                print(f"ID: {order['id']}")
                print(f"  Asset: {order['asset_id']}")
                print(
                    f"  Side: {order['side']} | Price: {order['price']} | Size: {order['original_size']}"
                )
                print(f"  Matched: {order['size_matched']} (Filled)")
                print("-" * 30)

        # 2. Check Recent Trades (成交记录)
        print("\n=== 🤝 Recent Trades (最近成交) ===")
        # Note: Polymarket API might not have a direct simple "my trades" endpoint in the basic client
        # that shows history easily without iterating markets or using specific params.

        try:
            # Using specific params for trades can be tricky, let's try a general fetch if supported
            # or we look at positions to infer current holding status.
            print("Fetching trades... (This might take a moment)")

            # Since get_trades might not support maker_address directly in this version of the lib,
            # we'll skip the history part or implement a more robust fetch if needed.
            # For now, let's rely on positions and orders which are most important for "current" status.
            print("Note: To view historical trades, please visit PolygonScan.")
            print(
                "      https://polygonscan.com/address/"
                + client.get_address()
                + "#tokentxns"
            )

        except Exception as e:
            print(f"Could not fetch trades directly: {e}")

        # 3. Check Current Positions (当前持仓)
        print("\n=== 💼 Current Positions (当前持仓) ===")
        import requests
        from web3 import Web3

        from poly_data.abis import erc20_abi

        # --- Helper to get USDC Balance ---
        def get_usdc_balance(address):
            try:
                web3 = Web3(Web3.HTTPProvider("https://polygon-rpc.com"))
                usdc_contract = web3.eth.contract(
                    address="0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174", abi=erc20_abi
                )
                balance = usdc_contract.functions.balanceOf(
                    Web3.to_checksum_address(address)
                ).call()
                return balance / 10**6
            except Exception as e:
                print(f"Error fetching USDC balance: {e}")
                return 0.0

        # --- Helper to Estimate Historical PnL ---
        def estimate_historical_pnl(address):
            try:
                # Gamma API for activity
                url = "https://gamma-api.polymarket.com/events"
                params = {"user": address, "limit": 100, "offset": 0}
                # Note: limit 100 might not cover full history for active traders

                resp = requests.get(url, params=params)
                if resp.status_code != 200:
                    return None

                events = resp.json()
                money_in = 0  # Buys
                money_out = 0  # Sells + Redemptions

                for e in events:
                    # Very rough approximation based on event types
                    # This is complex because 'value' fields vary.
                    # We will skip detailed calculation here to avoid misleading data
                    # and focus on Total Equity instead.
                    pass
                return None
            except:
                return None

        account = client.get_address()
        usdc_balance = get_usdc_balance(account)

        res = requests.get(f"https://data-api.polymarket.com/positions?user={account}")

        if res.status_code == 200:
            positions = res.json()
            total_portfolio_value = 0.0

            if not positions:
                print("No active positions.")
            else:
                print(
                    f"{'Title':<60} | {'Size':>10} | {'CurPrice':>8} | {'Value ($)':>10} | {'AvgPrice':>8} | {'PnL %':>8}"
                )
                print("-" * 115)

                for pos in positions:
                    size = float(pos.get("size", 0))
                    if size > 0.1:  # Filter dust
                        title = pos.get("title", "Unknown Market")
                        cur_price = float(pos.get("curPrice", 0))
                        avg_price = float(pos.get("avgPrice", 0))

                        value = size * cur_price
                        total_portfolio_value += value

                        pnl_pct = (
                            ((cur_price - avg_price) / avg_price * 100)
                            if avg_price > 0
                            else 0
                        )

                        display_title = (
                            (title[:57] + "...") if len(title) > 57 else title
                        )

                        print(
                            f"{display_title:<60} | {size:>10.2f} | {cur_price:>8.3f} | {value:>10.2f} | {avg_price:>8.3f} | {pnl_pct:>8.2f}%"
                        )

            print("-" * 115)

            # --- FINAL SUMMARY ---
            print("\n=== 💰 Account Summary (账户总览) ===")
            print(f"1. USDC Balance (可用余额):   ${usdc_balance:.2f}")
            print(f"2. Portfolio Value (持仓市值): ${total_portfolio_value:.2f}")
            print("-" * 40)
            print(
                f"🟢 Total Equity (总资产):     ${(usdc_balance + total_portfolio_value):.2f}"
            )
            print("(提示: 用 '总资产' 减去你的 '总入金本金' 即为你的总盈亏)")

        else:
            print("Failed to fetch positions.")

    except Exception as ex:
        print(f"Error: {ex}")


if __name__ == "__main__":
    monitor_status()
