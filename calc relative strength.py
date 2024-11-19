import pandas as pd
from IPython.display import display
from datetime import datetime
import os

def weighted_price_change(row):
    # Berechnung der gewichteten Preisänderung
    weighted_change = (row['change 3mo'] * 0.4 + 
                       row['change 6mo'] * 0.2 + 
                       row['change 9mo'] * 0.2 + 
                       row['change 12mo'] * 0.2)
    return weighted_change

def relative_strength_rating(df):
    # Berechnung der gewichteten Preisänderung
    df['Weighted Change'] = df.apply(weighted_price_change, axis=1)
    
    # Entfernen der Zeilen mit NaN-Werten in 'Weighted Change'
    df = df.dropna(subset=['Weighted Change'])
    
    # Sortieren nach gewichteter Preisänderung absteigend
    df.sort_values(by='Weighted Change', ascending=False, inplace=True)
    
    # Berechnung der relativen Stärke
    df['Relative Strength Rating'] = df['Weighted Change'].rank(ascending=False, method='min').apply(lambda x: int((len(df) - x) / len(df) * 99) + 1)
    
    # Sortieren nach relativer Stärke absteigend
    df.sort_values(by='Relative Strength Rating', ascending=False, inplace=True)
    
    return df

# Abfrage nach dem Dateipfad der Quelldatei
source_file_path = input("Bitte den Dateipfad der Quelldatei eingeben (z.B. /Users/fraal/Downloads/stocklist DOW JONES.csv): ")

# Einlesen der Liste der Aktien aus der CSV-Datei
df = pd.read_csv(source_file_path, sep=';')

# Entfernen der Zeilen mit NaN-Werten in den relevanten Spalten
df = df.dropna(subset=['last price', 'price 3mo', 'price 6mo', 'price 9mo', 'price 12mo', 'change 3mo', 'change 6mo', 'change 9mo', 'change 12mo'])

# Berechnen der relativen Stärke für alle Symbole
df = relative_strength_rating(df)

# Ausgabe der Ergebnisse
for index, row in df.iterrows():
    display(f"{row['Symbol']}: Last Price = {row['last price']:.2f}, Price 3mo = {row['price 3mo']:.2f}, Price 6mo = {row['price 6mo']:.2f}, Price 9mo = {row['price 9mo']:.2f}, Price 12mo = {row['price 12mo']:.2f}, Change 3mo = {row['change 3mo']:.2f}%, Change 6mo = {row['change 6mo']:.2f}%, Change 9mo = {row['change 9mo']:.2f}%, Change 12mo = {row['change 12mo']:.2f}%, Weighted Change = {row['Weighted Change']:.2f}%, Relative Strength Rating = {row['Relative Strength Rating']}")

# Aktuelles Datum im Format YYYYMMDD
current_date = datetime.now().strftime("%Y%m%d")

# Erstellen des Dateinamens für die Ausgabedatei mit 'RS_' als Prefix
output_file_name = f"RS_{os.path.basename(source_file_path).split('.')[0]}_{current_date}.csv"

# Bestimmen des Zielverzeichnisses (hier der gleiche Ordner wie die Eingabedatei)
output_dir = os.path.dirname(source_file_path)

# Überprüfen, ob das Zielverzeichnis beschreibbar ist
if not os.access(output_dir, os.W_OK):
    print(f"Fehler: Das Verzeichnis '{output_dir}' ist schreibgeschützt oder nicht beschreibbar.")
else:
    # Erstellen des vollständigen Pfades für die Ausgabedatei
    output_file_path = os.path.join(output_dir, output_file_name)

    # Speichern der Ergebnisse in einer CSV-Datei mit aktuellem Datum und 'RS_' Prefix
    df_output = df.round({'last price': 2, 'price 3mo': 2, 'price 6mo': 2, 'price 9mo': 2, 'price 12mo': 2, 'change 3mo': 2, 'change 6mo': 2, 'change 9mo': 2, 'change 12mo': 2, 'Weighted Change': 2})
    df_output.to_csv(output_file_path, index=False, sep=';')

    print(f"Die Ergebnisse wurden in der Datei {output_file_path} gespeichert.")
