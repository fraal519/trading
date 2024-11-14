import yfinance as yf
import pandas as pd
import numpy as np
from IPython.display import display

def calculate_relative_strength(stock):
    # Abrufen der historischen Daten der letzten 12 Monate
    hist = stock.history(period="1y")
    
    if hist.empty:
        return None
    
    # Berechnung der prozentualen Preisänderung
    price_change = (hist['Close'].iloc[-1] - hist['Close'].iloc[0]) / hist['Close'].iloc[0]
    return price_change

def relative_strength_rating(symbols):
    price_changes = []
    
    for symbol in symbols:
        stock = yf.Ticker(symbol)
        price_change = calculate_relative_strength(stock)
        
        if price_change is not None:
            price_changes.append((symbol, price_change))
    
    # Sortieren der Preisänderungen
    price_changes.sort(key=lambda x: x[1], reverse=True)
    
    # Berechnung der relativen Stärke
    relative_strengths = []
    for i, (symbol, price_change) in enumerate(price_changes):
        rs_rating = int(((len(price_changes) - i - 1) / len(price_changes)) * 99) + 1
        relative_strengths.append((symbol, rs_rating))
    
    # Sortieren nach relativer Stärke absteigend
    relative_strengths.sort(key=lambda x: x[1], reverse=True)
    
    return relative_strengths

# Einlesen der Liste der Aktien aus der CSV-Datei
file_path = "C:\\Users\\Q274152\\Downloads\\sp500_companies.csv"
df = pd.read_csv(file_path)

# Annahme: Die Symbole befinden sich in einer Spalte namens 'Symbol'
symbols = df['Symbol'].tolist()

# Berechnung der relativen Stärke
relative_strengths = relative_strength_rating(symbols)

# Ausgabe der Ergebnisse
for symbol, rs_rating in relative_strengths:
    display(f"{symbol}: Relative Stärke Rating = {rs_rating}")

# Speichern der Ergebnisse in einer CSV-Datei
output_file_path = "C:\\Users\\Q274152\\Downloads\\RS_SP500.csv"
df_output = pd.DataFrame(relative_strengths, columns=['Symbol', 'Relative Strength Rating'])
df_output.to_csv(output_file_path, index=False)

print(f"Die Ergebnisse wurden in der Datei {output_file_path} gespeichert.")