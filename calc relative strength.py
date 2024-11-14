import yfinance as yf
import pandas as pd
import numpy as np
from IPython.display import display
from datetime import datetime

def calculate_relative_strength(stock):
    # Abrufen der historischen Daten der letzten 12 Monate
    hist = stock.history(period="1y")
    
    if hist.empty:
        return None, None, None
    
    # Berechnung der prozentualen Preisänderung
    start_price = hist['Close'].iloc[0]
    end_price = hist['Close'].iloc[-1]
    price_change = (end_price - start_price) / start_price * 100  # in Prozent
    
    return start_price, end_price, price_change

def relative_strength_rating(symbols):
    price_changes = []
    
    for symbol in symbols:
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

# Einlesen der Liste der Aktien aus der CSV-Datei
file_path = "C:\\Users\\Q274152\\Downloads\\sp500_companies.csv"
df = pd.read_csv(file_path)

# Annahme: Die Symbole befinden sich in einer Spalte namens 'Symbol'
symbols = df['Symbol'].tolist()

# Berechnung der relativen Stärke
relative_strengths = relative_strength_rating(symbols)

# Ausgabe der Ergebnisse
for symbol, start_price, end_price, price_change, rs_rating in relative_strengths:
    display(f"{symbol}: Startpreis = {start_price:.2f}, Endpreis = {end_price:.2f}, Preisänderung = {price_change:.2f}%, Relative Stärke Rating = {rs_rating}")

# Aktuelles Datum im Format YYYYMMDD
current_date = datetime.now().strftime("%Y%m%d")

# Speichern der Ergebnisse in einer CSV-Datei mit aktuellem Datum im Dateinamen
output_file_path = f"C:\\Users\\Q274152\\Downloads\\RS_SP500_{current_date}.csv"
df_output = pd.DataFrame(relative_strengths, columns=['Symbol', 'Startpreis', 'Endpreis', 'Preisänderung (%)', 'Relative Strength Rating'])
df_output = df_output.round({'Startpreis': 2, 'Endpreis': 2, 'Preisänderung (%)': 2})
df_output.to_csv(output_file_path, index=False, sep=';')

print(f"Die Ergebnisse wurden in der Datei {output_file_path} gespeichert.")