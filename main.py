import requests
import pandas as pd
import pandas_ta as ta
import time
import threading
from flask import Flask
import telegram

# === Konfigurasi ===
PAIRS = ["vra_idr", "shib_idr", "doge_idr", "trx_idr", "jasmy_idr", "sun_idr", "sundog_idr", "pepe_idr", "bnb_idr", "avax_idr", "matic_idr", "ada_idr", "dot_idr", "sol_idr", "eth_idr", "xrp_idr", "bch_idr", "ltc_idr", "bonk_idr", "floki_idr", "zrx_idr", "alt_idr", "sand_idr", "zkj_idr", "cake_idr", "fart_idr", "fanCoin_idr", "chill_idr", "token_idr", "giga_idr", "alitas_idr", "alpaca_idr", "atlas_idr", "wozx_idr", "ignis_idr", "nxt_idr", "bts_idr", "abyss_idr"]
INTERVALS = ["1m", "5m", "15m", "1h", "4h", "1d"]
TELEGRAM_TOKEN = "7950867729:AAE8KCxGgFhZMr6qUpMl1baZ8IdALf9akLk"
CHAT_ID = "1144241819"
INTERVAL_SECONDS = 60
CANDLES = 100

bot = telegram.Bot(token=TELEGRAM_TOKEN)

app = Flask(__name__)
@app.route("/")
def home():
    return "📡 Bot Analisa Tren Aktif!"

# === Ambil Data Candle ===
def fetch_ohlcv(pair, interval):
    try:
        url = f"https://indodax.com/api/{pair}_ticker"
        kline_url = f"https://indodax.com/api/chart/{pair}/{interval}"
        r = requests.get(kline_url)
        data = r.json()["chart"]
        df = pd.DataFrame(data)
        df.columns = ["timestamp", "open", "high", "low", "close", "volume"]
        df = df.astype(float)
        return df.tail(CANDLES)
    except Exception as e:
        print(f"[{pair} - {interval}] Gagal ambil data: {e}")
        return None

# === Analisa Sinyal ===
def analyze(df):
    df["rsi"] = ta.rsi(df["close"], length=14)
    macd = ta.macd(df["close"])
    df["macd"] = macd["MACD_12_26_9"]
    df["macd_signal"] = macd["MACDs_12_26_9"]
    df["ema_fast"] = ta.ema(df["close"], length=9)
    df["ema_slow"] = ta.ema(df["close"], length=21)

    last = df.iloc[-1]
    signal = None

    if last["rsi"] < 30 and last["macd"] > last["macd_signal"] and last["ema_fast"] > last["ema_slow"]:
        signal = "BUY 🔼"
    elif last["rsi"] > 70 and last["macd"] < last["macd_signal"] and last["ema_fast"] < last["ema_slow"]:
        signal = "SELL 🔽"

    return signal

# === Monitor Tiap Pair dan Interval ===
def monitor(pair, interval):
    while True:
        df = fetch_ohlcv(pair, interval)
        if df is not None:
            signal = analyze(df)
            if signal:
                msg = (
                    f"📊 Sinyal {signal}\n"
                    f"⏰ Interval: {interval}\n"
                    f"💱 Pair: {pair.upper()}\n"
                    f"📈 Harga: {df.iloc[-1]['close']}\n"
                    f"🔗 https://indodax.com/market/{pair}"
                )
                bot.send_message(chat_id=CHAT_ID, text=msg)
        time.sleep(INTERVAL_SECONDS)

# === Jalankan Semua Thread ===
for pair in PAIRS:
    for interval in INTERVALS:
        threading.Thread(target=monitor, args=(pair, interval), daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
