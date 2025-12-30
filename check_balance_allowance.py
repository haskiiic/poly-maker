import os
import json
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware
from dotenv import load_dotenv

load_dotenv()

def check_status():
    pk = os.getenv("PK")
    browser_address = os.getenv("BROWSER_ADDRESS")
    
    if not pk:
        print("Error: PK not found in environment variables")
        return

    # Setup Web3
    web3 = Web3(Web3.HTTPProvider("https://polygon-rpc.com"))
    web3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
    
    # Signer Account (from PK)
    account = web3.eth.account.from_key(pk)
    signer_address = account.address
    print(f"Signer Address (from PK): {signer_address}")
    
    # Funder Address (from Env)
    print(f"Funder Address (BROWSER_ADDRESS): {browser_address}")
    
    if not browser_address:
        print("Warning: BROWSER_ADDRESS is not set. Assuming Signer is Funder.")
        target_address = signer_address
    else:
        target_address = Web3.to_checksum_address(browser_address)

    # USDC.e Contract (Bridged)
    usdc_e_address = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"
    # USDC Contract (Native)
    native_usdc_address = "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359"

    with open('data_updater/erc20ABI.json', 'r') as file:
        erc20_abi = json.load(file)
    
    usdc_e_contract = web3.eth.contract(address=usdc_e_address, abi=erc20_abi)
    native_usdc_contract = web3.eth.contract(address=native_usdc_address, abi=erc20_abi)

    # Check Balances
    matic_balance = web3.eth.get_balance(target_address) / 10**18
    usdc_e_balance = usdc_e_contract.functions.balanceOf(target_address).call() / 10**6
    native_usdc_balance = native_usdc_contract.functions.balanceOf(target_address).call() / 10**6
    
    print("\n--- Balances for Funder Address ---")
    print(f"Address: {target_address}")
    print(f"MATIC: {matic_balance:.4f}")
    print(f"USDC.e (Bridged): {usdc_e_balance:.2f}")
    print(f"USDC (Native): {native_usdc_balance:.2f}")
    
    if target_address != signer_address:
        signer_matic = web3.eth.get_balance(signer_address) / 10**18
        print(f"\n--- Balances for Signer Address ---")
        print(f"Address: {signer_address}")
        print(f"MATIC: {signer_matic:.4f} (Used for Gas)")

    # Check Allowances (checking against USDC.e as that's what Polymarket uses)
    exchange_address = "0x4bFb41d5B3570DeFd03C39a9A4D8dE6Bd8B8982E"
    allowance = usdc_e_contract.functions.allowance(target_address, exchange_address).call()
    
    print("\n--- Allowance Check (USDC.e) ---")
    print(f"Spender: Polymarket Exchange ({exchange_address})")
    print(f"Allowed Amount: {allowance / 10**6:.2f} USDC.e")
    
    if allowance == 0:
        print("❌ Funder has NOT approved the Exchange for USDC.e.")
    else:
        print("✅ Funder has approved the Exchange for USDC.e.")
        
    if usdc_e_balance < 1:
        print("\n❌ Funder has insufficient USDC.e.")
        if native_usdc_balance > 1:
            print(f"⚠️  You have {native_usdc_balance:.2f} Native USDC, but Polymarket uses USDC.e (Bridged).")
            print("💡 You need to swap your Native USDC to USDC.e on Uniswap or another DEX.")

if __name__ == "__main__":
    check_status()

