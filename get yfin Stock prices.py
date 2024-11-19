import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import os
import time
from requests import Session

# Definieren der LimiterSession Klasse
class LimiterSession(Session):
    def __init__(self, rate_limit=5, interval=5):
        super().__init__()
        self.rate_limit = rate_limit
        self.interval = interval
        self.requests_count = 0
        self.start_time = time.time()

    def request(self, *args, **kwargs):
        current_time = time.time()
        elapsed = current_time - self.start_time
        if self.requests_count >= self.rate_limit and elapsed < self.interval:
            sleep_time = self.interval - elapsed
            time.sleep(sleep_time)
            self.start_time = time.time()
            self.requests_count = 0
        elif elapsed >= self.interval:
            self.start_time = time.time()
            self.requests_count = 0
        self.requests_count += 1
        return super().request(*args, **kwargs)

# Initialisieren der Session mit Rate-Limiting
session = LimiterSession(rate_limit=5, interval=5)
session.headers['User-agent'] = 'my-program/1.0'

def fetch_closing_prices(csv_file_path):
    # Lesen der Aktien-Symbole aus der CSV-Datei
    df = pd.read_csv(csv_file_path, sep=',')
    symbols = df['Symbol'].tolist()

    # Erstellen eines DataFrame für die Ergebnisse
    results = []

    # Zeitraum für die Schlusskurse (ein Jahr zurück)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)

    # Funktion zum Abrufen der Daten mit Retry-Logik
    def download_data(symbols, start_date, end_date, retries=3):
        attempt = 0
        while attempt < retries:
            try:
                tickers = yf.Tickers(symbols, session=session)
                data = tickers.history(start=start_date.strftime('%Y-%m-%d'), end=end_date.strftime('%Y-%m-%d'), interval='3mo')
                return data, tickers
            except Exception as e:
                print(f"Fehler beim Abrufen der Daten: {e}")
                time.sleep(5)  # Wartezeit vor dem nächsten Versuch
                attempt += 1
        return None, None

    # Symbole in Batches von 10 aufteilen
    batches = [symbols[i:i + 10] for i in range(0, len(symbols), 10)]

    # Abrufen der historischen Daten für alle Symbole in Intervallen von 3 Monaten
    for batch in batches:
        data, tickers = download_data(batch, start_date, end_date)
        if data is None:
            print(f"Fehler beim Abrufen der Daten für Batch: {batch} nach mehreren Versuchen.")
            continue

        # Verarbeiten der abgerufenen Daten
        for symbol in batch:
            if symbol in data.columns.levels[1]:
                try:
                    closing_prices = data['Close'][symbol].dropna()
                    last_close = round(closing_prices.iloc[-1], 2) if not closing_prices.empty else None
                    price_3mo = round(closing_prices.iloc[-2], 2) if len(closing_prices) > 1 else None
                    price_6mo = round(closing_prices.iloc[-3], 2) if len(closing_prices) > 2 else None
                    price_9mo = round(closing_prices.iloc[-4], 2) if len(closing_prices) > 3 else None
                    price_12mo = round(closing_prices.iloc[-5], 2) if len(closing_prices) > 4 else None

                    # Berechnung der prozentualen Änderungen
                    change_3mo = round(((last_close - price_3mo) / price_3mo * 100), 2) if last_close and price_3mo else None
                    change_6mo = round(((last_close - price_6mo) / price_6mo * 100), 2) if last_close and price_6mo else None
                    change_9mo = round(((last_close - price_9mo) / price_9mo * 100), 2) if last_close and price_9mo else None
                    change_12mo = round(((last_close - price_12mo) / price_12mo * 100), 2) if last_close and price_12mo else None

                    results.append({
                        "Symbol": symbol,
                        "last price": last_close,
                        "price 3mo": price_3mo,
                        "price 6mo": price_6mo,
                        "price 9mo": price_9mo,
                        "price 12mo": price_12mo,
                        "change 3mo": change_3mo,
                        "change 6mo": change_6mo,
                        "change 9mo": change_9mo,
                        "change 12mo": change_12mo,
                    })
                except Exception as e:
                    print(f"Fehler beim Verarbeiten der Daten für {symbol}: {e}")
            else:
                print(f"Keine Daten für {symbol} verfügbar")

    # Generieren des Dateinamens für die Ausgabedatei
    base_name = os.path.splitext(os.path.basename(csv_file_path))[0]
    output_file_path = os.path.join(os.path.dirname(csv_file_path), f"{base_name}_prices_{datetime.now().strftime('%Y-%m-%d')}.csv")

    # Speichern der Ergebnisse in einer CSV-Datei
    try:
        results_df = pd.DataFrame(results)
        results_df.to_csv(output_file_path, index=False, sep=';', float_format='%.2f')
    except PermissionError:
        print(f"Fehler: Keine Berechtigung zum Schreiben der Datei {output_file_path}.")
        alternative_path = input("Bitte geben Sie einen alternativen Dateipfad ein: ")
        results_df.to_csv(alternative_path, index=False, sep=';', float_format='%.2f')

if __name__ == "__main__":
    # Abfragen des Dateipfads
    csv_file_path = input("Bitte den Dateipfad der Eingabedatei eingeben: ")
    
    # Ausführen der Funktion
    fetch_closing_prices(csv_file_path)