from SmartApi.smartWebSocketV2 import SmartWebSocketV2
from dotenv import load_dotenv
from logzero import logger

from concurrent.futures import ThreadPoolExecutor
import json, threading, os, queue, struct, mmap
import numpy as np

from Session import SessionGenerator

correlation_id = "abc123"
mode = 3

load_dotenv()

class DataFeeder(SessionGenerator):
    def __init__(self, TokenURL, API_KEY,  CLIENT_CODE):
        super().__init__(TokenURL, API_KEY)
        self.CLIENT_CODE = CLIENT_CODE

    def PrepareQueueList(self, PASSWORD, TOTP_SECRET):
        super().GenerateSession(self.CLIENT_CODE, PASSWORD, TOTP_SECRET)

        df1 = self.df[self.df["option"] == "50"]
        Token1 = list(map(str, df1["token"].tolist()))

        df2 = self.df[self.df["option"] == "UT"]
        Token2 = list(map(str, df2["token"].tolist()))
        
        df3 = self.df[self.df["option"].isin(["CE", "PE"])]
        Token3 = list(map(str, df3["token"].tolist()))

        token_list1 = [
            {
                "exchangeType": 1, 
                "tokens": Token1
            }
        ]

        token_list2 = [
            {
                "exchangeType": 2, 
                "tokens": Token2
            }
        ]

        token = []
        token.append(token_list1)
        token.append(token_list2)

        array = np.array_split(np.array(Token3), 10)
        for i in array :
            token_list = [
                {
                    "exchangeType": 2, 
                    "tokens": i.tolist()
                }
            ]

            token.append(token_list)

        q = queue.Queue()
        return token, q
    
    def SendData(self, PASSWORD, TOTP_SECRET):
        token, Queue = self.PrepareQueueList(PASSWORD, TOTP_SECRET)

        sws = SmartWebSocketV2(self.AUTH_TOKEN, self.API_KEY, self.CLIENT_CODE, self.FEED_TOKEN)

        def on_data(wsapp, message):
            Queue.put(message)

        def on_open(wsapp):
            logger.info("WebSocket Open")
            for i in token :
                sws.subscribe(correlation_id, mode, i)

        def on_error(wsapp, error):
            logger.error(f"WebSocket Error: {repr(error)}")

        def on_close(wsapp):
            logger.warning("WebSocket Closed")

        sws.on_open = on_open
        sws.on_data = on_data
        sws.on_error = on_error
        sws.on_close = on_close

        def consumer_thread(q, tickers_dir):
            while True:
                try:
                    message = q.get()
                    token = message.get('token')
                    if not token:
                        continue
                        
                    print(token)
                    path = os.path.join(tickers_dir, str(token))
                    if not os.path.exists(path):
                        continue
                        
                    v0 = float(message.get('exchange_timestamp', 0))
                    v1 = float(message.get('last_traded_price', 0))
                    v2 = float(message.get('closed_price', 0))
                    v3 = float(message.get('volume_trade_for_the_day', 0))
                    v4 = float(message.get('open_interest', 0))
                    v5 = float(message.get('total_buy_quantity', 0))
                    v6 = float(message.get('total_sell_quantity', 0))
                    
                    with open(path, "r+b") as f:
                        with mmap.mmap(f.fileno(), 0) as mm:
                            struct.pack_into('ddddddd', mm, 0, v0, v1, v2, v3, v4, v5, v6)
                except Exception as e:
                    print(f"Error processing tick: {e}")

        logger.info("Starting consumer thread...")
        parent = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        tickers_dir = os.path.join(parent, "tickers")
        threading.Thread(target=consumer_thread, args=(Queue, tickers_dir), daemon=True).start()

        logger.info("Connecting to WebSocket...")
        threading.Thread(target=sws.connect).start()

TokenURL = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"

API_KEY = os.getenv("API_KEY")
PASSWORD = os.getenv("PASSWORD")
TOTP_SECRET = os.getenv("TOKEN")
CLIENT_CODE = os.getenv("CLIENT_CODE")

if __name__ == "__main__":
    DF = DataFeeder(TokenURL, API_KEY, CLIENT_CODE)
    DF.SendData(PASSWORD, TOTP_SECRET)