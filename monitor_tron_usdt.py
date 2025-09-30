import os
import requests
import sys

# Get secrets from GitHub Actions
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
WALLET_ADDRESS = os.getenv("WALLET_ADDRESS")

# Tron USDT (TRC20) contract address
USDT_CONTRACT = "TXLAQ63Xg1NAzckPwKHvzw7CSEmLMEqcdj"

# TronGrid API
TRON_API = "https://apilist.tronscanapi.com/api/contract/events"

def send_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text}
    requests.post(url, data=payload)

def check_usdt_transactions():
    params = {
        "contract": USDT_CONTRACT,
        "limit": 5,
        "sort": "-timestamp"
    }
    try:
        response = requests.get(TRON_API, params=params, timeout=10)
        data = response.json()

        if "data" not in data:
            send_message("⚠️ Error: No transaction data received.")
            return

        for tx in data["data"]:
            if tx["event_name"] == "Transfer":
                to_address = tx["result"]["to"]
                amount = int(tx["result"]["value"]) / 1_000_000  # 6 decimals

                if to_address == WALLET_ADDRESS:
                    from_address = tx["result"]["from"]
                    tx_id = tx["transaction_id"]

                    message = (
                        f"💰 USDT Incoming!\n\n"
                        f"📥 To: {to_address}\n"
                        f"📤 From: {from_address}\n"
                        f"💵 Amount: {amount} USDT\n"
                        f"🔗 Tx: https://tronscan.org/#/transaction/{tx_id}"
                    )
                    send_message(message)

    except Exception as e:
        send_message(f"⚠️ Error checking transactions: {e}")

if __name__ == "__main__":
    # If you run manually with "test" argument, just send a test message
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        send_message("✅ Bot is running and secrets are working!")
    else:
        check_usdt_transactions()
