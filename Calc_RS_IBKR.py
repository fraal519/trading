import pandas as pd
from IPython.display import display
from datetime import datetime
import os
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from threading import Event

class IBApp(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)
        self.data = {}
        self.reqId = 0
        self.event = Event()

    def historicalData(self, reqId, bar):
        if reqId not in self.data:
            self.data[reqId] = []
        self.data[reqId].append(bar)

    def historicalDataEnd(self, reqId, start, end):
        self.event.set()

def fetch_historical_data(symbol):
    app = IBApp()
    app.connect("127.0.0.1", 4002, 0)  # Port auf 4002 geändert

    contract = Contract()
    contract.symbol = symbol
    contract.secType = "STK"
    contract.exchange = "SMART"
    contract.currency = "USD"

    app.reqId += 1
    app.reqHistoricalData(app.reqId, contract, "", "1 Y", "1 day", "MIDPOINT", 1, 1, False, [])
    
    app.event.clear()
    app.run()
    
    app.event.wait(timeout=60)
    app.disconnect()
    
    if app.reqId in app.data:
        return app.data[app.reqId]
    else:
        return None

def calculate_relative_strength(symbol):
    try:
        data = fetch_historical_data(symbol)
        
        if not data:
            return None, None, None
        
        start_price = data[0].close
        end_price = data[-1].close
        
        if pd.isna(start_price):
            return None, None, None
        
        price_change = (end_price - start_price) / start_price * 100
        
        return start_price, end_price, price_change
    except Exception as e:
        print(f"Fehler beim Abrufen von {symbol}: {e}")
        return None, None, None

def relative_strength_rating(symbols):
    price_changes = []
    
    for symbol in symbols:
        symbol = str(symbol).strip()
        
        if not symbol:
            continue
        
        start_price, end_price, price_change = calculate_relative_strength(symbol)
        
        if price_change is not None:
            price_changes.append((symbol, start_price, end_price, price_change))
    
    price_changes.sort(key=lambda x: x[3], reverse=True)
    
    relative_strengths = []
    for i, (symbol, start_price, end_price, price_change) in enumerate(price_changes):
        rs_rating = int(((len(price_changes) - i - 1) / len(price_changes)) * 99) + 1
        relative_strengths.append((symbol, start_price, end_price, price_change, rs_rating))
    
    relative_strengths.sort(key=lambda x: x[4], reverse=True)
    
    return relative_strengths

source_file_path = input("Bitte den Dateipfad der Quelldatei eingeben (z.B. /Users/fraal/Downloads/stocklist DOW JONES.csv): ")

df = pd.read_csv(source_file_path)
symbols = df['Symbol'].tolist()
relative_strengths = relative_strength_rating(symbols)
relative_strengths = [entry for entry in relative_strengths if entry[1] is not None]

for symbol, start_price, end_price, price_change, rs_rating in relative_strengths:
    display(f"{symbol}: Startpreis = {start_price:.2f}, Endpreis = {end_price:.2f}, Preisänderung = {price_change:.2f}%, Relative Stärke Rating = {rs_rating}")

current_date = datetime.now().strftime("%Y%m%d")
output_file_name = f"RS_{source_file_path.split('/')[-1].split('.')[0]}_{current_date}.csv"
output_dir = os.path.dirname(source_file_path)

if not os.access(output_dir, os.W_OK):
    print(f"Fehler: Das Verzeichnis '{output_dir}' ist schreibgeschützt oder nicht beschreibbar.")
else:
    output_file_path = os.path.join(output_dir, output_file_name)
    df_output = pd.DataFrame(relative_strengths, columns=['Symbol', 'Startpreis', 'Endpreis', 'Preisaenderung (%)', 'Relative Strength Rating'])
    df_output = df_output.round({'Startpreis': 2, 'Endpreis': 2, 'Preisaenderung (%)': 2})
    df_output.to_csv(output_file_path, index=False, sep=';')
    print(f"Die Ergebnisse wurden in der Datei {output_file_path} gespeichert.")
