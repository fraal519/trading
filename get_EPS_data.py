import yfinance as yf
import pandas as pd
from datetime import datetime
import os

def get_earnings_history(symbol):
    try:
        # Erstellen eines Ticker-Objekts für das gegebene Symbol
        ticker = yf.Ticker(symbol)
        
        # Abrufen der Earnings-Daten
        earnings = ticker.earnings_history
        
        if earnings.empty:
            print(f"Keine Earnings-Daten für das Symbol {symbol} verfügbar.")
            return pd.DataFrame()
        
        # Konvertieren der Earnings-Daten in einen DataFrame, einschließlich des Index-Werts als Spalte
        earnings['Date'] = earnings.index
        earnings.reset_index(drop=True, inplace=True)
        
        return earnings
    except Exception as e:
        print(f"Fehler beim Abrufen der Earnings-Daten für {symbol}: {e}")
        return pd.DataFrame()

if __name__ == "__main__":
    # Abfragen des Pfads zur Eingabedatei
    input_file = input("Bitte den Pfad zur Eingabedatei eingeben: ")
    
    try:
        # Lesen der Eingabedatei
        symbols_df = pd.read_csv(input_file)
        
        # Überprüfen, ob die Spalte 'Symbol' vorhanden ist
        if 'Symbol' not in symbols_df.columns:
            print("Die Eingabedatei muss eine Spalte 'Symbol' enthalten.")
        else:
            # Erstellen eines DataFrames für die EPS-Daten
            eps_data = []
            
            for symbol in symbols_df['Symbol']:
                earnings = get_earnings_history(symbol)
                if not earnings.empty:
                    eps_actuals = earnings['epsActual'].tolist()[:4]
                else:
                    eps_actuals = [None, None, None, None]
                
                # Auffüllen mit None, falls weniger als 4 Werte vorhanden sind
                while len(eps_actuals) < 4:
                    eps_actuals.append(None)
                
                eps_data.append([symbol] + eps_actuals)
            
            # Erstellen des DataFrames mit den EPS-Daten
            eps_df = pd.DataFrame(eps_data, columns=['Symbol', 'EPS-1', 'EPS-2', 'EPS-3', 'EPS-4'])
            
            # Erstellen des Dateinamens für die Ausgabedatei
            output_dir = os.path.dirname(input_file)
            output_file_name = f"EPS_{os.path.basename(input_file).split('.')[0]}_{datetime.now().strftime('%Y%m%d')}.csv"
            output_file = os.path.join(output_dir, output_file_name)
            
            # Speichern der EPS-Daten in einer CSV-Datei
            eps_df.to_csv(output_file, index=False)
            
            print(f"EPS-Daten wurden erfolgreich in {output_file} gespeichert.")
    except FileNotFoundError:
        print(f"Die Datei {input_file} wurde nicht gefunden.")
    except pd.errors.EmptyDataError:
        print(f"Die Datei {input_file} ist leer oder ungültig.")
    except Exception as e:
        print(f"Ein Fehler ist aufgetreten: {e}")
