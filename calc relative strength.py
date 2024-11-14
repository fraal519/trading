import yfinance as yf
import pandas as pd
from IPython.display import display
from datetime import datetime
import os

def calculate_relative_strength(stock):
    # Abrufen der historischen Daten der letzten 12 Monate
    hist = stock.history(period="1y")
    
    if hist.empty:
        return None, None, None
    
    # Berechnung des Startpreises und Endpreises
    start_price = hist['Close'].iloc[0]
    end_price = hist['Close'].iloc[-1]
    
    if pd.isna(start_price):  # Wenn der Startpreis NaN ist, zurückkehren
        return None, None, None
    
    # Berechnung der prozentualen Preisänderung
    price_change = (end_price - start_price) / start_price * 100  # in Prozent
    
    return start_price, end_price, price_change

def relative_strength_rating(symbols):
    price_changes = []
    
    for symbol in symbols:
        # Sicherstellen, dass das Symbol als string behandelt wird
        symbol = str(symbol).strip()
        
        if not symbol:
            continue
        
        stock = yf.Ticker(symbol)
        start_price, end_price, price_change = calculate_relative_strength(stock)
        
        if price_change is not None:
            price_changes.append((symbol, start_price, end_price, price_change))
    
    # Sortieren der Preisänderungen
    price_changes.sort(key=lambda x: x[3], reverse=True)
    
    # Berechnung der relativen Stärke
    relative_strengths = []
    for i, (symbol, start_price, end_price, price_change) in enumerate(price_changes):
        rs_rating = int(((len(price_changes) - i - 1) / len(price_changes)) * 99) + 1
        relative_strengths.append((symbol, start_price, end_price, price_change, rs_rating))
    
    # Sortieren nach relativer Stärke absteigend
    relative_strengths.sort(key=lambda x: x[4], reverse=True)
    
    return relative_strengths

# Abfrage nach dem Dateipfad der Quelldatei
source_file_path = input("Bitte den Dateipfad der Quelldatei eingeben (z.B. /Users/fraal/Downloads/stocklist DOW JONES.csv): ")

# Einlesen der Liste der Aktien aus der CSV-Datei
df = pd.read_csv(source_file_path)

# Annahme: Die Symbole befinden sich in einer Spalte namens 'Symbol'
symbols = df['Symbol'].tolist()

# Berechnen der relativen Stärke für alle Symbole
relative_strengths = relative_strength_rating(symbols)

# Entfernen der Zeilen, bei denen der Startpreis NaN ist
relative_strengths = [entry for entry in relative_strengths if entry[1] is not None]

# Ausgabe der Ergebnisse
for symbol, start_price, end_price, price_change, rs_rating in relative_strengths:
    display(f"{symbol}: Startpreis = {start_price:.2f}, Endpreis = {end_price:.2f}, Preisänderung = {price_change:.2f}%, Relative Stärke Rating = {rs_rating}")

# Aktuelles Datum im Format YYYYMMDD
current_date = datetime.now().strftime("%Y%m%d")

# Erstellen des Dateinamens für die Ausgabedatei mit 'RS_' als Prefix
output_file_name = f"RS_{source_file_path.split('/')[-1].split('.')[0]}_{current_date}.csv"

# Bestimmen des Zielverzeichnisses (hier der gleiche Ordner wie die Eingabedatei)
output_dir = os.path.dirname(source_file_path)

# Überprüfen, ob das Zielverzeichnis beschreibbar ist
if not os.access(output_dir, os.W_OK):
    print(f"Fehler: Das Verzeichnis '{output_dir}' ist schreibgeschützt oder nicht beschreibbar.")
else:
    # Erstellen des vollständigen Pfades für die Ausgabedatei
    output_file_path = os.path.join(output_dir, output_file_name)

    # Speichern der Ergebnisse in einer CSV-Datei mit aktuellem Datum und 'RS_' Prefix
    df_output = pd.DataFrame(relative_strengths, columns=['Symbol', 'Startpreis', 'Endpreis', 'Preisaenderung (%)', 'Relative Strength Rating'])
    df_output = df_output.round({'Startpreis': 2, 'Endpreis': 2, 'Preisaenderung (%)': 2})
    df_output.to_csv(output_file_path, index=False, sep=';')

    print(f"Die Ergebnisse wurden in der Datei {output_file_path} gespeichert.")