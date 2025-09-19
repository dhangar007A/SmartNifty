from SmartApi import SmartConnect
import SharedArray as sa
import pandas as pd

import os, requests, shutil
import pyotp, json
import warnings

warnings.filterwarnings("ignore")

parent = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
tickers = os.path.join(parent, "tickers")

pd.set_option('display.max_rows', 500)

def ClearFolder(path):
    shutil.rmtree(path, ignore_errors=True)
    os.makedirs(path, exist_ok=True)

class TickerGenerator:
    def __init__(self, TokenURL):
        self.TokenURL = TokenURL
        self.df = self.PrepareDF()

    def PrepareDF(self):
        try :
            response = requests.get(self.TokenURL)
            JSON = json.loads(response.text)
            df = pd.DataFrame(JSON)

            mask1 = (df['name'].isin(["NIFTY"])) 
            df = df[mask1]

            mask2 = (df["exch_seg"].isin(["NSE", "NFO"])) 
            df = df[mask2]

            mask3 = (df["instrumenttype"].isin(["AMXIDX", "FUTIDX", "OPTIDX"])) 
            df = df[mask3]

            dataType = {'token': int, 'strike': float, 'lotsize': float, 'tick_size': float}
            df = df.apply(lambda col: col.astype(dataType[col.name]) if col.name in dataType else col)

            df["option"] = df["symbol"].apply(lambda x: x[-2:] if isinstance(x, str) else "")
            df["expiry"] = pd.to_datetime(df["expiry"], errors="coerce")
            df["strike"] = pd.to_numeric(df["strike"], errors="coerce").fillna(0).astype(int) // 100

            df["expiry"] = df["expiry"].fillna(pd.to_datetime(df["expiry"].min()))

            mask4 = (df["instrumenttype"].isin(["AMXIDX", "FUTIDX"]))
            df1 = df[mask4]

            expiry = df["expiry"].value_counts()
            expiry = list(expiry[expiry > 100].index)
            df2 = df[df["expiry"].isin(expiry)]

            mask5 = (df["instrumenttype"].isin(["OPTIDX"]))
            df2 = df2[mask5]

            df = pd.DataFrame()
            for i in [df1, df2]:
                i["expiry"] = i["expiry"].dt.date
                df = pd.concat([df, i], ignore_index=True)

            df = df[["strike", "option", "token", "expiry"]]
            df = df.sort_values(by=["strike", "option", "token", "expiry"])

            df.to_csv(os.path.join(parent, "Ticker.csv"), index=False)
            return df

        except requests.exceptions.RequestException as e:
            print(f"Error fetching URL: {e}")

    def PrepareTicker(self):
        ClearFolder("logs")
        ClearFolder(tickers)

        tokens = self.df['token'].tolist()
        
        size = 5000
        dtype = 'float64'
        for token in tokens:
            path = f"file://{os.path.join(tickers, str(token))}"
            try:
                sa.create(path, size, dtype=dtype)
            except FileExistsError:
                print(f"Ticker for token {token} already exists. Skipping.")
            except Exception as e:
                print(f"Error creating ticker for token {token}: {e}")

class SessionGenerator(TickerGenerator):
    def __init__(self, TokenURL, API_KEY):
        super().__init__(TokenURL)

        self.API_KEY = API_KEY
        self.Angel = SmartConnect(API_KEY)
        self.AUTH_TOKEN = self.FEED_TOKEN = None

    def GenerateSession(self, CLIENT_CODE, PASSWORD, TOTP_SECRET):
        super().PrepareTicker()

        session = self.Angel.generateSession(CLIENT_CODE, PASSWORD, pyotp.TOTP(TOTP_SECRET).now())
        self.AUTH_TOKEN = session["data"]["jwtToken"]
        self.FEED_TOKEN = session["data"]["feedToken"]
