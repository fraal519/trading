import pandas as pd
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from threading import Event
import time
from datetime import datetime, timedelta

class IBApp(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)
        self.closing_prices = {}
        self.reqId = 1
        self.data_event = Event()

    def error(self, reqId, errorCode, errorString):
        print(f"Error {reqId}, Code: {errorCode}, Msg: {errorString}")

    def historicalData(self, reqId, bar):
        self.closing_prices[reqId] = bar.close
        self.data_event.set()

    def historicalDataEnd(self, reqId, start, end):
        self.data_event.set()

def fetch_closing_prices(csv_file_path, output_file_path):
    # Lesen der Aktien-Symbole aus der CSV-Datei
    df = pd.read_csv(csv_file_path)
    symbols = df['Symbol'].tolist()

    # Erstellen einer Instanz der IBApp
    app = IBApp()
    app.connect("127.0.0.1", 4002, clientId=1)

    # Warten, bis die Verbindung hergestellt ist
    time.sleep(1)

    # Erstellen eines DataFrame für die Ergebnisse
    results = []

    # Abrufen der Schlusskurse für jedes Symbol
    for symbol in symbols:
        contract = Contract()
        contract.symbol = symbol
        contract.secType = "STK"
        contract.exchange = "SMART"
        contract.currency = "USD"

        closing_prices = {}

        # Zeitpunkte für die Schlusskurse
        time_points = {
            "last_close": "",
            "3_months_ago": (datetime.now() - timedelta(days=90)).strftime("%Y%m%d %H:%M:%S"),
            "6_months_ago": (datetime.now() - timedelta(days=180)).strftime("%Y%m%d %H:%M:%S"),
            "9_months_ago": (datetime.now() - timedelta(days=270)).strftime("%Y%m%d %H:%M:%S"),
            "12_months_ago": (datetime.now() - timedelta(days=360)).strftime("%Y%m%d %H:%M:%S")
        }

        for key, time_point in time_points.items():
            app.data_event.clear()
            app.reqHistoricalData(app.reqId, contract, time_point, "1 D", "1 day", "MIDPOINT", 1, 1, False, [])
            app.data_event.wait(timeout=10)

            if app.reqId in app.closing_prices:
                closing_prices[key] = app.closing_prices[app.reqId]
            else:
                closing_prices[key] = None

            app.reqId += 1

        results.append({
            "Symbol": symbol,
            "Last Close": closing_prices.get("last_close"),
            "Close 3 Months Ago": closing_prices.get("3_months_ago"),
            "Close 6 Months Ago": closing_prices.get("6_months_ago"),
            "Close 9 Months Ago": closing_prices.get("9_months_ago"),
            "Close 12 Months Ago": closing_prices.get("12_months_ago")
        })

    # Trennen der Verbindung
    app.disconnect()

    # Speichern der Ergebnisse in einer CSV-Datei
    results_df = pd.DataFrame(results)
    results_df.to_csv(output_file_path, index=False)

# Beispielaufruf der Funktion
csv_file_path = input("Bitte den Dateipfad der CSV-Datei eingeben: ")
output_file_path = input("Bitte den Dateipfad der Ausgabedatei eingeben: ")
fetch_closing_prices(csv_file_path, output_file_path)
