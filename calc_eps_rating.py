import pandas as pd
from datetime import datetime
import os

def calculate_eps_rating(eps_values):
    try:
        # Konvertiere die EPS-Werte in float, falls sie als str vorliegen
        eps_values = [float(value.replace(',', '.')) if isinstance(value, str) else float(value) for value in eps_values]
        
        # Berechne die Veränderungen zwischen den EPS-Werten
        change_1 = eps_values[1] - eps_values[0]
        change_2 = eps_values[2] - eps_values[1]
        change_3 = eps_values[3] - eps_values[2]
        
        # Berechne das gewichtete EPS-Rating
        eps_rating = (change_1 * 0.4) + (change_2 * 0.3) + (change_3 * 0.3)
        
        return eps_rating
    except Exception as e:
        print(f"Fehler bei der Berechnung des EPS-Ratings: {e}")
        return None

if __name__ == "__main__":
    # Abfragen des Pfads zur Eingabedatei
    input_file = input("Bitte den Pfad zur Eingabedatei eingeben: ")
    
    try:
        # Lesen der Eingabedatei
        df = pd.read_csv(input_file, delimiter=',')
        
        # Überprüfen, ob die erforderlichen Spalten vorhanden sind
        required_columns = ['Symbol', 'EPS-1', 'EPS-2', 'EPS-3', 'EPS-4']
        if not all(column in df.columns for column in required_columns):
            print("Die Eingabedatei muss die Spalten 'Symbol', 'EPS-1', 'EPS-2', 'EPS-3' und 'EPS-4' enthalten.")
        else:
            # Ersetzen von NaN-Werten durch 0
            df.fillna(0, inplace=True)
            
            # Berechnen des EPS-Ratings für jedes Symbol
            df['EPS-Raw-Rating'] = df.apply(lambda row: calculate_eps_rating([row['EPS-1'], row['EPS-2'], row['EPS-3'], row['EPS-4']]), axis=1)
            
            # Entferne Zeilen mit None-Werten in der EPS-Raw-Rating-Spalte
            df = df.dropna(subset=['EPS-Raw-Rating'])
            
            # Sortieren der Symbole basierend auf dem EPS-Raw-Rating
            df = df.sort_values(by='EPS-Raw-Rating', ascending=False).reset_index(drop=True)
            
            # Berechnen des EPS-Ratings auf einer Skala von 1 bis 99
            df['EPS-Rating'] = df.index.map(lambda x: round((x + 1) / len(df) * 99))
            
            # Entfernen der EPS-Raw-Rating-Spalte
            df = df.drop(columns=['EPS-Raw-Rating'])
            
            # Sortieren der Ergebnisse nach EPS-Rating absteigend
            df = df.sort_values(by='EPS-Rating', ascending=False).reset_index(drop=True)
            
            # Erstellen des Dateinamens für die Ausgabedatei
            output_dir = os.path.dirname(input_file)
            output_file_name = f"EPS_rate_{os.path.basename(input_file).split('.')[0]}_{datetime.now().strftime('%Y%m%d')}.csv"
            output_file = os.path.join(output_dir, output_file_name)
            
            # Speichern der EPS-Ratings in einer CSV-Datei
            df.to_csv(output_file, index=False, sep=',')
            
            print(f"EPS-Ratings wurden erfolgreich in {output_file} gespeichert.")
    except FileNotFoundError:
        print(f"Die Datei {input_file} wurde nicht gefunden.")
    except pd.errors.EmptyDataError:
        print(f"Die Datei {input_file} ist leer oder ungültig.")
    except Exception as e:
        print(f"Ein Fehler ist aufgetreten: {e}")
