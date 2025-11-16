import shioaji as sj
from shioaji import TickSTKv1, Exchange
import time
import os
from dotenv import load_dotenv

api = sj.Shioaji(simulation=True)   # simulation=True 即表示使用模擬環境
accounts =  api.login("DjfiMXMcmwgGeG7752TSKxZggAXJWnPpozUTgFgabmAG", "CEyt2NQcotntHiyMc6nAciApu2iTSxhzMN3fJ5T13UAX")
api.activate_ca(
    ca_path="./Sinopac.pfx",
    ca_passwd="L124793253",
    person_id="L124793253",
)


print("Login and activate CA success")

# Define callback function for real-time quotes
@api.on_tick_stk_v1()
def quote_callback(exchange: Exchange, tick: TickSTKv1):
    # print(tick)
    print(f"Exchange: {exchange}")
    print(f"Code: {tick.code}")
    print(f"Price: {tick.close}")
    print(f"Volume: {tick.volume}")
    print(f"Time: {tick.datetime}")
    print("-" * 50)

# Subscribe to 2330 (TSMC) real-time quotes
# api.quote.subscribe(
#     api.Contracts.Stocks["2330"],
#     quote_type=sj.constant.QuoteType.Tick,
#     version=sj.constant.QuoteVersion.v1
# )

# Subscribe to different futures contracts
# TXF = 台指期貨 (Taiwan Stock Index Futures)
# api.quote.subscribe(
#     api.Contracts.Futures.TXF['TXFR1'],  # TXFR1 = nearest month contract
#     quote_type = sj.constant.QuoteType.Tick,
#     version = sj.constant.QuoteVersion.v1,
# )

# MXF = 小台指期貨 (Mini Taiwan Stock Index Futures)
api.quote.subscribe(
    api.Contracts.Futures.TXF['TXFR1'],  # 2025年11月小台指
    quote_type = sj.constant.QuoteType.Tick,
    version = sj.constant.QuoteVersion.v1,
)

# TGF = 電子期貨 (Electronic Sector Index Futures)
# api.quote.subscribe(
#     api.Contracts.Futures.TGF['TGF202512'],  # 2025年12月電子期
#     quote_type = sj.constant.QuoteType.Tick,
#     version = sj.constant.QuoteVersion.v1,
# )

# # TJF = 金融期貨 (Finance Sector Index Futures)
# api.quote.subscribe(
#     api.Contracts.Futures.TJF['TJF202511'],  # 2025年11月金融期
#     quote_type = sj.constant.QuoteType.Tick,
#     version = sj.constant.QuoteVersion.v1,
# )


print("Starting to receive 2330 real-time quotes...")
print("Press Ctrl+C to stop")

# Keep the program running to receive real-time data
try:
    while True:
        time.sleep(.5)  # Sleep in short intervals to allow Ctrl+C to work
except KeyboardInterrupt:
    print("\nStopping quote reception")
    api.logout()
    print("Logged out successfully")