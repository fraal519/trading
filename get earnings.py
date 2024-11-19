import yfinance as yf
import pandas as pd

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
    # Abfragen des Aktiensymbols
    symbol = input("Bitte das Aktiensymbol eingeben: ")
    
    # Ausführen der Funktion
    earnings_history_df = get_earnings_history(symbol)
    
    # Ausgabe der Ergebnisse
    if not earnings_history_df.empty:
        print(f"Earnings History für {symbol}:")
        print(earnings_history_df)
    else:
        print(f"Keine Earnings-Daten für {symbol} gefunden.")