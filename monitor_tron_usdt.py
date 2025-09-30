# monitor_tron_usdt.py
# Read-only TRON TRC20 USDT monitor -> Telegram alerts
import os
import time
from tronpy import Tron
from tronpy.keys import is_address
import requests

# Config via environment variables (set these in GitHub Secrets)
TRON_ADDRESS = os.getenv("TRON_ADDRESS", "")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
USDT_CONTRACT = os.getenv("USDT_CONTRACT", "TLa2f6VPqDgRE67v1736s7bJ8Ray5wYjU")
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "60"))  # seconds

if not (TRON_ADDRESS and TELEGRAM_TOKEN and TELEGRAM_CHAT_ID):
    raise SystemExit("Please set TRON_ADDRESS, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID environment variables.")

tron = Tron(network='mainnet')

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text}
    try:
        r = requests.post(url, json=payload, timeout=10)
        return r.ok
    except Exception as e:
        print("Telegram send error:", e)
        return False

def get_current_block():
    st = tron.trx.get_now_block()
    return st['block_header']['raw_data']['number']

def fetch_events(from_block, to_block):
    try:
        events = tron.get_event_result(USDT_CONTRACT, event_name='Transfer',
                                       only_confirmed=True, since=from_block, to=to_block)
        return events or []
    except Exception as e:
        print("event fetch error:", e)
        return []

def normalize_event(evt):
    res = evt.get('result') if isinstance(evt, dict) and 'result' in evt else evt
    if not isinstance(res, dict):
        return None, None, None, None
    frm = res.get('_from') or res.get('from') or res.get('owner') or res.get('sender')
    to = res.get('_to') or res.get('to') or res.get('recipient')
    val = res.get('_value') or res.get('value')
    txid = evt.get('transaction_id') or evt.get('transactionHash') or evt.get('txID') or res.get('transaction')
    return frm, to, val, txid

def main():
    current = get_current_block()
    last = max(0, current - 20)
    seen = set()
    send_telegram(f"Started TRON USDT monitor for {TRON_ADDRESS} from block {last}")
    while True:
        try:
            current = get_current_block()
            events = fetch_events(last+1, current)
            for e in events:
                frm, to, val, txid = normalize_event(e)
                if not to:
                    continue
                if to == TRON_ADDRESS and txid not in seen:
                    seen.add(txid)
                    amount = int(val) / 1_000_000 if val else None
                    text = f"USDT incoming to {TRON_ADDRESS}\nFrom: {frm}\nAmount: {amount}\nTx: {txid}"
                    print(text)
                    send_telegram(text)
            last = current
        except Exception as ex:
            print("Loop error:", ex)
        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    if not is_address(TRON_ADDRESS):
        raise SystemExit("Invalid TRON address.")
    main()
