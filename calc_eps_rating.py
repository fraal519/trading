import pandas as pd
from datetime import datetime
import os

def calculate_eps_rating(filename):
    # Laden der CSV-Datei
    df = pd.read_csv(filename, delimiter=';')
    
    # Umwandlung der EPS-Wachstumswerte von Strings zu Floats
    for col in df.columns:
        if 'growth' in col:
            df[col] = df[col].str.replace(',', '.').astype(float)
    
    # Berechnung des gewichteten EPS-Wachstums
    df['Weighted_EPS_Growth'] = (df['EPS1-growth'] * 0.5 +
                                 df['EPS-2 growth'] * 0.25 +
                                 df['EPS-3 growth'] * 0.25)
    
    # Berechnung des EPS-Ratings (zwischen 1 und 99)
    df['EPS_Rating'] = df['Weighted_EPS_Growth'].rank(pct=True) * 98 + 1
    df['EPS_Rating'] = df['EPS_Rating'].round().astype(int)
    
    # Ausgabe der Ergebnisse
    for index, row in df.iterrows():
        print(f"Symbol: {row['Symbol']}, EPS Rating: {row['EPS_Rating']}")
    
    # Aktuelles Datum
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    # Extrahieren des Dateinamens ohne Verzeichnis und Erweiterung
    base_filename = os.path.splitext(os.path.basename(filename))[0]
    
    # Erstellen des Dateinamens für die Ausgabedatei
    output_filename = f"eps_rate_{base_filename}_{current_date}.csv"
    
    # Erstellen des vollständigen Pfads für die Ausgabedatei im gleichen Verzeichnis wie die Eingabedatei
    output_filepath = os.path.join(os.path.dirname(filename), output_filename)
    
    # Speichern der Ergebnisse in eine neue CSV-Datei
    df.to_csv(output_filepath, index=False, sep=';')
    print(f"Die Ergebnisse wurden in die Datei {output_filepath} geschrieben.")

if __name__ == "__main__":
    filename = input("Bitte geben Sie den Dateinamen ein: ")
    calculate_eps_rating(filename)
