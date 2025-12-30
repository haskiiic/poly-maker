from data_updater.trading_utils import approveContracts

print("Starting approval process...")
try:
    approveContracts()
    print("Approval process finished successfully.")
except Exception as e:
    print(f"Approval process failed: {e}")

